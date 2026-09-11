package service

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	core "github.com/go-admin-team/go-admin-core/v2/sdk/service"
	"github.com/google/uuid"
	"go-admin/app/passport/models"
	"go-admin/app/passport/service/dto"
	"go-admin/common/actions"
	"gorm.io/gorm"
	"strings"
	"time"
)

type Products struct {
	core.Service
	Actor      int
	Admin      bool
	Permission *actions.DataPermission
}
type ProductRow struct {
	models.Product
	ProductName   string `json:"product_name"`
	RevisionCount int64  `json:"revision_count"`
	DefaultNumber *int64 `json:"default_number"`
}
type TranslationView struct {
	models.Translation
	ProcessLabels map[string]string `json:"process_labels"`
}
type RevisionView struct {
	models.Revision
	ProcessSteps []dto.Step        `json:"process_steps"`
	Translations []TranslationView `json:"translations"`
	Token        string            `json:"token"`
	CreatorName  string            `json:"creator_name"`
}
type ProductView struct {
	Product   ProductRow     `json:"product"`
	Revisions []RevisionView `json:"revisions"`
}

func stamp() string               { return time.Now().UTC().Format("2006-01-02T15:04:05.000Z") }
func encode(v interface{}) string { b, _ := json.Marshal(v); return string(b) }
func digest(v interface{}) string {
	h := sha256.Sum256([]byte(encode(v)))
	return hex.EncodeToString(h[:])
}
func (s *Products) fail(e error) error {
	if e == nil {
		return nil
	}
	var b *BusinessError
	if errors.As(e, &b) {
		return e
	}
	if errors.Is(e, gorm.ErrRecordNotFound) {
		return &BusinessError{404, "产品或版本不存在，或不在您的数据权限范围内"}
	}
	if s.Log != nil {
		s.Log.Errorf("product template: %v", e)
	}
	msg := e.Error()
	switch {
	case strings.Contains(msg, "products.product_code"):
		return conflict("产品编码已存在，归档编码也不能重复使用")
	case strings.Contains(msg, "UNIQUE"):
		return conflict("记录或版本已存在，请刷新后重试")
	case strings.Contains(msg, "locked") || strings.Contains(msg, "busy"):
		return conflict("其他用户正在保存，请稍后刷新重试")
	case strings.Contains(msg, "frozen") || strings.Contains(msg, "sealed"):
		return conflict("此版本已冻结，不能修改；请创建新版本")
	case strings.Contains(msg, "constraint"):
		return invalid("数据不符合模板规则，请检查填写内容")
	}
	return &BusinessError{500, "保存或读取失败，请稍后重试"}
}

// Adapt the business created_by column to upstream Permission without changing it.
func (s *Products) scope(db *gorm.DB) *gorm.DB {
	if s.Admin {
		return db.Table("products")
	}
	if s.Permission == nil || s.Permission.DataScope == "" {
		return db.Table("products").Where("1=0")
	}
	inner := db.Session(&gorm.Session{NewDB: true}).Table("products").Select("products.*, created_by AS create_by")
	owned := db.Session(&gorm.Session{NewDB: true}).Table("(?) AS owner_scope", inner).Scopes(actions.Permission("owner_scope", s.Permission)).Select("owner_scope.id")
	return db.Table("products").Where("products.id IN (?)", owned)
}
func (s *Products) product(db *gorm.DB, id string) (models.Product, error) {
	var p models.Product
	err := s.scope(db).Where("products.id=?", id).Take(&p).Error
	return p, err
}
func (s *Products) List(q dto.Query) ([]ProductRow, int64, error) {
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
	db := s.scope(s.Orm)
	if q.Status != "" {
		if q.Status != "active" && q.Status != "disabled" && q.Status != "archived" {
			return nil, 0, invalid("产品状态不正确")
		}
		db = db.Where("products.lifecycle_status=?", q.Status)
	}
	if q.Search != "" {
		like := "%" + strings.TrimSpace(q.Search) + "%"
		db = db.Where("(products.product_code LIKE ? OR EXISTS (SELECT 1 FROM product_revisions r JOIN product_revision_translations t ON t.product_revision_id=r.id WHERE r.product_id=products.id AND t.product_name LIKE ?))", like, like)
	}
	var count int64
	if e := db.Count(&count).Error; e != nil {
		return nil, 0, s.fail(e)
	}
	selectSQL := `products.*, (SELECT count(*) FROM product_revisions WHERE product_id=products.id) AS revision_count,
 (SELECT revision_number FROM product_revisions WHERE id=products.current_revision_id) AS default_number,
 COALESCE((SELECT t.product_name FROM product_revisions r JOIN product_revision_translations t ON t.product_revision_id=r.id AND t.language_code=r.source_language WHERE r.product_id=products.id ORDER BY (r.id=products.current_revision_id) DESC, r.revision_number DESC LIMIT 1),'') AS product_name`
	rows := []ProductRow{}
	e := db.Select(selectSQL).Order("products.updated_at DESC, products.id").Limit(q.PageSize).Offset((q.PageIndex - 1) * q.PageSize).Scan(&rows).Error
	return rows, count, s.fail(e)
}
func (s *Products) revision(db *gorm.DB, pid, rid string) (RevisionView, error) {
	var v RevisionView
	err := db.Where("id=? AND product_id=?", rid, pid).Take(&v.Revision).Error
	if err != nil {
		return v, err
	}
	if err = json.Unmarshal([]byte(v.Revision.ProcessSteps), &v.ProcessSteps); err != nil {
		return v, err
	}
	rows := []models.Translation{}
	if err = db.Where("product_revision_id=?", rid).Order("language_code").Find(&rows).Error; err != nil {
		return v, err
	}
	v.Translations = []TranslationView{}
	for _, r := range rows {
		t := TranslationView{Translation: r}
		if err = json.Unmarshal([]byte(r.ProcessLabels), &t.ProcessLabels); err != nil {
			return v, err
		}
		v.Translations = append(v.Translations, t)
	}
	v.Token = digest(struct {
		Revision     models.Revision
		Translations []models.Translation
	}{v.Revision, rows})
	sections, sectionErr := loadSections(db, "product_revision_id", rid)
	if sectionErr != nil {
		return v, sectionErr
	}
	media, me := aggregateMedia(db, rid, "")
	if me != nil {
		return v, me
	}
	v.Token = digest([]interface{}{v.Token, sections, media})
	// Include JSON content in the optimistic token, not only scalar metadata.
	v.Token = digest([]interface{}{v.Token, v.ProcessSteps, v.Translations})
	if err = db.Table("sys_user").Select("nick_name").Where("user_id=?", v.CreatedBy).Scan(&v.CreatorName).Error; err != nil {
		return v, err
	}
	return v, nil
}
func (s *Products) Get(id string) (ProductView, error) {
	var out ProductView
	e := s.Orm.Transaction(func(tx *gorm.DB) error {
		p, e := s.product(tx, id)
		if e != nil {
			return e
		}
		out.Product.Product = p
		out.Revisions = []RevisionView{}
		var rows []models.Revision
		if e = tx.Where("product_id=?", id).Order("revision_number DESC").Find(&rows).Error; e != nil {
			return e
		}
		for _, r := range rows {
			v, e := s.revision(tx, id, r.ID)
			if e != nil {
				return e
			}
			out.Revisions = append(out.Revisions, v)
		}
		out.Product.RevisionCount = int64(len(rows))
		return nil
	})
	return out, s.fail(e)
}
func (s *Products) GetRevision(pid, rid string) (RevisionView, error) {
	var out RevisionView
	e := s.Orm.Transaction(func(tx *gorm.DB) error {
		if _, e := s.product(tx, pid); e != nil {
			return e
		}
		v, e := s.revision(tx, pid, rid)
		out = v
		return e
	})
	return out, s.fail(e)
}
func (s *Products) audit(tx *gorm.DB, event, entity, id, now string, meta map[string]interface{}) error {
	meta["event_schema_version"] = 1
	return tx.Table("passport_audit_events").Create(map[string]interface{}{"id": uuid.NewString(), "actor_user_id": s.Actor, "created_at": now, "event_type": event, "entity_type": entity, "entity_id": id, "summary": "产品模板操作：" + event, "metadata": encode(meta)}).Error
}
func contentMap(c dto.RevisionContent) map[string]interface{} {
	b, _ := json.Marshal(c)
	m := map[string]interface{}{}
	_ = json.Unmarshal(b, &m)
	m["process_steps"] = encode(c.ProcessSteps)
	return m
}
func translationMap(c dto.TranslationRequest) map[string]interface{} {
	b, _ := json.Marshal(c)
	m := map[string]interface{}{}
	_ = json.Unmarshal(b, &m)
	m["process_labels"] = encode(c.ProcessLabels)
	return m
}
func metadata(m map[string]interface{}, actor int, now string) {
	m["id"] = uuid.NewString()
	m["created_by"] = actor
	m["updated_by"] = actor
	m["created_at"] = now
	m["updated_at"] = now
}
func (s *Products) Create(req dto.CreateProductRequest) (string, error) {
	code, e := validateCode(req.ProductCode)
	if e != nil {
		return "", e
	}
	if e = validateContent(&req.Content); e != nil {
		return "", e
	}
	if len(req.Translations) < 1 || len(req.Translations) > 6 {
		return "", invalid("请填写源语言名称；最多六种翻译")
	}
	seen := map[string]bool{}
	for i := range req.Translations {
		t := &req.Translations[i]
		if e = validateTranslation(t, req.Content); e != nil {
			return "", e
		}
		if seen[t.LanguageCode] {
			return "", invalid("同一语言不能重复")
		}
		seen[t.LanguageCode] = true
	}
	if !seen[req.Content.SourceLanguage] {
		return "", invalid("请填写源语言的产品名称")
	}
	id := uuid.NewString()
	e = s.Orm.Transaction(func(tx *gorm.DB) error {
		var n int64
		if e := tx.Model(&models.Product{}).Where("product_code=?", code).Count(&n).Error; e != nil {
			return e
		}
		if n > 0 {
			return conflict("产品编码已存在，归档编码也不能重复使用")
		}
		now := stamp()
		p := models.Product{ID: id, ProductCode: code, LifecycleStatus: "active", CreatedAt: now, UpdatedAt: now, CreatedBy: s.Actor, UpdatedBy: s.Actor}
		if e := tx.Create(&p).Error; e != nil {
			return e
		}
		m := contentMap(req.Content)
		metadata(m, s.Actor, now)
		m["product_id"] = id
		m["revision_number"] = 1
		rid := m["id"].(string)
		if e := tx.Table("product_revisions").Create(m).Error; e != nil {
			return e
		}
		for _, t := range req.Translations {
			m := translationMap(t)
			metadata(m, s.Actor, now)
			m["product_revision_id"] = rid
			if e := tx.Table("product_revision_translations").Create(m).Error; e != nil {
				return e
			}
		}
		if e := s.audit(tx, "product_created", "products", id, now, map[string]interface{}{}); e != nil {
			return e
		}
		return s.audit(tx, "product_revision_created", "product_revisions", rid, now, map[string]interface{}{})
	})
	return id, s.fail(e)
}

// Reserve SQLite's writer BEFORE reading a revision number or state. No max+1 in browser.
func (s *Products) write(pid string, fn func(*gorm.DB, models.Product, string) error) error {
	if s.Actor < 1 {
		return &BusinessError{401, "请先登录"}
	}
	e := s.Orm.Transaction(func(tx *gorm.DB) error {
		if e := tx.Exec("UPDATE products SET id=id WHERE id=?", pid).Error; e != nil {
			return e
		}
		p, e := s.product(tx, pid)
		if e != nil {
			return e
		}
		if p.LifecycleStatus == "archived" {
			return conflict("产品已归档，历史版本只读")
		}
		return fn(tx, p, stamp())
	})
	return s.fail(e)
}
func unmanaged(tx *gorm.DB, rid string) error {
	for _, table := range []string{"certification_links"} {
		var n int64
		if e := tx.Table(table).Where("product_revision_id=?", rid).Count(&n).Error; e != nil {
			return e
		}
		if n > 0 {
			return conflict("此版本包含尚未开放管理的模块或关联，不能在本阶段复制或封版")
		}
	}
	if e := validateManagedMedia(tx, "product_revision_id", []string{rid}); e != nil {
		return e
	}
	rows, err := loadSections(tx, "product_revision_id", rid)
	if err != nil {
		return err
	}
	return validateSectionRows(tx, rows)
}
func (s *Products) Clone(pid string, req dto.CreateRevisionRequest) (string, error) {
	var rid string
	e := s.write(pid, func(tx *gorm.DB, p models.Product, now string) error {
		if req.SourceRevisionID == "" {
			return invalid("请选择来源版本")
		}
		source, e := s.revision(tx, pid, req.SourceRevisionID)
		if e != nil {
			return e
		}
		if e = unmanaged(tx, source.ID); e != nil {
			return e
		}
		if source.RevisionStatus == "abandoned" {
			return conflict("已弃用版本不能作为复制来源")
		}
		var n int64
		if e = tx.Model(&models.Revision{}).Where("product_id=?", pid).Select("COALESCE(MAX(revision_number),0)").Scan(&n).Error; e != nil {
			return e
		}
		if n >= 9007199254740991 {
			return conflict("版本号已达到上限")
		}
		r := source.Revision
		old := r.ID
		r.ID = uuid.NewString()
		rid = r.ID
		r.SourceRevisionID = &old
		r.RevisionNumber = n + 1
		r.RevisionStatus = "draft"
		r.SealedAt = nil
		r.SealedBy = nil
		r.ContentHash = nil
		r.CreatedAt = now
		r.UpdatedAt = now
		r.CreatedBy = s.Actor
		r.UpdatedBy = s.Actor
		if e = tx.Create(&r).Error; e != nil {
			return e
		}
		for _, v := range source.Translations {
			t := v.Translation
			t.ID = uuid.NewString()
			t.ProductRevisionID = rid
			t.TranslationStatus = "draft"
			t.CreatedAt = now
			t.UpdatedAt = now
			t.CreatedBy = s.Actor
			t.UpdatedBy = s.Actor
			if e = tx.Create(&t).Error; e != nil {
				return e
			}
		}
		if e = cloneMediaLinks(tx, "product_revision_id", old, rid, s.Actor, now); e != nil {
			return e
		}
		if e = cloneSections(tx, "product_revision_id", old, rid, s.Actor, now); e != nil {
			return e
		}
		if e = tx.Model(&p).Updates(map[string]interface{}{"updated_at": now, "updated_by": s.Actor}).Error; e != nil {
			return e
		}
		return s.audit(tx, "product_revision_cloned", "product_revisions", rid, now, map[string]interface{}{"source_id": old})
	})
	return rid, e
}
func editable(v RevisionView, token string) error {
	if v.RevisionStatus != "draft" {
		return conflict("此版本已冻结或弃用，不能修改；请创建新版本")
	}
	if token == "" || token != v.Token {
		return conflict("内容已变化，请刷新后重试，避免覆盖他人的修改")
	}
	return nil
}
func viewContent(v RevisionView) dto.RevisionContent {
	return dto.RevisionContent{SourceLanguage: v.SourceLanguage, CategoryCode: v.CategoryCode, OriginCountryCode: v.OriginCountryCode, PackageQuantity: v.PackageQuantity, PackageUnit: v.PackageUnit, PackageTypeCode: v.PackageTypeCode, ShelfLifeDays: v.ShelfLifeDays, ProcessSteps: v.ProcessSteps, InternalNote: v.InternalNote}
}
func viewTranslation(v TranslationView) dto.TranslationRequest {
	var d dto.TranslationRequest
	_ = json.Unmarshal([]byte(encode(v)), &d)
	return d
}
func (s *Products) UpdateRevision(pid, rid string, req dto.UpdateRevisionRequest) error {
	if e := validateContent(&req.Content); e != nil {
		return e
	}
	return s.write(pid, func(tx *gorm.DB, p models.Product, now string) error {
		v, e := s.revision(tx, pid, rid)
		if e != nil {
			return e
		}
		if e = editable(v, req.ExpectedToken); e != nil {
			return e
		}
		if v.SourceLanguage != req.Content.SourceLanguage {
			var n int64
			if e = tx.Table("custom_sections").Where("product_revision_id=?", rid).Count(&n).Error; e != nil {
				return e
			}
			if n > 0 {
				return invalid("已有模块时不能更换源语言，请在新增模块前选择源语言")
			}
		}
		hasSource := false
		for _, t := range v.Translations {
			d := viewTranslation(t)
			if e = validateTranslation(&d, req.Content); e != nil {
				return e
			}
			hasSource = hasSource || d.LanguageCode == req.Content.SourceLanguage
		}
		if !hasSource {
			return invalid("请先添加所选源语言的翻译")
		}
		m := contentMap(req.Content)
		m["updated_at"] = now
		m["updated_by"] = s.Actor
		if e = tx.Model(&models.Revision{}).Where("id=?", rid).Updates(m).Error; e != nil {
			return e
		}
		return s.audit(tx, "product_revision_updated", "product_revisions", rid, now, map[string]interface{}{"changed_fields": []string{"template_content"}})
	})
}
func (s *Products) Translate(pid, rid string, req dto.UpdateTranslationRequest) error {
	return s.write(pid, func(tx *gorm.DB, p models.Product, now string) error {
		v, e := s.revision(tx, pid, rid)
		if e != nil {
			return e
		}
		if e = editable(v, req.ExpectedToken); e != nil {
			return e
		}
		if e = validateTranslation(&req.Translation, viewContent(v)); e != nil {
			return e
		}
		m := translationMap(req.Translation)
		m["updated_at"] = now
		m["updated_by"] = s.Actor
		var old models.Translation
		e = tx.Where("product_revision_id=? AND language_code=?", rid, req.Translation.LanguageCode).Take(&old).Error
		if errors.Is(e, gorm.ErrRecordNotFound) {
			metadata(m, s.Actor, now)
			m["product_revision_id"] = rid
			e = tx.Table("product_revision_translations").Create(m).Error
		} else if e == nil {
			e = tx.Model(&old).Updates(m).Error
		}
		if e != nil {
			return e
		}
		if e = tx.Model(&models.Revision{}).Where("id=?", rid).Updates(map[string]interface{}{"updated_at": now, "updated_by": s.Actor}).Error; e != nil {
			return e
		}
		return s.audit(tx, "product_translation_updated", "product_revisions", rid, now, map[string]interface{}{"changed_fields": []string{req.Translation.LanguageCode}})
	})
}
func (s *Products) Seal(pid, rid string, req dto.TokenRequest) error {
	return s.write(pid, func(tx *gorm.DB, p models.Product, now string) error {
		v, e := s.revision(tx, pid, rid)
		if e != nil {
			return e
		}
		if e = editable(v, req.ExpectedToken); e != nil {
			return e
		}
		if e = unmanaged(tx, rid); e != nil {
			return e
		}
		c := viewContent(v)
		if e = validateContent(&c); e != nil {
			return e
		}
		approved := false
		translations := []dto.TranslationRequest{}
		for _, t := range v.Translations {
			d := viewTranslation(t)
			if e = validateTranslation(&d, c); e != nil {
				return e
			}
			approved = approved || (d.LanguageCode == c.SourceLanguage && d.TranslationStatus == "approved")
			translations = append(translations, d)
		}
		if !approved {
			return invalid("封版前请确认源语言翻译，其他语言可以留待新版本补充")
		}
		sectionRows, e := loadSections(tx, "product_revision_id", rid)
		if e != nil {
			return e
		}
		sectionContent := []dto.SectionContent{}
		for _, v := range sectionRows {
			sectionContent = append(sectionContent, sectionDTO(v))
		}
		media, me := aggregateMedia(tx, rid, "")
		if me != nil {
			return me
		}
		hash := digest(struct {
			Schema       string
			Content      dto.RevisionContent
			Translations []dto.TranslationRequest
			Sections     []dto.SectionContent
			Media        []map[string]interface{}
		}{"product-template-v3", c, translations, sectionContent, media})
		if e = tx.Model(&models.Revision{}).Where("id=?", rid).Updates(map[string]interface{}{"revision_status": "sealed", "sealed_at": now, "sealed_by": s.Actor, "content_hash": hash, "updated_at": now, "updated_by": s.Actor}).Error; e != nil {
			return e
		}
		return s.audit(tx, "product_revision_sealed", "product_revisions", rid, now, map[string]interface{}{"after_hash": hash})
	})
}
func (s *Products) SetDefault(pid string, req dto.DefaultRequest) error {
	return s.write(pid, func(tx *gorm.DB, p models.Product, now string) error {
		if encode(p.CurrentRevisionID) != encode(req.ExpectedCurrentID) {
			return conflict("当前默认版本已变化，请刷新后重试")
		}
		v, e := s.revision(tx, pid, req.RevisionID)
		if e != nil {
			return invalid("所选版本不存在或不属于此产品")
		}
		if v.RevisionStatus != "sealed" {
			return invalid("只有已封版的版本才能设为默认")
		}
		if e = tx.Model(&p).Updates(map[string]interface{}{"current_revision_id": v.ID, "updated_at": now, "updated_by": s.Actor}).Error; e != nil {
			return e
		}
		return s.audit(tx, "product_default_revision_changed", "products", pid, now, map[string]interface{}{"source_id": v.ID})
	})
}
func (s *Products) UpdateProduct(pid string, req dto.UpdateProductRequest) error {
	if req.LifecycleStatus != "active" && req.LifecycleStatus != "disabled" {
		return invalid("这里只能启用或停用；归档请使用归档操作")
	}
	return s.write(pid, func(tx *gorm.DB, p models.Product, now string) error {
		var locked int64
		if e := tx.Table("batches").Where("product_id=? AND workflow_status='pending_review'", pid).Count(&locked).Error; e != nil {
			return e
		}
		if locked > 0 {
			return conflict("产品存在待审核或待发布批次，不能改变启用/归档状态；默认版本选择不影响已冻结候选")
		}

		if e := tx.Model(&p).Updates(map[string]interface{}{"lifecycle_status": req.LifecycleStatus, "updated_at": now, "updated_by": s.Actor}).Error; e != nil {
			return e
		}
		return s.audit(tx, "product_updated", "products", pid, now, map[string]interface{}{"changed_fields": []string{"lifecycle_status"}})
	})
}
func (s *Products) Archive(pid string) error {
	return s.write(pid, func(tx *gorm.DB, p models.Product, now string) error {
		var locked int64
		if e := tx.Table("batches").Where("product_id=? AND workflow_status='pending_review'", pid).Count(&locked).Error; e != nil {
			return e
		}
		if locked > 0 {
			return conflict("产品存在待审核或待发布批次，不能改变启用/归档状态；默认版本选择不影响已冻结候选")
		}

		if e := tx.Model(&p).Updates(map[string]interface{}{"lifecycle_status": "archived", "archived_at": now, "updated_at": now, "updated_by": s.Actor}).Error; e != nil {
			return e
		}
		return s.audit(tx, "archived", "products", pid, now, map[string]interface{}{})
	})
}
