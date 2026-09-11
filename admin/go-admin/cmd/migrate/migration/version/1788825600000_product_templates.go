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

//go:embed 1788825600000_product_templates.sql
var productTemplateUpgrade string

func init() { migration.Migrate.SetVersion("1788825600000", productTemplates) }
func productTemplates(db *gorm.DB, version string) error {
	return db.Transaction(func(tx *gorm.DB) error {
		if err := tx.Exec(productTemplateUpgrade).Error; err != nil {
			return err
		}
		apis := []models.SysApi{
			{Id: 9101, Handle: "passport.Products.List", Title: "产品模板 List", Path: "/api/v1/passport-products", Type: "SYS", Action: "GET"},
			{Id: 9102, Handle: "passport.Products.Get", Title: "产品模板 Get", Path: "/api/v1/passport-products/:id", Type: "SYS", Action: "GET"},
			{Id: 9103, Handle: "passport.Products.Create", Title: "产品模板 Create", Path: "/api/v1/passport-products", Type: "SYS", Action: "POST"},
			{Id: 9104, Handle: "passport.Products.Update", Title: "产品模板 Update", Path: "/api/v1/passport-products/:id", Type: "SYS", Action: "PUT"},
			{Id: 9105, Handle: "passport.Products.Archive", Title: "产品模板 Archive", Path: "/api/v1/passport-products/:id/archive", Type: "SYS", Action: "POST"},
			{Id: 9106, Handle: "passport.Products.Revisions", Title: "产品模板 Revisions", Path: "/api/v1/passport-products/:id/revisions", Type: "SYS", Action: "GET"},
			{Id: 9107, Handle: "passport.Products.Revision", Title: "产品模板 Revision", Path: "/api/v1/passport-products/:id/revisions/:rid", Type: "SYS", Action: "GET"},
			{Id: 9108, Handle: "passport.Products.Clone", Title: "产品模板 Clone", Path: "/api/v1/passport-products/:id/revisions", Type: "SYS", Action: "POST"},
			{Id: 9109, Handle: "passport.Products.EditRevision", Title: "产品模板 EditRevision", Path: "/api/v1/passport-products/:id/revisions/:rid", Type: "SYS", Action: "PUT"},
			{Id: 9110, Handle: "passport.Products.Translate", Title: "产品模板 Translate", Path: "/api/v1/passport-products/:id/revisions/:rid/translations", Type: "SYS", Action: "PUT"},
			{Id: 9111, Handle: "passport.Products.Seal", Title: "产品模板 Seal", Path: "/api/v1/passport-products/:id/revisions/:rid/seal", Type: "SYS", Action: "POST"},
			{Id: 9112, Handle: "passport.Products.Default", Title: "产品模板 Default", Path: "/api/v1/passport-products/:id/default-revision", Type: "SYS", Action: "PUT"},
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
			{MenuId: 9100, MenuName: "ProductPassport", Title: "产品数字身份证", Path: "/passport", Paths: "/0/9100", MenuType: "M", Component: "Layout", Icon: "documentation", Sort: 105, Visible: "0", IsFrame: "1"},
			{MenuId: 9101, MenuName: "PassportProducts", Title: "产品模板", Path: "/passport/products", Paths: "/0/9100/9101", MenuType: "C", ParentId: 9100, Component: "/passport/products/index", Icon: "documentation", Sort: 1, Visible: "0", IsFrame: "1"},
			{MenuId: 9102, MenuName: "PassportProductsWrite", Title: "维护产品模板", MenuType: "F", ParentId: 9101, Paths: "/0/9100/9101/9102", Permission: "passport:products:write", Sort: 1, Visible: "0", IsFrame: "1"},
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
			menu := 9102
			if a.Action == "GET" {
				menu = 9101
			}
			if err := tx.Exec("INSERT INTO sys_menu_api_rule(sys_menu_menu_id,sys_api_id) VALUES(?,?)", menu, a.Id).Error; err != nil {
				return err
			}
		}
		var role struct{ RoleId int }
		if err := tx.Table("sys_role").Where("role_key=? AND deleted_at=0", "admin").Take(&role).Error; err != nil {
			return err
		}
		for _, id := range []int{9100, 9101, 9102} {
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
