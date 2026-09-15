package apis

import (
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"go-admin/app/passport/publishing"
	"go-admin/app/passport/service"
	"go-admin/app/passport/service/dto"
	"io"
	"net/http"
)

type Media struct{ Sections }

func (e *Media) mediaService(c *gin.Context) *service.Media {
	s := e.sectionSetup(c)
	if s == nil {
		return nil
	}
	return &service.Media{Sections: *s}
}

// ListMedia returns authorized images and normalized private previews.
// @Summary List scoped working images
// @Tags PassportMedia
// @Success 200 {object} response.Response
// @Failure 403 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/{id}/revisions/{rid}/media [get]
// @Router /api/v1/passport-products/{id}/revisions/{rid}/sections/{sid}/media [get]
// @Router /api/v1/passport-batches/{id}/sections/{sid}/media [get]
func (e Media) List(c *gin.Context) {
	s := e.mediaService(c)
	if s == nil {
		return
	}
	pid, rid, bid := sectionOwner(c)
	v, err := s.ListMedia(pid, rid, bid, c.Param("sid"), c.Query("display_target"))
	e.result(v, err)
}

// Upload atomically creates a private media object and a Draft association.
// @Summary Upload and attach PNG or JPEG to Draft
// @Tags PassportMedia
// @Accept multipart/form-data
// @Param file formData file true "PNG or JPEG, max 2 MiB"
// @Param expected_token formData string true "Current media token"
// @Param public_label formData string true "Plain text label"
// @Param is_public formData boolean true "Explicit public eligibility and link intention"
// @Success 200 {object} response.Response
// @Failure 422 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/{id}/revisions/{rid}/media [post]
// @Router /api/v1/passport-products/{id}/revisions/{rid}/sections/{sid}/media [post]
// @Router /api/v1/passport-batches/{id}/sections/{sid}/media [post]
func (e Media) Upload(c *gin.Context) {
	s := e.mediaService(c)
	if s == nil {
		return
	}
	c.Request.Body = http.MaxBytesReader(c.Writer, c.Request.Body, publishing.MaxSourceBytes+65536)
	if err := c.Request.ParseMultipartForm(512 * 1024); err != nil {
		if c.Request.MultipartForm != nil {
			_ = c.Request.MultipartForm.RemoveAll()
		}
		e.Error(422, nil, "上传表单或大小不符合限制")
		return
	}
	defer c.Request.MultipartForm.RemoveAll()
	form := c.Request.MultipartForm
	for k, values := range form.Value {
		if (k != "expected_token" && k != "public_label" && k != "is_public" && k != "display_target") || len(values) != 1 {
			e.Error(422, nil, "上传参数不正确")
			return
		}
	}
	if len(form.File) != 1 || len(form.File["file"]) != 1 || (c.PostForm("is_public") != "true" && c.PostForm("is_public") != "false") {
		e.Error(422, nil, "请选择一张图片并明确公开属性")
		return
	}
	h := form.File["file"][0]
	f, err := h.Open()
	if err != nil {
		e.Error(422, nil, "图片读取失败")
		return
	}
	defer f.Close()
	raw, err := io.ReadAll(io.LimitReader(f, publishing.MaxSourceBytes+1))
	if err != nil {
		e.Error(422, nil, "图片读取失败")
		return
	}
	pid, rid, bid := sectionOwner(c)
	id, err := s.UploadMedia(pid, rid, bid, c.Param("sid"), service.MediaUpload{DisplayTarget: c.PostForm("display_target"), ExpectedToken: c.PostForm("expected_token"), PublicLabel: c.PostForm("public_label"), IsPublic: c.PostForm("is_public") == "true", Filename: h.Filename, MIME: h.Header.Get("Content-Type"), Bytes: raw})
	e.result(map[string]string{"id": id}, err)
}

// Detach keeps source media bytes and all immutable published copies.
// @Summary Detach a scoped Draft image
// @Tags PassportMedia
// @Param body body dto.TokenRequest true "Current token"
// @Success 200 {object} response.Response
// @Failure 409 {object} response.Response
// @Security Bearer
// @Router /api/v1/passport-products/{id}/revisions/{rid}/media/{aid} [delete]
// @Router /api/v1/passport-products/{id}/revisions/{rid}/sections/{sid}/media/{aid} [delete]
// @Router /api/v1/passport-batches/{id}/sections/{sid}/media/{aid} [delete]
func (e Media) Detach(c *gin.Context) {
	s := e.mediaService(c)
	if s == nil {
		return
	}
	if _, err := uuid.Parse(c.Param("aid")); err != nil {
		e.Error(422, nil, "图片关联编号不正确")
		return
	}
	var q dto.TokenRequest
	if err := strict(c, &q); err != nil {
		e.Error(422, nil, "请求字段不正确")
		return
	}
	pid, rid, bid := sectionOwner(c)
	e.result(nil, s.DetachMedia(pid, rid, bid, c.Param("sid"), c.Param("aid"), q.ExpectedToken))
}
