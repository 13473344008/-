//go:build t4_schema

package version

import (
	_ "embed"
	"fmt"
	"go-admin/cmd/migrate/migration"
	common "go-admin/common/models"
	"gorm.io/gorm"
)

//go:embed 1788739201000_passport_nullable.sql
var passportNullableSchema string

func init() {
	migration.Migrate.SetVersion("1788739201000", func(db *gorm.DB, version string) error {
		return db.Transaction(func(tx *gorm.DB) error {
			var n0 int64
			if err := tx.Table("products").Count(&n0).Error; err != nil {
				return err
			}
			if n0 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in products; refusing destructive rebuild")
			}
			var n1 int64
			if err := tx.Table("product_revisions").Count(&n1).Error; err != nil {
				return err
			}
			if n1 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in product_revisions; refusing destructive rebuild")
			}
			var n2 int64
			if err := tx.Table("product_revision_translations").Count(&n2).Error; err != nil {
				return err
			}
			if n2 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in product_revision_translations; refusing destructive rebuild")
			}
			var n3 int64
			if err := tx.Table("batches").Count(&n3).Error; err != nil {
				return err
			}
			if n3 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in batches; refusing destructive rebuild")
			}
			var n4 int64
			if err := tx.Table("batch_overrides").Count(&n4).Error; err != nil {
				return err
			}
			if n4 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in batch_overrides; refusing destructive rebuild")
			}
			var n5 int64
			if err := tx.Table("batch_override_translations").Count(&n5).Error; err != nil {
				return err
			}
			if n5 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in batch_override_translations; refusing destructive rebuild")
			}
			var n6 int64
			if err := tx.Table("inspection_items").Count(&n6).Error; err != nil {
				return err
			}
			if n6 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in inspection_items; refusing destructive rebuild")
			}
			var n7 int64
			if err := tx.Table("inspection_item_translations").Count(&n7).Error; err != nil {
				return err
			}
			if n7 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in inspection_item_translations; refusing destructive rebuild")
			}
			var n8 int64
			if err := tx.Table("certifications").Count(&n8).Error; err != nil {
				return err
			}
			if n8 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in certifications; refusing destructive rebuild")
			}
			var n9 int64
			if err := tx.Table("certification_translations").Count(&n9).Error; err != nil {
				return err
			}
			if n9 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in certification_translations; refusing destructive rebuild")
			}
			var n10 int64
			if err := tx.Table("certification_links").Count(&n10).Error; err != nil {
				return err
			}
			if n10 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in certification_links; refusing destructive rebuild")
			}
			var n11 int64
			if err := tx.Table("media_assets").Count(&n11).Error; err != nil {
				return err
			}
			if n11 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in media_assets; refusing destructive rebuild")
			}
			var n12 int64
			if err := tx.Table("asset_links").Count(&n12).Error; err != nil {
				return err
			}
			if n12 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in asset_links; refusing destructive rebuild")
			}
			var n13 int64
			if err := tx.Table("custom_sections").Count(&n13).Error; err != nil {
				return err
			}
			if n13 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in custom_sections; refusing destructive rebuild")
			}
			var n14 int64
			if err := tx.Table("custom_section_translations").Count(&n14).Error; err != nil {
				return err
			}
			if n14 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in custom_section_translations; refusing destructive rebuild")
			}
			var n15 int64
			if err := tx.Table("passport_revisions").Count(&n15).Error; err != nil {
				return err
			}
			if n15 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in passport_revisions; refusing destructive rebuild")
			}
			var n16 int64
			if err := tx.Table("published_assets").Count(&n16).Error; err != nil {
				return err
			}
			if n16 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in published_assets; refusing destructive rebuild")
			}
			var n17 int64
			if err := tx.Table("publish_records").Count(&n17).Error; err != nil {
				return err
			}
			if n17 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in publish_records; refusing destructive rebuild")
			}
			var n18 int64
			if err := tx.Table("passport_audit_events").Count(&n18).Error; err != nil {
				return err
			}
			if n18 != 0 {
				return fmt.Errorf("T4 nullable correction requires empty business tables; found rows in passport_audit_events; refusing destructive rebuild")
			}
			if err := tx.Exec(passportNullableSchema).Error; err != nil {
				return err
			}
			return tx.Create(&common.Migration{Version: version}).Error
		})
	})
}
