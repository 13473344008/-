package apis

import (
	"errors"
	"github.com/gin-gonic/gin"
	"github.com/go-admin-team/go-admin-core/v2/jwtauth/user"
	"github.com/go-admin-team/go-admin-core/v2/sdk/api"
	"github.com/google/uuid"
	"go-admin/app/passport/service"
	"go-admin/app/passport/service/dto"
	"go-admin/common/actions"
)

type Batches struct{ api.Api }

func (e *Batches) setup(c *gin.Context) *service.Batches {
	s := &service.Batches{Products: service.Products{Actor: user.GetUserId(c), Admin: user.ExtractClaims(c)["rolekey"] == "admin", Permission: actions.GetPermissionFromContext(c)}}
	if err := e.MakeContext(c).MakeOrm().MakeService(&s.Service).Errors; err != nil {
		e.Error(500, err, "服务暂时不可用")
		return nil
	}
	for _, key := range []string{"id"} {
		if v := c.Param(key); v != "" {
			if _, err := uuid.Parse(v); err != nil {
				e.Error(422, err, "批次编号格式不正确")
				return nil
			}
		}
	}
	return s
}
func (e *Batches) result(data interface{}, err error) {
	if err != nil {
		var b *service.BusinessError
		if errors.As(err, &b) {
			e.Error(b.Code, nil, b.Message)
		} else {
			e.Logger.Error(err)
			e.Error(500, nil, "操作失败，请稍后重试")
		}
		return
	}
	e.OK(data, "操作成功")
}

// List batches
// @Summary List batches
// @Tags Batches
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-batches [get]
func (e Batches) List(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	q := dto.BatchQuery{PageIndex: 1, PageSize: 10}
	if err := c.ShouldBindQuery(&q); err != nil {
		e.Error(422, nil, "分页参数不正确")
		return
	}
	if q.PageIndex < 1 {
		q.PageIndex = 1
	}
	if q.PageSize < 1 {
		q.PageSize = 10
	}
	if q.PageSize > 100 {
		q.PageSize = 100
	}
	rows, n, err := s.ListBatches(q)
	if err != nil {
		e.result(nil, err)
		return
	}
	e.PageOK(rows, int(n), q.PageIndex, q.PageSize, "查询成功")
}

// Get batches
// @Summary Get batches
// @Tags Batches
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-batches/{id} [get]
func (e Batches) Get(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	v, err := s.GetBatch(c.Param("id"), c.Query("language"))
	e.result(v, err)
}

// Create batches
// @Summary Create batches
// @Tags Batches
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-batches [post]
func (e Batches) Create(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	var req dto.CreateBatchRequest
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	id, err := s.CreateBatch(req)
	e.result(gin.H{"id": id}, err)
}

// Update batches
// @Summary Update batches
// @Tags Batches
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-batches/{id} [put]
func (e Batches) Update(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	var req dto.UpdateBatchRequest
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	e.result(nil, s.UpdateBatch(c.Param("id"), req))
}

// Clone batches
// @Summary Clone batches
// @Tags Batches
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-batches/{id}/clone [post]
func (e Batches) Clone(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	var req dto.CloneBatchRequest
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	id, err := s.CloneBatch(c.Param("id"), req)
	e.result(gin.H{"id": id}, err)
}
