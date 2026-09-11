//go:build t4_schema

package version

import (
	"go-admin/cmd/migrate/migration"
	"go-admin/cmd/migrate/migration/models"
	common "go-admin/common/models"
	"gorm.io/gorm"
)

func init() { migration.Migrate.SetVersion("1789344000000", privatePreview) }
func privatePreview(db *gorm.DB, version string) error {
	return db.Transaction(func(tx *gorm.DB) error {
		menu := models.SysMenu{MenuId: 9701, MenuName: "PassportPrivatePreview", Title: "内部数字身份证预览", MenuType: "F", ParentId: 9201, Paths: "/0/9100/9201/9701", Permission: "passport:preview:read", Sort: 7, Visible: "0", IsFrame: "1"}
		if e := tx.Omit("DeletedAt").Create(&menu).Error; e != nil {
			return e
		}
		if e := tx.Exec("INSERT INTO sys_role_menu(role_id,menu_id) SELECT role_id,9701 FROM sys_role WHERE role_key IN ('admin','passport_editor','passport_reviewer','passport_viewer','passport_editor_reviewer') AND deleted_at=0").Error; e != nil {
			return e
		}
		a := models.SysApi{Id: 9701, Handle: "passport.Reviews.Preview", Title: "内部数字身份证预览", Path: "/api/v1/passport-batches/:id/preview", Type: "SYS", Action: "GET"}
		if e := tx.Omit("DeletedAt").Create(&a).Error; e != nil {
			return e
		}
		if e := tx.Exec("INSERT INTO sys_menu_api_rule(sys_menu_menu_id,sys_api_id) VALUES(9701,9701)").Error; e != nil {
			return e
		}
		for _, role := range []string{"admin", "passport_editor", "passport_reviewer", "passport_viewer", "passport_editor_reviewer"} {
			if e := tx.Exec("INSERT INTO casbin_rule(ptype,v0,v1,v2,v3,v4,v5) VALUES('p',?,'/api/v1/passport-batches/:id/preview','GET','','','')", role).Error; e != nil {
				return e
			}
		}
		return tx.Create(&common.Migration{Version: version}).Error
	})
}
