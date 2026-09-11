//go:build t4_schema

package version

import (
	_ "embed"
	"fmt"
	"go-admin/cmd/migrate/migration"
	"go-admin/cmd/migrate/migration/models"
	common "go-admin/common/models"
	"gorm.io/gorm"
)

//go:embed 1788912000000_batch_management.sql
var batchManagementUpgrade string

func init() { migration.Migrate.SetVersion("1788912000000", batchManagement) }
func batchManagement(db *gorm.DB, version string) error {
	return db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Exec(batchManagementUpgrade).Error; err != nil {
			return err
		}
		apis := []models.SysApi{
			{Id: 9201, Handle: "passport.Batches.List", Title: "批次 List", Path: "/api/v1/passport-batches", Type: "SYS", Action: "GET"},
			{Id: 9202, Handle: "passport.Batches.Get", Title: "批次 Get", Path: "/api/v1/passport-batches/:id", Type: "SYS", Action: "GET"},
			{Id: 9203, Handle: "passport.Batches.Create", Title: "批次 Create", Path: "/api/v1/passport-batches", Type: "SYS", Action: "POST"},
			{Id: 9204, Handle: "passport.Batches.Update", Title: "批次 Update", Path: "/api/v1/passport-batches/:id", Type: "SYS", Action: "PUT"},
			{Id: 9205, Handle: "passport.Batches.Clone", Title: "批次 Clone", Path: "/api/v1/passport-batches/:id/clone", Type: "SYS", Action: "POST"},
		}

		for _, a := range apis {
			var n int64
			if err := tx.Unscoped().Model(&models.SysApi{}).Where("id=?", a.Id).Count(&n).Error; err != nil {
				return err
			}
			if n > 0 {
				return fmt.Errorf("product API id %d already occupied", a.Id)
			}
			if err := tx.Omit("DeletedAt").Create(&a).Error; err != nil {
				return err
			}
		}
		pages := []models.SysMenu{
			{MenuId: 9201, MenuName: "PassportBatches", Title: "批次身份证", Path: "/passport/batches", Paths: "/0/9100/9201", MenuType: "C", ParentId: 9100, Component: "/passport/batches/index", Icon: "documentation", Sort: 2, Visible: "0", IsFrame: "1"},
			{MenuId: 9202, MenuName: "PassportBatchesWrite", Title: "维护批次身份证", MenuType: "F", ParentId: 9201, Paths: "/0/9100/9201/9202", Permission: "passport:batches:write", Sort: 1, Visible: "0", IsFrame: "1"},
		}
		for i := range pages {
			var n int64
			if err := tx.Unscoped().Model(&models.SysMenu{}).Where("menu_id=?", pages[i].MenuId).Count(&n).Error; err != nil {
				return err
			}
			if n > 0 {
				return fmt.Errorf("product menu id occupied")
			}
			if err := tx.Omit("DeletedAt").Create(&pages[i]).Error; err != nil {
				return err
			}
		}
		for _, a := range apis {
			menu := 9202
			if a.Action == "GET" {
				menu = 9201
			}
			if err := tx.Exec("INSERT INTO sys_menu_api_rule(sys_menu_menu_id,sys_api_id) VALUES(?,?)", menu, a.Id).Error; err != nil {
				return err
			}
		}
		var role struct{ RoleId int }
		if err := tx.Table("sys_role").Where("role_key=? AND deleted_at=0", "admin").Take(&role).Error; err != nil {
			return err
		}
		for _, id := range []int{9201, 9202} {
			if err := tx.Exec("INSERT INTO sys_role_menu(role_id,menu_id) VALUES(?,?)", role.RoleId, id).Error; err != nil {
				return err
			}
		}
		for _, a := range apis {
			if err := tx.Exec("INSERT INTO casbin_rule(ptype,v0,v1,v2,v3,v4,v5) VALUES('p','admin',?,?,'','','')", a.Path, a.Action).Error; err != nil {
				return err
			}
		}
		return tx.Create(&common.Migration{Version: version}).Error
	})
}
