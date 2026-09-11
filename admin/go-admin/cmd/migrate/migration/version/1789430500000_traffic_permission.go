//go:build t4_schema

package version

import (
	"go-admin/cmd/migrate/migration"
	"go-admin/cmd/migrate/migration/models"
	common "go-admin/common/models"
	"gorm.io/gorm"
)

func init() { migration.Migrate.SetVersion("1789430500000", trafficPermission) }
func trafficPermission(db *gorm.DB, version string) error {
	return db.Transaction(func(tx *gorm.DB) error {
		a := models.SysApi{Id: 9901, Handle: "passport.Traffic", Title: "二维码页面访问统计", Path: "/api/v1/passport-traffic", Type: "SYS", Action: "GET"}
		if e := tx.Omit("DeletedAt").Create(&a).Error; e != nil {
			return e
		}
		if e := tx.Exec("INSERT INTO sys_menu_api_rule(sys_menu_menu_id,sys_api_id) VALUES(9101,9901)").Error; e != nil {
			return e
		}
		for _, role := range []string{"admin", "passport_editor", "passport_reviewer", "passport_viewer", "passport_editor_reviewer"} {
			if e := tx.Exec("INSERT INTO casbin_rule(ptype,v0,v1,v2,v3,v4,v5) VALUES('p',?,'/api/v1/passport-traffic','GET','','','')", role).Error; e != nil {
				return e
			}
		}
		return tx.Create(&common.Migration{Version: version}).Error
	})
}
