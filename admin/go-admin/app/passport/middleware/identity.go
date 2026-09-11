package middleware

import (
	"github.com/gin-gonic/gin"
	jwt "github.com/go-admin-team/go-admin-core/v2/jwtauth"
	"github.com/go-admin-team/go-admin-core/v2/jwtauth/user"
	"github.com/go-admin-team/go-admin-core/v2/sdk/api"
	"github.com/go-admin-team/go-admin-core/v2/sdk/pkg"
)

// Re-read current account and role before the existing Casbin middleware.
// JWT remains the only authentication mechanism; stale role claims cannot retain privileges.
func LiveIdentity() gin.HandlerFunc {
	return func(c *gin.Context) {
		e := api.Api{}
		e.MakeContext(c)
		db, err := pkg.GetOrm(c)
		if err != nil {
			e.Error(500, nil, "权限信息暂时不可用")
			c.Abort()
			return
		}
		var row struct {
			RoleKey   string
			RoleID    int
			DataScope string
			DeptID    int
		}
		err = db.Table("sys_user u").Select("r.role_key,r.role_id,r.data_scope,u.dept_id").Joins("JOIN sys_role r ON r.role_id=u.role_id").Where("u.user_id=? AND u.status='2' AND u.deleted_at=0 AND r.status='2' AND r.deleted_at=0", user.GetUserId(c)).Take(&row).Error
		if err != nil {
			e.Error(401, nil, "账号或角色已停用，请重新登录或联系管理员")
			c.Abort()
			return
		}
		claims := user.ExtractClaims(c)
		claims["rolekey"] = row.RoleKey
		claims["roleid"] = float64(row.RoleID)
		claims["datascope"] = row.DataScope
		claims["deptid"] = float64(row.DeptID)
		c.Set(jwt.JwtPayloadKey, claims)
		c.Next()
	}
}
