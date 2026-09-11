package service

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"github.com/google/uuid"
	"go-admin/app/passport/models"
	"go-admin/app/passport/service/dto"
	"gorm.io/gorm"
	"sort"
	"strings"
)

const reviewSchema = "review-v2"
const reviewBuilder = "internal-review-v2"

type ReviewIssue struct {
	Code    string `json:"code"`
	Field   string `json:"field"`
	Message string `json:"message"`
}
type Readiness struct {
	Ready       bool          `json:"ready"`
	Errors      []ReviewIssue `json:"errors"`
	EditVersion int64         `json:"edit_version"`
}
type ReadinessError struct{ Result Readiness }

func (e *ReadinessError) Error() string { return "提交审核前请修正以下问题" }

type ReviewBatch struct {
	ID             string           `json:"id"`
	BatchCode      string           `json:"batch_code"`
	ProductID      string           `json:"product_id"`
	BaseRevisionID string           `json:"base_product_revision_id"`
	RecordType     string           `json:"record_type"`
	Content        dto.BatchContent `json:"content"`
}
type ReviewBase struct {
	ID             string                   `json:"id"`
	RevisionNumber int64                    `json:"revision_number"`
	ContentHash    *string                  `json:"content_hash"`
	Content        dto.RevisionContent      `json:"content"`
	Translations   []dto.TranslationRequest `json:"translations"`
}
type ReviewCandidate struct {
	Assets                 []ReviewAsset                  `json:"assets,omitempty"`
	Schema                 string                         `json:"schema"`
	Batch                  ReviewBatch                    `json:"batch"`
	ProductCode            string                         `json:"product_code"`
	Base                   ReviewBase                     `json:"base"`
	Effective              []EffectiveField               `json:"effective"`
	Overrides              []models.BatchOverride         `json:"overrides"`
	OverrideTranslations   []models.OverrideTranslation   `json:"override_translations"`
	Inspections            []models.InspectionItem        `json:"inspections"`
	InspectionTranslations []models.InspectionTranslation `json:"inspection_translations"`
	BaseSections           []SectionView                  `json:"base_sections"`
	BatchSections          []SectionView                  `json:"batch_sections"`
	EffectiveSections      []EffectiveSection             `json:"effective_sections"`
	HiddenSections         []EffectiveSection             `json:"hidden_sections"`
}
type ReviewView struct {
	models.ReviewRecord
	Candidate *ReviewCandidate `json:"candidate,omitempty"`
	Submitter string           `json:"submitter"`
	Reviewer  string           `json:"reviewer"`
}
type ReviewDetail struct {
	State       string                   `json:"state"`
	Current     *ReviewView              `json:"current"`
	History     []ReviewView             `json:"history"`
	Audit       []map[string]interface{} `json:"audit"`
	PreviewKind string                   `json:"preview_kind"`
}
type ReviewQueueRow struct {
	ID            string `json:"id"`
	BatchCode     string `json:"batch_code"`
	ProductCode   string `json:"product_code"`
	BaseNumber    int64  `json:"base_number"`
	SubmittedBy   int64  `json:"submitted_by"`
	Submitter     string `json:"submitter"`
	SubmittedAt   string `json:"submitted_at"`
	Decision      string `json:"decision"`
	CandidateHash string `json:"candidate_hash"`
}
type Reviews struct{ Batches }

func rawHash(raw string) string { h := sha256.Sum256([]byte(raw)); return hex.EncodeToString(h[:]) }
func (s *Reviews) readiness(tx *gorm.DB, id string) (Readiness, ReviewCandidate, error) {
	result := Readiness{Errors: []ReviewIssue{}}
	candidate := ReviewCandidate{Schema: reviewSchema}
	add := func(code, field string, e error) {
		result.Errors = append(result.Errors, ReviewIssue{code, field, e.Error()})
	}
	b, e := s.batch(tx, id)
	if e != nil {
		return result, candidate, e
	}
	result.EditVersion = b.EditVersion
	if b.WorkflowStatus != "draft" || b.ActivePublishRecordID != nil {
		add("not_draft", "workflow_status", fmt.Errorf("只允许提交未锁定草稿"))
	}
	if _, e := validateCode(b.BatchCode); e != nil {
		add("invalid_batch_code", "batch_code", e)
	}
	content := dto.BatchContent{ProductionDate: b.ProductionDate, ExpiryDate: b.ExpiryDate, QualityStatus: b.QualityStatus, InternalNote: b.InternalNote}
	if b.ProductionDate == nil {
		add("missing_production_date", "production_date", fmt.Errorf("请填写生产日期"))
	}
	if b.ExpiryDate == nil {
		add("missing_expiry_date", "expiry_date", fmt.Errorf("请填写有效期"))
	}
	if e := validateBatchContent(&content); e != nil {
		add("invalid_batch_dates", "dates", e)
	}
	var p models.Product
	if e = tx.Where("id=?", b.ProductID).Take(&p).Error; e != nil {
		return result, candidate, e
	}
	if p.LifecycleStatus != "active" {
		add("inactive_product", "product", fmt.Errorf("产品必须处于启用状态"))
	}
	var base models.Revision
	if e = tx.Where("id=? AND product_id=?", b.BaseProductRevisionID, b.ProductID).Take(&base).Error; e != nil {
		add("missing_base_revision", "base", fmt.Errorf("基础版本不存在或归属不正确"))
		return result, candidate, nil
	}
	if base.RevisionStatus != "sealed" {
		add("unsealed_base_revision", "base", fmt.Errorf("基础模板尚未封版"))
	}
	v, e := s.loadBatch(tx, id, base.SourceLanguage)
	if e != nil {
		add("invalid_effective_content", "effective", fmt.Errorf("有效内容无法解析：%s", s.batchFail(e).Error()))
		return result, candidate, nil
	}
	bc := viewContent(v.Base)
	if e := validateContent(&bc); e != nil {
		add("invalid_base_content", "base", e)
	}
	candidate.Batch = ReviewBatch{ID: b.ID, BatchCode: b.BatchCode, ProductID: b.ProductID, BaseRevisionID: b.BaseProductRevisionID, RecordType: b.RecordType, Content: content}
	candidate.ProductCode = p.ProductCode
	candidate.Base = ReviewBase{ID: base.ID, RevisionNumber: base.RevisionNumber, ContentHash: base.ContentHash, Content: bc, Translations: []dto.TranslationRequest{}}
	sourceOK := false
	for _, tr := range v.Base.Translations {
		d := viewTranslation(tr)
		if e := validateTranslation(&d, bc); e != nil {
			add("invalid_translation", "base.translations."+d.LanguageCode, e)
		}
		if d.LanguageCode == bc.SourceLanguage && d.TranslationStatus == "approved" {
			sourceOK = true
		}
		candidate.Base.Translations = append(candidate.Base.Translations, d)
	}
	if !sourceOK {
		add("missing_source_translation", "base.translations", fmt.Errorf("请确认源语言产品文字，无需强制六语言齐全"))
	}
	for _, o := range v.Overrides {
		d := dto.OverrideInput{FieldKey: o.FieldKey, Operation: o.Operation, ValueText: o.ValueText, ValueInteger: o.ValueInteger}
		if o.ValueJson != nil {
			if e := json.Unmarshal([]byte(*o.ValueJson), &d.Process); e != nil {
				add("invalid_override", o.FieldKey, e)
			}
		}
		if e := validateOverride(&d); e != nil {
			add("invalid_override", o.FieldKey, e)
		}
	}
	for _, i := range v.Inspections {
		var d dto.InspectionInput
		if e := json.Unmarshal([]byte(encode(i)), &d); e != nil {
			return result, candidate, e
		}
		if e := validateInspection(&d); e != nil {
			add("invalid_inspection", i.ItemCode, e)
		}
	}
	candidate.BaseSections, e = loadSections(tx, "product_revision_id", base.ID)
	if e != nil {
		return result, candidate, e
	}
	candidate.BatchSections, e = loadSections(tx, "batch_id", b.ID)
	if e != nil {
		return result, candidate, e
	}
	for _, rows := range [][]SectionView{candidate.BaseSections, candidate.BatchSections} {
		for _, section := range rows {
			if section.SourceLanguage != base.SourceLanguage {
				add("invalid_custom_section", section.SectionKey, fmt.Errorf("模块源语言不一致"))
			}
			if e := validateSection(sectionDTO(section), base.SourceLanguage); e != nil {
				add("invalid_custom_section", section.SectionKey, e)
			}
			if section.IsPublic && section.IsVisible && section.Operation != "hide" && section.Operation != "inherit" {
				approved := false
				for _, tr := range section.Translations {
					approved = approved || (tr.LanguageCode == base.SourceLanguage && tr.TranslationStatus == "approved")
				}
				if section.Status != "ready" || !approved {
					add("unready_public_section", section.SectionKey, fmt.Errorf("公开意图模块须就绪并确认源语言文字"))
				}
			}
		}
	}
	var certCount int64
	if e = tx.Table("certification_links").Where("product_revision_id=? OR batch_id=?", base.ID, b.ID).Count(&certCount).Error; e != nil {
		return result, candidate, e
	}
	if certCount > 0 {
		add("unsupported_certification_review", "certifications", fmt.Errorf("认证关联尚未开放审核"))
	}
	candidate.Effective = v.Effective
	candidate.Overrides = v.Overrides
	candidate.Inspections = v.Inspections
	candidate.EffectiveSections = v.Sections
	candidate.HiddenSections = v.HiddenSections
	candidate.OverrideTranslations = []models.OverrideTranslation{}
	candidate.InspectionTranslations = []models.InspectionTranslation{}
	if e = tx.Where("batch_override_id IN (SELECT id FROM batch_overrides WHERE batch_id=?)", b.ID).Order("batch_override_id,language_code").Find(&candidate.OverrideTranslations).Error; e != nil {
		return result, candidate, e
	}
	if e = tx.Where("inspection_item_id IN (SELECT id FROM inspection_items WHERE batch_id=?)", b.ID).Order("inspection_item_id,language_code").Find(&candidate.InspectionTranslations).Error; e != nil {
		return result, candidate, e
	}

	for _, tr := range candidate.OverrideTranslations {
		if !languages[tr.LanguageCode] || (tr.TranslationStatus != "draft" && tr.TranslationStatus != "approved") {
			add("invalid_override_translation", tr.BatchOverrideID, invalid("翻译语言或状态不正确"))
		}
		if tr.TranslatedValue != nil && !safeSectionText(*tr.TranslatedValue, 4000, false) {
			add("invalid_override_translation", tr.BatchOverrideID, invalid("翻译文字不合法"))
		}
		if tr.TranslatedProcess != nil {
			var labels map[string]string
			if json.Unmarshal([]byte(*tr.TranslatedProcess), &labels) != nil {
				add("invalid_override_translation", tr.BatchOverrideID, invalid("工艺翻译结构不正确"))
			} else {
				allowed := map[string]bool{}
				for _, o := range candidate.Overrides {
					if o.ID == tr.BatchOverrideID && o.ValueJson != nil {
						var steps []struct {
							StepKey string `json:"step_key"`
						}
						if json.Unmarshal([]byte(*o.ValueJson), &steps) == nil {
							for _, step := range steps {
								allowed[step.StepKey] = true
							}
						}
					}
				}

				for key, value := range labels {
					if !allowed[key] || !safeSectionText(key, 64, true) || !safeSectionText(value, 500, true) {
						add("invalid_override_translation", tr.BatchOverrideID, invalid("工艺翻译不合法"))
					}
				}
			}
		}
	}
	for _, tr := range candidate.InspectionTranslations {
		valid := languages[tr.LanguageCode] && (tr.TranslationStatus == "draft" || tr.TranslationStatus == "approved") && safeSectionText(tr.DisplayName, 200, true)
		for _, value := range []*string{tr.Specification, tr.TestMethod, tr.ResultDisplayText} {
			if value != nil {
				valid = valid && safeSectionText(*value, 4000, false)
			}
		}
		if !valid {
			add("invalid_inspection_translation", tr.InspectionItemID, invalid("检测翻译不合法"))
		}
	}
	if e := freezeReviewAssets(tx, &candidate); e != nil {
		add("invalid_review_assets", "assets", e)
	}
	if len(encode(candidate)) > 4*1024*1024 {
		add("candidate_too_large", "candidate", fmt.Errorf("审核输入不得超过 4 MiB"))
	}
	result.Ready = len(result.Errors) == 0
	return result, candidate, nil
}
func (s *Reviews) Readiness(id string) (Readiness, error) {
	var r Readiness
	e := s.Orm.Transaction(func(tx *gorm.DB) error { var e error; r, _, e = s.readiness(tx, id); return e })
	return r, s.batchFail(e)
}
func (s *Reviews) recordView(tx *gorm.DB, r models.ReviewRecord) (ReviewView, error) {
	v := ReviewView{ReviewRecord: r, Candidate: &ReviewCandidate{}}
	if rawHash(r.CandidateInput) != r.CandidateHash {
		return v, conflict("审核输入摘要不匹配")
	}
	if e := json.Unmarshal([]byte(r.CandidateInput), &v.Candidate); e != nil {
		return v, e
	}
	if e := tx.Table("sys_user").Select("username").Where("user_id=?", r.SubmittedBy).Scan(&v.Submitter).Error; e != nil {
		return v, e
	}
	if r.ReviewedBy != nil {
		if e := tx.Table("sys_user").Select("username").Where("user_id=?", *r.ReviewedBy).Scan(&v.Reviewer).Error; e != nil {
			return v, e
		}
	}
	return v, nil
}
func reviewState(b models.Batch, current *models.ReviewRecord) string {
	if b.ActivePublishRecordID != nil {
		return "publishing"
	}
	if b.WorkflowStatus == "pending_review" && current != nil && current.Decision == "approved" {
		return "ready_for_publish"
	}
	return b.WorkflowStatus
}
func (s *Reviews) detail(tx *gorm.DB, id string) (ReviewDetail, error) {
	d := ReviewDetail{History: []ReviewView{}, Audit: []map[string]interface{}{}, PreviewKind: "INTERNAL REVIEW PREVIEW — NOT PUBLISHED"}
	b, e := s.batch(tx, id)
	if e != nil {
		return d, e
	}
	d.State = b.WorkflowStatus
	rows := []models.ReviewRecord{}
	if e = tx.Where("batch_id=?", id).Order("attempt_number DESC").Find(&rows).Error; e != nil {
		return d, e
	}
	for _, r := range rows {
		v, e := s.recordView(tx, r)
		if e != nil {
			return d, e
		}
		summary := v
		summary.Candidate = nil
		d.History = append(d.History, summary)
		if b.CurrentReviewRecordID != nil && r.ID == *b.CurrentReviewRecordID {
			vv := v
			d.Current = &vv
			d.State = reviewState(b, &r)
		}
	}
	e = tx.Table("passport_audit_events").Where("batch_id=?", id).Order("created_at DESC,id DESC").Limit(100).Find(&d.Audit).Error
	return d, e
}
func (s *Reviews) Detail(id string) (ReviewDetail, error) {
	var d ReviewDetail
	e := s.Orm.Transaction(func(tx *gorm.DB) error { var e error; d, e = s.detail(tx, id); return e })
	return d, s.batchFail(e)
}
func (s *Reviews) Queue(q dto.ReviewQuery) ([]ReviewQueueRow, int64, error) {
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
	if q.State == "" {
		q.State = "pending"
	}
	if q.State != "pending" && q.State != "approved" {
		return nil, 0, invalid("队列状态不正确")
	}
	db := s.batchScope(s.Orm).Joins("JOIN review_records rr ON rr.id=batches.current_review_record_id AND rr.batch_id=batches.id").Joins("JOIN products p ON p.id=batches.product_id").Joins("JOIN product_revisions pr ON pr.id=batches.base_product_revision_id").Joins("JOIN sys_user u ON u.user_id=rr.submitted_by").Where("batches.workflow_status='pending_review' AND rr.decision=?", q.State)
	if q.Search != "" {
		db = db.Where("batches.batch_code LIKE ? OR p.product_code LIKE ?", "%"+q.Search+"%", "%"+q.Search+"%")
	}
	var n int64
	if e := db.Count(&n).Error; e != nil {
		return nil, 0, s.batchFail(e)
	}
	rows := []ReviewQueueRow{}
	e := db.Select("batches.id,batches.batch_code,p.product_code,pr.revision_number AS base_number,rr.submitted_by,u.username AS submitter,rr.submitted_at,rr.decision,rr.candidate_hash").Order("rr.submitted_at,batches.id").Offset((q.PageIndex - 1) * q.PageSize).Limit(q.PageSize).Scan(&rows).Error
	return rows, n, s.batchFail(e)
}
func (s *Reviews) reviewTx(id string, fn func(*gorm.DB, models.Batch, string) error) error {
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
		if b.ActivePublishRecordID != nil {
			return conflict("批次存在未决发布操作")
		}
		return fn(tx, b, stamp())
	})
	var ready *ReadinessError
	if errors.As(e, &ready) {
		return e
	}
	return s.batchFail(e)
}
func (s *Reviews) reviewAudit(tx *gorm.DB, bid, event, reviewID string, meta map[string]interface{}) error {
	meta["review_id"] = reviewID
	return s.batchAudit(tx, bid, event, "batches", bid, nil, meta)
}
func (s *Reviews) contributors(tx *gorm.DB, b models.Batch) ([]int64, error) {
	ids := []int64{b.CreatedBy, b.UpdatedBy, int64(s.Actor)}
	var past []int64
	if e := tx.Table("passport_audit_events").Where("batch_id=? AND event_type NOT LIKE 'review_%'", b.ID).Distinct("actor_user_id").Pluck("actor_user_id", &past).Error; e != nil {
		return nil, e
	}
	ids = append(ids, past...)
	set := map[int64]bool{}
	out := []int64{}
	for _, id := range ids {
		if !set[id] {
			set[id] = true
			out = append(out, id)
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i] < out[j] })
	return out, nil
}
func (s *Reviews) Submit(id string, req dto.SubmitReview) (string, error) {
	var rid string
	e := s.reviewTx(id, func(tx *gorm.DB, b models.Batch, now string) error {
		if b.WorkflowStatus != "draft" {
			return conflict("此批次已提交审核或已锁定")
		}
		if b.EditVersion != req.ExpectedEditVersion {
			return conflict("内容已改变，请刷新后重新检查")
		}
		ready, candidate, e := s.readiness(tx, id)
		if e != nil {
			return e
		}
		if !ready.Ready {
			return &ReadinessError{ready}
		}
		actors, e := s.contributors(tx, b)
		if e != nil {
			return e
		}
		var number int64
		if e = tx.Model(&models.ReviewRecord{}).Where("batch_id=?", id).Select("COALESCE(MAX(attempt_number),0)").Scan(&number).Error; e != nil {
			return e
		}
		raw := encode(candidate)
		hash := rawHash(raw)
		rid = uuid.NewString()
		record := models.ReviewRecord{ID: rid, BatchID: id, AttemptNumber: number + 1, Decision: "pending", CandidateInput: raw, CandidateHash: hash, PreviewHash: hash, SourceEditVersion: b.EditVersion, SchemaVersion: reviewSchema, BuilderVersion: reviewBuilder, SubmittedBy: int64(s.Actor), SubmittedAt: now, Contributors: encode(actors)}
		if e = tx.Create(&record).Error; e != nil {
			return e
		}
		m := map[string]interface{}{"workflow_status": "pending_review", "current_review_record_id": rid, "submitted_edit_version": b.EditVersion, "submitted_content_hash": hash, "submitted_input": raw, "submitted_schema_version": reviewSchema, "submitted_builder_version": reviewBuilder, "submitted_preview_hash": hash, "submitted_at": now, "submitted_by": s.Actor, "reviewed_at": nil, "reviewed_by": nil, "rejection_reason": nil, "updated_at": now, "updated_by": s.Actor}
		if e = tx.Model(&models.Batch{}).Where("id=?", id).Updates(m).Error; e != nil {
			return e
		}
		return s.reviewAudit(tx, id, "review_submitted", rid, map[string]interface{}{"candidate_hash": hash, "attempt_number": number + 1})
	})
	return rid, e
}
func (s *Reviews) Decide(id, decision string, req dto.DecideReview) error {
	if decision != "approved" && decision != "rejected" {
		return invalid("审核决定不正确")
	}
	if !safeSectionText(req.Comment, 2000, false) || !safeSectionText(req.RejectionReason, 2000, decision == "rejected") {
		return invalid("审核意见须为纯文本，驳回理由必填且不超过 2000 字符")
	}
	if decision == "approved" && req.RejectionReason != "" {
		return invalid("批准不能携带驳回理由")
	}
	e := s.reviewTx(id, func(tx *gorm.DB, b models.Batch, now string) error {
		if b.WorkflowStatus != "pending_review" || b.CurrentReviewRecordID == nil || *b.CurrentReviewRecordID != req.ReviewID {
			return conflict("当前审核记录已变化")
		}
		var r models.ReviewRecord
		if e := tx.Where("id=? AND batch_id=?", req.ReviewID, id).Take(&r).Error; e != nil {
			return e
		}
		if r.Decision != "pending" {
			return conflict("该审核已有决定")
		}
		if req.CandidateHash != r.CandidateHash || rawHash(r.CandidateInput) != r.CandidateHash || b.SubmittedContentHash == nil || *b.SubmittedContentHash != r.CandidateHash || b.SubmittedInput == nil || *b.SubmittedInput != r.CandidateInput || b.EditVersion != r.SourceEditVersion || b.SubmittedEditVersion == nil || *b.SubmittedEditVersion != r.SourceEditVersion || b.SubmittedPreviewHash == nil || *b.SubmittedPreviewHash != r.PreviewHash || r.PreviewHash != r.CandidateHash || b.SubmittedSchemaVersion == nil || *b.SubmittedSchemaVersion != r.SchemaVersion || b.SubmittedBuilderVersion == nil || *b.SubmittedBuilderVersion != r.BuilderVersion || b.SubmittedBy == nil || *b.SubmittedBy != r.SubmittedBy || b.SubmittedAt == nil || *b.SubmittedAt != r.SubmittedAt {
			return conflict("审核输入或版本不一致，请撤回检查")
		}
		var contributors []int64
		if e := json.Unmarshal([]byte(r.Contributors), &contributors); e != nil {
			return e
		}
		for _, actor := range contributors {
			if actor == int64(s.Actor) {
				return &BusinessError{403, "不得审核自己创建、编辑或提交的批次，请由另一位审核人处理"}
			}
		}
		m := map[string]interface{}{"decision": decision, "reviewed_by": s.Actor, "reviewed_at": now, "comment": strings.TrimSpace(req.Comment)}
		bm := map[string]interface{}{"reviewed_by": s.Actor, "reviewed_at": now, "updated_at": now, "updated_by": b.UpdatedBy}
		event := "review_approved"
		if decision == "rejected" {
			m["rejection_reason"] = strings.TrimSpace(req.RejectionReason)
			bm["rejection_reason"] = strings.TrimSpace(req.RejectionReason)
			bm["workflow_status"] = "draft"
			event = "review_rejected"
		}
		result := tx.Model(&models.ReviewRecord{}).Where("id=? AND decision='pending'", r.ID).Updates(m)
		if result.Error != nil {
			return result.Error
		}
		if result.RowsAffected != 1 {
			return conflict("已有其他审核人完成处理")
		}
		if e := tx.Model(&models.Batch{}).Where("id=?", id).Updates(bm).Error; e != nil {
			return e
		}
		return s.reviewAudit(tx, id, event, r.ID, map[string]interface{}{"candidate_hash": r.CandidateHash, "attempt_number": r.AttemptNumber, "comment": req.Comment, "rejection_reason": req.RejectionReason})
	})
	var b *BusinessError
	if errors.As(e, &b) && b.Code == 409 {
		// Conflict audit is a separate failed-attempt event; no business transition was committed.
		ae := s.Orm.Transaction(func(tx *gorm.DB) error {
			if _, err := s.batch(tx, id); err != nil {
				return err
			}
			return s.reviewAudit(tx, id, "review_conflict", req.ReviewID, map[string]interface{}{"reason": "stale_review", "candidate_hash": req.CandidateHash})
		})
		if ae != nil {
			return s.batchFail(ae)
		}
	}
	return e
}
func (s *Reviews) Return(id string, req dto.ReturnReview) error {
	if !safeSectionText(req.Reason, 2000, true) {
		return invalid("改稿理由必填，须为 2000 字符以内纯文本")
	}
	return s.reviewTx(id, func(tx *gorm.DB, b models.Batch, now string) error {
		if b.WorkflowStatus != "pending_review" || b.CurrentReviewRecordID == nil || *b.CurrentReviewRecordID != req.ReviewID {
			return conflict("当前状态不能退回改稿")
		}
		var r models.ReviewRecord
		if e := tx.Where("id=? AND batch_id=?", req.ReviewID, id).Take(&r).Error; e != nil {
			return e
		}
		if r.Decision != "approved" {
			return conflict("尚未批准的审核须由审核人驳回")
		}
		m := map[string]interface{}{"workflow_status": "draft", "current_review_record_id": nil, "submitted_edit_version": nil, "submitted_content_hash": nil, "submitted_input": nil, "submitted_schema_version": nil, "submitted_builder_version": nil, "submitted_preview_hash": nil, "submitted_at": nil, "submitted_by": nil, "reviewed_at": nil, "reviewed_by": nil, "rejection_reason": nil, "updated_at": now, "updated_by": s.Actor}
		if e := tx.Model(&models.Batch{}).Where("id=?", id).Updates(m).Error; e != nil {
			return e
		}
		return s.reviewAudit(tx, id, "review_returned_to_draft", r.ID, map[string]interface{}{"reason": req.Reason, "invalidated_approval_hash": r.CandidateHash})
	})
}
func (s *Reviews) ArchiveBatch(id string) error {
	return s.reviewTx(id, func(tx *gorm.DB, b models.Batch, now string) error {
		if !s.Admin {
			return &BusinessError{403, "只有 Super Admin 可以归档"}
		}
		if b.WorkflowStatus != "draft" && b.WorkflowStatus != "published" {
			return conflict("仅允许归档未锁定草稿或已发布批次")
		}
		if e := tx.Model(&models.Batch{}).Where("id=?", id).Updates(map[string]interface{}{"workflow_status": "archived", "archived_at": now, "archived_by": s.Actor, "updated_at": now, "updated_by": s.Actor}).Error; e != nil {
			return e
		}
		return s.batchAudit(tx, id, "archived", "batches", id, nil, map[string]interface{}{"scope": "working_batch"})
	})
}
