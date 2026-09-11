package router

import (
	"github.com/gin-gonic/gin"
	jwt "github.com/go-admin-team/go-admin-core/v2/jwtauth"
	"go-admin/app/passport/apis"
	passportMiddleware "go-admin/app/passport/middleware"
	"go-admin/common/actions"
	"go-admin/common/middleware"
)

func init() { routerCheckRole = append(routerCheckRole, registerPassportReviews) }
func registerPassportReviews(v1 *gin.RouterGroup, auth *jwt.GinJWTMiddleware) {
	a := apis.Reviews{}
	r := v1.Group("/passport-batches/:id/review").Use(auth.MiddlewareFunc()).Use(passportMiddleware.LiveIdentity()).Use(middleware.AuthCheckRole()).Use(actions.PermissionAction())
	r.GET("", a.Detail)
	r.GET("/readiness", a.Readiness)
	r.POST("/submit", a.Submit)
	r.POST("/approve", a.Approve)
	r.POST("/reject", a.Reject)
	r.POST("/return", a.Return)
	r.POST("/archive", a.Archive)
	q := v1.Group("/passport-reviews").Use(auth.MiddlewareFunc()).Use(passportMiddleware.LiveIdentity()).Use(middleware.AuthCheckRole()).Use(actions.PermissionAction())
	q.GET("", a.Queue)
}
