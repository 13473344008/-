//go:build t6_validation

package service

import (
	"encoding/json"
	"fmt"
	"go-admin/app/passport/models"
	"go-admin/app/passport/service/dto"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"os"
	"sync"
	"testing"
)

func TestT6Batches(t *testing.T) {
	path := os.Getenv("T6_TEST_DB")
	if path == "" {
		t.Fatal("dedicated fresh T6_TEST_DB required")
	}
	db, e := gorm.Open(sqlite.Open("file:"+path+"?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL"), &gorm.Config{Logger: logger.Default.LogMode(logger.Silent)})
	if e != nil {
		t.Fatal(e)
	}
	pool, _ := db.DB()
	pool.SetMaxOpenConns(5)
	defer pool.Close()
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
			t.Fatal("assertion failed")
		}
	}
	run := func(n string, f func()) {
		if !t.Run(n, func(t *testing.T) { f() }) {
			t.FailNow()
		}
	}
	ptr := func(s string) *string { return &s }
	product := func(code string) (string, string) {
		id, e := s.Create(dto.CreateProductRequest{ProductCode: code, Content: dto.RevisionContent{SourceLanguage: "en", PackageQuantity: ptr("25"), PackageUnit: ptr("kg"), ProcessSteps: []dto.Step{}}, Translations: []dto.TranslationRequest{{LanguageCode: "en", TranslationStatus: "approved", ProductName: "T6 TEST RECORD — NOT FOR COMMERCIAL USE", ProcessLabels: map[string]string{}, StorageConditions: ptr("Dry place")}}})
		must(e)
		v, e := s.Get(id)
		must(e)
		return id, v.Revisions[0].ID
	}
	seal := func(pid, rid string) {
		v, e := s.GetRevision(pid, rid)
		must(e)
		must(s.Seal(pid, rid, dto.TokenRequest{ExpectedToken: v.Token}))
	}
	get := func(id string) BatchView { v, e := s.GetBatch(id, ""); must(e); return v }
	work := func() dto.BatchWork {
		return dto.BatchWork{Content: dto.BatchContent{QualityStatus: "pending"}, Overrides: []dto.OverrideInput{}, Inspections: []dto.InspectionInput{}}
	}
	create := func(pid, code string) (string, error) {
		return s.CreateBatch(dto.CreateBatchRequest{ProductID: pid, BatchCode: code, BatchWork: work()})
	}
	update := func(id string, w dto.BatchWork) error {
		return s.UpdateBatch(id, dto.UpdateBatchRequest{ExpectedEditVersion: get(id).Batch.EditVersion, BatchWork: w})
	}
	effective := func(id, key string) interface{} {
		for _, f := range get(id).Effective {
			if f.FieldKey == key {
				var v interface{}
				_ = json.Unmarshal([]byte(encode(f.Value)), &v)
				return v
			}
		}
		return nil
	}
	var pid, r1, r2, foreign, fr, bid, newid, clone string
	run("CreateProductFixture", func() { pid, r1 = product("PF-T6-TEST-SERVICE-TEST"); foreign, fr = product("PF-T6-TEST-OTHER-TEST") })
	run("NoDefaultRejected", func() { _, e := create(pid, "PF-T6-TEST-NODEFAULT"); assert(e != nil) })
	run("DraftDefaultRejectedByDB", func() { assert(db.Exec("UPDATE products SET current_revision_id=? WHERE id=?", r1, pid).Error != nil) })
	run("SealAndSetDefault", func() { seal(pid, r1); seal(foreign, fr); must(s.SetDefault(pid, dto.DefaultRequest{RevisionID: r1})) })
	run("CreateBindsSealedDefault", func() {
		bid, e = create(pid, " pf-t6-TEST-service-a ")
		must(e)
		v := get(bid)
		assert(v.Batch.BaseProductRevisionID == r1 && v.Batch.BatchCode == "PF-T6-TEST-SERVICE-A" && v.Batch.WorkflowStatus == "draft")
	})
	run("ListPaginationSearchProduct", func() {
		rows, n, e := s.ListBatches(dto.BatchQuery{Search: "SERVICE-A", ProductID: pid, PageIndex: 1, PageSize: 1})
		must(e)
		assert(n == 1 && len(rows) == 1)
	})
	run("DuplicateCodeBusiness409", func() {
		_, e := create(pid, "pf-t6-TEST-service-a")
		b, ok := e.(*BusinessError)
		assert(ok && b.Code == 409)
	})
	run("InvalidBatchCodes", func() {
		for _, c := range []string{"", " ", "../a", "中文", "A B"} {
			_, e := create(pid, c)
			assert(e != nil)
		}
	})
	run("DatabaseUniqueCode", func() {
		assert(db.Exec("INSERT INTO batches(id,created_at,created_by,updated_at,updated_by,batch_code,product_id,base_product_revision_id) SELECT '11111111-1111-4111-8111-111111111111',created_at,created_by,updated_at,updated_by,batch_code,product_id,base_product_revision_id FROM batches WHERE id=?", bid).Error != nil)
	})
	run("DatabaseBaseImmutable", func() {
		assert(db.Exec("UPDATE batches SET base_product_revision_id=? WHERE id=?", fr, bid).Error != nil)
	})
	run("DatabaseProductImmutable", func() { assert(db.Exec("UPDATE batches SET product_id=? WHERE id=?", foreign, bid).Error != nil) })
	run("CrossProductBaseRejected", func() {
		assert(db.Exec("INSERT INTO batches(id,created_at,created_by,updated_at,updated_by,batch_code,product_id,base_product_revision_id) VALUES('22222222-2222-4222-8222-222222222222',?,1,?,1,'PF-T6-TEST-CROSS',?,?)", stamp(), stamp(), pid, fr).Error != nil)
	})
	run("ReferencedRevisionDeleteRejected", func() { assert(db.Delete(&models.Revision{}, "id=?", r1).Error != nil) })
	run("InheritResolver", func() { assert(effective(bid, "package_quantity") == "25") })
	w := work()
	run("SetOverrideResolver", func() {
		w.Overrides = []dto.OverrideInput{{FieldKey: "package_quantity", Operation: "set", ValueText: ptr("20")}}
		must(update(bid, w))
		assert(effective(bid, "package_quantity") == "20")
	})
	run("ClearOverrideResolver", func() {
		w.Overrides = []dto.OverrideInput{{FieldKey: "package_quantity", Operation: "clear"}}
		must(update(bid, w))
		assert(effective(bid, "package_quantity") == nil)
	})
	run("ResetDeletesOverrideRestoresBase", func() {
		w.Overrides = []dto.OverrideInput{}
		must(update(bid, w))
		assert(len(get(bid).Overrides) == 0 && effective(bid, "package_quantity") == "25")
	})
	for _, field := range []string{"batch_code", "product_id", "base_product_revision_id", "workflow_status", "quality_status", "created_by", "product_name", "unknown", "product_image_asset"} {
		run("ForbiddenOverride_"+field, func() {
			bad := work()
			bad.Overrides = []dto.OverrideInput{{FieldKey: field, Operation: "clear"}}
			assert(update(bid, bad) != nil)
		})
	}
	run("TypedOverrideValidation", func() {
		for _, o := range []dto.OverrideInput{{FieldKey: "package_quantity", Operation: "set", ValueText: ptr("NaN")}, {FieldKey: "shelf_life_days", Operation: "set", ValueText: ptr("20")}, {FieldKey: "storage_conditions", Operation: "clear", ValueText: ptr("leftover")}, {FieldKey: "process", Operation: "set", Process: []dto.ProcessLabel{{StepKey: "x", Label: ""}}}} {
			bad := work()
			bad.Overrides = []dto.OverrideInput{o}
			assert(update(bid, bad) != nil)
		}
	})
	run("DateValidationAndNullable", func() {
		bad := work()
		bad.Content.ProductionDate = ptr("2026-02-30")
		assert(update(bid, bad) != nil)
		bad.Content.ProductionDate = ptr("2026-09-08")
		bad.Content.ExpiryDate = ptr("2026-09-07")
		assert(update(bid, bad) != nil)
		must(update(bid, work()))
	})
	item := func(code string) dto.InspectionInput {
		return dto.InspectionInput{ItemCode: code, Name: code + " TEST", ValueType: "decimal", NumericValue: ptr("6.8"), Unit: ptr("%"), MinLimit: ptr("0"), MaxLimit: ptr("10"), MinInclusive: true, MaxInclusive: true, Judgement: "pass", TestedOn: ptr("2026-09-08"), InternalNote: ptr("OLD BATCH FACT")}
	}
	run("CreateDynamicInspection", func() {
		w.Inspections = []dto.InspectionInput{item("MOISTURE")}
		must(update(bid, w))
		assert(len(get(bid).Inspections) == 1)
	})
	run("UpdateInspectionPreservesIdentity", func() {
		old := get(bid).Inspections[0].ID
		w.Inspections[0].NumericValue = ptr("7")
		must(update(bid, w))
		assert(get(bid).Inspections[0].ID == old)
	})
	run("UnknownInspectionNoSchemaChange", func() {
		var before, after int
		must(db.Raw("PRAGMA schema_version").Scan(&before).Error)
		w.Inspections = append(w.Inspections, item("BULK_DENSITY"), item("BLACK_SPECKS"), item("ASH"))
		must(update(bid, w))
		must(db.Raw("PRAGMA schema_version").Scan(&after).Error)
		assert(before == after && len(get(bid).Inspections) == 4)
	})
	run("TextInspectionAndAllStatuses", func() {
		for _, status := range []string{"pass", "fail", "not_tested", "not_applicable", "pending", "informational"} {
			i := item("APPEARANCE")
			i.ValueType = "text"
			i.NumericValue = nil
			i.TextValue = ptr("Off-white flakes")
			i.Judgement = status
			if status == "not_tested" || status == "not_applicable" {
				i.TextValue = nil
			}
			assert(validateInspection(&i) == nil)
		}
	})
	run("InspectionInvalidStatesAndValues", func() {
		i := item("X")
		i.Judgement = "approved"
		assert(validateInspection(&i) != nil)
		i.Judgement = "pass"
		i.NumericValue = ptr("abc")
		assert(validateInspection(&i) != nil)
		i.NumericValue = nil
		assert(validateInspection(&i) != nil)
		i.NumericValue = ptr("7")
		i.MinLimit = ptr("11")
		assert(validateInspection(&i) != nil)
		i.MinLimit = ptr("0")
		i.ValueType = "integer"
		i.NumericValue = ptr("1.5")
		assert(validateInspection(&i) != nil)
	})
	run("ExactDecimalComparison", func() {
		i := item("X")
		i.MinLimit = ptr("999999999999999999.000000002")
		i.MaxLimit = ptr("999999999999999999.000000001")
		assert(validateInspection(&i) != nil)
	})
	run("DeleteDraftInspection", func() {
		old := w.Inspections
		w.Inspections = w.Inspections[:3]
		must(update(bid, w))
		assert(len(get(bid).Inspections) == 3)
		w.Inspections = old
		must(update(bid, w))
	})
	run("DuplicateInspectionCodeRejected", func() {
		bad := work()
		bad.Inspections = []dto.InspectionInput{item("SAME"), item("same")}
		assert(update(bid, bad) != nil)
	})
	run("StaleEditVersionRejected", func() {
		v := get(bid).Batch.EditVersion
		must(update(bid, w))
		assert(s.UpdateBatch(bid, dto.UpdateBatchRequest{ExpectedEditVersion: v, BatchWork: w}) != nil)
	})
	run("MissingChildListsRejected", func() { assert(update(bid, dto.BatchWork{}) != nil) })
	run("CreateAuditFailureRollsBack", func() {
		must(db.Exec("CREATE TRIGGER t6_fail_audit BEFORE INSERT ON passport_audit_events WHEN NEW.event_type='batch_created' BEGIN SELECT RAISE(ABORT,'injected'); END").Error)
		_, e := create(pid, "PF-T6-TEST-ROLLBACK-CREATE")
		assert(e != nil)
		must(db.Exec("DROP TRIGGER t6_fail_audit").Error)
		var n int64
		must(db.Table("batches").Where("batch_code=?", "PF-T6-TEST-ROLLBACK-CREATE").Count(&n).Error)
		assert(n == 0)
	})
	run("OverrideAuditFailureRollsBackWholeAggregate", func() {
		old := encode(get(bid))
		must(db.Exec("CREATE TRIGGER t6_fail_audit BEFORE INSERT ON passport_audit_events WHEN NEW.event_type='override_set' BEGIN SELECT RAISE(ABORT,'injected'); END").Error)
		bad := w
		bad.Overrides = []dto.OverrideInput{{FieldKey: "package_quantity", Operation: "set", ValueText: ptr("17")}}
		bad.Content.InternalNote = ptr("must rollback")
		assert(update(bid, bad) != nil)
		must(db.Exec("DROP TRIGGER t6_fail_audit").Error)
		assert(encode(get(bid)) == old)
	})
	run("CreateR2DefaultHistoricalBatchStable", func() {
		r2, e = s.Clone(pid, dto.CreateRevisionRequest{SourceRevisionID: r1})
		must(e)
		v, e := s.GetRevision(pid, r2)
		must(e)
		tr := viewTranslation(v.Translations[0])
		tr.TranslationStatus = "approved"
		must(s.Translate(pid, r2, dto.UpdateTranslationRequest{ExpectedToken: v.Token, Translation: tr}))
		seal(pid, r2)
		must(s.SetDefault(pid, dto.DefaultRequest{RevisionID: r2, ExpectedCurrentID: &r1}))
		assert(get(bid).Batch.BaseProductRevisionID == r1)
		newid, e = create(pid, "PF-T6-TEST-SERVICE-B")
		must(e)
		assert(get(newid).Batch.BaseProductRevisionID == r2)
	})
	run("ClonePreservesOverrideAndBase", func() {
		w.Overrides = []dto.OverrideInput{{FieldKey: "package_quantity", Operation: "set", ValueText: ptr("20")}}
		must(update(bid, w))
		clone, e = s.CloneBatch(bid, dto.CloneBatchRequest{BatchCode: "PF-T6-TEST-SERVICE-CLONE", ExpectedEditVersion: get(bid).Batch.EditVersion})
		must(e)
		v := get(clone)
		assert(v.Batch.ID != bid && v.Batch.BaseProductRevisionID == r1 && v.Batch.BatchCode == "PF-T6-TEST-SERVICE-CLONE" && effective(clone, "package_quantity") == "20")
	})
	run("CloneClearsProductionFacts", func() {
		v := get(clone)
		assert(v.Batch.ProductionDate == nil && v.Batch.ExpiryDate == nil && v.Batch.QualityStatus == "pending" && v.Batch.CurrentPassportRevisionID == nil && v.Batch.NextVersionNumber == 1 && v.Batch.SubmittedAt == nil)
		for _, i := range v.Inspections {
			assert(i.NumericValue == nil && i.TextValue == nil && i.TestedOn == nil && i.InternalNote == nil && i.Judgement == "not_tested")
		}
	})
	run("CloneCopiesDefinitionsNewIDs", func() {
		a, b := get(bid), get(clone)
		assert(len(a.Inspections) == len(b.Inspections))
		for n, i := range b.Inspections {
			old := a.Inspections[n]
			assert(i.ID != old.ID && i.Name == old.Name && encode(i.MaxLimit) == encode(old.MaxLimit) && i.Unit != nil)
		}
	})
	run("CloneFailureRollsBack", func() {
		must(db.Exec("CREATE TRIGGER t6_fail_copy BEFORE INSERT ON inspection_items WHEN NEW.batch_id NOT IN (SELECT id FROM batches WHERE batch_code!='PF-T6-TEST-ROLLBACK-CLONE') BEGIN SELECT RAISE(ABORT,'injected copy failure'); END").Error)
		_, e := s.CloneBatch(bid, dto.CloneBatchRequest{BatchCode: "PF-T6-TEST-ROLLBACK-CLONE", ExpectedEditVersion: get(bid).Batch.EditVersion})
		assert(e != nil)
		must(db.Exec("DROP TRIGGER t6_fail_copy").Error)
		var n int64
		must(db.Table("batches").Where("batch_code=?", "PF-T6-TEST-ROLLBACK-CLONE").Count(&n).Error)
		assert(n == 0)
	})
	run("ResetCloneOverride", func() { c := work(); must(update(clone, c)); assert(effective(clone, "package_quantity") == "25") })
	run("PendingBatchApplicationFreeze", func() {
		must(db.Exec("UPDATE batches SET workflow_status='archived',archived_at=?,archived_by=1 WHERE id=?", stamp(), clone).Error)
		assert(update(clone, work()) != nil)
		_, e := s.CloneBatch(clone, dto.CloneBatchRequest{BatchCode: "PF-T6-TEST-FROZEN-CLONE", ExpectedEditVersion: get(clone).Batch.EditVersion})
		assert(e != nil)
	})
	run("ConcurrentDifferentCodes", func() {
		var wg sync.WaitGroup
		errs := make(chan error, 5)
		for i := 0; i < 5; i++ {
			wg.Add(1)
			go func(i int) { defer wg.Done(); _, e := create(pid, fmt.Sprintf("PF-T6-TEST-CONCURRENT-%d", i)); errs <- e }(i)
		}
		wg.Wait()
		close(errs)
		for e := range errs {
			must(e)
		}
	})
	run("ConcurrentSameCodeOneSuccess", func() {
		var wg sync.WaitGroup
		errs := make(chan error, 5)
		for i := 0; i < 5; i++ {
			wg.Add(1)
			go func() { defer wg.Done(); _, e := create(pid, "PF-T6-TEST-SAME-CODE"); errs <- e }()
		}
		wg.Wait()
		close(errs)
		ok := 0
		for e := range errs {
			if e == nil {
				ok++
			} else {
				b, yes := e.(*BusinessError)
				assert(yes && b.Code == 409)
			}
		}
		assert(ok == 1)
	})
	run("ConcurrentClonesNoDirtyCopies", func() {
		version := get(bid).Batch.EditVersion
		var wg sync.WaitGroup
		errs := make(chan error, 3)
		for n := 0; n < 3; n++ {
			wg.Add(1)
			go func(n int) {
				defer wg.Done()
				_, e := s.CloneBatch(bid, dto.CloneBatchRequest{BatchCode: fmt.Sprintf("PF-T6-TEST-CONCURRENT-CLONE-%d", n), ExpectedEditVersion: version})
				errs <- e
			}(n)
		}
		wg.Wait()
		close(errs)
		for e := range errs {
			must(e)
		}
	})
	run("AuditEventsAndAppendOnly", func() {
		var n int64
		must(db.Table("passport_audit_events").Where("batch_id=?", bid).Count(&n).Error)
		assert(n >= 8)
		assert(db.Exec("DELETE FROM passport_audit_events WHERE batch_id=?", bid).Error != nil)
	})
	run("IntegrityAndForeignKeys", func() {
		var v string
		must(db.Raw("PRAGMA integrity_check").Scan(&v).Error)
		assert(v == "ok")
		var rows []map[string]interface{}
		must(db.Raw("PRAGMA foreign_key_check").Scan(&rows).Error)
		assert(len(rows) == 0)
	})
}
