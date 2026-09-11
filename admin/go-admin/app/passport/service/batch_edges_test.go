//go:build t6_validation

package service

import (
	"errors"
	"go-admin/app/passport/models"
	"go-admin/app/passport/service/dto"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"os"
	"testing"
)

func TestT6ResolverEdges(t *testing.T) {
	db, e := gorm.Open(sqlite.Open("file:"+os.Getenv("T6_TEST_DB")+"?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL"), &gorm.Config{Logger: logger.Default.LogMode(logger.Silent)})
	if e != nil {
		t.Fatal(e)
	}
	pool, _ := db.DB()
	defer pool.Close()
	pool.SetMaxOpenConns(1)
	s := Batches{Products: Products{Actor: 1, Admin: true}}
	s.Orm = db
	must := func(e error) {
		t.Helper()
		if e != nil {
			t.Fatal(e)
		}
	}
	assert := func(v bool) {
		t.Helper()
		if !v {
			t.Fatal("edge assertion")
		}
	}
	run := func(n string, f func()) {
		if !t.Run(n, func(t *testing.T) { f() }) {
			t.FailNow()
		}
	}
	ptr := func(v string) *string { return &v }
	var pid, rid, bid string
	run("MultilingualBaseFixture", func() {
		pid, e = s.Create(dto.CreateProductRequest{ProductCode: "PF-T6-EDGE-TEST", Content: dto.RevisionContent{SourceLanguage: "en", ProcessSteps: []dto.Step{{StepKey: "wash"}}}, Translations: []dto.TranslationRequest{{LanguageCode: "en", ProductName: "T6 EDGE TEST", TranslationStatus: "approved", StorageConditions: ptr("Base EN"), ProcessLabels: map[string]string{"wash": "Wash"}}, {LanguageCode: "zh-CN", ProductName: "T6 测试", TranslationStatus: "approved", StorageConditions: ptr("模板中文"), ProcessLabels: map[string]string{"wash": "清洗"}}}})
		must(e)
		p, e := s.Get(pid)
		must(e)
		rid = p.Revisions[0].ID
	})
	run("ApplicationRejectsCorruptDraftDefault", func() {
		rollback := errors.New("rollback test DDL")
		e := db.Transaction(func(tx *gorm.DB) error {
			var triggers []struct{ Name string }
			must(tx.Raw("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='products'").Scan(&triggers).Error)
			for _, tr := range triggers {
				must(tx.Exec("DROP TRIGGER \"" + tr.Name + "\"").Error)
			}
			must(tx.Exec("UPDATE products SET current_revision_id=? WHERE id=?", rid, pid).Error)
			local := s
			local.Orm = tx
			_, e := local.CreateBatch(dto.CreateBatchRequest{ProductID: pid, BatchCode: "PF-T6-CORRUPT-DEFAULT", BatchWork: dto.BatchWork{Overrides: []dto.OverrideInput{}, Inspections: []dto.InspectionInput{}}})
			assert(e != nil)
			return rollback
		})
		assert(errors.Is(e, rollback))
		p, e := s.Get(pid)
		must(e)
		assert(p.Product.CurrentRevisionID == nil)
	})
	run("CreateEdgeBatch", func() {
		v, e := s.GetRevision(pid, rid)
		must(e)
		must(s.Seal(pid, rid, dto.TokenRequest{ExpectedToken: v.Token}))
		must(s.SetDefault(pid, dto.DefaultRequest{RevisionID: rid}))
		bid, e = s.CreateBatch(dto.CreateBatchRequest{ProductID: pid, BatchCode: "PF-T6-EDGE-BATCH", BatchWork: dto.BatchWork{Overrides: []dto.OverrideInput{{FieldKey: "storage_conditions", Operation: "set", ValueText: ptr("Override EN")}}, Inspections: []dto.InspectionInput{}}})
		must(e)
	})
	run("OverrideMissingTranslationFallsBackToOverrideSource", func() {
		v, e := s.GetBatch(bid, "zh-CN")
		must(e)
		for _, f := range v.Effective {
			if f.FieldKey == "storage_conditions" {
				assert(encode(f.Value) == `"Override EN"` && f.Language == "en")
			}
			if f.FieldKey == "process" {
				assert(encode(f.Value) == `[{"step_key":"wash","label":"清洗"}]`)
			}
		}
	})
	run("OverrideOwnTranslationResolves", func() {
		v, e := s.GetBatch(bid, "")
		must(e)
		m := map[string]interface{}{"batch_override_id": v.Overrides[0].ID, "language_code": "zh-CN", "translated_value": "覆盖中文"}
		metadata(m, 1, stamp())
		must(db.Table("batch_override_translations").Create(m).Error)
		v, e = s.GetBatch(bid, "zh-CN")
		must(e)
		for _, f := range v.Effective {
			if f.FieldKey == "storage_conditions" {
				assert(encode(f.Value) == `"覆盖中文"` && f.Language == "zh-CN")
			}
		}
	})
	run("CloneCopiesTranslationButResetsApproval", func() {
		v, e := s.GetBatch(bid, "")
		must(e)
		id, e := s.CloneBatch(bid, dto.CloneBatchRequest{BatchCode: "PF-T6-EDGE-CLONE", ExpectedEditVersion: v.Batch.EditVersion})
		must(e)
		v, e = s.GetBatch(id, "zh-CN")
		must(e)
		var tr models.OverrideTranslation
		must(db.Where("batch_override_id=?", v.Overrides[0].ID).Take(&tr).Error)
		assert(tr.TranslationStatus == "draft" && *tr.TranslatedValue == "覆盖中文")
	})
	run("ResetDeletesOverrideTranslations", func() {
		v, e := s.GetBatch(bid, "")
		must(e)
		must(s.UpdateBatch(bid, dto.UpdateBatchRequest{ExpectedEditVersion: v.Batch.EditVersion, BatchWork: dto.BatchWork{Overrides: []dto.OverrideInput{}, Inspections: []dto.InspectionInput{}}}))
		v, e = s.GetBatch(bid, "zh-CN")
		must(e)
		assert(len(v.Overrides) == 0)
		for _, f := range v.Effective {
			if f.FieldKey == "storage_conditions" {
				assert(encode(f.Value) == `"模板中文"`)
			}
		}
	})
	run("UnopenedAssetOverridePreviewFailsClosed", func() {
		v, e := s.GetRevision(pid, rid)
		must(e)
		_, e = ResolveEffectiveBatch(db, v, []models.BatchOverride{{FieldKey: "product_image_asset", ValueKind: "asset", Operation: "clear"}}, "en")
		assert(e != nil)
	})
	run("ProcessSetAndClearAreWholeArray", func() {
		v, e := s.GetBatch(bid, "")
		must(e)
		w := dto.BatchWork{Overrides: []dto.OverrideInput{{FieldKey: "process", Operation: "set", Process: []dto.ProcessLabel{{StepKey: "pack", Label: "Pack"}}}}, Inspections: []dto.InspectionInput{}}
		must(s.UpdateBatch(bid, dto.UpdateBatchRequest{ExpectedEditVersion: v.Batch.EditVersion, BatchWork: w}))
		v, e = s.GetBatch(bid, "")
		must(e)
		for _, f := range v.Effective {
			if f.FieldKey == "process" {
				assert(encode(f.Value) == `[{"step_key":"pack","label":"Pack"}]`)
			}
		}
		w.Overrides = []dto.OverrideInput{{FieldKey: "process", Operation: "clear"}}
		must(s.UpdateBatch(bid, dto.UpdateBatchRequest{ExpectedEditVersion: v.Batch.EditVersion, BatchWork: w}))
		v, e = s.GetBatch(bid, "")
		must(e)
		for _, f := range v.Effective {
			if f.FieldKey == "process" {
				assert(encode(f.Value) == `[]` && f.Source == "cleared")
			}
		}
	})
}
