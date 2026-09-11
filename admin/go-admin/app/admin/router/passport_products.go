package router

import (
	"github.com/gin-gonic/gin"
	jwt "github.com/go-admin-team/go-admin-core/v2/jwtauth"
	"go-admin/app/passport/apis"
	passportMiddleware "go-admin/app/passport/middleware"
	"go-admin/common/actions"
	"go-admin/common/middleware"
)

func init() { routerCheckRole = append(routerCheckRole, registerPassportProducts) }
func registerPassportProducts(v1 *gin.RouterGroup, auth *jwt.GinJWTMiddleware) {
	a := apis.Products{}
	r := v1.Group("/passport-products").Use(auth.MiddlewareFunc()).Use(passportMiddleware.LiveIdentity()).Use(middleware.AuthCheckRole()).Use(actions.PermissionAction())
	r.GET("", a.List)
	r.GET("/:id", a.Get)
	r.POST("", a.Create)
	r.PUT("/:id", a.Update)
	r.POST("/:id/archive", a.Archive)
	r.GET("/:id/revisions", a.Revisions)
	r.GET("/:id/revisions/:rid", a.Revision)
	r.POST("/:id/revisions", a.Clone)
	r.PUT("/:id/revisions/:rid", a.EditRevision)
	r.PUT("/:id/revisions/:rid/translations", a.Translate)
	r.POST("/:id/revisions/:rid/seal", a.Seal)
	r.PUT("/:id/default-revision", a.Default)
}
