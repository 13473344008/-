//go:build t4_schema

package version

import (
	_ "embed"
	"go-admin/cmd/migrate/migration"
	common "go-admin/common/models"
	"gorm.io/gorm"
)

//go:embed 1788739200000_passport.sql
var passportSchema string

func init() {
	migration.Migrate.SetVersion("1788739200000", func(db *gorm.DB, version string) error {
		return db.Transaction(func(tx *gorm.DB) error {
			if err := tx.Exec(passportSchema).Error; err != nil {
				return err
			}
			return tx.Create(&common.Migration{Version: version}).Error
		})
	})
}
