//go:build t5_validation

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

func TestT5ProductTemplates(t *testing.T) {
	path := os.Getenv("T5_TEST_DB")
	if path == "" {
		t.Fatal("T5_TEST_DB must be a dedicated fresh T5 database")
	}
	db, e := gorm.Open(sqlite.Open("file:"+path+"?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL"), &gorm.Config{Logger: logger.Default.LogMode(logger.Silent)})
	if e != nil {
		t.Fatal(e)
	}
	pool, _ := db.DB()
	pool.SetMaxOpenConns(5)
	defer pool.Close()
	s := Products{Actor: 1, Admin: true}
	s.Orm = db
	run := func(name string, fn func(*testing.T)) {
		if !t.Run(name, fn) {
			t.FailNow()
		}
	}
	must := func(e error) {
		t.Helper()
		if e != nil {
			t.Fatal(e)
		}
	}
	var pid, r1, r2, foreign string
	create := func(code string) dto.CreateProductRequest {
		return dto.CreateProductRequest{ProductCode: code, Content: dto.RevisionContent{SourceLanguage: "en", ProcessSteps: []dto.Step{{StepKey: "washing"}}}, Translations: []dto.TranslationRequest{{LanguageCode: "en", TranslationStatus: "draft", ProductName: "Potato Flakes T5 Test — TEST RECORD — NOT FOR COMMERCIAL USE", ProcessLabels: map[string]string{"washing": "Wash"}}}}
	}
	get := func(rid string) RevisionView { v, e := s.GetRevision(pid, rid); must(e); return v }
	run("CreateProductRevisionTranslationTransaction", func(t *testing.T) {
		pid, e = s.Create(create("  pf-t5-test  "))
		must(e)
		v, e := s.Get(pid)
		must(e)
		if v.Product.ProductCode != "PF-T5-TEST" || len(v.Revisions) != 1 || len(v.Revisions[0].Translations) != 1 {
			t.Fatal(v)
		}
		r1 = v.Revisions[0].ID
	})
	run("DuplicateProductCodeReadable", func(t *testing.T) {
		_, e = s.Create(create("pf-t5-test"))
		if e == nil || e.Error() != "产品编码已存在，归档编码也不能重复使用" {
			t.Fatal(e)
		}
	})
	run("CodeValidation", func(t *testing.T) {
		for _, c := range []string{"", " ", "BAD SPACE", "中文", "T5\nX"} {
			if _, e := s.Create(create(c)); e == nil {
				t.Fatal(c)
			}
		}
	})
	run("RollbackOnTranslationDatabaseFailure", func(t *testing.T) {
		must(db.Exec("CREATE TRIGGER t5_translation_failure BEFORE INSERT ON product_revision_translations WHEN NEW.product_name='T5 FORCE FAILURE' BEGIN SELECT RAISE(ABORT,'T5 deliberate translation failure'); END").Error)
		req := create("PF-T5-ROLLBACK")
		req.Translations[0].ProductName = "T5 FORCE FAILURE"
		var before, after int64
		db.Table("product_revisions").Count(&before)
		_, e = s.Create(req)
		if e == nil {
			t.Fatal("expected failure")
		}
		db.Table("product_revisions").Count(&after)
		var n int64
		db.Table("products").Where("product_code='PF-T5-ROLLBACK'").Count(&n)
		if n != 0 || before != after {
			t.Fatal("partial write")
		}
		must(db.Exec("DROP TRIGGER t5_translation_failure").Error)
	})
	run("RollbackOnAuditFailure", func(t *testing.T) {
		must(db.Exec("CREATE TRIGGER t5_audit_failure BEFORE INSERT ON passport_audit_events BEGIN SELECT RAISE(ABORT,'T5 deliberate audit failure'); END").Error)
		_, e = s.Create(create("PF-T5-AUDIT-FAIL"))
		if e == nil {
			t.Fatal("expected failure")
		}
		var n int64
		db.Table("products").Where("product_code='PF-T5-AUDIT-FAIL'").Count(&n)
		if n != 0 {
			t.Fatal("partial write")
		}
		must(db.Exec("DROP TRIGGER t5_audit_failure").Error)
	})
	run("DraftEditAndStaleWriteRejected", func(t *testing.T) {
		v := get(r1)
		c := viewContent(v)
		q := "25"
		c.PackageQuantity = &q
		must(s.UpdateRevision(pid, r1, dto.UpdateRevisionRequest{ExpectedToken: v.Token, Content: c}))
		if get(r1).PackageQuantity == nil || *get(r1).PackageQuantity != "25" {
			t.Fatal("not saved")
		}
		if e := s.UpdateRevision(pid, r1, dto.UpdateRevisionRequest{ExpectedToken: v.Token, Content: c}); e == nil {
			t.Fatal("stale write accepted")
		}
	})
	run("InvalidStructuredFieldsRejected", func(t *testing.T) {
		v := get(r1)
		for _, q := range []string{"1e2", "NaN", "-5"} {
			c := viewContent(v)
			c.PackageQuantity = &q
			if s.UpdateRevision(pid, r1, dto.UpdateRevisionRequest{ExpectedToken: v.Token, Content: c}) == nil {
				t.Fatal(q)
			}
		}
	})
	run("SixLanguageUpsert", func(t *testing.T) {
		for _, lang := range []string{"en", "zh-CN", "es", "ar", "fr", "de"} {
			v := get(r1)
			d := dto.TranslationRequest{LanguageCode: lang, ProductName: "T5 Test " + lang, TranslationStatus: "approved", ProcessLabels: map[string]string{"washing": "T5 washing"}}
			must(s.Translate(pid, r1, dto.UpdateTranslationRequest{ExpectedToken: v.Token, Translation: d}))
		}
		v := get(r1)
		if len(v.Translations) != 6 {
			t.Fatal(len(v.Translations))
		}
		must(s.Translate(pid, r1, dto.UpdateTranslationRequest{ExpectedToken: v.Token, Translation: viewTranslation(v.Translations[0])}))
		if len(get(r1).Translations) != 6 {
			t.Fatal("duplicate")
		}
	})
	run("LanguageAndStepLabelValidation", func(t *testing.T) {
		v := get(r1)
		d := viewTranslation(v.Translations[0])
		d.LanguageCode = "xx"
		if s.Translate(pid, r1, dto.UpdateTranslationRequest{ExpectedToken: v.Token, Translation: d}) == nil {
			t.Fatal("bad lang")
		}
		d.LanguageCode = "en"
		d.ProcessLabels = map[string]string{"unknown": "bad"}
		if s.Translate(pid, r1, dto.UpdateTranslationRequest{ExpectedToken: v.Token, Translation: d}) == nil {
			t.Fatal("unknown step")
		}
	})
	run("SealStoresHashAndMetadata", func(t *testing.T) {
		must(s.Seal(pid, r1, dto.TokenRequest{ExpectedToken: get(r1).Token}))
		v := get(r1)
		if v.RevisionStatus != "sealed" || v.SealedAt == nil || v.ContentHash == nil || len(*v.ContentHash) != 64 {
			t.Fatal(v)
		}
	})
	run("FrozenRevisionApplicationRejected", func(t *testing.T) {
		v := get(r1)
		if s.UpdateRevision(pid, r1, dto.UpdateRevisionRequest{ExpectedToken: v.Token, Content: viewContent(v)}) == nil {
			t.Fatal("accepted")
		}
	})
	run("FrozenTranslationApplicationRejected", func(t *testing.T) {
		v := get(r1)
		if s.Translate(pid, r1, dto.UpdateTranslationRequest{ExpectedToken: v.Token, Translation: viewTranslation(v.Translations[0])}) == nil {
			t.Fatal("accepted")
		}
	})
	run("FrozenRawSQLRejected", func(t *testing.T) {
		if db.Exec("UPDATE product_revisions SET package_quantity='30' WHERE id=?", r1).Error == nil {
			t.Fatal("raw revision accepted")
		}
		if db.Exec("UPDATE product_revision_translations SET product_name='changed' WHERE product_revision_id=?", r1).Error == nil {
			t.Fatal("raw child accepted")
		}
	})
	run("SetSealedDefaultExplicitly", func(t *testing.T) {
		must(s.SetDefault(pid, dto.DefaultRequest{RevisionID: r1}))
		v, e := s.Get(pid)
		must(e)
		if v.Product.CurrentRevisionID == nil || *v.Product.CurrentRevisionID != r1 {
			t.Fatal("wrong default")
		}
	})
	var beforeR1 string
	run("CloneIndependentIDsAndResetSystemFields", func(t *testing.T) {
		beforeR1 = encode(get(r1))
		r2, e = s.Clone(pid, dto.CreateRevisionRequest{SourceRevisionID: r1})
		must(e)
		v := get(r2)
		if v.ID == r1 || v.RevisionNumber != 2 || v.RevisionStatus != "draft" || v.SealedAt != nil || v.SealedBy != nil || v.ContentHash != nil || len(v.Translations) != 6 || *v.SourceRevisionID != r1 {
			t.Fatal(v)
		}
		for _, n := range v.Translations {
			if n.TranslationStatus != "draft" || n.ProductRevisionID != r2 {
				t.Fatal(n)
			}
		}
		if beforeR1 != encode(get(r1)) {
			t.Fatal("source changed")
		}
	})
	run("NewRevisionDoesNotSwitchDefault", func(t *testing.T) {
		v, e := s.Get(pid)
		must(e)
		if *v.Product.CurrentRevisionID != r1 {
			t.Fatal("implicit default switch")
		}
	})
	run("NewRevisionEditsLeaveHistoryIntact", func(t *testing.T) {
		v := get(r2)
		c := viewContent(v)
		q := "20"
		c.PackageQuantity = &q
		must(s.UpdateRevision(pid, r2, dto.UpdateRevisionRequest{ExpectedToken: v.Token, Content: c}))
		if beforeR1 != encode(get(r1)) {
			t.Fatal("source changed")
		}
	})
	run("DraftDefaultRejected", func(t *testing.T) {
		if s.SetDefault(pid, dto.DefaultRequest{RevisionID: r2, ExpectedCurrentID: &r1}) == nil {
			t.Fatal("draft default accepted")
		}
	})
	run("SealRequiresConfirmedSourceLanguage", func(t *testing.T) {
		if s.Seal(pid, r2, dto.TokenRequest{ExpectedToken: get(r2).Token}) == nil {
			t.Fatal("unconfirmed source accepted")
		}
		v := get(r2)
		d := dto.TranslationRequest{LanguageCode: "en", TranslationStatus: "approved", ProductName: "T5 New English"}
		must(s.Translate(pid, r2, dto.UpdateTranslationRequest{ExpectedToken: v.Token, Translation: d}))
		must(s.Seal(pid, r2, dto.TokenRequest{ExpectedToken: get(r2).Token}))
	})
	run("SwitchDefaultPreservesR1R2", func(t *testing.T) {
		must(s.SetDefault(pid, dto.DefaultRequest{RevisionID: r2, ExpectedCurrentID: &r1}))
		if beforeR1 != encode(get(r1)) {
			t.Fatal("source changed")
		}
		v, e := s.Get(pid)
		must(e)
		if len(v.Revisions) != 2 || *v.Product.CurrentRevisionID != r2 {
			t.Fatal(v)
		}
	})
	run("ForeignProductRevisionRejected", func(t *testing.T) {
		foreign, e = s.Create(create("PF-T5-OTHER"))
		must(e)
		if s.SetDefault(foreign, dto.DefaultRequest{RevisionID: r1}) == nil {
			t.Fatal("cross product default")
		}
		if _, e = s.Clone(foreign, dto.CreateRevisionRequest{SourceRevisionID: r1}); e == nil {
			t.Fatal("cross product clone")
		}
	})
	run("ConcurrentRevisionNumbers", func(t *testing.T) {
		errs := make(chan error, 5)
		var wg sync.WaitGroup
		for i := 0; i < 5; i++ {
			wg.Add(1)
			go func() {
				defer wg.Done()
				_, e := s.Clone(pid, dto.CreateRevisionRequest{SourceRevisionID: r1})
				errs <- e
			}()
		}
		wg.Wait()
		close(errs)
		for e := range errs {
			must(e)
		}
		var rows []int64
		must(db.Model(&models.Revision{}).Where("product_id=?", pid).Order("revision_number").Pluck("revision_number", &rows).Error)
		if fmt.Sprint(rows) != "[1 2 3 4 5 6 7]" {
			t.Fatal(rows)
		}
	})
	run("DatabaseUniqueLastDefense", func(t *testing.T) {
		v := get(r1)
		if db.Exec("INSERT INTO product_revisions(id,created_at,created_by,updated_at,updated_by,product_id,revision_number) VALUES('12345678-1234-4234-8234-123456789abc',?,1,?,1,?,1)", v.CreatedAt, v.UpdatedAt, pid).Error == nil {
			t.Fatal("duplicate revision")
		}
		if db.Exec("INSERT INTO products(id,created_at,created_by,updated_at,updated_by,product_code) VALUES('12345678-1234-4234-8234-123456789abc',?,1,?,1,'PF-T5-TEST')", v.CreatedAt, v.UpdatedAt).Error == nil {
			t.Fatal("duplicate code")
		}
	})
	run("ArchivePreservesHistoryAndBlocksWrites", func(t *testing.T) {
		v, e := s.Get(pid)
		must(e)
		n := len(v.Revisions)
		must(s.Archive(pid))
		v, e = s.Get(pid)
		must(e)
		if len(v.Revisions) != n || v.Product.LifecycleStatus != "archived" || beforeR1 != encode(get(r1)) {
			t.Fatal("history damaged")
		}
		if _, e = s.Clone(pid, dto.CreateRevisionRequest{SourceRevisionID: r1}); e == nil {
			t.Fatal("archived clone accepted")
		}
	})
	run("AuditEventsInSameDatabase", func(t *testing.T) {
		var events []string
		must(db.Table("passport_audit_events").Distinct().Pluck("event_type", &events).Error)
		for _, want := range []string{"product_created", "product_revision_created", "product_revision_cloned", "product_revision_updated", "product_translation_updated", "product_revision_sealed", "product_default_revision_changed", "archived"} {
			found := false
			for _, v := range events {
				found = found || v == want
			}
			if !found {
				t.Fatal(want)
			}
		}
	})
	run("IntegrityAndForeignKeys", func(t *testing.T) {
		var v string
		must(db.Raw("PRAGMA integrity_check").Scan(&v).Error)
		if v != "ok" {
			t.Fatal(v)
		}
		var rows []map[string]interface{}
		must(db.Raw("PRAGMA foreign_key_check").Scan(&rows).Error)
		if len(rows) > 0 {
			t.Fatal(rows)
		}
	})
	run("ListSearchPaginationAndStatus", func(t *testing.T) {
		r, n, e := s.List(dto.Query{Search: "PF-T5-TEST", Status: "archived", PageIndex: 1, PageSize: 1})
		must(e)
		if n != 1 || len(r) != 1 || r[0].RevisionCount != 7 {
			t.Fatal(r, n)
		}
	})
	data, _ := json.Marshal(map[string]string{"product": pid, "r1": r1, "r2": r2})
	if p := os.Getenv("T5_SERVICE_FIXTURES"); p != "" {
		must(os.WriteFile(p, data, 0600))
	}
}
