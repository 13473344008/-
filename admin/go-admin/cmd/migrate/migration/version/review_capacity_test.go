//go:build t4_schema

package version

import (
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"path/filepath"
	"strings"
	"testing"
)

func TestReviewCapacityPreservesRecordsAndGuards(t *testing.T) {
	db, e := gorm.Open(sqlite.Open(filepath.Join(t.TempDir(), "test.db")+"?_foreign_keys=on"), &gorm.Config{})
	if e != nil {
		t.Fatal(e)
	}
	sql := `CREATE TABLE sys_migration(version TEXT, apply_time DATETIME); CREATE TABLE review_records(id TEXT PRIMARY KEY,candidate_input TEXT CHECK(json_valid(candidate_input) AND length(CAST(candidate_input AS BLOB))<=4194304)); CREATE TABLE pointer(id TEXT REFERENCES review_records(id)); CREATE INDEX review_idx ON review_records(id); CREATE TRIGGER frozen BEFORE DELETE ON review_records BEGIN SELECT RAISE(ABORT,'frozen'); END; INSERT INTO review_records VALUES('old','{}'); INSERT INTO pointer VALUES('old');`
	if e = db.Exec(sql).Error; e != nil {
		t.Fatal(e)
	}
	if e = reviewCapacity(db, "1790000000000"); e != nil {
		t.Fatal(e)
	}
	var n int64
	db.Table("pointer").Where("id='old'").Count(&n)
	if n != 1 {
		t.Fatal("pointer lost")
	}
	if e = db.Exec("INSERT INTO review_records VALUES(?,?)", "large", `"`+strings.Repeat("x", 5*1024*1024)+`"`).Error; e != nil {
		t.Fatal(e)
	}
	if e = db.Exec("DELETE FROM review_records WHERE id='old'").Error; e == nil {
		t.Fatal("immutable guard lost")
	}
	if e = db.Exec("INSERT INTO pointer VALUES('missing')").Error; e == nil {
		t.Fatal("foreign keys not restored")
	}
}
