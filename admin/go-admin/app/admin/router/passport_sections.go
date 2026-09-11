package router

import (
	"github.com/gin-gonic/gin"
	jwt "github.com/go-admin-team/go-admin-core/v2/jwtauth"
	"go-admin/app/passport/apis"
	passportMiddleware "go-admin/app/passport/middleware"
	"go-admin/common/actions"
	"go-admin/common/middleware"
)

func init() { routerCheckRole = append(routerCheckRole, registerPassportSectionsRouter) }
func registerPassportSectionsRouter(v1 *gin.RouterGroup, authMiddleware *jwt.GinJWTMiddleware) {
	a := apis.Sections{}
	for _, path := range []string{"/passport-products/:id/revisions/:rid/sections", "/passport-batches/:id/sections"} {
		r := v1.Group(path).Use(authMiddleware.MiddlewareFunc()).Use(passportMiddleware.LiveIdentity()).Use(middleware.AuthCheckRole()).Use(actions.PermissionAction())
		r.GET("", a.List)
		r.GET("/:sid", a.Get)
		r.POST("", a.Create)
		r.PUT("/:sid", a.Update)
		r.DELETE("/:sid", a.Delete)
		r.PUT("/reorder", a.Reorder)
		r.PUT("/:sid/translations", a.Translate)
	}
}
