package router

import (
	"github.com/gin-gonic/gin"
	jwt "github.com/go-admin-team/go-admin-core/v2/jwtauth"
	"go-admin/app/passport/apis"
	passportMiddleware "go-admin/app/passport/middleware"
	"go-admin/common/actions"
	"go-admin/common/middleware"
)

func init() { routerCheckRole = append(routerCheckRole, registerPassportMediaRouter) }
func registerPassportMediaRouter(v1 *gin.RouterGroup, auth *jwt.GinJWTMiddleware) {
	a := apis.Media{}
	for _, path := range []string{"/passport-products/:id/revisions/:rid/media", "/passport-products/:id/revisions/:rid/sections/:sid/media", "/passport-batches/:id/sections/:sid/media"} {
		r := v1.Group(path).Use(auth.MiddlewareFunc()).Use(passportMiddleware.LiveIdentity()).Use(middleware.AuthCheckRole()).Use(actions.PermissionAction())
		r.GET("", a.List)
		r.POST("", a.Upload)
		r.DELETE("/:aid", a.Detach)
	}
}
