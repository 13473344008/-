//go:build t9_validation

package service

import (
	"encoding/json"
	"fmt"
	"github.com/google/uuid"
	"go-admin/app/passport/models"
	"go-admin/app/passport/publishing"
	"go-admin/app/passport/service/dto"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"os"
	"testing"
)

func TestT9FaultRecovery(t *testing.T) {
	dbpath := os.Getenv("T9_TEST_DB")
	fixtures := os.Getenv("T9_FIXTURES")
	if dbpath == "" || fixtures == "" {
		t.Fatal("dedicated T9 paths required")
	}
	db, e := gorm.Open(sqlite.Open("file:"+dbpath+"?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL"), &gorm.Config{Logger: logger.Default.LogMode(logger.Silent)})
	if e != nil {
		t.Fatal(e)
	}
	pool, _ := db.DB()
	pool.SetMaxOpenConns(1)
	defer pool.Close()
	s := Publishing{}
	s.Orm = db
	s.Actor = 1
	s.Admin = true
	raw, e := os.ReadFile(fixtures)
	if e != nil {
		t.Fatal(e)
	}
	var f struct {
		Faults map[string]struct {
			BatchID string         `json:"batch_id"`
			Request PublishRequest `json:"request"`
		} `json:"faults"`
	}
	if e = json.Unmarshal(raw, &f); e != nil {
		t.Fatal(e)
	}
	var editor, reviewer int
	db.Table("sys_user u").Joins("JOIN sys_role r ON r.role_id=u.role_id").Where("r.role_key='passport_editor'").Select("u.user_id").Order("u.user_id DESC").Limit(1).Scan(&editor)
	db.Table("sys_user u").Joins("JOIN sys_role r ON r.role_id=u.role_id").Where("r.role_key='passport_reviewer'").Select("u.user_id").Order("u.user_id DESC").Limit(1).Scan(&reviewer)
	for _, stage := range []string{"build", "write", "copy1", "copy2", "validation", "rename", "finalize"} {
		t.Run(stage, func(t *testing.T) {
			must := func(e error) {
				t.Helper()
				if e != nil {
					t.Fatal(e)
				}
			}
			fixture := f.Faults[stage]
			v1, e := s.Publish(fixture.BatchID, fixture.Request)
			must(e)
			if v1.Record.PublishStatus != "published" {
				t.Fatalf("V1 failed: %+v", v1)
			}
			store, e := publishing.OpenStore(os.Getenv("PASSPORT_PUBLISH_ROOT"), os.Getenv("PASSPORT_RELEASE_WORK_ROOT"))
			must(e)
			defer store.Close()
			var candidate ReviewCandidate
			must(json.Unmarshal([]byte(v1.Revision.FrozenInput), &candidate))
			old, e := store.Current(candidate.Batch.BatchCode)
			must(e)
			// Explicit local fixture only: opens a new review after V1 without exposing the deferred T10 transition in production APIs.
			must(db.Model(&models.Batch{}).Where("id=?", fixture.BatchID).Updates(map[string]interface{}{"workflow_status": "draft", "current_review_record_id": nil, "submitted_input": nil, "submitted_content_hash": nil, "submitted_preview_hash": nil, "submitted_edit_version": nil, "submitted_schema_version": nil, "submitted_builder_version": nil, "submitted_by": nil, "submitted_at": nil, "reviewed_by": nil, "reviewed_at": nil}).Error)
			var b models.Batch
			must(db.Where("id=?", fixture.BatchID).Take(&b).Error)
			rs := s.Reviews
			rs.Actor = editor
			rid, e := rs.Submit(b.ID, dto.SubmitReview{ExpectedEditVersion: b.EditVersion})
			must(e)
			var review models.ReviewRecord
			must(db.Where("id=?", rid).Take(&review).Error)
			rs.Actor = reviewer
			must(rs.Decide(b.ID, "approved", dto.DecideReview{ReviewID: rid, CandidateHash: review.CandidateHash}))
			req := PublishRequest{ReviewID: rid, CandidateHash: review.CandidateHash, IdempotencyKey: uuid.NewString(), ExpectedCurrentRevisionID: &v1.Revision.ID}
			want := stage
			if stage == "copy1" {
				want = "copy:1"
			}
			if stage == "copy2" {
				want = "copy:2"
			}
			s.Fault = func(got string) error {
				if got == want {
					return fmt.Errorf("injected %s", want)
				}
				return nil
			}
			failed, e := s.Publish(b.ID, req)
			must(e)
			s.Fault = nil
			head, e := store.Current(candidate.Batch.BatchCode)
			must(e)
			status, e := s.Status(b.ID)
			must(e)
			if status.Current.ID != v1.Revision.ID {
				t.Fatal("failed operation changed DB head")
			}
			history, e := publishing.ReadRegular(store.Public, *v1.Revision.SnapshotPath, publishing.MaxPayloadBytes)
			must(e)
			if string(history) != string(old) {
				t.Fatal("historical V1 changed")
			}
			if stage == "finalize" {
				if failed.Record.PublishStatus != "recovery_required" || string(head) == string(old) {
					t.Fatal("postrename state incorrect")
				}
				req.IdempotencyKey = uuid.NewString()
				if _, e = s.Publish(b.ID, req); e == nil {
					t.Fatal("uncertain operation allowed retry")
				}
				recovered, e := s.Reconcile(b.ID)
				must(e)
				if recovered.Record.ID != failed.Record.ID || recovered.Record.PublishStatus != "published" {
					t.Fatal("recovery did not complete same operation")
				}
			} else {
				if failed.Record.PublishStatus != "failed" || string(head) != string(old) {
					t.Fatal("pre-switch fault changed head")
				}
				req.IdempotencyKey = uuid.NewString()
				retry, e := s.Publish(b.ID, req)
				must(e)
				if retry.Record.PublishStatus != "published" || retry.Record.ID == failed.Record.ID || retry.Revision.VersionNumber <= failed.Revision.VersionNumber {
					t.Fatal("new retry attempt/version missing")
				}
			}
			final, e := s.Status(b.ID)
			must(e)
			if final.Current.ID == v1.Revision.ID || final.ActiveRecordID != nil {
				t.Fatal("final state")
			}
			history, e = publishing.ReadRegular(store.Public, *v1.Revision.SnapshotPath, publishing.MaxPayloadBytes)
			must(e)
			if string(history) != string(old) {
				t.Fatal("V1 overwritten by later version")
			}
		})
	}
}
