package service

import (
	"bytes"
	"encoding/base64"
	"fmt"
	"github.com/google/uuid"
	"go-admin/app/passport/publishing"
	"gorm.io/gorm"
	"image"
	"os"
	"path/filepath"
	"strings"
)

// Media is scoped to an accessible template or batch gallery, never a global file browser.
type Media struct{ Sections }
type MediaItem struct {
	DisplayTarget string `json:"display_target"`
	ID            string `json:"id"`
	MediaID       string `json:"media_id"`
	AssetKey      string `json:"asset_key"`
	PublicLabel   string `json:"public_label"`
	IsPublic      bool   `json:"is_public"`
	MimeType      string `json:"mime_type"`
	FileSize      int64  `json:"file_size"`
	SHA256        string `json:"sha256"`
	Width         int    `json:"width" gorm:"-"`
	Height        int    `json:"height" gorm:"-"`
	Preview       string `json:"preview" gorm:"-"`
	StorageKey    string `json:"-"`
}
type MediaSet struct {
	Token string      `json:"token"`
	Items []MediaItem `json:"items"`
}
type MediaUpload struct {
	DisplayTarget string
	ExpectedToken string
	PublicLabel   string
	IsPublic      bool
	Filename      string
	MIME          string
	Bytes         []byte
}

func mediaColumn(rid, sid string) (string, string) {
	if sid != "" {
		return "custom_section_id", sid
	}
	return "product_revision_id", rid
}
func mediaRows(tx *gorm.DB, column, id string) ([]MediaItem, error) {
	rows := []MediaItem{}
	e := tx.Table("asset_links a").Joins("JOIN media_assets m ON m.id=a.media_asset_id").Select("a.id,m.id media_id,a.asset_key,a.display_target,a.public_label,a.is_public,m.mime_type,m.file_size,m.sha256,m.storage_key").Where("a."+column+"=?", id).Order("a.asset_key").Scan(&rows).Error
	return rows, e
}
func mediaOwner(set SectionSet, rid, bid, sid string) error {
	if sid == "" {
		if bid != "" || rid == "" {
			return invalid("请选择模板或图片模块")
		}
		return nil
	}
	for _, v := range set.Sections {
		if v.ID == sid {
			if v.SectionType != "asset_gallery" || (v.Operation != "add" && v.Operation != "replace") {
				return conflict("仅允许维护当前对象的图片模块")
			}
			return nil
		}
	}
	return &BusinessError{404, "图片模块不存在或不属于当前对象"}
}
func (s *Media) ListMedia(pid, rid, bid, sid string, targets ...string) (MediaSet, error) {
	out := MediaSet{Items: []MediaItem{}}
	e := s.Orm.Transaction(func(tx *gorm.DB) error {
		set, e := s.sectionSet(tx, pid, rid, bid, "")
		if e != nil {
			return e
		}
		if e = mediaOwner(set, rid, bid, sid); e != nil {
			return e
		}
		col, id := mediaColumn(rid, sid)
		out.Items, e = mediaRows(tx, col, id)
		if e != nil {
			return e
		}
		if len(targets) > 0 {
			filtered := []MediaItem{}
			for _, item := range out.Items {
				if item.DisplayTarget == targets[0] {
					filtered = append(filtered, item)
				}
			}
			out.Items = filtered
		}
		out.Token = set.Token
		for i := range out.Items {
			v := &out.Items[i]
			raw, e := publishing.ReadPrivate(os.Getenv("PASSPORT_PRIVATE_MEDIA_ROOT"), v.StorageKey)
			if e != nil {
				return conflict("工作图片不可用")
			}
			if publishing.Hash(raw) != v.SHA256 || int64(len(raw)) != v.FileSize {
				return conflict("工作图片摘要不符")
			}
			png, e := publishing.Normalize(raw, v.MimeType)
			if e != nil {
				return conflict("工作图片无效")
			}
			cfg, _, _ := image.DecodeConfig(bytes.NewReader(raw))
			v.Width = cfg.Width
			v.Height = cfg.Height
			v.Preview = "data:image/png;base64," + base64.StdEncoding.EncodeToString(png)
		}
		return nil
	})
	return out, s.fail(e)
}
func (s *Media) UploadMedia(pid, rid, bid, sid string, q MediaUpload) (string, error) {
	if !safeSectionText(q.PublicLabel, 200, true) {
		return "", invalid("请填写纯文本图片名称")
	}
	ext := strings.ToLower(filepath.Ext(q.Filename))
	if (q.MIME != "image/png" || ext != ".png") && (q.MIME != "image/jpeg" || (ext != ".jpg" && ext != ".jpeg")) {
		return "", invalid("仅允许扩展名与MIME一致的PNG/JPEG图片")
	}
	if strings.ContainsAny(q.Filename, "/\\\x00") || len(q.Filename) > 255 {
		return "", invalid("图片文件名不安全")
	}
	if _, e := publishing.Normalize(q.Bytes, q.MIME); e != nil {
		return "", invalid("图片内容、大小或像素不符合限制")
	}
	root := os.Getenv("PASSPORT_PRIVATE_MEDIA_ROOT")
	st, e := os.Lstat(root)
	if e != nil || !st.IsDir() || st.Mode()&os.ModeSymlink != 0 {
		return "", fmt.Errorf("private media root unavailable")
	}
	mediaID := uuid.NewString()
	key := mediaID + ext
	linkID := uuid.NewString()
	written := false
	e = s.sectionWrite(pid, rid, bid, q.ExpectedToken, func(tx *gorm.DB, set SectionSet, now string) error {
		if e := mediaOwner(set, rid, bid, sid); e != nil {
			return e
		}
		if e := validateMediaTarget(tx, rid, sid, q.DisplayTarget); e != nil {
			return e
		}
		col, id := mediaColumn(rid, sid)
		rows, e := mediaRows(tx, col, id)
		if e != nil {
			return e
		}
		count := 0
		for _, item := range rows {
			if item.DisplayTarget == q.DisplayTarget {
				count++
			}
		}
		if len(rows) >= 64 || count >= 4 || sid == "" && q.DisplayTarget == "" && count > 0 {
			return conflict("图片数量已达上限；主图请先解除原关联")
		}
		rr, e := os.OpenRoot(root)
		if e != nil {
			return e
		}
		defer rr.Close()
		file, e := rr.OpenFile(key, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
		if e != nil {
			return e
		}
		written = true
		_, e = file.Write(q.Bytes)
		if e == nil {
			e = file.Sync()
		}
		ce := file.Close()
		if e != nil {
			return e
		}
		if ce != nil {
			return ce
		}
		if e = tx.Table("media_assets").Create(map[string]interface{}{"id": mediaID, "created_at": now, "created_by": s.Actor, "storage_key": key, "original_filename": q.Filename, "mime_type": q.MIME, "file_size": len(q.Bytes), "sha256": publishing.Hash(q.Bytes), "is_public_eligible": q.IsPublic}).Error; e != nil {
			return e
		}
		role := "section_image"
		if sid == "" && q.DisplayTarget == "" {
			role = "product_image"
		}
		assetKey := "image_" + strings.ReplaceAll(uuid.NewString(), "-", "")
		if e = tx.Table("asset_links").Create(map[string]interface{}{"id": linkID, "created_at": now, "created_by": s.Actor, "updated_at": now, "updated_by": s.Actor, col: id, "media_asset_id": mediaID, "asset_key": assetKey, "asset_role": role, "display_target": q.DisplayTarget, "public_label": q.PublicLabel, "is_public": q.IsPublic}).Error; e != nil {
			return e
		}
		return s.mediaAudit(tx, bid, linkID, now, []string{"upload", "attach"}, mediaID)
	})
	if e != nil && written {
		if rr, err := os.OpenRoot(root); err == nil {
			_ = rr.Remove(key)
			rr.Close()
		}
	}
	return linkID, e
}
func (s *Media) mediaAudit(tx *gorm.DB, bid, id, now string, fields []string, source string) error {
	if bid == "" {
		return s.audit(tx, "media_replaced", "asset_links", id, now, map[string]interface{}{"changed_fields": fields, "source_id": source})
	}
	return s.batchAudit(tx, bid, "media_replaced", "asset_links", id, nil, map[string]interface{}{"source_id": source, "changed_fields": fields})
}
func (s *Media) DetachMedia(pid, rid, bid, sid, id, token string) error {
	return s.sectionWrite(pid, rid, bid, token, func(tx *gorm.DB, set SectionSet, now string) error {
		if e := mediaOwner(set, rid, bid, sid); e != nil {
			return e
		}
		col, owner := mediaColumn(rid, sid)
		var source string
		if e := tx.Table("asset_links").Select("media_asset_id").Where("id=? AND "+col+"=?", id, owner).Scan(&source).Error; e != nil {
			return e
		}
		if source == "" {
			return &BusinessError{404, "图片关联不存在"}
		}
		if e := tx.Exec("DELETE FROM asset_links WHERE id=? AND "+col+"=?", id, owner).Error; e != nil {
			return e
		}
		return s.mediaAudit(tx, bid, id, now, []string{"detach"}, source)
	})
}

// Stored links are immutable references to source bytes; copies get new relation IDs.
type workingLink struct {
	DisplayTarget     string
	ID                string
	CreatedAt         string
	CreatedBy         int
	UpdatedAt         string
	UpdatedBy         int
	ProductRevisionID *string
	CertificationID   *string
	InspectionItemID  *string
	CustomSectionID   *string
	MediaAssetID      string
	AssetKey          string
	AssetRole         string
	PublicLabel       string
	SortOrder         int
	IsPublic          bool
}

func aggregateMedia(tx *gorm.DB, rid, bid string) ([]map[string]interface{}, error) {
	rows := []map[string]interface{}{}
	e := tx.Table("asset_links a").Joins("JOIN media_assets m ON m.id=a.media_asset_id").Select("a.*,m.sha256,m.file_size,m.mime_type,m.is_public_eligible,m.availability_status").Where("a.product_revision_id=? OR a.custom_section_id IN (SELECT id FROM custom_sections WHERE product_revision_id=? OR batch_id=?)", rid, rid, bid).Order("a.id").Find(&rows).Error
	return rows, e
}
func validateManagedMedia(tx *gorm.DB, col string, ids []string) error {
	var links []workingLink
	if e := tx.Table("asset_links").Where(col+" IN ?", ids).Find(&links).Error; e != nil {
		return e
	}
	for _, link := range links {
		role := "section_image"
		if col == "product_revision_id" && link.DisplayTarget == "" {
			role = "product_image"
		}
		if link.AssetRole != role {
			return conflict("资产类型未开放")
		}
		var m struct {
			StorageKey         string
			SHA256             string
			MimeType           string
			FileSize           int64
			AvailabilityStatus string
		}
		if e := tx.Table("media_assets").Where("id=?", link.MediaAssetID).Take(&m).Error; e != nil {
			return e
		}
		raw, e := publishing.ReadPrivate(os.Getenv("PASSPORT_PRIVATE_MEDIA_ROOT"), m.StorageKey)
		if e != nil || m.AvailabilityStatus != "ready" || publishing.Hash(raw) != m.SHA256 || int64(len(raw)) != m.FileSize {
			return conflict("关联工作图片不可用或摘要不符")
		}
		if _, e = publishing.Normalize(raw, m.MimeType); e != nil {
			return conflict("关联图片格式不支持")
		}
	}
	return nil
}
func cloneMediaLinks(tx *gorm.DB, col, source, target string, actor int, now string) error {
	var rows []workingLink
	if e := tx.Table("asset_links").Where(col+"=?", source).Find(&rows).Error; e != nil {
		return e
	}
	for _, v := range rows {
		v.ID = uuid.NewString()
		v.CreatedAt = now
		v.UpdatedAt = now
		v.CreatedBy = actor
		v.UpdatedBy = actor
		if col == "product_revision_id" {
			v.ProductRevisionID = &target
		} else {
			v.CustomSectionID = &target
		}
		if e := tx.Table("asset_links").Create(&v).Error; e != nil {
			return e
		}
	}
	return nil
}
