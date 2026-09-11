package service

import (
	"fmt"
	"go-admin/app/passport/publishing"
	"gorm.io/gorm"
	"os"
)

type ReviewAsset struct {
	SourceMediaID      string `json:"source_media_id"`
	StorageKey         string `json:"storage_key"`
	OriginalFilename   string `json:"original_filename"`
	MimeType           string `json:"mime_type"`
	FileSize           int64  `json:"file_size"`
	SHA256             string `json:"sha256"`
	AvailabilityStatus string `json:"availability_status"`
	IsPublicEligible   bool   `json:"is_public_eligible"`
	AssetKey           string `json:"asset_key"`
	AssetRole          string `json:"asset_role"`
	PublicLabel        string `json:"public_label"`
	IsPublic           bool   `json:"is_public"`
	OwnerID            string `json:"owner_id"`
	Publish            bool   `json:"publish" gorm:"-"`
	NormalizedSHA256   string `json:"normalized_sha256" gorm:"-"`
	NormalizedSize     int64  `json:"normalized_size" gorm:"-"`
	NormalizedPreview  []byte `json:"normalized_preview_base64" gorm:"-"`
	TransformVersion   string `json:"transform_version" gorm:"-"`
}

func freezeReviewAssets(tx *gorm.DB, c *ReviewCandidate) error {
	rows := []ReviewAsset{}
	e := tx.Table("asset_links a").Joins("JOIN media_assets m ON m.id=a.media_asset_id").Select("m.id AS source_media_id,m.storage_key,m.original_filename,m.mime_type,m.file_size,m.sha256,m.availability_status,m.is_public_eligible,a.asset_key,a.asset_role,a.public_label,a.is_public,COALESCE(a.product_revision_id,a.inspection_item_id,a.custom_section_id) AS owner_id").Where(`a.product_revision_id=? OR a.inspection_item_id IN (SELECT id FROM inspection_items WHERE batch_id=?) OR a.custom_section_id IN (SELECT id FROM custom_sections WHERE batch_id=? OR product_revision_id=?)`, c.Base.ID, c.Batch.ID, c.Batch.ID, c.Base.ID).Order("a.sort_order,a.asset_key,a.id").Scan(&rows).Error
	if e != nil {
		return e
	}
	if len(rows) > 16 {
		return fmt.Errorf("审核资产关联不得超过 16 项")
	}
	owners := map[string]bool{c.Base.ID: true}
	for _, i := range c.Inspections {
		owners[i.ID] = i.IsPublic
	}
	for _, s := range c.EffectiveSections {
		owners[s.SectionID] = s.IsPublic
	}
	keys := map[string]bool{}
	for i := range rows {
		a := &rows[i]
		a.Publish = a.IsPublic && a.IsPublicEligible && owners[a.OwnerID]
		if !a.Publish {
			continue
		}
		if keys[a.AssetKey] {
			return fmt.Errorf("公开资产 key 重复")
		}
		keys[a.AssetKey] = true
		if !safeSectionText(a.PublicLabel, 200, true) {
			return fmt.Errorf("公开资产标签必须为非空纯文本")
		}
		if a.OwnerID == c.Base.ID && a.AssetRole != "product_image" {
			return fmt.Errorf("模板独立资产必须为产品主图")
		}
		if a.AvailabilityStatus != "ready" {
			return fmt.Errorf("公开资产不可用")
		}
		raw, e := publishing.ReadPrivate(os.Getenv("PASSPORT_PRIVATE_MEDIA_ROOT"), a.StorageKey)
		if e != nil {
			return fmt.Errorf("公开资产源文件缺失或路径不安全")
		}
		if int64(len(raw)) != a.FileSize || publishing.Hash(raw) != a.SHA256 {
			return fmt.Errorf("公开资产源文件摘要不符")
		}
		normalized, e := publishing.Normalize(raw, a.MimeType)
		if e != nil {
			return fmt.Errorf("公开资产须为有效且受限的 PNG/JPEG 图片")
		}
		a.NormalizedPreview = normalized
		a.NormalizedSize = int64(len(normalized))
		a.NormalizedSHA256 = publishing.Hash(normalized)
		a.TransformVersion = publishing.TransformVersion
	}
	c.Assets = rows
	return nil
}
