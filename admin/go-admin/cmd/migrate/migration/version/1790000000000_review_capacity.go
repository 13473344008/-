//go:build t4_schema

package version

import (
	"fmt"
	"go-admin/cmd/migrate/migration"
	common "go-admin/common/models"
	"gorm.io/gorm"
	"strings"
)

func init() { migration.Migrate.SetVersion("1790000000000", reviewCapacity) }

// SQLite cannot ALTER a CHECK constraint. Copy all rows transactionally and
// restore the original indexes/triggers; never modify frozen review contents.
func reviewCapacity(db *gorm.DB, version string) error {
	return db.Connection(func(conn *gorm.DB) error {
		conn = conn.Session(&gorm.Session{NewDB: true})
		var fk int
		if e := conn.Raw("PRAGMA foreign_keys").Scan(&fk).Error; e != nil {
			return e
		}
		if e := conn.Exec("PRAGMA foreign_keys=OFF").Error; e != nil {
			return e
		}
		defer conn.Exec(fmt.Sprintf("PRAGMA foreign_keys=%d", fk))
		return conn.Transaction(func(tx *gorm.DB) error {
			var ddl string
			if e := tx.Raw("SELECT sql FROM sqlite_master WHERE type='table' AND name='review_records'").Scan(&ddl).Error; e != nil {
				return e
			}
			old := "length(CAST(candidate_input AS BLOB))<=4194304"
			if strings.Count(ddl, old) != 1 {
				return fmt.Errorf("unexpected review_records constraint; migration stopped")
			}
			var objects []struct {
				Name string
				Type string
				SQL  string
			}
			if e := tx.Raw("SELECT name,type,sql FROM sqlite_master WHERE sql IS NOT NULL AND (type='trigger' OR (type='index' AND tbl_name='review_records')) ORDER BY type,name").Scan(&objects).Error; e != nil {
				return e
			}
			for _, o := range objects {
				if o.Type == "trigger" {
					if e := tx.Exec(`DROP TRIGGER "` + strings.ReplaceAll(o.Name, `"`, `""`) + `"`).Error; e != nil {
						return e
					}
				}
			}
			create := strings.Replace(ddl, "CREATE TABLE review_records", "CREATE TABLE review_records_capacity", 1)
			if create == ddl {
				return fmt.Errorf("unexpected review table declaration")
			}
			create = strings.Replace(create, old, "length(CAST(candidate_input AS BLOB))<=33554432", 1)
			if e := tx.Exec(create).Error; e != nil {
				return e
			}
			if e := tx.Exec("INSERT INTO review_records_capacity SELECT * FROM review_records").Error; e != nil {
				return e
			}
			for _, q := range []string{"DROP TABLE review_records", "ALTER TABLE review_records_capacity RENAME TO review_records"} {
				if e := tx.Exec(q).Error; e != nil {
					return e
				}
			}
			for _, o := range objects {
				if e := tx.Exec(o.SQL).Error; e != nil {
					return e
				}
			}
			rows, e := tx.Raw("PRAGMA foreign_key_check").Rows()
			if e != nil {
				return e
			}
			bad := rows.Next()
			rows.Close()
			if bad {
				return fmt.Errorf("foreign key validation failed")
			}

			return tx.Create(&common.Migration{Version: version}).Error
		})
	})
}
