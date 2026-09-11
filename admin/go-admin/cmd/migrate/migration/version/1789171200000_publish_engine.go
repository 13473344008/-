//go:build t4_schema

package version

import (
	_ "embed"
	"go-admin/cmd/migrate/migration"
	"go-admin/cmd/migrate/migration/models"
	common "go-admin/common/models"
	"gorm.io/gorm"
)

//go:embed 1789171200000_publish_engine.sql
var publishEngineSQL string

func init() { migration.Migrate.SetVersion("1789171200000", publishEngine) }
func publishEngine(db *gorm.DB, version string) error {
	return db.Transaction(func(tx *gorm.DB) error {
		if e := tx.Exec(publishEngineSQL).Error; e != nil {
			return e
		}
		menu := models.SysMenu{MenuId: 9501, MenuName: "PassportPublish", Title: "发布数字身份证", MenuType: "F", ParentId: 9201, Paths: "/0/9100/9201/9501", Permission: "passport:publish:execute", Sort: 6, Visible: "0", IsFrame: "1"}
		if e := tx.Omit("DeletedAt").Create(&menu).Error; e != nil {
			return e
		}
		if e := tx.Exec("INSERT INTO sys_role_menu(role_id,menu_id) SELECT role_id,9501 FROM sys_role WHERE role_key='admin' AND deleted_at=0").Error; e != nil {
			return e
		}
		for i, route := range []struct{ Path, Action, Handle string }{{"/api/v1/passport-batches/:id/publication", "GET", "Status"}, {"/api/v1/passport-batches/:id/publication", "POST", "Publish"}, {"/api/v1/passport-batches/:id/publication/reconcile", "POST", "Reconcile"}} {
			a := models.SysApi{Id: 9501 + i, Handle: "passport.Publishing." + route.Handle, Title: "发布 " + route.Handle, Path: route.Path, Type: "SYS", Action: route.Action}
			if e := tx.Omit("DeletedAt").Create(&a).Error; e != nil {
				return e
			}
			mid := 9501
			if route.Action == "GET" {
				mid = 9201
			}
			if e := tx.Exec("INSERT INTO sys_menu_api_rule(sys_menu_menu_id,sys_api_id) VALUES(?,?)", mid, a.Id).Error; e != nil {
				return e
			}
			roles := []string{"admin"}
			if route.Action == "GET" {
				roles = append(roles, "passport_editor", "passport_reviewer", "passport_viewer", "passport_editor_reviewer")
			}
			for _, role := range roles {
				if e := tx.Exec("INSERT INTO casbin_rule(ptype,v0,v1,v2,v3,v4,v5) VALUES('p',?,?,?,'','','')", role, route.Path, route.Action).Error; e != nil {
					return e
				}
			}
		}
		return tx.Create(&common.Migration{Version: version}).Error
	})
}
