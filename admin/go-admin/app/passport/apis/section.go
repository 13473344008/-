package apis

import (
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go-admin/app/passport/service"
	"go-admin/app/passport/service/dto"
)

type Sections struct{ Batches }

func (e *Sections) sectionSetup(c *gin.Context) *service.Sections {
	b := e.setup(c)
	if b == nil {
		return nil
	}
	for _, key := range []string{"rid", "sid"} {
		if v := c.Param(key); v != "" {
			if _, err := uuid.Parse(v); err != nil {
				e.Error(422, nil, "模块 ID 格式不正确")
				return nil
			}
		}
	}
	return &service.Sections{Batches: *b}
}
func sectionOwner(c *gin.Context) (string, string, string) {
	if c.Param("rid") != "" {
		return c.Param("id"), c.Param("rid"), ""
	}
	return "", "", c.Param("id")
}

// List custom sections
// @Summary List custom sections
// @Tags CustomSections
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/{id}/revisions/{rid}/sections [get]
// @Router /api/v1/passport-batches/{id}/sections [get]
func (e Sections) List(c *gin.Context) {
	service := e.sectionSetup(c)
	if service == nil {
		return
	}
	pid, rid, bid := sectionOwner(c)
	v, err := service.GetSections(pid, rid, bid, c.Query("language"))
	e.result(v, err)
}

// Get custom sections
// @Summary Get custom sections
// @Tags CustomSections
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/{id}/revisions/{rid}/sections/{sid} [get]
// @Router /api/v1/passport-batches/{id}/sections/{sid} [get]
func (e Sections) Get(c *gin.Context) {
	service := e.sectionSetup(c)
	if service == nil {
		return
	}
	pid, rid, bid := sectionOwner(c)
	v, err := service.GetSections(pid, rid, bid, c.Query("language"))
	if err == nil {
		for _, row := range v.Sections {
			if row.ID == c.Param("sid") {
				e.result(row, nil)
				return
			}
		}
		e.Error(404, nil, "模块不存在")
		return
	}
	e.result(v, err)
}

// Create custom sections
// @Summary Create custom sections
// @Tags CustomSections
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/{id}/revisions/{rid}/sections [post]
// @Router /api/v1/passport-batches/{id}/sections [post]
func (e Sections) Create(c *gin.Context) {
	service := e.sectionSetup(c)
	if service == nil {
		return
	}
	pid, rid, bid := sectionOwner(c)
	var req dto.SectionWrite
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	id, err := service.PutSection(pid, rid, bid, "", req)
	e.result(gin.H{"id": id}, err)
}

// Update custom sections
// @Summary Update custom sections
// @Tags CustomSections
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/{id}/revisions/{rid}/sections/{sid} [put]
// @Router /api/v1/passport-batches/{id}/sections/{sid} [put]
func (e Sections) Update(c *gin.Context) {
	service := e.sectionSetup(c)
	if service == nil {
		return
	}
	pid, rid, bid := sectionOwner(c)
	var req dto.SectionWrite
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	id, err := service.PutSection(pid, rid, bid, c.Param("sid"), req)
	e.result(gin.H{"id": id}, err)
}

// Delete custom sections
// @Summary Delete custom sections
// @Tags CustomSections
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/{id}/revisions/{rid}/sections/{sid} [delete]
// @Router /api/v1/passport-batches/{id}/sections/{sid} [delete]
func (e Sections) Delete(c *gin.Context) {
	service := e.sectionSetup(c)
	if service == nil {
		return
	}
	pid, rid, bid := sectionOwner(c)
	var req dto.TokenRequest
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	e.result(nil, service.DeleteSection(pid, rid, bid, c.Param("sid"), req.ExpectedToken))
}

// Reorder custom sections
// @Summary Reorder custom sections
// @Tags CustomSections
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/{id}/revisions/{rid}/sections/reorder [put]
// @Router /api/v1/passport-batches/{id}/sections/reorder [put]
func (e Sections) Reorder(c *gin.Context) {
	service := e.sectionSetup(c)
	if service == nil {
		return
	}
	pid, rid, bid := sectionOwner(c)
	var req dto.SectionReorder
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	e.result(nil, service.ReorderSections(pid, rid, bid, req))
}

// Translate custom sections
// @Summary Translate custom sections
// @Tags CustomSections
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/{id}/revisions/{rid}/sections/{sid}/translations [put]
// @Router /api/v1/passport-batches/{id}/sections/{sid}/translations [put]
func (e Sections) Translate(c *gin.Context) {
	service := e.sectionSetup(c)
	if service == nil {
		return
	}
	pid, rid, bid := sectionOwner(c)
	var req dto.SectionTranslate
	if err := strict(c, &req); err != nil {
		e.Error(422, nil, err.Error())
		return
	}
	e.result(nil, service.TranslateSection(pid, rid, bid, c.Param("sid"), req))
}
