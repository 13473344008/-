package router

import (
	"github.com/gin-gonic/gin"
	jwt "github.com/go-admin-team/go-admin-core/v2/jwtauth"
	"go-admin/app/passport/apis"
	passportMiddleware "go-admin/app/passport/middleware"
	"go-admin/common/actions"
	"go-admin/common/middleware"
)

func init() { routerCheckRole = append(routerCheckRole, registerPassportBatches) }
func registerPassportBatches(v1 *gin.RouterGroup, auth *jwt.GinJWTMiddleware) {
	a := apis.Batches{}
	r := v1.Group("/passport-batches").Use(auth.MiddlewareFunc()).Use(passportMiddleware.LiveIdentity()).Use(middleware.AuthCheckRole()).Use(actions.PermissionAction())
	{
		r.GET("", a.List)
		r.GET("/:id", a.Get)
		r.POST("", a.Create)
		r.PUT("/:id", a.Update)
		r.POST("/:id/clone", a.Clone)
	}
}
