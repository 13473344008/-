//go:build t10_validation

package service

import (
	"encoding/json"
	"fmt"
	"github.com/google/uuid"
	"go-admin/app/passport/models"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"os"
	"testing"
)

func TestT10RollbackFaults(t *testing.T) {
	root := os.Getenv("T10_RUNTIME")
	if root == "" {
		t.Fatal("isolated T10 runtime required")
	}
	db, e := gorm.Open(sqlite.Open("file:"+root+"/db/passport-admin-t10.db?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL"), &gorm.Config{Logger: logger.Default.LogMode(logger.Silent)})
	if e != nil {
		t.Fatal(e)
	}
	pool, _ := db.DB()
	pool.SetMaxOpenConns(1)
	defer pool.Close()
	s := Publishing{}
	s.Orm = db
	s.Admin = true
	s.Actor = 1
	raw, e := os.ReadFile(root + "/test-artifacts/history-fixtures.json")
	if e != nil {
		t.Fatal(e)
	}
	var f struct {
		Faults map[string]struct {
			BatchID string `json:"batch_id"`
			Target  string `json:"target"`
		} `json:"faults"`
	}
	if e = json.Unmarshal(raw, &f); e != nil {
		t.Fatal(e)
	}
	for _, stage := range []string{"build", "validation", "manifest", "asset", "rename", "finalize"} {
		t.Run(stage, func(t *testing.T) {
			must := func(e error) {
				t.Helper()
				if e != nil {
					t.Fatal(e)
				}
			}
			fixture := f.Faults[stage]
			var b models.Batch
			must(db.Where("id=?", fixture.BatchID).Take(&b).Error)
			old, e := os.ReadFile(root + "/publish/published/" + b.BatchCode + ".json")
			must(e)
			s.Fault = func(got string) error {
				if got == stage {
					return fmt.Errorf("injected %s", stage)
				}
				return nil
			}
			failed, e := s.Rollback(b.ID, RollbackRequest{TargetRevisionID: fixture.Target, ExpectedCurrentRevisionID: b.CurrentPassportRevisionID, IdempotencyKey: uuid.NewString(), RollbackReason: "T10 controlled " + stage + " failure"})
			must(e)
			s.Fault = nil
			actual, e := os.ReadFile(root + "/publish/published/" + b.BatchCode + ".json")
			must(e)
			status, e := s.Status(b.ID)
			must(e)
			if status.Current.ID != *b.CurrentPassportRevisionID {
				t.Fatal("failure moved DB head")
			}
			if stage == "finalize" {
				if failed.Record.PublishStatus != "recovery_required" || string(actual) == string(old) {
					t.Fatal("post-switch state incorrect")
				}
				h, e := s.Health(b.ID)
				must(e)
				if h.Classification != "file_switched_db_pending" {
					t.Fatalf("health %+v", h)
				}
				if _, e = s.Rollback(b.ID, RollbackRequest{TargetRevisionID: fixture.Target, ExpectedCurrentRevisionID: b.CurrentPassportRevisionID, IdempotencyKey: uuid.NewString(), RollbackReason: "must block"}); e == nil {
					t.Fatal("unresolved operation allowed rollback")
				}
				recovered, e := s.ReconcileReason(b.ID, "Finalize verified interrupted rollback")
				must(e)
				if recovered.Record.ID != failed.Record.ID || recovered.Record.PublishStatus != "published" {
					t.Fatal("reconcile lost original attempt")
				}
			} else {
				if failed.Record.PublishStatus != "failed" || string(actual) != string(old) {
					t.Fatal("pre-switch failure damaged head")
				}
				retry, e := s.Rollback(b.ID, RollbackRequest{TargetRevisionID: fixture.Target, ExpectedCurrentRevisionID: b.CurrentPassportRevisionID, IdempotencyKey: uuid.NewString(), RollbackReason: "Retry failed rollback as new version"})
				must(e)
				if retry.Record.PublishStatus != "published" || retry.Revision.VersionNumber <= failed.Revision.VersionNumber {
					t.Fatal("retry reused version or failed")
				}
			}
			hist, e := s.History(b.ID, "")
			must(e)
			seenFail, seenSuccess := false, false
			for _, a := range hist.Audit {
				if a.EventType == "rollback_failed" || a.EventType == "rollback_reconcile_required" {
					seenFail = true
				}
				if a.EventType == "rollback_succeeded" {
					seenSuccess = true
				}
			}
			if !seenFail || !seenSuccess || len(hist.Attempts) != 3 && stage != "finalize" {
				t.Fatal("failure history missing")
			}
			v, e := s.Version(b.ID, fixture.Target)
			must(e)
			if v.Integrity.State != "verified" {
				t.Fatal("source no longer verified")
			}
		})
	}
}

func TestT10OperationLockAndLiveServiceRole(t *testing.T) {
	root := os.Getenv("T10_RUNTIME")
	if root == "" {
		t.Fatal("T10 runtime required")
	}
	db, e := gorm.Open(sqlite.Open("file:"+root+"/db/passport-admin-t10.db?_foreign_keys=on&_busy_timeout=5000"), &gorm.Config{Logger: logger.Default.LogMode(logger.Silent)})
	if e != nil {
		t.Fatal(e)
	}
	pool, _ := db.DB()
	defer pool.Close()
	var b models.Batch
	if e = db.Where("workflow_status='published' AND active_publish_record_id IS NULL").First(&b).Error; e != nil {
		t.Fatal(e)
	}
	s := Publishing{}
	s.Orm = db
	s.Actor = 1
	s.Admin = true
	st, e := openPublicationStore()
	if e != nil {
		t.Fatal(e)
	}
	defer st.Close()
	unlock, e := st.Lock(b.ID)
	if e != nil {
		t.Fatal(e)
	}
	defer unlock()
	q := RollbackRequest{TargetRevisionID: *b.CurrentPassportRevisionID, ExpectedCurrentRevisionID: b.CurrentPassportRevisionID, IdempotencyKey: uuid.NewString(), RollbackReason: "Lock verification"}
	for _, name := range []string{"publish", "rollback", "reconcile"} {
		t.Run(name, func(t *testing.T) {
			var e error
			switch name {
			case "publish":
				_, e = s.Publish(b.ID, PublishRequest{IdempotencyKey: uuid.NewString()})
			case "rollback":
				_, e = s.Rollback(b.ID, q)
			case "reconcile":
				_, e = s.ReconcileReason(b.ID, "Lock verification")
			}
			if e == nil {
				t.Fatal("OS lock bypassed")
			}
		})
	}
	for _, role := range []string{"passport_editor", "passport_reviewer", "passport_viewer"} {
		t.Run(role, func(t *testing.T) {
			var actor int
			if e := db.Table("sys_user u").Joins("JOIN sys_role r ON r.role_id=u.role_id").Where("r.role_key=?", role).Select("u.user_id").Limit(1).Scan(&actor).Error; e != nil || actor == 0 {
				t.Fatal("role missing")
			}
			s.Actor = actor
			s.Admin = true
			_, e := s.Rollback(b.ID, q)
			be, ok := e.(*BusinessError)
			if !ok || be.Code != 403 {
				t.Fatalf("live service role bypass: %v", e)
			}
		})
	}
}
