package service

import (
	"encoding/json"
	"errors"
	"github.com/google/uuid"
	"go-admin/app/passport/models"
	"go-admin/app/passport/publishing"
	"gorm.io/gorm"
	"os"
	"path"
	"reflect"
	"strings"
	"unicode"
	"unicode/utf8"
)

type RollbackRequest struct {
	TargetRevisionID          string  `json:"target_revision_id"`
	ExpectedCurrentRevisionID *string `json:"expected_current_revision_id"`
	IdempotencyKey            string  `json:"idempotency_key"`
	RollbackReason            string  `json:"rollback_reason"`
}
type CurrentHealth struct {
	FileVersion          *int64  `json:"file_version"`
	FilesystemRevisionID *string `json:"filesystem_revision_id"`
	State                string  `json:"state"`
	Classification       string  `json:"classification"`
	DBCurrentID          *string `json:"db_current_id"`
	DBVersion            *int64  `json:"db_version"`
	FileHash             string  `json:"file_hash"`
	ManifestVersion      *int64  `json:"manifest_version"`
	ActiveRecordID       *string `json:"active_record_id"`
}

func historyUUID(s string) bool {
	v, e := uuid.Parse(s)
	return e == nil && v.Version() == 4 && v.String() == s
}
func reasonValid(reason string) bool {
	if strings.TrimSpace(reason) == "" || utf8.RuneCountInString(reason) > 1000 || !utf8.ValidString(reason) || strings.ContainsAny(reason, "<>") {
		return false
	}
	for _, r := range reason {
		if unicode.IsControl(r) && r != '\n' && r != '\t' {
			return false
		}
	}
	return true
}
func openPublicationStore() (*publishing.Store, error) {
	return publishing.OpenStore(os.Getenv("PASSPORT_PUBLISH_ROOT"), os.Getenv("PASSPORT_RELEASE_WORK_ROOT"))
}
func (s *Publishing) revisionEntry(id, rid string) (PublishEntry, error) {
	var r models.PublishRecord
	if e := s.Orm.Where("batch_id=? AND passport_revision_id=? AND publish_status='published'", id, rid).Take(&r).Error; e != nil {
		return PublishEntry{}, s.batchFail(e)
	}
	return s.entry(r.ID)
}
func (s *Publishing) inspectCurrent(store *publishing.Store, b models.Batch) CurrentHealth {
	h := CurrentHealth{State: "consistent", Classification: "consistent", DBCurrentID: b.CurrentPassportRevisionID, ActiveRecordID: b.ActivePublishRecordID}
	bad := func(c string) CurrentHealth { h.State = "reconciliation_required"; h.Classification = c; return h }
	actual, e := currentHash(store, b.BatchCode)
	h.FileHash = actual
	if actual != "" {
		var fileRevision models.PassportRevision
		if s.Orm.Where("batch_id=? AND payload_hash=?", b.ID, actual).Take(&fileRevision).Error == nil {
			h.FileVersion = &fileRevision.VersionNumber
			h.FilesystemRevisionID = &fileRevision.ID
		}
	}
	if e != nil {
		return bad("integrity_failure")
	}
	old := ""
	if b.CurrentPassportRevisionID != nil {
		v, e := s.revisionEntry(b.ID, *b.CurrentPassportRevisionID)
		if e != nil {
			return bad("database_inconsistent")
		}
		h.DBVersion = &v.Revision.VersionNumber
		if _, _, e = s.verifyPrepared(store, v); e != nil {
			return bad("integrity_failure")
		}
		h.ManifestVersion = &v.Revision.VersionNumber
		old = *v.Revision.PayloadHash
	}
	if b.ActivePublishRecordID != nil {
		v, e := s.entry(*b.ActivePublishRecordID)
		if e != nil {
			return bad("database_inconsistent")
		}
		if !same(v.Record.ExpectedCurrentRevisionID, b.CurrentPassportRevisionID) {
			return bad("database_inconsistent")
		}
		if v.Revision.SealedAt != nil {
			if _, _, e = s.verifyPrepared(store, v); e != nil {
				return bad("integrity_failure")
			}
			if actual == *v.Revision.PayloadHash {
				h.ManifestVersion = &v.Revision.VersionNumber
				return bad("file_switched_db_pending")
			}
		}
		if actual != old {
			return bad("unknown_current")
		}
		return bad(v.Record.PublishStatus)
	}
	if actual != old {
		if actual == "" {
			return bad("missing_current")
		}
		var n int64
		if s.Orm.Model(&models.PassportRevision{}).Where("batch_id=? AND published_at IS NOT NULL AND payload_hash=?", b.ID, actual).Count(&n).Error == nil && n == 1 {
			return bad("db_published_current_old")
		}
		return bad("unknown_current")
	}
	var last models.PublishRecord
	if s.Orm.Where("batch_id=?", b.ID).Order("created_at DESC,id DESC").Take(&last).Error == nil && last.PublishStatus == "failed" {
		h.Classification = "failed_old_current_safe"
	}
	return h
}
func (s *Publishing) saveHealth(h CurrentHealth, id string) error {
	return s.Orm.Exec("INSERT INTO publication_health(batch_id,reconciliation_required,classification,checked_at) VALUES(?,?,?,?) ON CONFLICT(batch_id) DO UPDATE SET reconciliation_required=excluded.reconciliation_required,classification=excluded.classification,checked_at=excluded.checked_at", id, h.State != "consistent", h.Classification, stamp()).Error
}
func (s *Publishing) Health(id string) (CurrentHealth, error) {
	b, e := s.batch(s.Orm, id)
	if e != nil {
		return CurrentHealth{}, e
	}
	st, e := openPublicationStore()
	if e != nil {
		return CurrentHealth{}, e
	}
	defer st.Close()
	unlock, e := st.Lock(id)
	if e != nil {
		return CurrentHealth{State: "reconciliation_required", Classification: "operation_running", DBCurrentID: b.CurrentPassportRevisionID, ActiveRecordID: b.ActivePublishRecordID}, nil
	}
	defer unlock()
	b, e = s.batch(s.Orm, id)
	if e != nil {
		return CurrentHealth{}, e
	}
	h := s.inspectCurrent(st, b)
	return h, s.saveHealth(h, id)
}

// Every writer re-proves integrity under the same process-independent lock. Stored health is never trusted as proof.
func (s *Publishing) guardCurrent(st *publishing.Store, tx *gorm.DB, b models.Batch) error {
	local := *s
	local.Orm = tx
	h := local.inspectCurrent(st, b)
	if h.State != "consistent" {
		return conflict("reconciliation_required: " + h.Classification)
	}
	return nil
}
func (s *Publishing) Rollback(id string, q RollbackRequest) (PublishEntry, error) {
	if e := s.authorize(); e != nil {
		return PublishEntry{}, e
	}
	if !reasonValid(q.RollbackReason) || !historyUUID(q.TargetRevisionID) || !historyUUID(q.IdempotencyKey) {
		return PublishEntry{}, &BusinessError{422, "回滚版本、幂等键和纯文本原因必填（最多 1000 字）"}
	}
	st, e := openPublicationStore()
	if e != nil {
		return PublishEntry{}, e
	}
	defer st.Close()
	unlock, e := st.Lock(id)
	if e != nil {
		return PublishEntry{}, conflict("批次操作正在运行")
	}
	defer unlock()
	b, e := s.batch(s.Orm, id)
	if e != nil {
		return PublishEntry{}, e
	}
	var existing models.PublishRecord
	if e = s.Orm.Where("batch_id=? AND idempotency_key=?", id, q.IdempotencyKey).Take(&existing).Error; e == nil {
		v, e := s.entry(existing.ID)
		if e != nil {
			return v, e
		}
		if existing.OperationType != "rollback" || existing.RollbackReason == nil || *existing.RollbackReason != q.RollbackReason || !same(v.Revision.RollbackSourceRevisionID, &q.TargetRevisionID) || !same(existing.ExpectedCurrentRevisionID, q.ExpectedCurrentRevisionID) {
			return v, conflict("幂等键请求内容不一致")
		}
		return v, nil
	} else if !errors.Is(e, gorm.ErrRecordNotFound) {
		return PublishEntry{}, e
	}
	h := s.inspectCurrent(st, b)
	if e = s.saveHealth(h, id); e != nil {
		return PublishEntry{}, e
	}
	if h.State != "consistent" {
		return PublishEntry{}, conflict("reconciliation_required: " + h.Classification)
	}
	if b.WorkflowStatus != "published" || b.ActivePublishRecordID != nil || !same(b.CurrentPassportRevisionID, q.ExpectedCurrentRevisionID) {
		return PublishEntry{}, conflict("仅允许对当前已发布、未锁定批次回滚；请刷新版本")
	}
	target, e := s.revisionEntry(id, q.TargetRevisionID)
	if e != nil {
		return target, e
	}
	if _, _, e = s.verifyPrepared(st, target); e != nil {
		return PublishEntry{}, conflict("历史版本完整性校验失败，禁止回滚")
	}
	var entry PublishEntry
	e = s.Orm.Transaction(func(tx *gorm.DB) error {
		if e := tx.Exec("UPDATE batches SET id=id WHERE id=?", id).Error; e != nil {
			return e
		}
		current, e := s.batch(tx, id)
		if e != nil {
			return e
		}
		if current.WorkflowStatus != "published" || current.ActivePublishRecordID != nil || !same(current.CurrentPassportRevisionID, q.ExpectedCurrentRevisionID) {
			return conflict("当前版本已变化")
		}
		p := target.Revision
		p.ID = uuid.NewString()
		p.CreatedAt = stamp()
		p.CreatedBy = int64(s.Actor)
		p.PublishedBy = int64(s.Actor)
		p.VersionNumber = current.NextVersionNumber
		p.SourceRevisionID = current.CurrentPassportRevisionID
		p.RollbackSourceRevisionID = &q.TargetRevisionID
		p.ReleaseIdentifier = uuid.NewString()
		p.BuilderVersion = publishing.BuilderVersion
		p.Payload = nil
		p.PayloadHash = nil
		p.ContentHash = nil
		p.AssetManifestHash = nil
		p.SnapshotPath = nil
		p.SealedAt = nil
		p.PublishedAt = nil
		r := models.PublishRecord{ID: uuid.NewString(), CreatedAt: p.CreatedAt, CreatedBy: int64(s.Actor), BatchID: id, PassportRevisionID: p.ID, OperationType: "rollback", RollbackReason: &q.RollbackReason, PublishStatus: "pending", IdempotencyKey: q.IdempotencyKey, ReleaseIdentifier: p.ReleaseIdentifier, ExpectedCurrentRevisionID: current.CurrentPassportRevisionID, StartedAt: &p.CreatedAt, UpdatedAt: p.CreatedAt, AttemptCount: 1, StateVersion: 1, SourceReviewRecordID: p.SourceReviewRecordID}
		if e = tx.Create(&p).Error; e != nil {
			return e
		}
		if e = tx.Create(&r).Error; e != nil {
			return e
		}
		if e = tx.Model(&models.Batch{}).Where("id=?", id).Updates(map[string]interface{}{"active_publish_record_id": r.ID, "next_version_number": current.NextVersionNumber + 1}).Error; e != nil {
			return e
		}
		entry = PublishEntry{r, p}
		return s.pubAudit(tx, r, "rollback_requested", "prepare", map[string]interface{}{"rollback_source_revision_id": q.TargetRevisionID})
	})
	if e != nil {
		return entry, s.batchFail(e)
	}
	if e = s.buildRollback(st, &entry, target); e != nil {
		return s.fail(entry, e, false)
	}
	return s.switchAndFinalize(st, entry)
}
func (s *Publishing) buildRollback(st *publishing.Store, v *PublishEntry, target PublishEntry) error {
	if e := s.setState(v.Record, "building", nil); e != nil {
		return e
	}
	if e := s.hit("build"); e != nil {
		return e
	}
	raw, code, e := s.verifyPrepared(st, target)
	if e != nil {
		return e
	}
	if e = s.hit("asset"); e != nil {
		return e
	}
	val, e := publishing.Decode(raw)
	if e != nil {
		return e
	}
	payload := val.(map[string]interface{})
	payload["publication"] = map[string]interface{}{"version_number": v.Revision.VersionNumber, "issued_at": v.Revision.CreatedAt, "kind": "rollback", "source_version_number": target.Revision.VersionNumber}
	bytes, e := publishing.Canonical(payload)
	if e != nil {
		return e
	}
	assets := []map[string]interface{}{}
	for _, a := range payload["assets"].([]interface{}) {
		assets = append(assets, a.(map[string]interface{}))
	}
	var rows []models.PublishedAsset
	if e = s.Orm.Where("passport_revision_id=?", target.Revision.ID).Order("asset_key").Find(&rows).Error; e != nil {
		return e
	}
	for i := range rows {
		rows[i].ID = uuid.NewString()
		rows[i].PassportRevisionID = v.Revision.ID
		rows[i].CreatedAt = v.Revision.CreatedAt
		rows[i].CreatedBy = int64(s.Actor)
	}
	return s.sealBuilt(st, v, publishing.BuildResult{Payload: bytes, PayloadHash: publishing.Hash(bytes), ContentHash: *target.Revision.ContentHash, Assets: assets}, rows, code)
}
func (s *Publishing) ReconcileReason(id, reason string) (result PublishEntry, err error) {
	if e := s.authorize(); e != nil {
		return result, e
	}
	if !reasonValid(reason) {
		return result, &BusinessError{422, "恢复原因必填，纯文本最多 1000 字"}
	}
	st, e := openPublicationStore()
	if e != nil {
		return result, e
	}
	defer st.Close()
	unlock, e := st.Lock(id)
	if e != nil {
		return result, conflict("批次操作正在运行")
	}
	defer unlock()
	b, e := s.batch(s.Orm, id)
	if e != nil {
		return result, e
	}
	if e = s.batchAudit(s.Orm, id, "reconcile_started", "batches", id, nil, map[string]interface{}{"reason": reason}); e != nil {
		return result, e
	}
	defer func() {
		b, e := s.batch(s.Orm, id)
		if e == nil {
			h := s.inspectCurrent(st, b)
			if he := s.saveHealth(h, id); he != nil && err == nil {
				err = he
			}
			if h.State != "consistent" && err == nil {
				err = conflict("reconciliation_required: " + h.Classification)
			}
		}
		event := "reconcile_completed"
		if err != nil {
			event = "reconcile_failed"
		}
		ae := s.batchAudit(s.Orm, id, event, "batches", id, nil, map[string]interface{}{"reason": reason, "publish_record_id": result.Record.ID})
		if ae != nil && err == nil {
			err = ae
		}
	}()
	h := s.inspectCurrent(st, b)
	if h.Classification == "integrity_failure" || h.Classification == "unknown_current" || h.Classification == "database_inconsistent" {
		return result, conflict("无法证明安全，拒绝自动恢复：" + h.Classification)
	}
	if b.ActivePublishRecordID != nil {
		return s.reconcileLocked(st, id)
	}
	if h.State == "consistent" {
		return result, conflict("没有待恢复发布")
	}
	// Only a missing head or a known older successful snapshot can be restored from the verified DB head.
	if h.Classification != "db_published_current_old" && h.Classification != "missing_current" {
		return result, conflict("恢复路径不明确")
	}
	result, e = s.revisionEntry(id, *b.CurrentPassportRevisionID)
	if e != nil {
		return result, e
	}
	raw, code, e := s.verifyPrepared(st, result)
	if e != nil {
		return result, e
	}
	if h.FileHash != "" {
		var old models.PassportRevision
		if e = s.Orm.Where("batch_id=? AND payload_hash=? AND published_at IS NOT NULL AND version_number<?", id, h.FileHash, result.Revision.VersionNumber).Take(&old).Error; e != nil {
			return result, conflict("不能覆盖未知或更新的文件版本")
		}
		ov, e := s.revisionEntry(id, old.ID)
		if e != nil {
			return result, e
		}
		if _, _, e = s.verifyPrepared(st, ov); e != nil {
			return result, conflict("旧文件来源未验证")
		}
	}
	_, e = st.Switch(code, raw)
	return result, e
}

type VersionSummary struct {
	PublishEntry
	VersionType string `json:"version_type"`
	Current     bool   `json:"current"`
}
type AuditItem struct {
	ID                 string      `json:"id"`
	BatchID            *string     `json:"batch_id"`
	PassportRevisionID *string     `json:"passport_revision_id"`
	ActorUserID        int64       `json:"actor_user_id"`
	CreatedAt          string      `json:"created_at"`
	EventType          string      `json:"event_type"`
	EntityType         string      `json:"entity_type"`
	EntityID           string      `json:"entity_id"`
	Summary            string      `json:"summary"`
	Metadata           string      `json:"metadata"`
	BeforeData         *string     `json:"-"`
	AfterData          *string     `json:"-"`
	Category           string      `gorm:"-" json:"category"`
	BeforeHash         string      `gorm:"-" json:"before_hash"`
	AfterHash          string      `gorm:"-" json:"after_hash"`
	Detail             interface{} `gorm:"-" json:"detail"`
}
type VersionHistory struct {
	Versions []VersionSummary      `json:"versions"`
	Attempts []PublishEntry        `json:"attempts"`
	Reviews  []models.ReviewRecord `json:"reviews"`
	Audit    []AuditItem           `json:"audit"`
}

func (s *Publishing) History(id, category string) (VersionHistory, error) {
	out := VersionHistory{Versions: []VersionSummary{}, Attempts: []PublishEntry{}, Reviews: []models.ReviewRecord{}, Audit: []AuditItem{}}
	b, e := s.batch(s.Orm, id)
	if e != nil {
		return out, e
	}
	var records []models.PublishRecord
	if e = s.Orm.Where("batch_id=?", id).Order("created_at DESC,id DESC").Find(&records).Error; e != nil {
		return out, e
	}
	for _, r := range records {
		v, e := s.entry(r.ID)
		if e != nil {
			return out, e
		}
		out.Attempts = append(out.Attempts, v)
		if v.Revision.PublishedAt != nil {
			kind := "normal_publish"
			if r.OperationType == "rollback" {
				kind = "rollback"
			}
			out.Versions = append(out.Versions, VersionSummary{v, kind, same(b.CurrentPassportRevisionID, &v.Revision.ID)})
		}
	}
	if e = s.Orm.Where("batch_id=?", id).Order("attempt_number DESC").Find(&out.Reviews).Error; e != nil {
		return out, e
	}
	var audits []AuditItem
	e = s.Orm.Table("passport_audit_events").Where("batch_id=? OR entity_id=? OR entity_id IN (SELECT id FROM product_revisions WHERE product_id=?) OR entity_id IN (SELECT t.id FROM product_revision_translations t JOIN product_revisions p ON p.id=t.product_revision_id WHERE p.product_id=?)", id, b.ProductID, b.ProductID, b.ProductID).Order("created_at DESC,id DESC").Find(&audits).Error
	if e != nil {
		return out, e
	}
	for _, a := range audits {
		a.Category = "Batch"
		switch {
		case strings.HasPrefix(a.EventType, "reconcile_"):
			a.Category = "SystemRecovery"
		case strings.HasPrefix(a.EventType, "rollback_"):
			a.Category = "Rollback"
		case strings.HasPrefix(a.EventType, "publish_"):
			a.Category = "Publish"
		case strings.HasPrefix(a.EventType, "review_"):
			a.Category = "Review"
		case strings.HasPrefix(a.EventType, "product_") || strings.HasPrefix(a.EntityType, "product"):
			a.Category = "Product"
		case strings.Contains(a.EntityType, "asset") || strings.Contains(a.EventType, "media"):
			a.Category = "Asset"
		}
		if a.BeforeData != nil {
			a.BeforeHash = rawHash(*a.BeforeData)
		}
		if a.AfterData != nil {
			a.AfterHash = rawHash(*a.AfterData)
			if a.Category == "Publish" || a.Category == "Rollback" || a.Category == "SystemRecovery" {
				var d map[string]interface{}
				if json.Unmarshal([]byte(*a.AfterData), &d) == nil {
					a.Detail = d
					if rid, ok := d["passport_revision_id"].(string); ok {
						a.PassportRevisionID = &rid
					}
				}
			}
		}
		if category == "" || a.Category == category {
			out.Audit = append(out.Audit, a)
		}
	}
	return out, nil
}

type IntegrityResult struct {
	State   string `json:"state"`
	Message string `json:"message"`
}
type AssetDetail struct {
	models.PublishedAsset
	ReferenceCount int64 `json:"reference_count"`
}
type VersionDetail struct {
	Version   VersionSummary  `json:"version"`
	Payload   interface{}     `json:"payload"`
	Manifest  interface{}     `json:"manifest"`
	Assets    []AssetDetail   `json:"assets"`
	Integrity IntegrityResult `json:"integrity"`
	Audit     []AuditItem     `json:"audit"`
}

func (s *Publishing) Version(id, rid string) (VersionDetail, error) {
	out := VersionDetail{Assets: []AssetDetail{}, Audit: []AuditItem{}}
	b, e := s.batch(s.Orm, id)
	if e != nil {
		return out, e
	}
	v, e := s.revisionEntry(id, rid)
	if e != nil {
		return out, e
	}
	kind := "normal_publish"
	if v.Record.OperationType == "rollback" {
		kind = "rollback"
	}
	out.Version = VersionSummary{v, kind, same(b.CurrentPassportRevisionID, &rid)}
	if v.Revision.Payload != nil {
		if e = json.Unmarshal([]byte(*v.Revision.Payload), &out.Payload); e != nil {
			return out, e
		}
	}
	st, e := openPublicationStore()
	if e != nil {
		return out, e
	}
	defer st.Close()
	out.Integrity = IntegrityResult{State: "verified"}
	if _, _, e = s.verifyPrepared(st, v); e != nil {
		out.Integrity = IntegrityResult{State: "integrity_error", Message: "Historical JSON, manifest or asset failed verification"}
	}
	raw, me := publishing.ReadRegular(st.Work, "manifests/"+v.Revision.ReleaseIdentifier+".json", 65536)
	if me == nil {
		_ = json.Unmarshal(raw, &out.Manifest)
	}
	var assets []models.PublishedAsset
	if e = s.Orm.Where("passport_revision_id=?", rid).Order("asset_key").Find(&assets).Error; e != nil {
		return out, e
	}
	for _, a := range assets {
		var n int64
		if e = s.Orm.Table("published_assets a").Joins("JOIN passport_revisions p ON p.id=a.passport_revision_id").Where("a.sha256=? AND p.published_at IS NOT NULL", a.SHA256).Distinct("a.passport_revision_id").Count(&n).Error; e != nil {
			return out, e
		}
		out.Assets = append(out.Assets, AssetDetail{a, n})
	}
	hist, e := s.History(id, "")
	if e != nil {
		return out, e
	}
	for _, a := range hist.Audit {
		if same(a.PassportRevisionID, &rid) || a.EntityID == v.Record.ID {
			out.Audit = append(out.Audit, a)
		}
	}
	return out, nil
}

type Difference struct {
	Group  string      `json:"group"`
	Path   string      `json:"path"`
	Change string      `json:"change"`
	Before interface{} `json:"before"`
	After  interface{} `json:"after"`
}
type VersionDiff struct {
	LeftRevisionID  string       `json:"left_revision_id"`
	RightRevisionID string       `json:"right_revision_id"`
	Differences     []Difference `json:"differences"`
}

func (s *Publishing) Compare(id, left, right string) (VersionDiff, error) {
	out := VersionDiff{LeftRevisionID: left, RightRevisionID: right, Differences: []Difference{}}
	if _, e := s.batch(s.Orm, id); e != nil {
		return out, e
	}
	a, e := s.revisionEntry(id, left)
	if e != nil {
		return out, e
	}
	b, e := s.revisionEntry(id, right)
	if e != nil {
		return out, e
	}
	st, e := openPublicationStore()
	if e != nil {
		return out, e
	}
	defer st.Close()
	ar, _, e := s.verifyPrepared(st, a)
	if e != nil {
		return out, conflict("左版本完整性失败")
	}
	br, _, e := s.verifyPrepared(st, b)
	if e != nil {
		return out, conflict("右版本完整性失败")
	}
	av, _ := publishing.Decode(ar)
	bv, _ := publishing.Decode(br)
	am, bm := av.(map[string]interface{}), bv.(map[string]interface{})
	add := func(group, key string, x, y interface{}) {
		change := "changed"
		if reflect.DeepEqual(x, y) {
			change = "unchanged"
		} else if x == nil {
			change = "added"
		} else if y == nil {
			change = "removed"
		}
		out.Differences = append(out.Differences, Difference{group, key, change, x, y})
	}
	for _, key := range []string{"product", "batch", "raw_material", "process", "inspection", "certifications", "packaging", "storage", "manufacturer", "custom_sections", "localization", "publication"} {
		add(key, key, am[key], bm[key])
	}
	// Keyed asset comparison includes filename derived from immutable public path, role/hash/size.
	assetMap := func(v interface{}) map[string]interface{} {
		out := map[string]interface{}{}
		for _, x := range v.([]interface{}) {
			a := x.(map[string]interface{})
			a["filename"] = path.Base(a["path"].(string))
			out[a["key"].(string)] = a
		}
		return out
	}
	aa, bb := assetMap(am["assets"]), assetMap(bm["assets"])
	keys := map[string]bool{}
	for k := range aa {
		keys[k] = true
	}
	for k := range bb {
		keys[k] = true
	}
	for k := range keys {
		add("assets", k, aa[k], bb[k])
	}
	add("hash", "payload_hash", a.Revision.PayloadHash, b.Revision.PayloadHash)
	add("hash", "content_hash", a.Revision.ContentHash, b.Revision.ContentHash)
	return out, nil
}
