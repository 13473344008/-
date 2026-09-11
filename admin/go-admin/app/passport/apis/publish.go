package apis

import (
	"github.com/gin-gonic/gin"
	"go-admin/app/passport/service"
)

type Publishing struct{ Reviews }

func (e *Publishing) publishSetup(c *gin.Context) *service.Publishing {
	s := e.reviewSetup(c)
	if s == nil {
		return nil
	}
	return &service.Publishing{Reviews: *s}
}

// Status publication
// @Summary Status publication
// @Tags Publication
// @Security Bearer
// @Success 200 {object} response.Response
// @Router /api/v1/passport-batches/{id}/publication [get]
func (e Publishing) Status(c *gin.Context) {
	s := e.publishSetup(c)
	if s == nil {
		return
	}
	v, err := s.Status(c.Param("id"))
	e.result(v, err)
}

// Publish approved input
// @Summary Publish approved input
// @Tags Publication
// @Security Bearer
// @Success 200 {object} response.Response
// @Router /api/v1/passport-batches/{id}/publication [post]
func (e Publishing) Publish(c *gin.Context) {
	s := e.publishSetup(c)
	if s == nil {
		return
	}
	var req service.PublishRequest
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	v, err := s.Publish(c.Param("id"), req)
	e.result(v, err)
}

// Reconcile interrupted publication
// @Summary Reconcile interrupted publication
// @Tags Publication
// @Security Bearer
// @Success 200 {object} response.Response
// @Router /api/v1/passport-batches/{id}/publication/reconcile [post]
func (e Publishing) Reconcile(c *gin.Context) {
	s := e.publishSetup(c)
	if s == nil {
		return
	}
	var req struct {
		Reason string `json:"reason"`
	}
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	v, err := s.ReconcileReason(c.Param("id"), req.Reason)
	e.result(v, err)
}
