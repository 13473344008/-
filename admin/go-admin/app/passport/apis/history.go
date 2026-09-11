package apis

import "github.com/gin-gonic/gin"
import "go-admin/app/passport/service"

// History lists immutable versions and complete business attempts.
// @Summary Version and audit history
// @Tags Publication
// @Security Bearer
// @Param id path string true "Batch ID"
// @Param category query string false "Audit category"
// @Success 200 {object} response.Response
// @Router /api/v1/passport-batches/{id}/publication/history [get]
func (e Publishing) History(c *gin.Context) {
	s := e.publishSetup(c)
	if s == nil {
		return
	}
	v, err := s.History(c.Param("id"), c.Query("category"))
	e.result(v, err)
}

// Version returns a read-only snapshot, manifest, assets and provenance.
// @Summary Published version detail
// @Tags Publication
// @Security Bearer
// @Param id path string true "Batch ID"
// @Param rid path string true "Published Revision ID"
// @Success 200 {object} response.Response
// @Router /api/v1/passport-batches/{id}/publication/versions/{rid} [get]
func (e Publishing) Version(c *gin.Context) {
	s := e.publishSetup(c)
	if s == nil {
		return
	}
	v, err := s.Version(c.Param("id"), c.Param("rid"))
	e.result(v, err)
}

// Integrity verifies all historical release bytes without repair.
// @Summary Verify version integrity
// @Tags Publication
// @Security Bearer
// @Param id path string true "Batch ID"
// @Param rid path string true "Published Revision ID"
// @Success 200 {object} response.Response
// @Router /api/v1/passport-batches/{id}/publication/versions/{rid}/integrity [get]
func (e Publishing) Integrity(c *gin.Context) {
	s := e.publishSetup(c)
	if s == nil {
		return
	}
	v, err := s.Version(c.Param("id"), c.Param("rid"))
	e.result(v.Integrity, err)
}

// Compare uses only verified published snapshots.
// @Summary Compare published versions
// @Tags Publication
// @Security Bearer
// @Param id path string true "Batch ID"
// @Param left query string true "Left revision"
// @Param right query string true "Right revision"
// @Success 200 {object} response.Response
// @Router /api/v1/passport-batches/{id}/publication/compare [get]
func (e Publishing) Compare(c *gin.Context) {
	s := e.publishSetup(c)
	if s == nil {
		return
	}
	v, err := s.Compare(c.Param("id"), c.Query("left"), c.Query("right"))
	e.result(v, err)
}

// Health checks DB, stable file, immutable manifests and assets.
// @Summary Publication consistency
// @Tags Publication
// @Security Bearer
// @Param id path string true "Batch ID"
// @Success 200 {object} response.Response
// @Router /api/v1/passport-batches/{id}/publication/health [get]
func (e Publishing) Health(c *gin.Context) {
	s := e.publishSetup(c)
	if s == nil {
		return
	}
	v, err := s.Health(c.Param("id"))
	e.result(v, err)
}

// Rollback creates a new immutable version under the shared publish lock.
// @Summary Rollback as new version
// @Tags Publication
// @Security Bearer
// @Param id path string true "Batch ID"
// @Param body body service.RollbackRequest true "Rollback request"
// @Success 200 {object} response.Response
// @Failure 401,403,409,422 {object} response.Response
// @Router /api/v1/passport-batches/{id}/publication/rollback [post]
func (e Publishing) Rollback(c *gin.Context) {
	s := e.publishSetup(c)
	if s == nil {
		return
	}
	var q service.RollbackRequest
	if err := strict(c, &q); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	v, err := s.Rollback(c.Param("id"), q)
	e.result(v, err)
}
