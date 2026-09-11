//go:build t4_schema

package version

import (
	_ "embed"
	"fmt"
	"go-admin/cmd/migrate/migration"
	"go-admin/cmd/migrate/migration/models"
	common "go-admin/common/models"
	"gorm.io/gorm"
	"strings"
)

//go:embed 1789084800000_review_workflow.sql
var reviewWorkflowSQL string

func init() { migration.Migrate.SetVersion("1789084800000", reviewWorkflow) }
func reviewWorkflow(db *gorm.DB, version string) error {
	return db.Transaction(func(tx *gorm.DB) error {
		if e := tx.Exec(reviewWorkflowSQL).Error; e != nil {
			return e
		}
		apis := []models.SysApi{
			{Id: 9401, Handle: "passport.Reviews.Queue", Title: "审核 Queue", Path: "/api/v1/passport-reviews", Type: "SYS", Action: "GET"},
			{Id: 9402, Handle: "passport.Reviews.Detail", Title: "审核 Detail", Path: "/api/v1/passport-batches/:id/review", Type: "SYS", Action: "GET"},
			{Id: 9403, Handle: "passport.Reviews.Readiness", Title: "审核 Readiness", Path: "/api/v1/passport-batches/:id/review/readiness", Type: "SYS", Action: "GET"},
			{Id: 9404, Handle: "passport.Reviews.Submit", Title: "审核 Submit", Path: "/api/v1/passport-batches/:id/review/submit", Type: "SYS", Action: "POST"},
			{Id: 9405, Handle: "passport.Reviews.Approve", Title: "审核 Approve", Path: "/api/v1/passport-batches/:id/review/approve", Type: "SYS", Action: "POST"},
			{Id: 9406, Handle: "passport.Reviews.Reject", Title: "审核 Reject", Path: "/api/v1/passport-batches/:id/review/reject", Type: "SYS", Action: "POST"},
			{Id: 9407, Handle: "passport.Reviews.Return", Title: "审核 Return", Path: "/api/v1/passport-batches/:id/review/return", Type: "SYS", Action: "POST"},
			{Id: 9408, Handle: "passport.Reviews.Archive", Title: "审核 Archive", Path: "/api/v1/passport-batches/:id/review/archive", Type: "SYS", Action: "POST"},
		}
		for _, a := range apis {
			var n int64
			if e := tx.Table("sys_api").Where("id=?", a.Id).Count(&n).Error; e != nil {
				return e
			}
			if n > 0 {
				return fmt.Errorf("review API id occupied")
			}
			if e := tx.Omit("DeletedAt").Create(&a).Error; e != nil {
				return e
			}
		}
		menus := []models.SysMenu{
			{MenuId: 9401, MenuName: "PassportReviews", Title: "审核队列", MenuType: "C", ParentId: 9100, Paths: "/0/9100/9401", Path: "/passport/reviews", Component: "/passport/reviews/index", Icon: "documentation", Sort: 3, Visible: "0", IsFrame: "1"},
			{MenuId: 9402, MenuName: "PassportReviewSubmit", Title: "提交审核", MenuType: "F", ParentId: 9201, Paths: "/0/9100/9201/9402", Permission: "passport:review:submit", Sort: 3, Visible: "0", IsFrame: "1"},
			{MenuId: 9403, MenuName: "PassportReviewDecide", Title: "批准或驳回", MenuType: "F", ParentId: 9401, Paths: "/0/9100/9401/9403", Permission: "passport:review:decide", Sort: 1, Visible: "0", IsFrame: "1"},
			{MenuId: 9404, MenuName: "PassportReviewReturn", Title: "撤销批准并改稿", MenuType: "F", ParentId: 9201, Paths: "/0/9100/9201/9404", Permission: "passport:review:return", Sort: 4, Visible: "0", IsFrame: "1"},
			{MenuId: 9405, MenuName: "PassportBatchArchive", Title: "归档批次", MenuType: "F", ParentId: 9201, Paths: "/0/9100/9201/9405", Permission: "passport:review:archive", Sort: 5, Visible: "0", IsFrame: "1"},
		}
		for _, m := range menus {
			var n int64
			if e := tx.Table("sys_menu").Where("menu_id=?", m.MenuId).Count(&n).Error; e != nil {
				return e
			}
			if n > 0 {
				return fmt.Errorf("review menu id occupied")
			}
			if e := tx.Omit("DeletedAt").Create(&m).Error; e != nil {
				return e
			}
		}
		for _, a := range apis {
			mid := 9401
			switch a.Id {
			case 9402:
				mid = 9201
			case 9403, 9404:
				mid = 9402
			case 9405, 9406:
				mid = 9403
			case 9407:
				mid = 9404
			case 9408:
				mid = 9405
			}
			if e := tx.Exec("INSERT INTO sys_menu_api_rule(sys_menu_menu_id,sys_api_id) VALUES(?,?)", mid, a.Id).Error; e != nil {
				return e
			}
		}
		// Lifecycle operations are admin-only, including future menu-derived grant rebuilds.
		if e := tx.Exec("UPDATE sys_menu_api_rule SET sys_menu_menu_id=9405 WHERE sys_api_id IN (SELECT id FROM sys_api WHERE path='/api/v1/passport-products/:id/archive' OR (path='/api/v1/passport-products/:id' AND action='PUT'))").Error; e != nil {
			return e
		}
		var admin struct{ RoleId int }
		if e := tx.Table("sys_role").Where("role_key='admin' AND deleted_at=0").Take(&admin).Error; e != nil {
			return e
		}
		for _, m := range menus {
			if e := tx.Exec("INSERT INTO sys_role_menu(role_id,menu_id) VALUES(?,?)", admin.RoleId, m.MenuId).Error; e != nil {
				return e
			}
		}
		for _, a := range apis {
			if e := tx.Exec("INSERT INTO casbin_rule(ptype,v0,v1,v2,v3,v4,v5) VALUES('p','admin',?,?,'','','')", a.Path, a.Action).Error; e != nil {
				return e
			}
		}
		// The upstream user model has one role_id. Composite role grants are the union of the two sets.
		var businessAPIs []models.SysApi
		if e := tx.Unscoped().Select("id,path,action").Where("path LIKE '/api/v1/passport-%'").Find(&businessAPIs).Error; e != nil {
			return e
		}
		for _, key := range []string{"passport_editor", "passport_reviewer", "passport_viewer", "passport_editor_reviewer"} {
			var n int64
			if e := tx.Table("sys_role").Where("role_key=?", key).Count(&n).Error; e != nil {
				return e
			}
			if n > 0 {
				return fmt.Errorf("reserved passport role occupied: %s", key)
			}
			role := models.SysRole{RoleName: map[string]string{"passport_editor": "Editor", "passport_reviewer": "Reviewer", "passport_viewer": "Viewer", "passport_editor_reviewer": "Editor + Reviewer"}[key], RoleKey: key, Status: "2", RoleSort: 90, DataScope: "1", Remark: "T8 business role; self review always prohibited"}
			if e := tx.Omit("DeletedAt").Create(&role).Error; e != nil {
				return e
			}
			editor := strings.Contains(key, "editor")
			reviewer := strings.Contains(key, "reviewer")
			ids := []int{9100, 9101, 9201}
			if editor {
				ids = append(ids, 9102, 9202, 9301, 9302, 9402, 9404)
			}
			if reviewer {
				ids = append(ids, 9401, 9403)
			}
			for _, id := range ids {
				if e := tx.Exec("INSERT INTO sys_role_menu(role_id,menu_id) VALUES(?,?)", role.RoleId, id).Error; e != nil {
					return e
				}
			}
			for _, a := range businessAPIs {
				grant := a.Action == "GET" && (a.Id != 9401 || reviewer)
				if editor && a.Action != "GET" && a.Id < 9401 && !strings.HasSuffix(a.Path, "/archive") && !(a.Path == "/api/v1/passport-products/:id" && a.Action == "PUT") {
					grant = true
				}
				if editor && (a.Id == 9404 || a.Id == 9407) {
					grant = true
				}
				if reviewer && (a.Id == 9405 || a.Id == 9406) {
					grant = true
				}
				if grant {
					if e := tx.Exec("INSERT INTO casbin_rule(ptype,v0,v1,v2,v3,v4,v5) VALUES('p',?,?,?,'','','')", key, a.Path, a.Action).Error; e != nil {
						return e
					}
				}
			}
		}
		return tx.Create(&common.Migration{Version: version}).Error
	})
}
