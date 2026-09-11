//go:build t4_schema

package version

import (
	"go-admin/cmd/migrate/migration"
	"go-admin/cmd/migrate/migration/models"
	common "go-admin/common/models"
	"gorm.io/gorm"
)

func init() { migration.Migrate.SetVersion("1789430400000", mediaPermissions) }
func mediaPermissions(db *gorm.DB, version string) error {
	return db.Transaction(func(tx *gorm.DB) error {
		menu := models.SysMenu{MenuId: 9801, MenuName: "PassportMediaWrite", Title: "维护工作图片", MenuType: "F", ParentId: 9101, Paths: "/0/9100/9101/9801", Permission: "passport:media:write", Sort: 8, Visible: "0", IsFrame: "1"}
		if e := tx.Omit("DeletedAt").Create(&menu).Error; e != nil {
			return e
		}
		if e := tx.Exec("INSERT INTO sys_role_menu(role_id,menu_id) SELECT role_id,9801 FROM sys_role WHERE role_key IN ('admin','passport_editor','passport_editor_reviewer') AND deleted_at=0").Error; e != nil {
			return e
		}
		i := 9801
		for _, path := range []string{"/api/v1/passport-products/:id/revisions/:rid/media", "/api/v1/passport-products/:id/revisions/:rid/sections/:sid/media", "/api/v1/passport-batches/:id/sections/:sid/media"} {
			for _, verb := range []string{"GET", "POST", "DELETE"} {
				p := path
				if verb == "DELETE" {
					p += "/:aid"
				}
				a := models.SysApi{Id: i, Handle: "passport.Media", Title: "工作图片 " + verb, Path: p, Type: "SYS", Action: verb}
				i++
				if e := tx.Omit("DeletedAt").Create(&a).Error; e != nil {
					return e
				}
				mid := 9801
				if verb == "GET" {
					mid = 9101
				}
				if e := tx.Exec("INSERT INTO sys_menu_api_rule(sys_menu_menu_id,sys_api_id) VALUES(?,?)", mid, a.Id).Error; e != nil {
					return e
				}
				roles := []string{"admin", "passport_editor", "passport_editor_reviewer"}
				if verb == "GET" {
					roles = append(roles, "passport_reviewer", "passport_viewer")
				}
				for _, role := range roles {
					if e := tx.Exec("INSERT INTO casbin_rule(ptype,v0,v1,v2,v3,v4,v5) VALUES('p',?,?,?,'','','')", role, p, verb).Error; e != nil {
						return e
					}
				}
			}
		}
		return tx.Create(&common.Migration{Version: version}).Error
	})
}
