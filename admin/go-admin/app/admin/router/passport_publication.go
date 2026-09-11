package router

import (
	"github.com/gin-gonic/gin"
	jwt "github.com/go-admin-team/go-admin-core/v2/jwtauth"
	"go-admin/app/passport/apis"
	passportMiddleware "go-admin/app/passport/middleware"
	"go-admin/common/actions"
	"go-admin/common/middleware"
)

func init() { routerCheckRole = append(routerCheckRole, registerPassportPublication) }
func registerPassportPublication(v1 *gin.RouterGroup, auth *jwt.GinJWTMiddleware) {
	a := apis.Publishing{}
	r := v1.Group("/passport-batches/:id/publication").Use(auth.MiddlewareFunc()).Use(passportMiddleware.LiveIdentity()).Use(middleware.AuthCheckRole()).Use(actions.PermissionAction())
	r.GET("", a.Status)
	r.GET("/history", a.History)
	r.GET("/versions/:rid", a.Version)
	r.GET("/versions/:rid/integrity", a.Integrity)
	r.GET("/compare", a.Compare)
	r.GET("/health", a.Health)
	r.POST("/rollback", a.Rollback)
	r.POST("", a.Publish)
	r.POST("/reconcile", a.Reconcile)
}
