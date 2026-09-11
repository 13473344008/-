package apis

import "github.com/gin-gonic/gin"

// Preview returns an authenticated, non-cacheable private preview.
// @Summary Private passport preview
// @Tags ReviewWorkflow
// @Param id path string true "Batch ID"
// @Param kind query string true "working or review"
// @Param review_id query string false "Frozen review ID"
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-batches/{id}/preview [get]
func (e Reviews) Preview(c *gin.Context) {
	c.Header("Cache-Control", "no-store, private")
	s := e.reviewSetup(c)
	if s == nil {
		return
	}
	p, err := s.Preview(c.Param("id"), c.Query("kind"), c.Query("review_id"))
	e.reviewResult(p, err)
}
