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

//go:embed 1788998400000_custom_sections.sql
var customSectionsUpgrade string

func init() { migration.Migrate.SetVersion("1788998400000", customSections) }
func customSections(db *gorm.DB, version string) error {
	return db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Exec(customSectionsUpgrade).Error; err != nil {
			return err
		}
		apis := []models.SysApi{{Id: 9301, Handle: "passport.Sections.List", Title: "模块 List", Path: "/api/v1/passport-products/:id/revisions/:rid/sections", Type: "SYS", Action: "GET"}, {Id: 9302, Handle: "passport.Sections.Get", Title: "模块 Get", Path: "/api/v1/passport-products/:id/revisions/:rid/sections/:sid", Type: "SYS", Action: "GET"}, {Id: 9303, Handle: "passport.Sections.Create", Title: "模块 Create", Path: "/api/v1/passport-products/:id/revisions/:rid/sections", Type: "SYS", Action: "POST"}, {Id: 9304, Handle: "passport.Sections.Update", Title: "模块 Update", Path: "/api/v1/passport-products/:id/revisions/:rid/sections/:sid", Type: "SYS", Action: "PUT"}, {Id: 9305, Handle: "passport.Sections.Delete", Title: "模块 Delete", Path: "/api/v1/passport-products/:id/revisions/:rid/sections/:sid", Type: "SYS", Action: "DELETE"}, {Id: 9306, Handle: "passport.Sections.Reorder", Title: "模块 Reorder", Path: "/api/v1/passport-products/:id/revisions/:rid/sections/reorder", Type: "SYS", Action: "PUT"}, {Id: 9307, Handle: "passport.Sections.Translate", Title: "模块 Translate", Path: "/api/v1/passport-products/:id/revisions/:rid/sections/:sid/translations", Type: "SYS", Action: "PUT"}, {Id: 9308, Handle: "passport.Sections.List", Title: "模块 List", Path: "/api/v1/passport-batches/:id/sections", Type: "SYS", Action: "GET"}, {Id: 9309, Handle: "passport.Sections.Get", Title: "模块 Get", Path: "/api/v1/passport-batches/:id/sections/:sid", Type: "SYS", Action: "GET"}, {Id: 9310, Handle: "passport.Sections.Create", Title: "模块 Create", Path: "/api/v1/passport-batches/:id/sections", Type: "SYS", Action: "POST"}, {Id: 9311, Handle: "passport.Sections.Update", Title: "模块 Update", Path: "/api/v1/passport-batches/:id/sections/:sid", Type: "SYS", Action: "PUT"}, {Id: 9312, Handle: "passport.Sections.Delete", Title: "模块 Delete", Path: "/api/v1/passport-batches/:id/sections/:sid", Type: "SYS", Action: "DELETE"}, {Id: 9313, Handle: "passport.Sections.Reorder", Title: "模块 Reorder", Path: "/api/v1/passport-batches/:id/sections/reorder", Type: "SYS", Action: "PUT"}, {Id: 9314, Handle: "passport.Sections.Translate", Title: "模块 Translate", Path: "/api/v1/passport-batches/:id/sections/:sid/translations", Type: "SYS", Action: "PUT"}}

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
			{MenuId: 9301, MenuName: "PassportProductSectionsWrite", Title: "维护模板模块", MenuType: "F", ParentId: 9101, Paths: "/0/9100/9101/9301", Permission: "passport:sections:write", Sort: 2, Visible: "0", IsFrame: "1"},
			{MenuId: 9302, MenuName: "PassportBatchSectionsWrite", Title: "维护批次模块", MenuType: "F", ParentId: 9201, Paths: "/0/9100/9201/9302", Permission: "passport:sections:write", Sort: 2, Visible: "0", IsFrame: "1"},
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
			menu := 9301
			if a.Id > 9307 {
				menu = 9302
			}
			if a.Action == "GET" {
				menu = 9101
				if a.Id > 9307 {
					menu = 9201
				}
			}
			if err := tx.Exec("INSERT INTO sys_menu_api_rule(sys_menu_menu_id,sys_api_id) VALUES(?,?)", menu, a.Id).Error; err != nil {
				return err
			}
		}
		var role struct{ RoleId int }
		if err := tx.Table("sys_role").Where("role_key=? AND deleted_at=0", "admin").Take(&role).Error; err != nil {
			return err
		}
		for _, id := range []int{9301, 9302} {
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
