package service

import (
	"go-admin/app/passport/models"
	"go-admin/app/passport/service/dto"
	"gorm.io/gorm"
	"reflect"
	"strings"
)

// updateStepLabels is part of the revision transaction: a failed label save
// must never leave new steps without their names. Existing stable keys survive.
func (s *Products) updateStepLabels(tx *gorm.DB, rid string, v *RevisionView, req dto.UpdateRevisionRequest, now string) error {
	allowed := map[string]bool{}
	for _, step := range req.Content.ProcessSteps {
		allowed[step.StepKey] = true
	}
	for lang, labels := range req.ProcessLabels {
		if lang != "en" && lang != "zh-CN" {
			return invalid("工艺名称仅支持中文和英文")
		}
		for key, label := range labels {
			if !allowed[key] || len([]rune(label)) > 200 {
				return invalid("工艺名称须对应有效步骤且不超过200字符")
			}
		}
	}
	sourceName := ""
	for _, tr := range v.Translations {
		if tr.LanguageCode == v.SourceLanguage {
			sourceName = tr.ProductName
		}
	}
	seen := map[string]bool{}
	requests := []dto.TranslationRequest{}
	for _, tr := range v.Translations {
		requests = append(requests, viewTranslation(tr))
		seen[tr.LanguageCode] = true
	}
	for _, lang := range []string{"zh-CN", "en"} {
		nonempty := false
		for _, label := range req.ProcessLabels[lang] {
			nonempty = nonempty || strings.TrimSpace(label) != ""
		}
		if !seen[lang] && nonempty {
			// Keep the source product name as an explicitly unapproved draft until edited.
			requests = append(requests, dto.TranslationRequest{LanguageCode: lang, ProductName: sourceName, TranslationStatus: "draft", ProcessLabels: map[string]string{}})
		}
	}
	for _, d := range requests {
		original := d.ProcessLabels
		labels := map[string]string{}
		for key, label := range original {
			if allowed[key] {
				labels[key] = label
			}
		}
		if replacement, ok := req.ProcessLabels[d.LanguageCode]; ok {
			labels = map[string]string{}
			for key, label := range replacement {
				if strings.TrimSpace(label) != "" {
					labels[key] = strings.TrimSpace(label)
				}
			}
		}
		d.ProcessLabels = labels
		if !reflect.DeepEqual(original, labels) {
			d.TranslationStatus = "draft"
		}
		if e := validateTranslation(&d, req.Content); e != nil {
			return e
		}
		m := translationMap(d)
		m["updated_at"] = now
		m["updated_by"] = s.Actor
		if seen[d.LanguageCode] {
			if e := tx.Model(&models.Translation{}).Where("product_revision_id=? AND language_code=?", rid, d.LanguageCode).Updates(m).Error; e != nil {
				return e
			}
		} else {
			metadata(m, s.Actor, now)
			m["product_revision_id"] = rid
			if e := tx.Table("product_revision_translations").Create(m).Error; e != nil {
				return e
			}
		}
	}
	var contextual []workingLink
	if e := tx.Table("asset_links").Where("product_revision_id=? AND display_target LIKE 'process:%'", rid).Find(&contextual).Error; e != nil {
		return e
	}
	for _, link := range contextual {
		if !allowed[strings.TrimPrefix(link.DisplayTarget, "process:")] {
			if e := tx.Exec("DELETE FROM asset_links WHERE id=?", link.ID).Error; e != nil {
				return e
			}
		}
	}
	updated, e := s.revision(tx, v.ProductID, rid)
	if e != nil {
		return e
	}
	*v = updated
	return nil
}
