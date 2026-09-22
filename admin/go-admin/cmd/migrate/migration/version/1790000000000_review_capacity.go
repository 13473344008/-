//go:build t4_schema

package version

import (
	"context"
	"errors"
	"fmt"
	"go-admin/cmd/migrate/migration"
	"gorm.io/gorm"
	"strings"
	"time"
)

func init() { migration.Migrate.SetVersion("1790000000000", reviewCapacity) }

// Use one SQL connection directly: resolver callbacks can otherwise reroute a
// GORM statement away from its pinned connection and deadlock a one-slot pool.
func reviewCapacity(db *gorm.DB, version string) (result error) {
	pool, err := db.DB()
	if err != nil {
		return err
	}
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	conn, err := pool.Conn(ctx)
	if err != nil {
		return err
	}
	defer conn.Close()
	var fk int
	if err = conn.QueryRowContext(ctx, "PRAGMA foreign_keys").Scan(&fk); err != nil {
		return err
	}
	if _, err = conn.ExecContext(ctx, "PRAGMA foreign_keys=OFF"); err != nil {
		return err
	}
	defer func() {
		restoreCtx, stop := context.WithTimeout(context.Background(), 5*time.Second)
		defer stop()
		_, err := conn.ExecContext(restoreCtx, fmt.Sprintf("PRAGMA foreign_keys=%d", fk))
		result = errors.Join(result, err)
	}()
	tx, err := conn.BeginTx(ctx, nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var ddl string
	if err = tx.QueryRowContext(ctx, "SELECT sql FROM sqlite_master WHERE type='table' AND name='review_records'").Scan(&ddl); err != nil {
		return err
	}
	old := "length(CAST(candidate_input AS BLOB))<=4194304"
	if strings.Count(ddl, old) != 1 {
		return fmt.Errorf("unexpected review_records constraint; migration stopped")
	}
	rows, err := tx.QueryContext(ctx, "SELECT name,type,sql FROM sqlite_master WHERE sql IS NOT NULL AND (type='trigger' OR (type='index' AND tbl_name='review_records')) ORDER BY type,name")
	if err != nil {
		return err
	}
	type object struct{ name, kind, sql string }
	var objects []object
	for rows.Next() {
		var o object
		if err = rows.Scan(&o.name, &o.kind, &o.sql); err != nil {
			rows.Close()
			return err
		}
		objects = append(objects, o)
	}
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	exec := func(q string) error { _, err := tx.ExecContext(ctx, q); return err }
	for _, o := range objects {
		if o.kind == "trigger" {
			if err = exec(`DROP TRIGGER "` + strings.ReplaceAll(o.name, `"`, `""`) + `"`); err != nil {
				return err
			}
		}
	}
	create := strings.Replace(ddl, "CREATE TABLE review_records", "CREATE TABLE review_records_capacity", 1)
	if create == ddl {
		return fmt.Errorf("unexpected review table declaration")
	}
	create = strings.Replace(create, old, "length(CAST(candidate_input AS BLOB))<=33554432", 1)
	for _, q := range []string{create, "INSERT INTO review_records_capacity SELECT * FROM review_records", "DROP TABLE review_records", "ALTER TABLE review_records_capacity RENAME TO review_records"} {
		if err = exec(q); err != nil {
			return err
		}
	}
	for _, o := range objects {
		if err = exec(o.sql); err != nil {
			return err
		}
	}
	rows, err = tx.QueryContext(ctx, "PRAGMA foreign_key_check")
	if err != nil {
		return err
	}
	bad := rows.Next()
	err = rows.Err()
	rows.Close()
	if err != nil {
		return err
	}
	if bad {
		return fmt.Errorf("foreign key validation failed")
	}
	if _, err = tx.ExecContext(ctx, "INSERT INTO sys_migration(version,apply_time) VALUES(?,?)", version, time.Now()); err != nil {
		return err
	}
	return tx.Commit()
}
