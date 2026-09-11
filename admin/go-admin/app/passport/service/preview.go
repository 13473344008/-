package service

import (
	"encoding/json"
	"errors"
	"go-admin/app/passport/models"
	"go-admin/app/passport/publishing"
	"gorm.io/gorm"
)

// Preview contains no release identifiers. Publication metadata inside Payload is
// only a builder placeholder; the shared private renderer never displays it.
type Preview struct {
	Kind        string            `json:"kind"`
	SourceHash  string            `json:"source_hash"`
	EditVersion int64             `json:"edit_version"`
	ReviewID    string            `json:"review_id,omitempty"`
	Payload     json.RawMessage   `json:"payload"`
	Assets      map[string][]byte `json:"assets"`
}

func (s *Reviews) Preview(id, kind, reviewID string) (Preview, error) {
	out := Preview{Kind: kind, Assets: map[string][]byte{}}
	err := s.Orm.Transaction(func(tx *gorm.DB) error {
		b, e := s.batch(tx, id)
		if e != nil {
			return e
		}
		var candidate ReviewCandidate
		raw := ""
		switch kind {
		case "working":
			if reviewID != "" {
				return invalid("工作预览不可指定审核记录")
			}
			ready, c, e := s.readiness(tx, id)
			if e != nil {
				return e
			}
			if !ready.Ready {
				return &ReadinessError{Result: ready}
			}
			candidate = c
			raw = encode(c)
			out.EditVersion = b.EditVersion
		case "review":
			if reviewID == "" {
				return invalid("请选择冻结审核记录")
			}
			var r models.ReviewRecord
			if e = tx.Where("id=? AND batch_id=?", reviewID, id).Take(&r).Error; e != nil {
				return e
			}
			if rawHash(r.CandidateInput) != r.CandidateHash {
				return conflict("审核快照摘要不匹配")
			}
			raw = r.CandidateInput
			out.ReviewID = r.ID
			out.EditVersion = r.SourceEditVersion
			if e = json.Unmarshal([]byte(raw), &candidate); e != nil {
				return conflict("审核快照无法解析")
			}
			if candidate.Batch.ID != id {
				return conflict("审核快照批次不匹配")
			}
		default:
			return invalid("不支持的预览类型")
		}
		built, e := publishing.Build([]byte(raw), 1, stamp())
		if e != nil {
			return invalid("预览内容不符合公开格式")
		}
		if e = publishing.ValidatePayload(built.Payload); e != nil {
			return invalid("预览内容不符合公开格式")
		}
		for _, a := range candidate.Assets {
			if a.Publish {
				if publishing.Hash(a.NormalizedPreview) != a.NormalizedSHA256 || int64(len(a.NormalizedPreview)) != a.NormalizedSize {
					return conflict("预览图片摘要不匹配")
				}
				out.Assets[a.AssetKey] = a.NormalizedPreview
			}
		}
		out.Payload = built.Payload
		out.SourceHash = rawHash(raw)
		return nil
	})
	var ready *ReadinessError
	if errors.As(err, &ready) {
		return out, err
	}
	return out, s.batchFail(err)
}
