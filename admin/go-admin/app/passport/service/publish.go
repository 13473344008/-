package service

import (
	"encoding/json"
	"errors"
	"fmt"
	"github.com/google/uuid"
	"go-admin/app/passport/models"
	"go-admin/app/passport/publishing"
	"gorm.io/gorm"
	"os"
	"path"
	"strings"
)

type PublishRequest struct {
	ReviewID                  string  `json:"review_id"`
	CandidateHash             string  `json:"candidate_hash"`
	IdempotencyKey            string  `json:"idempotency_key"`
	ExpectedCurrentRevisionID *string `json:"expected_current_revision_id"`
}
type PublishEntry struct {
	Record   models.PublishRecord    `json:"record"`
	Revision models.PassportRevision `json:"revision"`
}
type PublicationStatus struct {
	State          string                   `json:"state"`
	Current        *models.PassportRevision `json:"current"`
	ActiveRecordID *string                  `json:"active_record_id"`
	History        []PublishEntry           `json:"history"`
}

// Fault is a dependency-injected test seam, never set by a request, environment variable or route.
type Publishing struct {
	Reviews
	Fault func(string) error
}

func (s *Publishing) hit(stage string) error {
	if s.Fault != nil {
		return s.Fault(stage)
	}
	return nil
}
func ptr[T any](v T) *T      { return &v }
func same(a, b *string) bool { return a == nil && b == nil || a != nil && b != nil && *a == *b }
func (s *Publishing) authorize() error {
	if !s.Admin || s.Actor < 1 {
		return &BusinessError{403, "只有 Super Admin 可以发布"}
	}
	var n int64
	if e := s.Orm.Table("sys_user u").Joins("JOIN sys_role r ON r.role_id=u.role_id").Where("u.user_id=? AND u.status='2' AND u.deleted_at=0 AND r.role_key='admin' AND r.status='2' AND r.deleted_at=0", s.Actor).Count(&n).Error; e != nil {
		return e
	}
	if n != 1 {
		return &BusinessError{403, "发布权限已失效"}
	}
	return nil
}
func (s *Publishing) Status(id string) (PublicationStatus, error) {
	out := PublicationStatus{History: []PublishEntry{}}
	e := s.Orm.Transaction(func(tx *gorm.DB) error {
		b, e := s.batch(tx, id)
		if e != nil {
			return e
		}
		out.State = b.WorkflowStatus
		out.ActiveRecordID = b.ActivePublishRecordID
		if b.CurrentPassportRevisionID != nil {
			out.Current = &models.PassportRevision{}
			if e = tx.Where("id=? AND batch_id=?", *b.CurrentPassportRevisionID, id).Take(out.Current).Error; e != nil {
				return e
			}
		}
		var rows []models.PublishRecord
		if e = tx.Where("batch_id=?", id).Order("created_at DESC,id DESC").Limit(100).Find(&rows).Error; e != nil {
			return e
		}
		for _, r := range rows {
			var p models.PassportRevision
			if e = tx.Where("id=?", r.PassportRevisionID).Take(&p).Error; e != nil {
				return e
			}
			out.History = append(out.History, PublishEntry{r, p})
			if b.ActivePublishRecordID != nil && *b.ActivePublishRecordID == r.ID {
				out.State = r.PublishStatus
			}
		}
		return nil
	})
	return out, s.batchFail(e)
}
func (s *Publishing) entry(id string) (PublishEntry, error) {
	v := PublishEntry{}
	e := s.Orm.Where("id=?", id).Take(&v.Record).Error
	if e == nil {
		e = s.Orm.Where("id=?", v.Record.PassportRevisionID).Take(&v.Revision).Error
	}
	return v, e
}
func (s *Publishing) Publish(id string, req PublishRequest) (PublishEntry, error) {
	if e := s.authorize(); e != nil {
		return PublishEntry{}, e
	}
	if _, e := uuid.Parse(req.IdempotencyKey); e != nil {
		return PublishEntry{}, invalid("幂等键必须为 UUID")
	}
	if len(req.CandidateHash) != 64 {
		return PublishEntry{}, invalid("审核摘要格式不正确")
	}
	store, e := publishing.OpenStore(os.Getenv("PASSPORT_PUBLISH_ROOT"), os.Getenv("PASSPORT_RELEASE_WORK_ROOT"))
	if e != nil {
		return PublishEntry{}, fmt.Errorf("publish storage unavailable: %w", e)
	}
	defer store.Close()
	unlock, e := store.Lock(id)
	if e != nil {
		return PublishEntry{}, conflict("该批次正在发布，请刷新状态")
	}
	defer unlock()
	var entry PublishEntry
	existing := false
	e = s.Orm.Transaction(func(tx *gorm.DB) error {
		if e := tx.Exec("UPDATE batches SET id=id WHERE id=?", id).Error; e != nil {
			return e
		}
		b, e := s.batch(tx, id)
		if e != nil {
			return e
		}
		var old models.PublishRecord
		e = tx.Where("batch_id=? AND idempotency_key=?", id, req.IdempotencyKey).Take(&old).Error
		if e == nil {
			if old.OperationType != "publish" || old.SourceReviewRecordID == nil || *old.SourceReviewRecordID != req.ReviewID {
				return conflict("幂等键已绑定其他审核")
			}
			entry.Record = old
			existing = true
			if e := tx.Where("id=?", old.PassportRevisionID).Take(&entry.Revision).Error; e != nil {
				return e
			}
			if entry.Revision.SourceContentHash != req.CandidateHash || !same(old.ExpectedCurrentRevisionID, req.ExpectedCurrentRevisionID) {
				return conflict("幂等键请求内容不一致")
			}
			return nil
		}
		if !errors.Is(e, gorm.ErrRecordNotFound) {
			return e
		}
		if e := s.guardCurrent(store, tx, b); e != nil {
			return e
		}
		if b.WorkflowStatus != "pending_review" || b.ActivePublishRecordID != nil || b.CurrentReviewRecordID == nil || *b.CurrentReviewRecordID != req.ReviewID {
			return conflict("仅允许发布当前已批准且未锁定的审核")
		}
		if !same(b.CurrentPassportRevisionID, req.ExpectedCurrentRevisionID) {
			return conflict("当前发布版本已变化")
		}
		var r models.ReviewRecord
		if e = tx.Where("id=? AND batch_id=?", req.ReviewID, id).Take(&r).Error; e != nil {
			return e
		}
		if r.Decision != "approved" || r.ReviewedBy == nil || r.ReviewedAt == nil || r.CandidateHash != req.CandidateHash || rawHash(r.CandidateInput) != r.CandidateHash || r.PreviewHash != r.CandidateHash || b.SubmittedInput == nil || *b.SubmittedInput != r.CandidateInput || b.SubmittedContentHash == nil || *b.SubmittedContentHash != r.CandidateHash || b.SubmittedPreviewHash == nil || *b.SubmittedPreviewHash != r.PreviewHash || b.SubmittedEditVersion == nil || *b.SubmittedEditVersion != r.SourceEditVersion || b.EditVersion != r.SourceEditVersion || b.SubmittedSchemaVersion == nil || *b.SubmittedSchemaVersion != r.SchemaVersion || b.SubmittedBuilderVersion == nil || *b.SubmittedBuilderVersion != r.BuilderVersion || b.SubmittedBy == nil || *b.SubmittedBy != r.SubmittedBy || b.SubmittedAt == nil || *b.SubmittedAt != r.SubmittedAt || b.ReviewedBy == nil || *b.ReviewedBy != *r.ReviewedBy || b.ReviewedAt == nil || *b.ReviewedAt != *r.ReviewedAt {
			return conflict("批准输入与当前冻结版本不一致")
		}
		var c ReviewCandidate
		if json.Unmarshal([]byte(r.CandidateInput), &c) != nil || c.Batch.ID != id || c.Batch.BatchCode != b.BatchCode || c.Batch.BaseRevisionID != b.BaseProductRevisionID || c.Batch.ProductID != b.ProductID || c.Batch.RecordType != b.RecordType {
			return conflict("审核输入归属不正确")
		}
		var used int64
		if e = tx.Model(&models.PassportRevision{}).Where("source_review_record_id=? AND published_at IS NOT NULL AND rollback_source_revision_id IS NULL", r.ID).Count(&used).Error; e != nil {
			return e
		}
		if used > 0 {
			return conflict("此审核已发布")
		}
		if _, e = validateCode(b.BatchCode); e != nil {
			return e
		}
		if e = validateBatchRecordCode(b.BatchCode, b.RecordType); e != nil {
			return e
		}
		now := stamp()
		p := models.PassportRevision{ID: uuid.NewString(), CreatedAt: now, CreatedBy: int64(s.Actor), BatchID: id, VersionNumber: b.NextVersionNumber, BaseProductRevisionID: b.BaseProductRevisionID, SourceRevisionID: b.CurrentPassportRevisionID, SourceEditVersion: ptr(b.EditVersion), SourceContentHash: r.CandidateHash, FrozenInput: r.CandidateInput, SchemaVersion: "1.0", BuilderVersion: publishing.BuilderVersion, PublishedBy: int64(s.Actor), ReviewedBy: *r.ReviewedBy, ReviewedAt: *r.ReviewedAt, ReleaseIdentifier: uuid.NewString(), SourceReviewRecordID: &r.ID}
		rec := models.PublishRecord{ID: uuid.NewString(), CreatedAt: now, CreatedBy: int64(s.Actor), BatchID: id, PassportRevisionID: p.ID, OperationType: "publish", PublishStatus: "pending", IdempotencyKey: req.IdempotencyKey, ReleaseIdentifier: p.ReleaseIdentifier, ExpectedCurrentRevisionID: b.CurrentPassportRevisionID, StartedAt: &now, UpdatedAt: now, AttemptCount: 1, StateVersion: 1, SourceReviewRecordID: &r.ID}
		if e = tx.Create(&p).Error; e != nil {
			return e
		}
		if e = tx.Create(&rec).Error; e != nil {
			return e
		}
		if e = tx.Model(&models.Batch{}).Where("id=?", id).Updates(map[string]interface{}{"active_publish_record_id": rec.ID, "next_version_number": b.NextVersionNumber + 1}).Error; e != nil {
			return e
		}
		if e = s.pubAudit(tx, rec, "publish_requested", "prepare", nil); e != nil {
			return e
		}
		entry = PublishEntry{rec, p}
		return nil
	})
	if e != nil {
		if b, be := s.batch(s.Orm, id); be == nil {
			h := s.inspectCurrent(store, b)
			if he := s.saveHealth(h, id); he != nil {
				return entry, he
			}
		}
		return entry, s.batchFail(e)
	}
	if existing {
		return entry, nil
	}
	if e = s.build(store, &entry); e != nil {
		return s.fail(entry, e, false)
	}
	return s.switchAndFinalize(store, entry)
}
func (s *Publishing) pubAudit(tx *gorm.DB, r models.PublishRecord, event, stage string, extra map[string]interface{}) error {
	if extra == nil {
		extra = map[string]interface{}{}
	}
	if r.OperationType == "rollback" {
		switch event {
		case "publish_requested":
			event = "rollback_requested"
		case "publish_succeeded":
			event = "rollback_succeeded"
		case "publish_failed":
			event = "rollback_failed"
			if stage == "recovery_required" {
				event = "rollback_reconcile_required"
			}
		}
	}
	extra["rollback_reason"] = r.RollbackReason
	extra["stage"] = stage
	extra["publish_record_id"] = r.ID
	extra["passport_revision_id"] = r.PassportRevisionID
	extra["review_id"] = r.SourceReviewRecordID
	extra["release_identifier"] = r.ReleaseIdentifier
	return s.batchAudit(tx, r.BatchID, event, "publish_records", r.ID, nil, extra)
}
func (s *Publishing) setState(r models.PublishRecord, state string, extra map[string]interface{}) error {
	if extra == nil {
		extra = map[string]interface{}{}
	}
	extra["publish_status"] = state
	extra["updated_at"] = stamp()
	extra["state_version"] = gorm.Expr("state_version+1")
	return s.Orm.Model(&models.PublishRecord{}).Where("id=? AND publish_status NOT IN ('published','failed')", r.ID).Updates(extra).Error
}
func (s *Publishing) build(store *publishing.Store, v *PublishEntry) error {
	r, p := v.Record, v.Revision
	if e := s.setState(r, "building", nil); e != nil {
		return e
	}
	if e := s.hit("build"); e != nil {
		return e
	}
	built, e := publishing.Build([]byte(p.FrozenInput), p.VersionNumber, p.CreatedAt)
	if e != nil {
		return e
	}
	var c ReviewCandidate
	if e = json.Unmarshal([]byte(p.FrozenInput), &c); e != nil {
		return e
	}
	count := 0
	rows := []models.PublishedAsset{}
	for _, a := range c.Assets {
		if !a.Publish {
			continue
		}
		count++
		if e = s.hit(fmt.Sprintf("copy:%d", count)); e != nil {
			return e
		}
		source, e := publishing.ReadPrivate(os.Getenv("PASSPORT_PRIVATE_MEDIA_ROOT"), a.StorageKey)
		if e != nil {
			return fmt.Errorf("source asset missing or unsafe")
		}
		if publishing.Hash(source) != a.SHA256 || int64(len(source)) != a.FileSize {
			return fmt.Errorf("source asset changed")
		}
		normalized, e := publishing.Normalize(source, a.MimeType)
		if e != nil {
			return e
		}
		var eligible int64
		if e = s.Orm.Table("media_assets").Where("id=? AND availability_status='ready' AND is_public_eligible=1", a.SourceMediaID).Count(&eligible).Error; e != nil {
			return e
		}
		if eligible != 1 {
			return fmt.Errorf("source asset no longer eligible")
		}
		if a.TransformVersion != publishing.TransformVersion || publishing.Hash(normalized) != a.NormalizedSHA256 || publishing.Hash(a.NormalizedPreview) != a.NormalizedSHA256 || int64(len(normalized)) != a.NormalizedSize {
			return fmt.Errorf("approved asset bytes mismatch")
		}
		assetPath := "assets/sha256/" + a.NormalizedSHA256[:2] + "/" + a.NormalizedSHA256 + ".png"
		if e = publishing.Immutable(store.Public, assetPath, normalized, 0644); e != nil {
			return e
		}
		actual, e := publishing.ReadRegular(store.Public, assetPath, publishing.MaxSourceBytes)
		if e != nil || publishing.Hash(actual) != a.NormalizedSHA256 {
			return fmt.Errorf("published asset verification failed")
		}
		rows = append(rows, models.PublishedAsset{ID: uuid.NewString(), CreatedAt: stamp(), CreatedBy: int64(s.Actor), PassportRevisionID: p.ID, SourceMediaAssetID: a.SourceMediaID, AssetKey: a.AssetKey, AssetRole: a.AssetRole, OriginalFilename: a.OriginalFilename, PublicLabel: a.PublicLabel, PublishedFilename: path.Base(assetPath), MimeType: "image/png", FileSize: int64(len(actual)), SHA256: publishing.Hash(actual), PublishedPath: assetPath, TransformVersion: a.TransformVersion, SourceAssetSHA256: a.SHA256})
	}
	return s.sealBuilt(store, v, built, rows, c.Batch.BatchCode)
}
func (s *Publishing) sealBuilt(store *publishing.Store, v *PublishEntry, built publishing.BuildResult, rows []models.PublishedAsset, code string) error {
	r, p := v.Record, v.Revision
	var e error
	if e = s.setState(r, "validating", nil); e != nil {
		return e
	}
	if e = s.hit("validation"); e != nil {
		return e
	}
	if e = publishing.ValidatePayload(built.Payload); e != nil {
		return e
	}
	assetsRaw, e := publishing.Decode([]byte(encode(built.Assets)))
	if e != nil {
		return e
	}
	manifest, e := publishing.Canonical(assetsRaw)
	if e != nil {
		return e
	}
	mh := publishing.Hash(manifest)
	snapshot := fmt.Sprintf("versions/%s/v%d.json", code, p.VersionNumber)
	if e = s.hit("write"); e != nil {
		return e
	}
	if e = publishing.Immutable(store.Work, "tmp/"+r.ID+"/passport.json", built.Payload, 0600); e != nil {
		return e
	}
	if e = publishing.Immutable(store.Work, "tmp/"+r.ID+"/assets.json", manifest, 0600); e != nil {
		return e
	}
	if e = s.hit("manifest"); e != nil {
		return e
	}
	privateManifest := map[string]interface{}{"version_number": p.VersionNumber, "batch_code": code, "release_identifier": r.ReleaseIdentifier, "publish_record_id": r.ID, "passport_revision_id": p.ID, "review_id": p.SourceReviewRecordID, "payload_hash": built.PayloadHash, "content_hash": built.ContentHash, "asset_manifest_hash": mh, "asset_count": len(rows), "snapshot_path": snapshot, "schema_version": p.SchemaVersion, "builder_version": p.BuilderVersion}
	if e = publishing.Immutable(store.Work, "manifests/"+r.ReleaseIdentifier+".json", []byte(encode(privateManifest)), 0600); e != nil {
		return e
	}
	// Historical snapshot is complete before the public head is eligible to switch.
	if e = publishing.Immutable(store.Public, snapshot, built.Payload, 0644); e != nil {
		return e
	}
	check, e := publishing.ReadRegular(store.Public, snapshot, publishing.MaxPayloadBytes)
	if e != nil || publishing.Hash(check) != built.PayloadHash {
		return fmt.Errorf("snapshot verification failed")
	}
	e = s.Orm.Transaction(func(tx *gorm.DB) error {
		if len(rows) > 0 {
			if e := tx.Create(&rows).Error; e != nil {
				return e
			}
		}
		m := map[string]interface{}{"payload": string(built.Payload), "payload_hash": built.PayloadHash, "content_hash": built.ContentHash, "snapshot_path": snapshot, "asset_manifest_hash": mh, "sealed_at": stamp()}
		if e := tx.Model(&models.PassportRevision{}).Where("id=? AND sealed_at IS NULL", p.ID).Updates(m).Error; e != nil {
			return e
		}
		if e := tx.Model(&models.PublishRecord{}).Where("id=? AND publish_status='validating'", r.ID).Updates(map[string]interface{}{"publish_status": "prepared", "asset_count": len(rows), "updated_at": stamp(), "state_version": gorm.Expr("state_version+1")}).Error; e != nil {
			return e
		}
		return s.pubAudit(tx, r, "publish_requested", "prepared", map[string]interface{}{"payload_hash": built.PayloadHash, "asset_count": len(rows)})
	})
	if e != nil {
		return e
	}
	*v, e = s.entry(r.ID)
	return e
}
func (s *Publishing) expectedHash(r models.PublishRecord) (string, error) {
	if r.ExpectedCurrentRevisionID == nil {
		return "", nil
	}
	var p models.PassportRevision
	if e := s.Orm.Where("id=? AND batch_id=? AND published_at IS NOT NULL", *r.ExpectedCurrentRevisionID, r.BatchID).Take(&p).Error; e != nil {
		return "", e
	}
	if p.PayloadHash == nil {
		return "", fmt.Errorf("old hash absent")
	}
	return *p.PayloadHash, nil
}
func currentHash(store *publishing.Store, code string) (string, error) {
	data, e := store.Current(code)
	if os.IsNotExist(e) {
		return "", nil
	}
	if e != nil {
		return "", e
	}
	if e = publishing.ValidatePayload(data); e != nil {
		return "", e
	}
	return publishing.Hash(data), nil
}
func (s *Publishing) verifyPrepared(store *publishing.Store, v PublishEntry) ([]byte, string, error) {
	p := v.Revision
	if p.SealedAt == nil || p.SnapshotPath == nil || p.PayloadHash == nil || p.Payload == nil || p.AssetManifestHash == nil {
		return nil, "", fmt.Errorf("unsealed release")
	}
	var c ReviewCandidate
	if e := json.Unmarshal([]byte(p.FrozenInput), &c); e != nil {
		return nil, "", e
	}
	if _, e := validateCode(c.Batch.BatchCode); e != nil {
		return nil, "", e
	}
	data, e := publishing.ReadRegular(store.Public, *p.SnapshotPath, publishing.MaxPayloadBytes)
	if e != nil {
		return nil, "", e
	}
	if publishing.Hash(data) != *p.PayloadHash || string(data) != *p.Payload {
		return nil, "", fmt.Errorf("sealed payload mismatch")
	}
	if e = publishing.ValidatePayload(data); e != nil {
		return nil, "", e
	}
	manifestBytes, e := publishing.ReadRegular(store.Work, "manifests/"+p.ReleaseIdentifier+".json", 65536)
	if e != nil {
		return nil, "", fmt.Errorf("release manifest missing")
	}
	expectedManifest := map[string]interface{}{"version_number": p.VersionNumber, "batch_code": c.Batch.BatchCode, "release_identifier": p.ReleaseIdentifier, "publish_record_id": v.Record.ID, "passport_revision_id": p.ID, "review_id": p.SourceReviewRecordID, "payload_hash": p.PayloadHash, "content_hash": p.ContentHash, "asset_manifest_hash": p.AssetManifestHash, "asset_count": v.Record.AssetCount, "snapshot_path": p.SnapshotPath, "schema_version": p.SchemaVersion, "builder_version": p.BuilderVersion}
	expectedRaw, _ := publishing.Decode([]byte(encode(expectedManifest)))
	expectedCanonical, _ := publishing.Canonical(expectedRaw)
	actualRaw, me := publishing.Decode(manifestBytes)
	if me != nil {
		return nil, "", fmt.Errorf("release manifest malformed")
	}
	// T9's earliest immutable manifests encode the version in snapshot_path.
	if legacy, ok := actualRaw.(map[string]interface{}); ok {
		if _, exists := legacy["version_number"]; !exists {
			delete(expectedManifest, "version_number")
			expectedRaw, _ = publishing.Decode([]byte(encode(expectedManifest)))
			expectedCanonical, _ = publishing.Canonical(expectedRaw)
		}
	}
	actualCanonical, me := publishing.Canonical(actualRaw)
	if me != nil || string(expectedCanonical) != string(actualCanonical) || string(manifestBytes) != encode(expectedManifest) {
		return nil, "", fmt.Errorf("release manifest mismatch")
	}

	var rows []models.PublishedAsset
	if e = s.Orm.Where("passport_revision_id=?", p.ID).Order("asset_key").Find(&rows).Error; e != nil {
		return nil, "", e
	}
	manifest := []interface{}{}
	for _, a := range rows {
		raw, e := publishing.ReadRegular(store.Public, a.PublishedPath, publishing.MaxSourceBytes)
		if e != nil || int64(len(raw)) != a.FileSize || publishing.Hash(raw) != a.SHA256 {
			return nil, "", fmt.Errorf("published asset missing or changed")
		}
		manifest = append(manifest, map[string]interface{}{"key": a.AssetKey, "role": a.AssetRole, "label": a.PublicLabel, "path": a.PublishedPath, "mime_type": a.MimeType, "file_size": a.FileSize, "sha256": a.SHA256})
	}
	m, e := publishing.Canonical(manifest)
	if e != nil {
		return nil, "", e
	}
	if publishing.Hash(m) != *p.AssetManifestHash || v.Record.AssetCount == nil || int64(len(rows)) != *v.Record.AssetCount {
		return nil, "", fmt.Errorf("asset manifest mismatch")
	}
	pv, e := publishing.Decode(data)
	if e != nil {
		return nil, "", e
	}
	pa, e := publishing.Canonical(pv.(map[string]interface{})["assets"])
	if e != nil || string(pa) != string(m) {
		return nil, "", fmt.Errorf("payload asset references mismatch")
	}
	business := pv.(map[string]interface{})
	delete(business, "publication")
	br, be := publishing.Canonical(business)
	if be != nil || p.ContentHash == nil || publishing.Hash(br) != *p.ContentHash {
		return nil, "", fmt.Errorf("business hash mismatch")
	}
	return data, c.Batch.BatchCode, nil
}
func (s *Publishing) switchAndFinalize(store *publishing.Store, v PublishEntry) (PublishEntry, error) {
	data, code, e := s.verifyPrepared(store, v)
	if e != nil {
		return s.fail(v, e, false)
	}
	old, e := s.expectedHash(v.Record)
	if e != nil {
		return s.fail(v, e, true)
	}
	actual, e := currentHash(store, code)
	if e != nil || actual != old {
		return s.fail(v, fmt.Errorf("public head requires reconciliation"), true)
	}
	if e = s.setState(v.Record, "switching", nil); e != nil {
		return s.fail(v, e, false)
	}
	if e = s.hit("rename"); e != nil {
		return s.fail(v, e, false)
	}
	renamed, e := store.Switch(code, data)
	if e != nil {
		return s.fail(v, e, renamed)
	}
	if e = s.hit("finalize"); e != nil {
		return s.fail(v, e, true)
	}
	if e = s.finalize(v); e != nil {
		return s.fail(v, e, true)
	}
	return s.entry(v.Record.ID)
}
func (s *Publishing) finalize(v PublishEntry) error {
	return s.Orm.Transaction(func(tx *gorm.DB) error {
		var b models.Batch
		if e := tx.Where("id=?", v.Record.BatchID).Take(&b).Error; e != nil {
			return e
		}
		if b.ActivePublishRecordID == nil || *b.ActivePublishRecordID != v.Record.ID || !same(b.CurrentPassportRevisionID, v.Record.ExpectedCurrentRevisionID) {
			return conflict("数据库当前版本需人工对账")
		}
		now := stamp()
		if e := tx.Model(&models.PassportRevision{}).Where("id=? AND published_at IS NULL", v.Revision.ID).Update("published_at", now).Error; e != nil {
			return e
		}
		if e := tx.Model(&models.PublishRecord{}).Where("id=?", v.Record.ID).Updates(map[string]interface{}{"publish_status": "published", "completed_at": now, "switched_at": now, "updated_at": now, "error_code": nil, "error_message": nil, "state_version": gorm.Expr("state_version+1")}).Error; e != nil {
			return e
		}
		if e := tx.Model(&models.Batch{}).Where("id=?", b.ID).Updates(map[string]interface{}{"current_passport_revision_id": v.Revision.ID, "workflow_status": "published", "active_publish_record_id": nil}).Error; e != nil {
			return e
		}
		return s.pubAudit(tx, v.Record, "publish_succeeded", "database_confirmed", map[string]interface{}{"payload_hash": v.Revision.PayloadHash, "content_hash": v.Revision.ContentHash, "version_number": v.Revision.VersionNumber, "switched_at_reconstructed": true})
	})
}
func (s *Publishing) fail(v PublishEntry, cause error, uncertain bool) (PublishEntry, error) {
	state, code, msg := "failed", "publish_failed", "发布在切换前失败；旧版本保持不变，可使用新幂等键重试"
	if uncertain {
		state, code, msg = "recovery_required", "recovery_required", "发布结果待对账；禁止新发布，请恢复同一次操作"
	}
	e := s.Orm.Transaction(func(tx *gorm.DB) error {
		m := map[string]interface{}{"publish_status": state, "error_code": code, "error_message": msg, "updated_at": stamp(), "state_version": gorm.Expr("state_version+1")}
		if !uncertain {
			m["completed_at"] = stamp()
		}
		if e := tx.Model(&models.PublishRecord{}).Where("id=? AND publish_status NOT IN ('published','failed')", v.Record.ID).Updates(m).Error; e != nil {
			return e
		}
		if !uncertain {
			if e := tx.Model(&models.Batch{}).Where("id=? AND active_publish_record_id=?", v.Record.BatchID, v.Record.ID).Update("active_publish_record_id", nil).Error; e != nil {
				return e
			}
		}
		return s.pubAudit(tx, v.Record, "publish_failed", state, map[string]interface{}{"error_code": code, "cause_class": classifyPublishError(cause)})
	})
	if e != nil {
		return v, fmt.Errorf("publish state persistence requires reconciliation: %w", e)
	}
	return s.entry(v.Record.ID)
}
func classifyPublishError(e error) string {
	m := e.Error()
	for _, k := range []string{"source", "asset", "schema", "semantics", "permission", "snapshot", "immutable", "injected"} {
		if strings.Contains(m, k) {
			return k
		}
	}
	return "storage_or_database"
}

// Reconcile uses the OS batch lock and sealed bytes. It never starts a second attempt or edits a published revision.
func (s *Publishing) Reconcile(id string) (PublishEntry, error) {
	return s.ReconcileReason(id, "Resume interrupted operation using sealed release evidence")
}
func (s *Publishing) reconcileLocked(store *publishing.Store, id string) (PublishEntry, error) {
	b, e := s.batch(s.Orm, id)
	if e != nil {
		return PublishEntry{}, e
	}
	if b.ActivePublishRecordID == nil {
		return PublishEntry{}, conflict("没有待恢复发布")
	}
	v, e := s.entry(*b.ActivePublishRecordID)
	if e != nil {
		return v, e
	}
	var c ReviewCandidate
	if e = json.Unmarshal([]byte(v.Revision.FrozenInput), &c); e != nil {
		return v, e
	}
	actual, e := currentHash(store, c.Batch.BatchCode)
	if e != nil {
		return s.fail(v, e, true)
	}
	old, e := s.expectedHash(v.Record)
	if e != nil {
		return s.fail(v, e, true)
	}
	if v.Revision.PayloadHash != nil && actual == *v.Revision.PayloadHash {
		if _, _, e = s.verifyPrepared(store, v); e != nil {
			return s.fail(v, e, true)
		}
		if e = s.setState(v.Record, "recovery_required", nil); e != nil {
			return v, e
		}
		if e = s.finalize(v); e != nil {
			return s.fail(v, e, true)
		}
		return s.entry(v.Record.ID)
	}
	if actual != old {
		return s.fail(v, fmt.Errorf("unknown current file"), true)
	}
	if v.Revision.SealedAt == nil {
		return s.fail(v, fmt.Errorf("interrupted before prepared"), false)
	}
	return s.switchAndFinalize(store, v)
}
