package service

import (
	"encoding/json"
	"errors"
	"github.com/google/uuid"
	"go-admin/app/passport/models"
	"go-admin/app/passport/service/dto"
	"go-admin/common/actions"
	"gorm.io/gorm"
	"strings"
)

// Reuse the upstream service, actor and permission context; business writes are aggregate transactions.
type Batches struct{ Products }
type BatchRow struct {
	ReviewState string `json:"review_state"`
	models.Batch
	ProductCode     string `json:"product_code"`
	BaseNumber      int64  `json:"base_number"`
	OverrideCount   int64  `json:"override_count"`
	InspectionCount int64  `json:"inspection_count"`
}
type EffectiveField struct {
	FieldKey string      `json:"field_key"`
	Value    interface{} `json:"value"`
	Source   string      `json:"source"`
	Language string      `json:"language"`
}
type BatchView struct {
	Sections       []EffectiveSection       `json:"effective_sections"`
	HiddenSections []EffectiveSection       `json:"hidden_sections"`
	Batch          BatchRow                 `json:"batch"`
	Base           RevisionView             `json:"base"`
	Overrides      []models.BatchOverride   `json:"overrides"`
	Inspections    []models.InspectionItem  `json:"inspections"`
	Effective      []EffectiveField         `json:"effective"`
	Rules          []OverrideRule           `json:"rules"`
	Audit          []map[string]interface{} `json:"audit"`
	PreviewKind    string                   `json:"preview_kind"`
}

func (s *Batches) batchFail(e error) error {
	if errors.Is(e, gorm.ErrRecordNotFound) {
		return &BusinessError{404, "批次或所选产品不存在，或不在数据权限范围内"}
	}
	if e != nil && strings.Contains(e.Error(), "batches.batch_code") {
		return conflict("批次编码已存在，请使用新的编码")
	}
	return s.fail(e)
}
func (s *Batches) batchScope(db *gorm.DB) *gorm.DB {
	if s.Admin {
		return db.Table("batches")
	}
	if s.Permission == nil || s.Permission.DataScope == "" {
		return db.Table("batches").Where("1=0")
	}
	inner := db.Session(&gorm.Session{NewDB: true}).Table("batches").Select("batches.*,created_by AS create_by")
	owned := db.Session(&gorm.Session{NewDB: true}).Table("(?) AS batch_scope", inner).Scopes(actions.Permission("batch_scope", s.Permission)).Select("batch_scope.id")
	return db.Table("batches").Where("batches.id IN (?)", owned)
}
func (s *Batches) batch(db *gorm.DB, id string) (models.Batch, error) {
	var b models.Batch
	e := s.batchScope(db).Where("batches.id=?", id).Take(&b).Error
	return b, e
}

const batchSelect = `batches.*, CASE WHEN batches.workflow_status='pending_review' AND EXISTS(SELECT 1 FROM review_records rr WHERE rr.id=batches.current_review_record_id AND rr.decision='approved') THEN 'ready_for_publish' ELSE batches.workflow_status END AS review_state, (SELECT product_code FROM products WHERE id=batches.product_id) AS product_code,
(SELECT revision_number FROM product_revisions WHERE id=batches.base_product_revision_id) AS base_number,
(SELECT count(*) FROM batch_overrides WHERE batch_id=batches.id) AS override_count,
(SELECT count(*) FROM inspection_items WHERE batch_id=batches.id) AS inspection_count`

func (s *Batches) ListBatches(q dto.BatchQuery) ([]BatchRow, int64, error) {
	if q.PageIndex < 1 {
		q.PageIndex = 1
	}
	if q.PageSize < 1 {
		q.PageSize = 10
	}
	if q.PageSize > 100 {
		q.PageSize = 100
	}
	if len(q.Search) > 200 {
		return nil, 0, invalid("搜索内容过长")
	}
	db := s.batchScope(s.Orm)
	if q.Search != "" {
		db = db.Where("batches.batch_code LIKE ?", "%"+strings.TrimSpace(q.Search)+"%")
	}
	if q.ProductID != "" {
		db = db.Where("batches.product_id=?", q.ProductID)
	}
	if q.Status != "" {
		switch q.Status {
		case "draft", "pending_review", "published", "archived":
		default:
			return nil, 0, invalid("工作流状态不正确")
		}
		db = db.Where("batches.workflow_status=?", q.Status)
	}
	var n int64
	if e := db.Count(&n).Error; e != nil {
		return nil, 0, s.batchFail(e)
	}
	out := []BatchRow{}
	e := db.Select(batchSelect).Order("batches.updated_at DESC,batches.id").Limit(q.PageSize).Offset((q.PageIndex - 1) * q.PageSize).Scan(&out).Error
	return out, n, s.batchFail(e)
}
func (s *Batches) loadBatch(tx *gorm.DB, id, lang string) (BatchView, error) {
	out := BatchView{Overrides: []models.BatchOverride{}, Inspections: []models.InspectionItem{}, Audit: []map[string]interface{}{}, Rules: OverrideRules, PreviewKind: "DRAFT / INTERNAL WORKING PREVIEW"}
	b, e := s.batch(tx, id)
	if e != nil {
		return out, e
	}
	out.Batch.Batch = b
	if e = tx.Table("batches").Where("batches.id=?", id).Select(batchSelect).Scan(&out.Batch).Error; e != nil {
		return out, e
	}
	// Batch authorization is authoritative for historical base access; do not require the product's current owner scope.
	out.Base, e = s.revision(tx, b.ProductID, b.BaseProductRevisionID)
	if e != nil {
		return out, e
	}
	if e = tx.Where("batch_id=?", id).Order("field_key").Find(&out.Overrides).Error; e != nil {
		return out, e
	}
	if e = tx.Where("batch_id=?", id).Order("sort_order,item_code").Find(&out.Inspections).Error; e != nil {
		return out, e
	}
	baseSections, se := loadSections(tx, "product_revision_id", out.Base.ID)
	if se != nil {
		return out, se
	}
	ownSections, se := loadSections(tx, "batch_id", out.Batch.ID)
	if se != nil {
		return out, se
	}
	sectionLang := lang
	if sectionLang == "" {
		sectionLang = out.Base.SourceLanguage
	}
	out.Sections, out.HiddenSections, se = ResolveEffectiveSections(baseSections, ownSections, out.Base.ID, sectionLang)
	if se != nil {
		return out, se
	}
	out.Effective, e = ResolveEffectiveBatch(tx, out.Base, out.Overrides, lang)
	if e != nil {
		return out, e
	}
	e = tx.Table("passport_audit_events").Select("id,event_type,created_at,actor_user_id,summary,metadata").Where("batch_id=?", id).Order("created_at DESC,id DESC").Limit(50).Find(&out.Audit).Error
	return out, e
}
func (s *Batches) GetBatch(id, lang string) (BatchView, error) {
	var v BatchView
	if lang != "" && !languages[lang] {
		return v, invalid("不支持的语言")
	}
	e := s.Orm.Transaction(func(tx *gorm.DB) error { var e error; v, e = s.loadBatch(tx, id, lang); return e })
	return v, s.batchFail(e)
}

// ResolveEffectiveBatch is the one internal semantic resolver. It is NOT a published payload builder.
func ResolveEffectiveBatch(tx *gorm.DB, base RevisionView, overrides []models.BatchOverride, lang string) ([]EffectiveField, error) {
	if base.RevisionStatus != "sealed" {
		return nil, conflict("基础模板必须已封版")
	}
	if lang == "" {
		lang = base.SourceLanguage
	}
	if !languages[lang] {
		return nil, invalid("不支持的语言")
	}
	var source, requested map[string]interface{}
	for _, t := range base.Translations {
		var m map[string]interface{}
		_ = json.Unmarshal([]byte(encode(t)), &m)
		if t.LanguageCode == base.SourceLanguage {
			source = m
		}
		if t.LanguageCode == lang {
			requested = m
		}
	}
	if source == nil {
		return nil, conflict("基础模板源语言缺失")
	}
	var scalars map[string]interface{}
	_ = json.Unmarshal([]byte(encode(base.Revision)), &scalars)
	ov := map[string]models.BatchOverride{}
	for _, o := range overrides {
		if _, ok := overrideRule(o.FieldKey); !ok {
			return nil, conflict("此批次含尚未开放的覆盖类型，不能生成完整工作预览")
		}
		ov[o.FieldKey] = o
	}
	fields := []OverrideRule{{FieldKey: "product_name", Translatable: true}, {FieldKey: "short_description", Translatable: true}, {FieldKey: "category_code"}, {FieldKey: "origin_country_code"}, {FieldKey: "manufacturer_name", Translatable: true}, {FieldKey: "manufacturer_address", Translatable: true}}
	fields = append(fields, OverrideRules...)
	out := []EffectiveField{}
	for _, r := range fields {
		f := EffectiveField{FieldKey: r.FieldKey, Source: "inherited", Language: base.SourceLanguage}
		if r.Translatable {
			f.Value = source[r.FieldKey]
			if requested != nil && requested[r.FieldKey] != nil && requested[r.FieldKey] != "" {
				f.Value = requested[r.FieldKey]
				f.Language = lang
			}
		} else {
			f.Value = scalars[r.FieldKey]
		}
		if r.FieldKey == "process" {
			steps := []dto.ProcessLabel{}
			for _, p := range base.ProcessSteps {
				label := ""
				for _, t := range base.Translations {
					if t.LanguageCode == base.SourceLanguage {
						label = t.ProcessLabels[p.StepKey]
					}
				}
				for _, t := range base.Translations {
					if t.LanguageCode == lang && t.ProcessLabels[p.StepKey] != "" {
						label = t.ProcessLabels[p.StepKey]
					}
				}
				steps = append(steps, dto.ProcessLabel{StepKey: p.StepKey, Label: label})
			}
			f.Value = steps
		}
		if o, ok := ov[r.FieldKey]; ok {
			f.Source = "overridden"
			f.Language = o.SourceLanguage
			if o.Operation == "clear" {
				f.Source = "cleared"
				f.Value = nil
				if r.Kind == "json" {
					f.Value = []dto.ProcessLabel{}
				}
			} else {
				switch o.ValueKind {
				case "text", "decimal":
					f.Value = o.ValueText
				case "integer":
					f.Value = o.ValueInteger
				case "json":
					var p []dto.ProcessLabel
					if o.ValueJson == nil {
						return nil, invalid("工艺覆盖缺少内容")
					}
					if e := json.Unmarshal([]byte(*o.ValueJson), &p); e != nil {
						return nil, e
					}
					f.Value = p
				default:
					return nil, invalid("尚未开放的覆盖类型")
				}
				if r.Translatable && lang != o.SourceLanguage {
					var tr models.OverrideTranslation
					e := tx.Where("batch_override_id=? AND language_code=?", o.ID, lang).Take(&tr).Error
					if e != nil && !errors.Is(e, gorm.ErrRecordNotFound) {
						return nil, e
					}
					if e == nil {
						if tr.TranslatedValue != nil {
							f.Value = tr.TranslatedValue
							f.Language = lang
						}
						if tr.TranslatedProcess != nil {
							var p []dto.ProcessLabel
							if e = json.Unmarshal([]byte(*tr.TranslatedProcess), &p); e != nil {
								return nil, e
							}
							f.Value = p
							f.Language = lang
						}
					}
				}
			}
		}
		out = append(out, f)
	}
	return out, nil
}
func batchContentMap(c dto.BatchContent) map[string]interface{} {
	return map[string]interface{}{"production_date": c.ProductionDate, "expiry_date": c.ExpiryDate, "quality_status": c.QualityStatus, "internal_note": c.InternalNote}
}
func (s *Batches) batchAudit(tx *gorm.DB, bid, event, entity, id string, before, after interface{}) error {
	old, new := encode(before), encode(after)
	meta := map[string]interface{}{"event_schema_version": 1, "before_hash": digest(before), "after_hash": digest(after)}
	if len(old)+len(new) > 12000 {
		old = "null"
		new = "null"
		meta["truncated"] = true
	}
	return tx.Table("passport_audit_events").Create(map[string]interface{}{"id": uuid.NewString(), "batch_id": bid, "actor_user_id": s.Actor, "created_at": stamp(), "event_type": event, "entity_type": entity, "entity_id": id, "summary": "批次操作：" + event, "before_data": old, "after_data": new, "metadata": encode(meta)}).Error
}
func (s *Batches) batchWrite(id string, version int64, fn func(*gorm.DB, models.Batch) error) error {
	if s.Actor < 1 {
		return &BusinessError{401, "请先登录"}
	}
	e := s.Orm.Transaction(func(tx *gorm.DB) error {
		if e := tx.Exec("UPDATE batches SET id=id WHERE id=?", id).Error; e != nil {
			return e
		}
		b, e := s.batch(tx, id)
		if e != nil {
			return e
		}
		if b.WorkflowStatus != "draft" || b.ActivePublishRecordID != nil {
			return conflict("仅允许编辑未锁定的 Draft 批次")
		}
		if version < 1 || b.EditVersion != version {
			return conflict("批次已被修改，请刷新后重试")
		}
		return fn(tx, b)
	})
	return s.batchFail(e)
}
func (s *Batches) CreateBatch(req dto.CreateBatchRequest) (string, error) {
	code, e := validateCode(req.BatchCode)
	if e != nil {
		return "", invalid("批次编码须为 1–64 位字母、数字、下划线或连字符")
	}
	if e = validateBatchWork(&req.BatchWork); e != nil {
		return "", e
	}
	if req.RecordType == "" {
		req.RecordType = "test"
	}
	if req.RecordType != "test" && req.RecordType != "commercial" {
		return "", invalid("记录类型不正确")
	}
	if e = validateBatchRecordCode(code, req.RecordType); e != nil {
		return "", e
	}
	id := uuid.NewString()
	e = s.Orm.Transaction(func(tx *gorm.DB) error {
		// Acquire writer before reading the default; serializes with T5 default changes.
		if e := tx.Exec("UPDATE products SET id=id WHERE id=?", req.ProductID).Error; e != nil {
			return e
		}
		p, e := s.product(tx, req.ProductID)
		if e != nil {
			return e
		}
		if p.LifecycleStatus != "active" {
			return conflict("请选择已启用产品")
		}
		if p.CurrentRevisionID == nil {
			return conflict("此产品没有合法的已封版默认模板")
		}
		base, e := s.revision(tx, p.ID, *p.CurrentRevisionID)
		if e != nil || base.RevisionStatus != "sealed" {
			return conflict("此产品没有合法的已封版默认模板")
		}
		if e = unmanaged(tx, base.ID); e != nil {
			return e
		}
		m := batchContentMap(req.Content)
		metadata(m, s.Actor, stamp())
		m["id"] = id
		m["batch_code"] = code
		m["product_id"] = p.ID
		m["base_product_revision_id"] = base.ID
		m["record_type"] = req.RecordType
		var n int64
		if e = tx.Table("batches").Where("batch_code=?", code).Count(&n).Error; e != nil {
			return e
		}
		if n > 0 {
			return conflict("批次编码已存在，请使用新的编码")
		}
		if e = tx.Table("batches").Create(m).Error; e != nil {
			return e
		}
		if e = s.saveChildren(tx, id, base.SourceLanguage, req.BatchWork); e != nil {
			return e
		}
		return s.batchAudit(tx, id, "batch_created", "batches", id, nil, map[string]interface{}{"batch_code": code, "base_product_revision_id": base.ID})
	})
	return id, s.batchFail(e)
}
func (s *Batches) UpdateBatch(id string, req dto.UpdateBatchRequest) error {
	if e := validateBatchWork(&req.BatchWork); e != nil {
		return e
	}
	return s.batchWrite(id, req.ExpectedEditVersion, func(tx *gorm.DB, b models.Batch) error {
		base, e := s.revision(tx, b.ProductID, b.BaseProductRevisionID)
		if e != nil {
			return e
		}
		m := batchContentMap(req.Content)
		m["updated_at"] = stamp()
		m["updated_by"] = s.Actor
		m["edit_version"] = gorm.Expr("edit_version+1")
		if e = tx.Table("batches").Where("id=? AND edit_version=?", id, b.EditVersion).Updates(m).Error; e != nil {
			return e
		}
		if e = s.saveChildren(tx, id, base.SourceLanguage, req.BatchWork); e != nil {
			return e
		}
		return s.batchAudit(tx, id, "batch_edited", "batches", id, map[string]interface{}{"production_date": b.ProductionDate, "expiry_date": b.ExpiryDate, "quality_status": b.QualityStatus, "internal_note": b.InternalNote}, req.Content)
	})
}
func overrideMap(o dto.OverrideInput) map[string]interface{} {
	r, _ := overrideRule(o.FieldKey)
	var process *string
	if o.Process != nil {
		v := encode(o.Process)
		process = &v
	}
	return map[string]interface{}{"field_key": o.FieldKey, "value_kind": r.Kind, "operation": o.Operation, "value_text": o.ValueText, "value_integer": o.ValueInteger, "value_json": process, "value_media_asset_id": nil, "public_asset_label": nil}
}
func inspectionMap(i dto.InspectionInput) map[string]interface{} {
	var m map[string]interface{}
	_ = json.Unmarshal([]byte(encode(i)), &m)
	return m
}
func (s *Batches) saveChildren(tx *gorm.DB, bid, lang string, w dto.BatchWork) error {
	var oldOverrides []models.BatchOverride
	if e := tx.Where("batch_id=?", bid).Find(&oldOverrides).Error; e != nil {
		return e
	}
	wanted := map[string]dto.OverrideInput{}
	for _, o := range w.Overrides {
		wanted[o.FieldKey] = o
	}
	for _, old := range oldOverrides {
		o, exists := wanted[old.FieldKey]
		if exists {
			m := overrideMap(o)
			var raw map[string]interface{}
			_ = json.Unmarshal([]byte(encode(old)), &raw)
			same := true
			for k, v := range m {
				if encode(v) != encode(raw[k]) {
					same = false
				}
			}
			if same {
				delete(wanted, old.FieldKey)
				continue
			}
		}
		// No silent invalidation/loss of translations that this source-language form cannot edit.
		var n int64
		if e := tx.Table("batch_override_translations").Where("batch_override_id=?", old.ID).Count(&n).Error; e != nil {
			return e
		}
		if n > 0 && exists && o.Operation == "set" {
			return conflict("此覆盖已有其他语言译文，请先使用恢复继承清除旧覆盖后重新填写")
		}
		if e := tx.Where("batch_override_id=?", old.ID).Delete(&models.OverrideTranslation{}).Error; e != nil {
			return e
		}
		if e := tx.Delete(&old).Error; e != nil {
			return e
		}
		event := "override_reset"
		if exists {
			event = "override_set"
			if o.Operation == "clear" {
				event = "override_cleared"
			}
		}
		if e := s.batchAudit(tx, bid, event, "batch_overrides", old.ID, old, o); e != nil {
			return e
		}
	}
	for _, o := range wanted {
		m := overrideMap(o)
		metadata(m, s.Actor, stamp())
		m["batch_id"] = bid
		m["source_language"] = lang
		if e := tx.Table("batch_overrides").Create(m).Error; e != nil {
			return e
		}
		event := "override_set"
		if o.Operation == "clear" {
			event = "override_cleared"
		}
		if e := s.batchAudit(tx, bid, event, "batch_overrides", m["id"].(string), nil, o); e != nil {
			return e
		}
	}
	var oldItems []models.InspectionItem
	if e := tx.Where("batch_id=?", bid).Find(&oldItems).Error; e != nil {
		return e
	}
	items := map[string]dto.InspectionInput{}
	for _, i := range w.Inspections {
		items[i.ItemCode] = i
	}
	for _, old := range oldItems {
		i, exists := items[old.ItemCode]
		if exists {
			m := inspectionMap(i)
			var raw map[string]interface{}
			_ = json.Unmarshal([]byte(encode(old)), &raw)
			same := true
			for k, v := range m {
				if encode(v) != encode(raw[k]) {
					same = false
				}
			}
			if same {
				delete(items, old.ItemCode)
				continue
			}
		}
		var n int64
		if e := tx.Table("asset_links").Where("inspection_item_id=?", old.ID).Count(&n).Error; e != nil {
			return e
		}
		if n > 0 {
			return conflict("检测项目含尚未开放的附件，不能修改或删除")
		}
		if exists {
			if e := tx.Table("inspection_item_translations").Where("inspection_item_id=?", old.ID).Count(&n).Error; e != nil {
				return e
			}
			if n > 0 {
				return conflict("检测项目已有其他语言译文，本阶段不能改写该项目")
			}
			m := inspectionMap(i)
			m["updated_by"] = s.Actor
			m["updated_at"] = stamp()
			if e := tx.Model(&old).Updates(m).Error; e != nil {
				return e
			}
			delete(items, old.ItemCode)
		} else {
			if e := tx.Where("inspection_item_id=?", old.ID).Delete(&models.InspectionTranslation{}).Error; e != nil {
				return e
			}
			if e := tx.Delete(&old).Error; e != nil {
				return e
			}
		}
		if e := s.batchAudit(tx, bid, "inspection_changed", "inspection_items", old.ID, old, map[string]interface{}{"operation": map[bool]string{true: "update", false: "delete"}[exists], "item": i}); e != nil {
			return e
		}
	}
	for _, i := range items {
		m := inspectionMap(i)
		metadata(m, s.Actor, stamp())
		m["batch_id"] = bid
		m["source_language"] = lang
		if e := tx.Table("inspection_items").Create(m).Error; e != nil {
			return e
		}
		if e := s.batchAudit(tx, bid, "inspection_changed", "inspection_items", m["id"].(string), nil, map[string]interface{}{"operation": "create", "item": i}); e != nil {
			return e
		}
	}
	return nil
}
func (s *Batches) CloneBatch(id string, req dto.CloneBatchRequest) (string, error) {
	code, e := validateCode(req.BatchCode)
	if e != nil {
		return "", invalid("请填写合法的新批次编码")
	}
	c := dto.BatchContent{ProductionDate: req.ProductionDate, ExpiryDate: req.ExpiryDate, QualityStatus: "pending"}
	if e = validateBatchContent(&c); e != nil {
		return "", e
	}
	newid := uuid.NewString()
	// Source is read-only. Reserve the writer on the product before loading a consistent source.
	e = s.Orm.Transaction(func(tx *gorm.DB) error {
		if s.Actor < 1 {
			return &BusinessError{401, "请先登录"}
		}
		if e := tx.Exec("UPDATE products SET id=id WHERE id=(SELECT product_id FROM batches WHERE id=?)", id).Error; e != nil {
			return e
		}
		b, e := s.batch(tx, id)
		if e != nil {
			return e
		}
		if e = validateBatchRecordCode(code, b.RecordType); e != nil {
			return e
		}
		if (b.WorkflowStatus != "draft" && b.WorkflowStatus != "published") || b.ActivePublishRecordID != nil {
			return conflict("仅允许从未锁定的Draft或Published批次创建新草稿")
		}
		if b.EditVersion != req.ExpectedEditVersion {
			return conflict("来源已变化，请刷新后重试")
		}
		var p models.Product
		if e := tx.Where("id=?", b.ProductID).Take(&p).Error; e != nil {
			return e
		}
		if p.LifecycleStatus != "active" {
			return conflict("产品已停用或归档，不能复制新批次")
		}
		for _, table := range []string{"certification_links"} {
			var n int64
			if e := tx.Table(table).Where("batch_id=?", id).Count(&n).Error; e != nil {
				return e
			}
			if n > 0 {
				return conflict("来源含尚未开放的关联，不能静默遗漏后复制")
			}
		}
		v, e := s.loadBatch(tx, id, "")
		if e != nil {
			return e
		}
		if e = unmanaged(tx, v.Base.ID); e != nil {
			return e
		}
		var count int64
		if e = tx.Table("asset_links").Where("inspection_item_id IN (SELECT id FROM inspection_items WHERE batch_id=?)", id).Count(&count).Error; e != nil {
			return e
		}
		if count > 0 {
			return conflict("来源检测含附件，本阶段不能复制")
		}
		m := batchContentMap(c)
		metadata(m, s.Actor, stamp())
		m["id"] = newid
		m["batch_code"] = code
		m["product_id"] = b.ProductID
		m["base_product_revision_id"] = b.BaseProductRevisionID
		m["record_type"] = b.RecordType
		m["cloned_from_batch_id"] = id
		if e = tx.Table("batches").Create(m).Error; e != nil {
			return e
		}
		now := stamp()
		for _, o := range v.Overrides {
			if _, ok := overrideRule(o.FieldKey); !ok {
				return conflict("来源含尚未开放的覆盖类型")
			}
			old := o.ID
			o.ID = uuid.NewString()
			o.BatchID = newid
			o.CreatedBy = int64(s.Actor)
			o.UpdatedBy = int64(s.Actor)
			o.CreatedAt = now
			o.UpdatedAt = now
			if e = tx.Create(&o).Error; e != nil {
				return e
			}
			var tr []models.OverrideTranslation
			if e = tx.Where("batch_override_id=?", old).Find(&tr).Error; e != nil {
				return e
			}
			for _, t := range tr {
				t.ID = uuid.NewString()
				t.BatchOverrideID = o.ID
				t.CreatedBy = int64(s.Actor)
				t.UpdatedBy = int64(s.Actor)
				t.CreatedAt = now
				t.UpdatedAt = now
				t.TranslationStatus = "draft"
				if e = tx.Create(&t).Error; e != nil {
					return e
				}
			}
		}
		for _, i := range v.Inspections {
			old := i.ID
			i.ID = uuid.NewString()
			i.BatchID = newid
			i.CreatedBy = int64(s.Actor)
			i.UpdatedBy = int64(s.Actor)
			i.CreatedAt = now
			i.UpdatedAt = now
			i.NumericValue = nil
			i.TextValue = nil
			i.TestedOn = nil
			i.InternalNote = nil
			i.Judgement = "not_tested"
			if e = tx.Create(&i).Error; e != nil {
				return e
			}
			var tr []models.InspectionTranslation
			if e = tx.Where("inspection_item_id=?", old).Find(&tr).Error; e != nil {
				return e
			}
			for _, t := range tr {
				t.ID = uuid.NewString()
				t.InspectionItemID = i.ID
				t.CreatedBy = int64(s.Actor)
				t.UpdatedBy = int64(s.Actor)
				t.CreatedAt = now
				t.UpdatedAt = now
				t.TranslationStatus = "draft"
				t.ResultDisplayText = nil
				if e = tx.Create(&t).Error; e != nil {
					return e
				}
			}
		}
		if e = cloneSections(tx, "batch_id", id, newid, s.Actor, stamp()); e != nil {
			return e
		}
		return s.batchAudit(tx, newid, "batch_cloned", "batches", newid, nil, map[string]interface{}{"source_id": id, "base_product_revision_id": b.BaseProductRevisionID, "inspection_count": len(v.Inspections), "override_count": len(v.Overrides)})
	})
	return newid, s.batchFail(e)
}
