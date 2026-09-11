package apis

import (
	"github.com/gin-gonic/gin"
	"go-admin/app/passport/service"
)

type Traffic struct{ Products }

// @Summary Read scoped QR page visits from private static access logs
// @Tags Passport traffic
// @Param batch_code query string false "Batch code filter"
// @Param days query int false "Last 1 to 90 days"
// @Param pageIndex query int false "Page"
// @Param pageSize query int false "Page size, maximum 100"
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-traffic [get]
func (e Traffic) List(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	q := service.TrafficQuery{}
	if c.ShouldBindQuery(&q) != nil {
		e.Error(422, nil, "查询参数不正确")
		return
	}
	v, err := (&service.Traffic{Products: *s}).Read(q)
	e.result(v, err)
}
