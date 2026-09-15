//go:build t4_schema

package version

import (
	"go-admin/cmd/migrate/migration"
	common "go-admin/common/models"
	"gorm.io/gorm"
)

func init() { migration.Migrate.SetVersion("1789450000000", contextualMedia) }
func contextualMedia(db *gorm.DB, version string) error {
	return db.Transaction(func(tx *gorm.DB) error {
		for _, table := range []string{"asset_links", "published_assets"} {
			if e := tx.Exec("ALTER TABLE " + table + " ADD COLUMN display_target TEXT NOT NULL DEFAULT ''").Error; e != nil {
				return e
			}
		}
		return tx.Create(&common.Migration{Version: version}).Error
	})
}
