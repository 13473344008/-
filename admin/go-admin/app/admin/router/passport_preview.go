package router

import (
	"github.com/gin-gonic/gin"
	jwt "github.com/go-admin-team/go-admin-core/v2/jwtauth"
	"go-admin/app/passport/apis"
	passportMiddleware "go-admin/app/passport/middleware"
	"go-admin/common/actions"
	"go-admin/common/middleware"
)

func init() { routerCheckRole = append(routerCheckRole, registerPassportPreview) }
func registerPassportPreview(v1 *gin.RouterGroup, auth *jwt.GinJWTMiddleware) {
	a := apis.Reviews{}
	v1.Group("/passport-batches/:id/preview").Use(func(c *gin.Context) { c.Header("Cache-Control", "no-store, private"); c.Next() }).Use(auth.MiddlewareFunc()).Use(passportMiddleware.LiveIdentity()).Use(middleware.AuthCheckRole()).Use(actions.PermissionAction()).GET("", a.Preview)
}
