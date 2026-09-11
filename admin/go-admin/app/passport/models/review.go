package models

type ReviewRecord struct {
	ID                string  `gorm:"primaryKey" json:"id"`
	BatchID           string  `json:"batch_id"`
	AttemptNumber     int64   `json:"attempt_number"`
	Decision          string  `json:"decision"`
	CandidateInput    string  `json:"-"`
	CandidateHash     string  `json:"candidate_hash"`
	PreviewHash       string  `json:"preview_hash"`
	SourceEditVersion int64   `json:"source_edit_version"`
	SchemaVersion     string  `json:"schema_version"`
	BuilderVersion    string  `json:"builder_version"`
	SubmittedBy       int64   `json:"submitted_by"`
	SubmittedAt       string  `json:"submitted_at"`
	Contributors      string  `json:"-"`
	ReviewedBy        *int64  `json:"reviewed_by"`
	ReviewedAt        *string `json:"reviewed_at"`
	Comment           *string `json:"comment"`
	RejectionReason   *string `json:"rejection_reason"`
}

func (ReviewRecord) TableName() string { return "review_records" }
