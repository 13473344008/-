package models

type PassportRevision struct {
	ID                       string  `gorm:"column:id;primaryKey" json:"id"`
	CreatedAt                string  `gorm:"column:created_at" json:"created_at"`
	CreatedBy                int64   `gorm:"column:created_by" json:"created_by"`
	BatchID                  string  `gorm:"column:batch_id" json:"batch_id"`
	VersionNumber            int64   `gorm:"column:version_number" json:"version_number"`
	BaseProductRevisionID    string  `gorm:"column:base_product_revision_id" json:"base_product_revision_id"`
	SourceRevisionID         *string `gorm:"column:source_revision_id" json:"source_revision_id"`
	RollbackSourceRevisionID *string `gorm:"column:rollback_source_revision_id" json:"rollback_source_revision_id"`
	SourceEditVersion        *int64  `gorm:"column:source_edit_version" json:"source_edit_version"`
	SourceContentHash        string  `gorm:"column:source_content_hash" json:"source_content_hash"`
	FrozenInput              string  `gorm:"column:frozen_input" json:"-"`
	SchemaVersion            string  `gorm:"column:schema_version" json:"schema_version"`
	BuilderVersion           string  `gorm:"column:builder_version" json:"builder_version"`
	Payload                  *string `gorm:"column:payload" json:"-"`
	PayloadHash              *string `gorm:"column:payload_hash" json:"payload_hash"`
	ContentHash              *string `gorm:"column:content_hash" json:"content_hash"`
	SnapshotPath             *string `gorm:"column:snapshot_path" json:"snapshot_path"`
	AssetManifestHash        *string `gorm:"column:asset_manifest_hash" json:"asset_manifest_hash"`
	SealedAt                 *string `gorm:"column:sealed_at" json:"sealed_at"`
	PublishedAt              *string `gorm:"column:published_at" json:"published_at"`
	PublishedBy              int64   `gorm:"column:published_by" json:"published_by"`
	ReviewedBy               int64   `gorm:"column:reviewed_by" json:"reviewed_by"`
	ReviewedAt               string  `gorm:"column:reviewed_at" json:"reviewed_at"`
	ReleaseIdentifier        string  `gorm:"column:release_identifier" json:"release_identifier"`
	SourceReviewRecordID     *string `json:"source_review_record_id"`
}

func (PassportRevision) TableName() string { return "passport_revisions" }

type PublishRecord struct {
	RollbackReason            *string `json:"rollback_reason"`
	ID                        string  `gorm:"column:id;primaryKey" json:"id"`
	CreatedAt                 string  `gorm:"column:created_at" json:"created_at"`
	CreatedBy                 int64   `gorm:"column:created_by" json:"created_by"`
	BatchID                   string  `gorm:"column:batch_id" json:"batch_id"`
	PassportRevisionID        string  `gorm:"column:passport_revision_id" json:"passport_revision_id"`
	OperationType             string  `gorm:"column:operation_type" json:"operation_type"`
	PublishStatus             string  `gorm:"column:publish_status" json:"publish_status"`
	IdempotencyKey            string  `gorm:"column:idempotency_key" json:"idempotency_key"`
	ReleaseIdentifier         string  `gorm:"column:release_identifier" json:"release_identifier"`
	ExpectedCurrentRevisionID *string `gorm:"column:expected_current_revision_id" json:"expected_current_revision_id"`
	StartedAt                 *string `gorm:"column:started_at" json:"started_at"`
	CompletedAt               *string `gorm:"column:completed_at" json:"completed_at"`
	SwitchedAt                *string `gorm:"column:switched_at" json:"switched_at"`
	UpdatedAt                 string  `gorm:"column:updated_at" json:"updated_at"`
	AttemptCount              int64   `gorm:"column:attempt_count" json:"attempt_count"`
	AssetCount                *int64  `gorm:"column:asset_count" json:"asset_count"`
	ErrorCode                 *string `gorm:"column:error_code" json:"error_code"`
	ErrorMessage              *string `gorm:"column:error_message" json:"error_message"`
	StateVersion              int64   `gorm:"column:state_version" json:"state_version"`
	SourceReviewRecordID      *string `json:"source_review_record_id"`
}

func (PublishRecord) TableName() string { return "publish_records" }

type PublishedAsset struct {
	ID                 string `gorm:"column:id;primaryKey" json:"id"`
	CreatedAt          string `gorm:"column:created_at" json:"created_at"`
	CreatedBy          int64  `gorm:"column:created_by" json:"created_by"`
	PassportRevisionID string `gorm:"column:passport_revision_id" json:"passport_revision_id"`
	SourceMediaAssetID string `gorm:"column:source_media_asset_id" json:"source_media_asset_id"`
	AssetKey           string `gorm:"column:asset_key" json:"asset_key"`
	AssetRole          string `gorm:"column:asset_role" json:"asset_role"`
	OriginalFilename   string `gorm:"column:original_filename" json:"original_filename"`
	PublicLabel        string `gorm:"column:public_label" json:"public_label"`
	PublishedFilename  string `gorm:"column:published_filename" json:"published_filename"`
	MimeType           string `gorm:"column:mime_type" json:"mime_type"`
	FileSize           int64  `gorm:"column:file_size" json:"file_size"`
	SHA256             string `gorm:"column:sha256" json:"sha256"`
	PublishedPath      string `gorm:"column:published_path" json:"published_path"`
	TransformVersion   string `gorm:"column:transform_version" json:"transform_version"`
	SourceAssetSHA256  string `gorm:"column:source_asset_sha256" json:"source_asset_sha256"`
}

func (PublishedAsset) TableName() string { return "published_assets" }
