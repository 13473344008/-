package router

import (
	"github.com/gin-gonic/gin"
	jwt "github.com/go-admin-team/go-admin-core/v2/jwtauth"
	"go-admin/app/passport/apis"
	passportMiddleware "go-admin/app/passport/middleware"
	"go-admin/common/actions"
	"go-admin/common/middleware"
)

func init() { routerCheckRole = append(routerCheckRole, registerPassportTrafficRouter) }
func registerPassportTrafficRouter(v1 *gin.RouterGroup, auth *jwt.GinJWTMiddleware) {
	a := apis.Traffic{}
	r := v1.Group("/passport-traffic").Use(auth.MiddlewareFunc()).Use(passportMiddleware.LiveIdentity()).Use(middleware.AuthCheckRole()).Use(actions.PermissionAction())
	r.GET("", a.List)
}
