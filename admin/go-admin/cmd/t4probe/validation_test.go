//go:build t4_validation

package main

import (
	"encoding/json"
	"fmt"
	"github.com/google/uuid"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"os"
	"strings"
	"sync"
	"testing"
	"time"
)

func TestT4ActualGoDriver(t *testing.T) {
	rt := "/path/to/ID/runtime/t4"
	var ids map[string]interface{}
	b, _ := os.ReadFile(rt + "/evidence/schema-fixtures.json")
	if e := json.Unmarshal(b, &ids); e != nil {
		t.Fatal(e)
	}
	db, e := gorm.Open(sqlite.Open("file:"+rt+"/db/go-driver-check.db?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL"), &gorm.Config{Logger: logger.Default.LogMode(logger.Silent)})
	if e != nil {
		t.Fatal(e)
	}
	pool, _ := db.DB()
	pool.SetMaxOpenConns(5)
	defer pool.Close()
	clone := func(table, where string) string {
		columns, err := db.Migrator().ColumnTypes(table)
		if err != nil {
			t.Fatal(err)
		}
		var names, values []string
		for _, c := range columns {
			n := c.Name()
			names = append(names, `"`+n+`"`)
			if n == "id" || n == "release_identifier" {
				values = append(values, "'"+uuid.NewString()+"'")
			} else if (table == "products" && n == "current_revision_id") || (table == "passport_revisions" && (n == "published_at" || n == "sealed_at")) {
				values = append(values, "NULL")
			} else {
				values = append(values, `"`+n+`"`)
			}
		}
		return "INSERT INTO " + table + " (" + strings.Join(names, ",") + ") SELECT " + strings.Join(values, ",") + " FROM " + table + " WHERE " + where
	}
	tests := []struct {
		name, sql string
		args      []interface{}
	}{
		{"ProductUnique", clone("products", "id=?"), []interface{}{ids["product"]}},
		{"BatchCodeUnique", clone("batches", "batch_code='PF-T4-INHERIT'"), nil},
		{"ProductRevisionUnique", clone("product_revisions", "id=?"), []interface{}{ids["r1"]}},
		{"PassportVersionUnique", clone("passport_revisions", "batch_id=? AND version_number=1"), []interface{}{ids["batch"]}},
		{"FrozenTranslationInsert", clone("product_revision_translations", "product_revision_id=? AND language_code='en'"), []interface{}{ids["r1"]}},
		{"ReferencedProductFK", "DELETE FROM products WHERE id=?", []interface{}{ids["product"]}},
		{"FrozenTemplate", "UPDATE product_revisions SET package_quantity='999' WHERE id=?", []interface{}{ids["r1"]}},
		{"FrozenChild", "UPDATE product_revision_translations SET product_name='T4 invalid' WHERE product_revision_id=?", []interface{}{ids["r1"]}},
		{"FixedBatchBase", "UPDATE batches SET base_product_revision_id=? WHERE id=?", []interface{}{ids["r2"], ids["batch"]}},
		{"PublishedHistory", "DELETE FROM passport_revisions WHERE batch_id=?", []interface{}{ids["batch"]}},
		{"PublishedAsset", "DELETE FROM published_assets", nil},
	}
	for _, v := range tests {
		t.Run(v.name, func(t *testing.T) {
			tx := db.Begin()
			defer tx.Rollback()
			if e := tx.Exec(v.sql, v.args...).Error; e == nil {
				t.Fatal("illegal mutation accepted")
			} else if strings.Contains(v.name, "Unique") && !strings.Contains(e.Error(), "UNIQUE constraint failed") {
				t.Fatal(e)
			}
		})
	}
	t.Run("ConnectionPragmas", func(t *testing.T) {
		var fk, busy int
		var wal string
		db.Raw("pragma foreign_keys").Scan(&fk)
		db.Raw("pragma busy_timeout").Scan(&busy)
		db.Raw("pragma journal_mode").Scan(&wal)
		if fk != 1 || busy != 5000 || wal != "wal" {
			t.Fatalf("%d %d %s", fk, busy, wal)
		}
	})
	write := func(tx *gorm.DB, code string) (string, error) {
		id := uuid.NewString()
		stamp := time.Now().UTC().Format("2006-01-02T15:04:05.000Z")
		args := []interface{}{id, stamp, stamp, code, ids["product"], ids["r1"]}
		if e := tx.Exec("INSERT INTO batches(id,created_at,created_by,updated_at,updated_by,batch_code,product_id,base_product_revision_id) VALUES(?,?,1,?,1,?,?,?)", args...).Error; e != nil {
			return id, e
		}
		if e := tx.Exec("INSERT INTO inspection_items(id,created_at,created_by,updated_at,updated_by,batch_id,item_code,name) VALUES(?,?,1,?,1,?,'T4-GO','T4 Test')", uuid.NewString(), stamp, stamp, id).Error; e != nil {
			return id, e
		}
		if e := tx.Exec("INSERT INTO passport_audit_events(id,batch_id,actor_user_id,created_at,event_type,entity_type,entity_id,summary) VALUES(?,?,1,?,'batch_created','batches',?,'T4 Go driver')", uuid.NewString(), id, stamp, id).Error; e != nil {
			return id, e
		}
		return id, nil
	}
	t.Run("FourTableRollback", func(t *testing.T) {
		e := db.Transaction(func(tx *gorm.DB) error {
			id, e := write(tx, "T4-GO-ROLLBACK")
			if e != nil {
				return e
			}
			stamp := time.Now().UTC().Format("2006-01-02T15:04:05.000Z")
			if e = tx.Exec("INSERT INTO batch_overrides(id,created_at,created_by,updated_at,updated_by,batch_id,field_key,value_kind,value_text) VALUES(?,?,1,?,1,?,'package_quantity','decimal','20')", uuid.NewString(), stamp, stamp, id).Error; e != nil {
				return e
			}
			return fmt.Errorf("T4 deliberate abort after 4 table writes")
		})
		var n int64
		db.Table("batches").Where("batch_code=?", "T4-GO-ROLLBACK").Count(&n)
		if e == nil || n != 0 {
			t.Fatal("rollback failed")
		}
	})
	t.Run("FiveWriters25Transactions", func(t *testing.T) {
		start := time.Now()
		var wg sync.WaitGroup
		errs := make(chan error, 25)
		for w := 0; w < 5; w++ {
			wg.Add(1)
			go func(w int) {
				defer wg.Done()
				for i := 0; i < 5; i++ {
					errs <- db.Transaction(func(tx *gorm.DB) error { _, e := write(tx, fmt.Sprintf("T4-GO-%d-%d", w, i)); return e })
				}
			}(w)
		}
		wg.Wait()
		close(errs)
		for e := range errs {
			if e != nil {
				t.Error(e)
			}
		}
		for _, table := range []string{"batches", "inspection_items", "passport_audit_events"} {
			var n int64
			query := "SELECT count(*) FROM batches WHERE batch_code LIKE 'T4-GO-%'"
			if table != "batches" {
				query = "SELECT count(*) FROM " + table + " x JOIN batches b ON b.id=x.batch_id WHERE b.batch_code LIKE 'T4-GO-%'"
			}
			db.Raw(query).Scan(&n)
			if n != 25 {
				t.Errorf("%s count %d", table, n)
			}
		}
		t.Logf("5 writers,25 transactions,0 retries, elapsed=%s", time.Since(start))
	})
	t.Run("Integrity", func(t *testing.T) {
		var v string
		db.Raw("pragma integrity_check").Scan(&v)
		if v != "ok" {
			t.Fatal(v)
		}
		var rows []map[string]interface{}
		db.Raw("pragma foreign_key_check").Scan(&rows)
		if len(rows) != 0 {
			t.Fatal(rows)
		}
	})
}
