package service

import (
	"encoding/json"
	"errors"
	"github.com/google/uuid"
	"go-admin/app/passport/models"
	"go-admin/app/passport/service/dto"
	"gorm.io/gorm"
	"sort"
)

type SectionView struct {
	models.Section
	Translations []models.SectionTranslationView `json:"translations"`
}
type EffectiveSection struct {
	SectionKey     string          `json:"section_key"`
	SectionType    string          `json:"section_type"`
	Source         string          `json:"source"`
	BaseRevisionID string          `json:"base_revision_id"`
	SectionID      string          `json:"section_id"`
	SortOrder      int             `json:"sort_order"`
	IsPublic       bool            `json:"is_public"`
	AllowHide      bool            `json:"allow_hide"`
	Language       string          `json:"language"`
	Title          string          `json:"title"`
	Content        json.RawMessage `json:"content,omitempty"`
}
type SectionSet struct {
	Token          string             `json:"token"`
	Sections       []SectionView      `json:"sections"`
	BaseSections   []SectionView      `json:"base_sections"`
	Effective      []EffectiveSection `json:"effective"`
	Hidden         []EffectiveSection `json:"hidden"`
	SourceLanguage string             `json:"source_language"`
	BaseRevisionID string             `json:"base_revision_id"`
}

func loadSections(tx *gorm.DB, column, id string) ([]SectionView, error) {
	rows := []models.Section{}
	if e := tx.Where(column+"=?", id).Order("sort_order,section_key").Find(&rows).Error; e != nil {
		return nil, e
	}
	out := []SectionView{}
	for _, r := range rows {
		ts := []models.SectionTranslation{}
		if e := tx.Where("custom_section_id=?", r.ID).Order("language_code").Find(&ts).Error; e != nil {
			return nil, e
		}
		v := SectionView{Section: r, Translations: []models.SectionTranslationView{}}
		for _, t := range ts {
			v.Translations = append(v.Translations, models.SectionTranslationView{SectionTranslation: t, Content: json.RawMessage(t.Content)})
		}
		out = append(out, v)
	}
	return out, nil
}
func sectionDTO(v SectionView) dto.SectionContent {
	d := dto.SectionContent{SectionKey: v.SectionKey, Operation: v.Operation, SectionType: v.SectionType, SortOrder: v.SortOrder, IsVisible: v.IsVisible, IsPublic: v.IsPublic, AllowHide: v.AllowHide, Status: v.Status, Translations: []dto.SectionTranslation{}}
	for _, t := range v.Translations {
		d.Translations = append(d.Translations, dto.SectionTranslation{LanguageCode: t.LanguageCode, TranslationStatus: t.TranslationStatus, Title: t.Title, Content: t.Content})
	}
	return d
}
func sectionAssets(tx *gorm.DB, ids []string) error {
	var n int64
	if e := tx.Table("asset_links").Where("custom_section_id IN ?", ids).Count(&n).Error; e != nil {
		return e
	}
	if n > 0 {
		return conflict("模块含尚未开放的资产关联，不能编辑、复制或封版")
	}
	return nil
}
func validateSectionRows(tx *gorm.DB, rows []SectionView) error {
	ids := []string{}
	if len(rows) > MaxSections {
		return invalid("模块数量超限")
	}
	for _, v := range rows {
		if e := validateSection(sectionDTO(v), v.SourceLanguage); e != nil {
			return e
		}
		ids = append(ids, v.ID)
	}
	return validateManagedMedia(tx, "custom_section_id", ids)
}

// One resolver, shared by section endpoints and T6 Batch Detail. Hidden entries contain provenance only.
func ResolveEffectiveSections(base, own []SectionView, rid, lang string) ([]EffectiveSection, []EffectiveSection, error) {
	visible, hidden := []EffectiveSection{}, []EffectiveSection{}
	merged := map[string]SectionView{}
	sources := map[string]string{}
	baseMap := map[string]SectionView{}
	for _, v := range base {
		merged[v.SectionKey] = v
		baseMap[v.SectionKey] = v
		sources[v.SectionKey] = "inherited"
	}
	for _, v := range own {
		b, exists := baseMap[v.SectionKey]
		if (v.Operation == "add" && exists) || (v.Operation != "add" && !exists) {
			return nil, nil, invalid("模块覆盖目标不属于固定基础版本")
		}
		if exists && (((!v.IsVisible || v.Status == "disabled") && !b.AllowHide) || (v.Operation == "hide" && !b.AllowHide)) {
			return nil, nil, invalid("基础模块禁止隐藏")
		}
		switch v.Operation {
		case "add":
			merged[v.SectionKey] = v
			sources[v.SectionKey] = "batch-only"
		case "replace":
			v.AllowHide = b.AllowHide
			merged[v.SectionKey] = v
			sources[v.SectionKey] = "overridden"
		case "hide":
			b.IsVisible = false
			merged[v.SectionKey] = b
			sources[v.SectionKey] = "hidden"
		case "inherit":
			if v.IsPublic && !b.IsPublic {
				return nil, nil, invalid("继承不能把私有基础内容提升为公开")
			}
			if v.SortOrder != nil {
				b.SortOrder = v.SortOrder
			}
			if v.Status == "disabled" {
				b.Status = "disabled"
			}
			b.IsVisible = b.IsVisible && v.IsVisible
			b.IsPublic = b.IsPublic && v.IsPublic
			merged[v.SectionKey] = b
		default:
			return nil, nil, invalid("模块操作不正确")
		}
	}
	if len(merged) > MaxSections {
		return nil, nil, invalid("有效模块数超过 100")
	}
	for key, v := range merged {
		x := EffectiveSection{SectionKey: key, SectionType: v.SectionType, Source: sources[key], BaseRevisionID: rid, SectionID: v.ID, IsPublic: v.IsPublic, AllowHide: v.AllowHide}
		if v.SortOrder != nil {
			x.SortOrder = *v.SortOrder
		}
		if x.Source == "batch-only" {
			x.BaseRevisionID = ""
		}
		if !v.IsVisible || v.Status == "disabled" || x.Source == "hidden" {
			x.Source = "hidden"
			hidden = append(hidden, x)
			continue
		}
		var selected *models.SectionTranslationView
		for i := range v.Translations {
			t := &v.Translations[i]
			if t.LanguageCode == lang {
				selected = t
				break
			}
			if t.LanguageCode == v.SourceLanguage {
				selected = t
			}
		}
		if selected == nil {
			return nil, nil, invalid("模块缺少源语言翻译")
		}
		x.Title = selected.Title
		x.Content = selected.Content
		x.Language = selected.LanguageCode
		visible = append(visible, x)
	}
	less := func(a, b EffectiveSection) bool {
		if a.SortOrder == b.SortOrder {
			return a.SectionKey < b.SectionKey
		}
		return a.SortOrder < b.SortOrder
	}
	sort.Slice(visible, func(i, j int) bool { return less(visible[i], visible[j]) })
	sort.Slice(hidden, func(i, j int) bool { return less(hidden[i], hidden[j]) })
	return visible, hidden, nil
}

// Sections reuse the existing parent data-permission and transaction mechanisms.
type Sections struct{ Batches }

func (s *Sections) sectionSet(tx *gorm.DB, pid, rid, bid, lang string) (SectionSet, error) {
	out := SectionSet{Sections: []SectionView{}, BaseSections: []SectionView{}}
	var e error
	if bid != "" {
		var b models.Batch
		if e = s.batchScope(tx).Where("batches.id=?", bid).Take(&b).Error; e != nil {
			return out, e
		}
		out.BaseRevisionID = b.BaseProductRevisionID
		var r models.Revision
		if e = tx.Where("id=?", b.BaseProductRevisionID).Take(&r).Error; e != nil {
			return out, e
		}
		out.SourceLanguage = r.SourceLanguage
		out.BaseSections, e = loadSections(tx, "product_revision_id", b.BaseProductRevisionID)
		if e != nil {
			return out, e
		}
		out.Sections, e = loadSections(tx, "batch_id", bid)
	} else {
		if _, e = s.product(tx, pid); e != nil {
			return out, e
		}
		var r models.Revision
		if e = tx.Where("id=? AND product_id=?", rid, pid).Take(&r).Error; e != nil {
			return out, e
		}
		out.SourceLanguage = r.SourceLanguage
		out.BaseRevisionID = rid
		out.Sections, e = loadSections(tx, "product_revision_id", rid)
	}
	if e != nil {
		return out, e
	}
	media, me := aggregateMedia(tx, rid, bid)
	if me != nil {
		return out, me
	}
	out.Token = digest([]interface{}{out.Sections, out.BaseSections, media})
	if lang == "" {
		lang = out.SourceLanguage
	}
	if !languages[lang] {
		return out, invalid("不支持的语言")
	}
	if bid != "" {
		out.Effective, out.Hidden, e = ResolveEffectiveSections(out.BaseSections, out.Sections, out.BaseRevisionID, lang)
	} else {
		out.Effective, out.Hidden, e = ResolveEffectiveSections(out.Sections, nil, rid, lang)
	}
	return out, e
}
func (s *Sections) GetSections(pid, rid, bid, lang string) (SectionSet, error) {
	var out SectionSet
	e := s.Orm.Transaction(func(tx *gorm.DB) error { var e error; out, e = s.sectionSet(tx, pid, rid, bid, lang); return e })
	return out, s.fail(e)
}
func (s *Sections) sectionWrite(pid, rid, bid, token string, fn func(*gorm.DB, SectionSet, string) error) error {
	work := func(tx *gorm.DB, now string) error {
		set, e := s.sectionSet(tx, pid, rid, bid, "")
		if e != nil {
			return e
		}
		if token == "" || token != set.Token {
			return conflict("模块已变化，请刷新后重试")
		}
		if e = fn(tx, set, now); e != nil {
			return e
		}
		table, id := "product_revisions", rid
		if bid != "" {
			table, id = "batches", bid
		}
		return tx.Table(table).Where("id=?", id).Updates(map[string]interface{}{"updated_at": now, "updated_by": s.Actor}).Error
	}
	if bid == "" {
		return s.write(pid, func(tx *gorm.DB, p models.Product, now string) error {
			var r models.Revision
			if e := tx.Where("id=? AND product_id=?", rid, pid).Take(&r).Error; e != nil {
				return e
			}
			if r.RevisionStatus != "draft" {
				return conflict("版本已冻结")
			}
			return work(tx, now)
		})
	}
	return s.fail(s.Orm.Transaction(func(tx *gorm.DB) error {
		if s.Actor < 1 {
			return &BusinessError{401, "请先登录"}
		}
		if e := tx.Exec("UPDATE batches SET id=id WHERE id=?", bid).Error; e != nil {
			return e
		}
		var b models.Batch
		if e := s.batchScope(tx).Where("batches.id=?", bid).Take(&b).Error; e != nil {
			return e
		}
		if b.WorkflowStatus != "draft" || b.ActivePublishRecordID != nil {
			return conflict("批次已冻结")
		}
		return work(tx, stamp())
	}))
}
func (s *Sections) sectionAudit(tx *gorm.DB, bid, event, id, now string) error {
	if bid != "" {
		return s.batchAudit(tx, bid, event, "custom_sections", id, nil, map[string]interface{}{"changed_fields": []string{"sections"}})
	}
	return s.audit(tx, event, "custom_sections", id, now, map[string]interface{}{"changed_fields": []string{"sections"}})
}
func saveSectionTranslations(tx *gorm.DB, id string, ts []dto.SectionTranslation, actor int, now string) error {
	// Preserve existing language IDs on edits; no duplicate rows, delete omitted languages atomically.
	langs := []string{}
	for _, t := range ts {
		langs = append(langs, t.LanguageCode)
	}
	if e := tx.Where("custom_section_id=? AND language_code NOT IN ?", id, langs).Delete(&models.SectionTranslation{}).Error; e != nil {
		return e
	}
	if len(ts) == 0 {
		return tx.Where("custom_section_id=?", id).Delete(&models.SectionTranslation{}).Error
	}
	for _, t := range ts {
		m := map[string]interface{}{"language_code": t.LanguageCode, "translation_status": t.TranslationStatus, "title": t.Title, "content": string(t.Content), "updated_at": now, "updated_by": actor}
		var old models.SectionTranslation
		e := tx.Where("custom_section_id=? AND language_code=?", id, t.LanguageCode).Take(&old).Error
		if errors.Is(e, gorm.ErrRecordNotFound) {
			metadata(m, actor, now)
			m["custom_section_id"] = id
			e = tx.Table("custom_section_translations").Create(m).Error
		} else if e == nil {
			e = tx.Model(&old).Updates(m).Error
		}
		if e != nil {
			return e
		}
	}
	return nil
}
func (s *Sections) putSection(tx *gorm.DB, set SectionSet, bid, rid, id string, d dto.SectionContent, now string) (string, error) {
	if e := validateSection(d, set.SourceLanguage); e != nil {
		return "", e
	}
	var old *SectionView
	for i := range set.Sections {
		if set.Sections[i].ID == id {
			old = &set.Sections[i]
		}
	}
	if id != "" && old == nil {
		return "", gorm.ErrRecordNotFound
	}
	if old != nil && (old.SectionKey != d.SectionKey || old.SectionType != d.SectionType) {
		return "", invalid("模块键和类型创建后不可变")
	}
	if bid == "" && d.Operation != "add" {
		return "", invalid("模板模块只能 add")
	}
	if bid != "" && d.AllowHide {
		return "", invalid("批次不能授权自己隐藏基础模块")
	}
	if old == nil && len(set.Sections) >= MaxSections {
		return "", invalid("模块数超过 100")
	}
	candidate := SectionView{Section: models.Section{ID: id, SectionKey: d.SectionKey, SectionType: d.SectionType, Operation: d.Operation, SourceLanguage: set.SourceLanguage, SortOrder: d.SortOrder, IsPublic: d.IsPublic, IsVisible: d.IsVisible, AllowHide: d.AllowHide, Status: d.Status}, Translations: []models.SectionTranslationView{}}
	for _, t := range d.Translations {
		candidate.Translations = append(candidate.Translations, models.SectionTranslationView{SectionTranslation: models.SectionTranslation{LanguageCode: t.LanguageCode, Title: t.Title}, Content: t.Content})
	}
	if bid != "" {
		next := []SectionView{}
		for _, v := range set.Sections {
			if v.ID != id {
				next = append(next, v)
			}
		}
		next = append(next, candidate)
		if _, _, e := ResolveEffectiveSections(set.BaseSections, next, set.BaseRevisionID, set.SourceLanguage); e != nil {
			return "", e
		}
	}
	if old != nil && (d.SectionType != old.SectionType || d.Operation == "hide" || d.Operation == "inherit") {
		if e := sectionAssets(tx, []string{id}); e != nil {
			return "", e
		}
	}
	m := map[string]interface{}{"section_key": d.SectionKey, "section_type": d.SectionType, "operation": d.Operation, "source_language": set.SourceLanguage, "sort_order": d.SortOrder, "is_visible": d.IsVisible, "is_public": d.IsPublic, "allow_hide": d.AllowHide, "status": d.Status, "updated_at": now, "updated_by": s.Actor}
	event := "custom_section_updated"
	if old == nil {
		metadata(m, s.Actor, now)
		id = m["id"].(string)
		if bid == "" {
			m["product_revision_id"] = rid
		} else {
			m["batch_id"] = bid
		}
		if e := tx.Table("custom_sections").Create(m).Error; e != nil {
			return "", e
		}
		event = "custom_section_created"
	} else {
		if e := tx.Table("custom_sections").Where("id=?", id).Updates(m).Error; e != nil {
			return "", e
		}
	}
	if e := saveSectionTranslations(tx, id, d.Translations, s.Actor, now); e != nil {
		return "", e
	}
	if bid != "" {
		switch d.Operation {
		case "replace":
			event = "batch_section_overridden"
		case "hide":
			event = "batch_section_hidden"
		case "add":
			if old == nil {
				event = "batch_section_created"
			}
		}
	}
	return id, s.sectionAudit(tx, bid, event, id, now)
}
func (s *Sections) PutSection(pid, rid, bid, id string, req dto.SectionWrite) (string, error) {
	var result string
	e := s.sectionWrite(pid, rid, bid, req.ExpectedToken, func(tx *gorm.DB, set SectionSet, now string) error {
		var e error
		result, e = s.putSection(tx, set, bid, rid, id, req.Section, now)
		return e
	})
	return result, e
}
func (s *Sections) DeleteSection(pid, rid, bid, id, token string) error {
	return s.sectionWrite(pid, rid, bid, token, func(tx *gorm.DB, set SectionSet, now string) error {
		var found *SectionView
		for i := range set.Sections {
			if set.Sections[i].ID == id {
				found = &set.Sections[i]
			}
		}
		if found == nil {
			return gorm.ErrRecordNotFound
		}
		if e := sectionAssets(tx, []string{id}); e != nil {
			return e
		}
		if e := tx.Where("custom_section_id=?", id).Delete(&models.SectionTranslation{}).Error; e != nil {
			return e
		}
		if e := tx.Where("id=?", id).Delete(&models.Section{}).Error; e != nil {
			return e
		}
		event := "custom_section_deleted"
		if bid != "" && found.Operation != "add" {
			event = "batch_section_reset"
		}
		return s.sectionAudit(tx, bid, event, id, now)
	})
}
func (s *Sections) TranslateSection(pid, rid, bid, id string, req dto.SectionTranslate) error {
	return s.sectionWrite(pid, rid, bid, req.ExpectedToken, func(tx *gorm.DB, set SectionSet, now string) error {
		for _, v := range set.Sections {
			if v.ID == id {
				d := sectionDTO(v)
				if d.Operation == "hide" || d.Operation == "inherit" {
					return invalid("该操作不保存翻译")
				}
				found := false
				for i, t := range d.Translations {
					if t.LanguageCode == req.Translation.LanguageCode {
						d.Translations[i] = req.Translation
						found = true
					}
				}
				if !found {
					d.Translations = append(d.Translations, req.Translation)
				}
				if e := validateSection(d, set.SourceLanguage); e != nil {
					return e
				}
				if e := sectionAssets(tx, []string{id}); e != nil {
					return e
				}
				if e := saveSectionTranslations(tx, id, d.Translations, s.Actor, now); e != nil {
					return e
				}
				return s.sectionAudit(tx, bid, "custom_section_translation_updated", id, now)
			}
		}
		return gorm.ErrRecordNotFound
	})
}
func (s *Sections) ReorderSections(pid, rid, bid string, req dto.SectionReorder) error {
	return s.sectionWrite(pid, rid, bid, req.ExpectedToken, func(tx *gorm.DB, set SectionSet, now string) error {
		if len(req.Keys) != len(set.Sections) {
			return invalid("排序必须包含当前全部自有模块")
		}
		seen := map[string]bool{}
		for i, k := range req.Keys {
			if seen[k] {
				return invalid("排序键重复")
			}
			seen[k] = true
			var row *SectionView
			for j := range set.Sections {
				if set.Sections[j].SectionKey == k {
					row = &set.Sections[j]
				}
			}
			if row == nil {
				return invalid("排序包含未知模块")
			}
			if e := tx.Model(&models.Section{}).Where("id=?", row.ID).Updates(map[string]interface{}{"sort_order": i * 10, "updated_at": now, "updated_by": s.Actor}).Error; e != nil {
				return e
			}
		}
		id := rid
		if bid != "" {
			id = bid
		}
		return s.sectionAudit(tx, bid, "custom_section_reordered", id, now)
	})
}
func cloneSections(tx *gorm.DB, column, source, target string, actor int, now string) error {
	rows, e := loadSections(tx, column, source)
	if e != nil {
		return e
	}
	if e = validateSectionRows(tx, rows); e != nil {
		return e
	}
	for _, v := range rows {
		r := v.Section
		r.ID = uuid.NewString()
		r.CreatedAt = now
		r.UpdatedAt = now
		r.CreatedBy = actor
		r.UpdatedBy = actor
		r.Status = "draft"
		if column == "batch_id" {
			r.BatchID = &target
		} else {
			r.ProductRevisionID = &target
		}
		if e = tx.Create(&r).Error; e != nil {
			return e
		}
		ts := sectionDTO(v).Translations
		for i := range ts {
			ts[i].TranslationStatus = "draft"
		}
		if e = saveSectionTranslations(tx, r.ID, ts, actor, now); e != nil {
			return e
		}
		if e = cloneMediaLinks(tx, "custom_section_id", v.ID, r.ID, actor, now); e != nil {
			return e
		}
	}
	return nil
}
