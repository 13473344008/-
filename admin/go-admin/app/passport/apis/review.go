package apis

import (
	"errors"
	"github.com/gin-gonic/gin"
	"go-admin/app/passport/service"
	"go-admin/app/passport/service/dto"
)

type Reviews struct{ Batches }

func (e *Reviews) reviewSetup(c *gin.Context) *service.Reviews {
	b := e.setup(c)
	if b == nil {
		return nil
	}
	return &service.Reviews{Batches: *b}
}
func (e *Reviews) reviewResult(data interface{}, err error) {
	var ready *service.ReadinessError
	if errors.As(err, &ready) {
		e.Custom(gin.H{"code": 422, "msg": ready.Error(), "data": ready.Result})
		return
	}
	e.result(data, err)
}

// Queue review
// @Summary Queue review
// @Tags ReviewWorkflow
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-reviews [get]
func (e Reviews) Queue(c *gin.Context) {
	s := e.reviewSetup(c)
	if s == nil {
		return
	}
	q := dto.ReviewQuery{PageIndex: 1, PageSize: 10}
	if err := c.ShouldBindQuery(&q); err != nil {
		e.Error(422, nil, "队列参数不正确")
		return
	}
	rows, n, err := s.Queue(q)
	if err != nil {
		e.reviewResult(nil, err)
		return
	}
	e.PageOK(rows, int(n), q.PageIndex, q.PageSize, "查询成功")
}

// Detail review
// @Summary Detail review
// @Tags ReviewWorkflow
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-batches/{id}/review [get]
func (e Reviews) Detail(c *gin.Context) {
	s := e.reviewSetup(c)
	if s == nil {
		return
	}
	v, err := s.Detail(c.Param("id"))
	e.reviewResult(v, err)
}

// Readiness review
// @Summary Readiness review
// @Tags ReviewWorkflow
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-batches/{id}/review/readiness [get]
func (e Reviews) Readiness(c *gin.Context) {
	s := e.reviewSetup(c)
	if s == nil {
		return
	}
	v, err := s.Readiness(c.Param("id"))
	e.reviewResult(v, err)
}

// Submit review
// @Summary Submit review
// @Tags ReviewWorkflow
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-batches/{id}/review/submit [post]
func (e Reviews) Submit(c *gin.Context) {
	s := e.reviewSetup(c)
	if s == nil {
		return
	}
	var req dto.SubmitReview
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	id, err := s.Submit(c.Param("id"), req)
	e.reviewResult(gin.H{"id": id}, err)
}

// Approve review
// @Summary Approve review
// @Tags ReviewWorkflow
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-batches/{id}/review/approve [post]
func (e Reviews) Approve(c *gin.Context) {
	s := e.reviewSetup(c)
	if s == nil {
		return
	}
	var req dto.DecideReview
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	e.reviewResult(nil, s.Decide(c.Param("id"), "approved", req))
}

// Reject review
// @Summary Reject review
// @Tags ReviewWorkflow
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-batches/{id}/review/reject [post]
func (e Reviews) Reject(c *gin.Context) {
	s := e.reviewSetup(c)
	if s == nil {
		return
	}
	var req dto.DecideReview
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	e.reviewResult(nil, s.Decide(c.Param("id"), "rejected", req))
}

// Return review
// @Summary Return review
// @Tags ReviewWorkflow
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-batches/{id}/review/return [post]
func (e Reviews) Return(c *gin.Context) {
	s := e.reviewSetup(c)
	if s == nil {
		return
	}
	var req dto.ReturnReview
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	e.reviewResult(nil, s.Return(c.Param("id"), req))
}

// Archive review
// @Summary Archive review
// @Tags ReviewWorkflow
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-batches/{id}/review/archive [post]
func (e Reviews) Archive(c *gin.Context) {
	s := e.reviewSetup(c)
	if s == nil {
		return
	}
	e.reviewResult(nil, s.ArchiveBatch(c.Param("id")))
}
