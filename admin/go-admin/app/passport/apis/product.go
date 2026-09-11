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

type Products struct{ api.Api }

func (e *Products) setup(c *gin.Context) *service.Products {
	s := &service.Products{Actor: user.GetUserId(c), Admin: user.ExtractClaims(c)["rolekey"] == "admin", Permission: actions.GetPermissionFromContext(c)}
	if err := e.MakeContext(c).MakeOrm().MakeService(&s.Service).Errors; err != nil {
		e.Error(500, err, "服务暂时不可用")
		return nil
	}
	for _, key := range []string{"id", "rid"} {
		if v := c.Param(key); v != "" {
			if _, err := uuid.Parse(v); err != nil {
				e.Error(422, err, "产品或版本编号格式不正确")
				return nil
			}
		}
	}
	return s
}
func (e *Products) result(data interface{}, err error) {
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

// List product templates
// @Summary List product templates
// @Tags Product templates
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products [get]
func (e Products) List(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	req := dto.Query{PageIndex: 1, PageSize: 10}
	if err := c.ShouldBindQuery(&req); err != nil {
		e.Error(422, nil, "分页参数不正确")
		return
	}
	if req.PageIndex < 1 {
		req.PageIndex = 1
	}
	if req.PageSize < 1 {
		req.PageSize = 10
	}
	if req.PageSize > 100 {
		req.PageSize = 100
	}
	rows, count, err := s.List(req)
	if err != nil {
		e.result(nil, err)
		return
	}
	e.PageOK(rows, int(count), req.PageIndex, req.PageSize, "查询成功")
}

// Get product templates
// @Summary Get product templates
// @Tags Product templates
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/:id [get]
func (e Products) Get(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	data, err := s.Get(c.Param("id"))
	e.result(data, err)
}

// Create product templates
// @Summary Create product templates
// @Tags Product templates
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products [post]
func (e Products) Create(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	var req dto.CreateProductRequest
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	id, err := s.Create(req)
	e.result(gin.H{"id": id}, err)
}

// Update product templates
// @Summary Update product templates
// @Tags Product templates
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/:id [put]
func (e Products) Update(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	var req dto.UpdateProductRequest
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	e.result(nil, s.UpdateProduct(c.Param("id"), req))
}

// Archive product templates
// @Summary Archive product templates
// @Tags Product templates
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/:id/archive [post]
func (e Products) Archive(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	var req dto.TokenRequest
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	e.result(nil, s.Archive(c.Param("id")))
}

// Revisions product templates
// @Summary Revisions product templates
// @Tags Product templates
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/:id/revisions [get]
func (e Products) Revisions(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	data, err := s.Get(c.Param("id"))
	e.result(data.Revisions, err)
}

// Revision product templates
// @Summary Revision product templates
// @Tags Product templates
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/:id/revisions/:rid [get]
func (e Products) Revision(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	data, err := s.GetRevision(c.Param("id"), c.Param("rid"))
	e.result(data, err)
}

// Clone product templates
// @Summary Clone product templates
// @Tags Product templates
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/:id/revisions [post]
func (e Products) Clone(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	var req dto.CreateRevisionRequest
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	id, err := s.Clone(c.Param("id"), req)
	e.result(gin.H{"id": id}, err)
}

// EditRevision product templates
// @Summary EditRevision product templates
// @Tags Product templates
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/:id/revisions/:rid [put]
func (e Products) EditRevision(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	var req dto.UpdateRevisionRequest
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	e.result(nil, s.UpdateRevision(c.Param("id"), c.Param("rid"), req))
}

// Translate product templates
// @Summary Translate product templates
// @Tags Product templates
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/:id/revisions/:rid/translations [put]
func (e Products) Translate(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	var req dto.UpdateTranslationRequest
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	e.result(nil, s.Translate(c.Param("id"), c.Param("rid"), req))
}

// Seal product templates
// @Summary Seal product templates
// @Tags Product templates
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/:id/revisions/:rid/seal [post]
func (e Products) Seal(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	var req dto.TokenRequest
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	e.result(nil, s.Seal(c.Param("id"), c.Param("rid"), req))
}

// Default product templates
// @Summary Default product templates
// @Tags Product templates
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/:id/default-revision [put]
func (e Products) Default(c *gin.Context) {
	s := e.setup(c)
	if s == nil {
		return
	}
	var req dto.DefaultRequest
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	e.result(nil, s.SetDefault(c.Param("id"), req))
}
