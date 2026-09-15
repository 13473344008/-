package service

import (
	"github.com/google/uuid"
	"go-admin/app/passport/service/dto"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"os"
	"testing"
)

func TestBilingualStepTransaction(t *testing.T) {
	path := os.Getenv("BILINGUAL_TEST_DB")
	if path == "" {
		t.Skip("requires a disposable offline migrated database")
	}
	db, e := gorm.Open(sqlite.Open(path+"?_foreign_keys=on"), &gorm.Config{})
	if e != nil {
		t.Fatal(e)
	}
	s := Products{Actor: 1, Admin: true}
	s.Orm = db
	must := func(e error) {
		t.Helper()
		if e != nil {
			t.Fatal(e)
		}
	}
	pid, e := s.Create(dto.CreateProductRequest{ProductCode: "BILINGUAL-" + uuid.NewString(), Content: dto.RevisionContent{SourceLanguage: "en", ProcessSteps: []dto.Step{{StepKey: "legacy_wash"}}}, Translations: []dto.TranslationRequest{{LanguageCode: "en", ProductName: "Potato", TranslationStatus: "approved", ProcessLabels: map[string]string{"legacy_wash": "Washing"}}}})
	must(e)
	var rid string
	must(db.Table("product_revisions").Select("id").Where("product_id=?", pid).Scan(&rid).Error)
	v, e := s.revision(db, pid, rid)
	must(e)
	c := viewContent(v)
	c.ProcessSteps = append(c.ProcessSteps, dto.Step{StepKey: "STEP_001"})
	req := dto.UpdateRevisionRequest{ExpectedToken: v.Token, Content: c, ProcessLabels: map[string]map[string]string{"en": {"legacy_wash": "Washing", "STEP_001": "Drying"}, "zh-CN": {"legacy_wash": "清洗", "STEP_001": "干燥"}}}
	must(s.UpdateRevision(pid, rid, req))
	updated, e := s.revision(db, pid, rid)
	must(e)
	if len(updated.ProcessSteps) != 2 || len(updated.Translations) != 2 {
		t.Fatal("step names did not persist together")
	}
	for _, tr := range updated.Translations {
		if tr.TranslationStatus != "draft" || len(tr.ProcessLabels) != 2 {
			t.Fatal("expected draft bilingual labels")
		}
	}
	if s.UpdateRevision(pid, rid, req) == nil {
		t.Fatal("stale token accepted")
	}
	req.ExpectedToken = updated.Token
	req.ProcessLabels["zh-CN"]["invalid"] = "错误"
	if s.UpdateRevision(pid, rid, req) == nil {
		t.Fatal("invalid label accepted")
	}
	unchanged, e := s.revision(db, pid, rid)
	must(e)
	if unchanged.Token != updated.Token {
		t.Fatal("failed write partially committed")
	}
	delete(req.ProcessLabels["zh-CN"], "invalid")
	req.Content.ProcessSteps = req.Content.ProcessSteps[1:]
	delete(req.ProcessLabels["en"], "legacy_wash")
	delete(req.ProcessLabels["zh-CN"], "legacy_wash")
	must(s.UpdateRevision(pid, rid, req))
	last, e := s.revision(db, pid, rid)
	must(e)
	for _, tr := range last.Translations {
		if len(tr.ProcessLabels) != 1 || tr.ProcessLabels["STEP_001"] == "" {
			t.Fatal("deletion remapped or retained names")
		}
	}
}
