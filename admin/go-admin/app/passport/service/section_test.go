//go:build t7_validation

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
	"strings"
	"testing"
)

func TestT7Validation(t *testing.T) {
	cases := []struct {
		name, kind, raw string
		valid           bool
	}{
		{"empty text is explicit content, not hide", "text", `{"text":""}`, true},
		{"normal unicode", "text", `{"text":"测试 العربية"}`, true},
		{"HTML forbidden", "text", `{"text":"<b>text</b>"}`, false},
		{"nested unknown", "key_value", `{"items":[{"key":"a","label":"b","value":"c","id":1}]}`, false},
		{"null item", "key_value", `{"items":[null]}`, false},
		{"duplicate keys", "key_value", `{"items":[{"key":"a","label":"A","value":"1"},{"key":"a","label":"A","value":"2"}]}`, false},
		{"empty table columns", "table", `{"columns":[],"rows":[]}`, false},
		{"null cell", "table", `{"columns":[{"key":"a","label":"A"}],"rows":[{"cells":[null]}]}`, false},
		{"null content", "text", `null`, false},
		{"trailing object", "text", `{"text":"a"}{}`, false},
		{"JSON title injection", "asset_gallery", `{"caption":"javascript:alert(1)"}`, false},
		{"text exact limit", "text", encode(map[string]string{"text": strings.Repeat("中", 10000)}), true},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			_, e := validateSectionContent(c.kind, json.RawMessage(c.raw))
			if (e == nil) != c.valid {
				t.Fatalf("valid=%v error=%v", c.valid, e)
			}
		})
	}
}
func TestT7TransactionsAndCapacity(t *testing.T) {
	path := os.Getenv("T7_TEST_DB")
	if path == "" {
		t.Fatal("dedicated T7_TEST_DB required")
	}
	db, e := gorm.Open(sqlite.Open("file:"+path+"?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000"), &gorm.Config{Logger: logger.Default.LogMode(logger.Silent)})
	if e != nil {
		t.Fatal(e)
	}
	pool, _ := db.DB()
	defer pool.Close()
	s := Sections{Batches: Batches{Products: Products{Actor: 1, Admin: true}}}
	s.Orm = db
	must := func(e error) {
		t.Helper()
		if e != nil {
			t.Fatal(e)
		}
	}
	pid, e := s.Create(dto.CreateProductRequest{ProductCode: "PF-T7-SERVICE-TEST", Content: dto.RevisionContent{SourceLanguage: "en", ProcessSteps: []dto.Step{}}, Translations: []dto.TranslationRequest{{LanguageCode: "en", TranslationStatus: "approved", ProductName: "T7 TEST ONLY", ProcessLabels: map[string]string{}}}})
	must(e)
	p, e := s.Get(pid)
	must(e)
	rid := p.Revisions[0].ID
	section := func(key string) dto.SectionContent {
		n := 0
		return dto.SectionContent{SectionKey: key, Operation: "add", SectionType: "text", SortOrder: &n, IsVisible: true, Status: "draft", Translations: []dto.SectionTranslation{{LanguageCode: "en", TranslationStatus: "draft", Title: "TEST", Content: json.RawMessage(`{"text":"TEST"}`)}}}
	}
	put := func(key string) (string, error) {
		set, e := s.GetSections(pid, rid, "", "")
		if e != nil {
			return "", e
		}
		return s.PutSection(pid, rid, "", "", dto.SectionWrite{ExpectedToken: set.Token, Section: section(key)})
	}
	t.Run("owner capacity 100 and reject 101", func(t *testing.T) {
		for i := 0; i < 100; i++ {
			_, e := put(fmt.Sprintf("capacity_%03d", i))
			must(e)
		}
		_, e = put("overflow")
		if e == nil {
			t.Fatal("accepted 101")
		}
	})
	t.Run("reorder failure rolls all rows and audit back", func(t *testing.T) {
		before, e := s.GetSections(pid, rid, "", "")
		must(e)
		must(db.Exec(`CREATE TRIGGER t7_reorder_fail BEFORE UPDATE ON custom_sections WHEN OLD.section_key='capacity_050' BEGIN SELECT RAISE(ABORT,'injected'); END`).Error)
		defer db.Exec("DROP TRIGGER t7_reorder_fail")
		keys := []string{}
		for i := 99; i >= 0; i-- {
			keys = append(keys, fmt.Sprintf("capacity_%03d", i))
		}
		e = s.ReorderSections(pid, rid, "", dto.SectionReorder{ExpectedToken: before.Token, Keys: keys})
		if e == nil {
			t.Fatal("no failure")
		}
		after, e := s.GetSections(pid, rid, "", "")
		must(e)
		if encode(before) != encode(after) {
			t.Fatal("partial reorder")
		}
	})
	t.Run("clone audit failure rolls new revision and sections back", func(t *testing.T) {
		must(db.Exec(`CREATE TRIGGER t7_clone_fail BEFORE INSERT ON passport_audit_events WHEN NEW.event_type='product_revision_cloned' BEGIN SELECT RAISE(ABORT,'injected'); END`).Error)
		defer db.Exec("DROP TRIGGER t7_clone_fail")
		_, e = s.Clone(pid, dto.CreateRevisionRequest{SourceRevisionID: rid})
		if e == nil {
			t.Fatal("no failure")
		}
		p, e := s.Get(pid)
		must(e)
		if len(p.Revisions) != 1 {
			t.Fatal("partial clone")
		}
		var n int64
		must(db.Table("custom_sections").Count(&n).Error)
		if n != 100 {
			t.Fatal(n)
		}
	})
}

func TestT7InheritDisabled(t *testing.T) {
	for _, operation := range []string{"inherit", "replace", "hide"} {
		t.Run(operation, func(t *testing.T) {
			base := SectionView{Section: models.Section{ID: "base", SectionKey: "required", SectionType: "text", SourceLanguage: "en", IsVisible: true, Status: "ready"}, Translations: []models.SectionTranslationView{{SectionTranslation: models.SectionTranslation{LanguageCode: "en", Title: "TEST"}, Content: json.RawMessage(`{"text":"TEST"}`)}}}
			own := base
			own.ID = "own"
			own.Operation = operation
			own.Status = "disabled"
			if _, _, e := ResolveEffectiveSections([]SectionView{base}, []SectionView{own}, "revision", "en"); e == nil {
				t.Fatal("mandatory section was hidden")
			}
			base.AllowHide = true
			visible, hidden, e := ResolveEffectiveSections([]SectionView{base}, []SectionView{own}, "revision", "en")
			if e != nil || len(visible) != 0 || len(hidden) != 1 || len(hidden[0].Content) != 0 {
				t.Fatalf("disabled provenance invalid: %v %v %v", visible, hidden, e)
			}
		})
	}
}
