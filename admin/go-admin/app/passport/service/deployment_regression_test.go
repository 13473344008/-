package service

import (
	"github.com/google/uuid"
	"go-admin/app/passport/models"
	"go-admin/app/passport/service/dto"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Uses only an explicitly supplied OFFLINE disposable database copy.
func TestDeploymentBatchWorkflow(t *testing.T) {
	path := os.Getenv("T13_OFFLINE_TEST_DB")
	if path == "" {
		t.Skip("dedicated offline fixture required")
	}
	db, e := gorm.Open(sqlite.Open("file:"+path+"?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL"), &gorm.Config{Logger: logger.Default.LogMode(logger.Silent)})
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
	must := func(e error) {
		t.Helper()
		if e != nil {
			t.Fatal(e)
		}
	}
	root, e := filepath.EvalSymlinks(t.TempDir())
	must(e)
	for _, d := range []string{"published", "work", "media"} {
		must(os.Mkdir(filepath.Join(root, d), 0700))
	}
	t.Setenv("PASSPORT_PUBLISH_ROOT", filepath.Join(root, "published"))
	t.Setenv("PASSPORT_RELEASE_WORK_ROOT", filepath.Join(root, "work"))
	t.Setenv("PASSPORT_PRIVATE_MEDIA_ROOT", filepath.Join(root, "media"))
	// Previously approved malformed test data is rejected before allocating another release.
	var legacy models.Batch
	if db.Where("record_type='test' AND instr(batch_code,'TEST')=0 AND current_review_record_id IS NOT NULL AND current_passport_revision_id IS NULL").First(&legacy).Error == nil {
		ready, e := s.Readiness(legacy.ID)
		must(e)
		found := false
		for _, issue := range ready.Errors {
			found = found || issue.Code == "invalid_test_batch_code"
		}
		if !found {
			t.Fatal("legacy readiness missed invalid TEST code")
		}
		var r models.ReviewRecord
		must(db.Where("id=?", *legacy.CurrentReviewRecordID).Take(&r).Error)
		var before, after int64
		db.Model(&models.PublishRecord{}).Count(&before)
		_, e = s.Publish(legacy.ID, PublishRequest{ReviewID: r.ID, CandidateHash: r.CandidateHash, IdempotencyKey: uuid.NewString()})
		if e == nil || !strings.Contains(e.Error(), "TEST") {
			t.Fatalf("legacy publish error: %v", e)
		}
		db.Model(&models.PublishRecord{}).Count(&after)
		if before != after {
			t.Fatal("invalid legacy publish allocated release")
		}
	} else {
		t.Fatal("fixture missing approved malformed test batch")
	}
	pid, e := s.Create(dto.CreateProductRequest{ProductCode: "T13-" + uuid.NewString(), Content: dto.RevisionContent{SourceLanguage: "en", ProcessSteps: []dto.Step{}}, Translations: []dto.TranslationRequest{{LanguageCode: "en", TranslationStatus: "approved", ProductName: "Deployment TEST", ProcessLabels: map[string]string{}}}})
	must(e)
	p, e := s.Get(pid)
	must(e)
	rid := p.Revisions[0].ID
	rv, e := s.GetRevision(pid, rid)
	must(e)
	must(s.Seal(pid, rid, dto.TokenRequest{ExpectedToken: rv.Token}))
	must(s.SetDefault(pid, dto.DefaultRequest{RevisionID: rid}))
	work := dto.BatchWork{Content: dto.BatchContent{ProductionDate: ptr("2026-09-11"), ExpiryDate: ptr("2027-09-11"), QualityStatus: "pending"}, Overrides: []dto.OverrideInput{}, Inspections: []dto.InspectionInput{}}
	_, e = s.CreateBatch(dto.CreateBatchRequest{ProductID: pid, BatchCode: "T13-NOMARKER", RecordType: "test", BatchWork: work})
	if e == nil {
		t.Fatal("invalid create accepted")
	}
	_, e = s.CreateBatch(dto.CreateBatchRequest{ProductID: pid, BatchCode: "T13-COMMERCIAL", RecordType: "commercial", BatchWork: work})
	must(e)
	bid, e := s.CreateBatch(dto.CreateBatchRequest{ProductID: pid, BatchCode: "T13-TEST-" + uuid.NewString(), RecordType: "test", BatchWork: work})
	must(e)
	b, e := s.GetBatch(bid, "")
	must(e)
	_, e = s.CloneBatch(bid, dto.CloneBatchRequest{BatchCode: "T13-NOMARKER", ExpectedEditVersion: b.Batch.EditVersion})
	if e == nil {
		t.Fatal("invalid clone accepted")
	}
	_, e = s.CloneBatch(bid, dto.CloneBatchRequest{BatchCode: "T13-TEST-CLONE", ExpectedEditVersion: b.Batch.EditVersion})
	must(e)
	ready, e := s.Readiness(bid)
	must(e)
	if !ready.Ready {
		t.Fatalf("valid readiness: %+v", ready.Errors)
	}
	reviewID, e := s.Submit(bid, dto.SubmitReview{ExpectedEditVersion: b.Batch.EditVersion})
	must(e)
	var r models.ReviewRecord
	must(db.Where("id=?", reviewID).Take(&r).Error)
	decision := dto.DecideReview{ReviewID: reviewID, CandidateHash: r.CandidateHash}
	if s.Decide(bid, "approved", decision) == nil {
		t.Fatal("self approval accepted")
	}
	var reviewerID int
	must(db.Table("sys_user u").Joins("JOIN sys_role r ON r.role_id=u.role_id").Where("r.role_key='passport_reviewer'").Select("u.user_id").Scan(&reviewerID).Error)
	if reviewerID == 0 {
		t.Fatal("reviewer missing")
	}
	s.Actor = reviewerID
	must(s.Decide(bid, "approved", decision))
	s.Actor = 1
	pub, e := s.Publish(bid, PublishRequest{ReviewID: reviewID, CandidateHash: r.CandidateHash, IdempotencyKey: uuid.NewString()})
	must(e)
	if pub.Record.PublishStatus != "published" {
		t.Fatalf("valid publication failed: %+v", pub.Record)
	}
}
