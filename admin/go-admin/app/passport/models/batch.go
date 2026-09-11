package models

type Batch struct {
	CurrentReviewRecordID     *string `json:"current_review_record_id"`
	ID                        string  `gorm:"column:id;primaryKey" json:"id"`
	CreatedAt                 string  `gorm:"column:created_at" json:"created_at"`
	CreatedBy                 int64   `gorm:"column:created_by" json:"created_by"`
	UpdatedAt                 string  `gorm:"column:updated_at" json:"updated_at"`
	UpdatedBy                 int64   `gorm:"column:updated_by" json:"updated_by"`
	BatchCode                 string  `gorm:"column:batch_code" json:"batch_code"`
	ProductID                 string  `gorm:"column:product_id" json:"product_id"`
	BaseProductRevisionID     string  `gorm:"column:base_product_revision_id" json:"base_product_revision_id"`
	RecordType                string  `gorm:"column:record_type" json:"record_type"`
	ProductionDate            *string `gorm:"column:production_date" json:"production_date"`
	ExpiryDate                *string `gorm:"column:expiry_date" json:"expiry_date"`
	QualityStatus             string  `gorm:"column:quality_status" json:"quality_status"`
	WorkflowStatus            string  `gorm:"column:workflow_status" json:"workflow_status"`
	EditVersion               int64   `gorm:"column:edit_version" json:"edit_version"`
	SubmittedEditVersion      *int64  `gorm:"column:submitted_edit_version" json:"submitted_edit_version"`
	SubmittedContentHash      *string `gorm:"column:submitted_content_hash" json:"submitted_content_hash"`
	SubmittedInput            *string `gorm:"column:submitted_input" json:"submitted_input"`
	SubmittedSchemaVersion    *string `gorm:"column:submitted_schema_version" json:"submitted_schema_version"`
	SubmittedBuilderVersion   *string `gorm:"column:submitted_builder_version" json:"submitted_builder_version"`
	SubmittedPreviewHash      *string `gorm:"column:submitted_preview_hash" json:"submitted_preview_hash"`
	SubmittedAt               *string `gorm:"column:submitted_at" json:"submitted_at"`
	SubmittedBy               *int64  `gorm:"column:submitted_by" json:"submitted_by"`
	ReviewedAt                *string `gorm:"column:reviewed_at" json:"reviewed_at"`
	ReviewedBy                *int64  `gorm:"column:reviewed_by" json:"reviewed_by"`
	RejectionReason           *string `gorm:"column:rejection_reason" json:"rejection_reason"`
	CurrentPassportRevisionID *string `gorm:"column:current_passport_revision_id" json:"current_passport_revision_id"`
	ActivePublishRecordID     *string `gorm:"column:active_publish_record_id" json:"active_publish_record_id"`
	NextVersionNumber         int64   `gorm:"column:next_version_number" json:"next_version_number"`
	ClonedFromBatchID         *string `gorm:"column:cloned_from_batch_id" json:"cloned_from_batch_id"`
	ArchivedAt                *string `gorm:"column:archived_at" json:"archived_at"`
	ArchivedBy                *int64  `gorm:"column:archived_by" json:"archived_by"`
	InternalNote              *string `gorm:"column:internal_note" json:"internal_note"`
}

func (Batch) TableName() string { return "batches" }

type BatchOverride struct {
	ID                string  `gorm:"column:id;primaryKey" json:"id"`
	CreatedAt         string  `gorm:"column:created_at" json:"created_at"`
	CreatedBy         int64   `gorm:"column:created_by" json:"created_by"`
	UpdatedAt         string  `gorm:"column:updated_at" json:"updated_at"`
	UpdatedBy         int64   `gorm:"column:updated_by" json:"updated_by"`
	BatchID           string  `gorm:"column:batch_id" json:"batch_id"`
	FieldKey          string  `gorm:"column:field_key" json:"field_key"`
	ValueKind         string  `gorm:"column:value_kind" json:"value_kind"`
	Operation         string  `gorm:"column:operation" json:"operation"`
	ValueText         *string `gorm:"column:value_text" json:"value_text"`
	ValueInteger      *int64  `gorm:"column:value_integer" json:"value_integer"`
	ValueJson         *string `gorm:"column:value_json" json:"value_json"`
	ValueMediaAssetID *string `gorm:"column:value_media_asset_id" json:"value_media_asset_id"`
	PublicAssetLabel  *string `gorm:"column:public_asset_label" json:"public_asset_label"`
	SourceLanguage    string  `gorm:"column:source_language" json:"source_language"`
}

func (BatchOverride) TableName() string { return "batch_overrides" }

type InspectionItem struct {
	ID             string  `gorm:"column:id;primaryKey" json:"id"`
	CreatedAt      string  `gorm:"column:created_at" json:"created_at"`
	CreatedBy      int64   `gorm:"column:created_by" json:"created_by"`
	UpdatedAt      string  `gorm:"column:updated_at" json:"updated_at"`
	UpdatedBy      int64   `gorm:"column:updated_by" json:"updated_by"`
	BatchID        string  `gorm:"column:batch_id" json:"batch_id"`
	ItemCode       string  `gorm:"column:item_code" json:"item_code"`
	Name           string  `gorm:"column:name" json:"name"`
	SourceLanguage string  `gorm:"column:source_language" json:"source_language"`
	ValueType      string  `gorm:"column:value_type" json:"value_type"`
	NumericValue   *string `gorm:"column:numeric_value" json:"numeric_value"`
	TextValue      *string `gorm:"column:text_value" json:"text_value"`
	Unit           *string `gorm:"column:unit" json:"unit"`
	StandardValue  *string `gorm:"column:standard_value" json:"standard_value"`
	MinLimit       *string `gorm:"column:min_limit" json:"min_limit"`
	MaxLimit       *string `gorm:"column:max_limit" json:"max_limit"`
	MinInclusive   bool    `gorm:"column:min_inclusive" json:"min_inclusive"`
	MaxInclusive   bool    `gorm:"column:max_inclusive" json:"max_inclusive"`
	Specification  *string `gorm:"column:specification" json:"specification"`
	TestMethod     *string `gorm:"column:test_method" json:"test_method"`
	Judgement      string  `gorm:"column:judgement" json:"judgement"`
	SortOrder      int64   `gorm:"column:sort_order" json:"sort_order"`
	InternalNote   *string `gorm:"column:internal_note" json:"internal_note"`
	IsPublic       bool    `gorm:"column:is_public" json:"is_public"`
	TestedOn       *string `gorm:"column:tested_on" json:"tested_on"`
}

func (InspectionItem) TableName() string { return "inspection_items" }

type OverrideTranslation struct {
	ID                string  `gorm:"column:id;primaryKey" json:"id"`
	CreatedAt         string  `gorm:"column:created_at" json:"created_at"`
	CreatedBy         int64   `gorm:"column:created_by" json:"created_by"`
	UpdatedAt         string  `gorm:"column:updated_at" json:"updated_at"`
	UpdatedBy         int64   `gorm:"column:updated_by" json:"updated_by"`
	BatchOverrideID   string  `gorm:"column:batch_override_id" json:"batch_override_id"`
	LanguageCode      string  `gorm:"column:language_code" json:"language_code"`
	TranslationStatus string  `gorm:"column:translation_status" json:"translation_status"`
	TranslatedValue   *string `gorm:"column:translated_value" json:"translated_value"`
	TranslatedProcess *string `gorm:"column:translated_process" json:"translated_process"`
}

func (OverrideTranslation) TableName() string { return "batch_override_translations" }

type InspectionTranslation struct {
	ID                string  `gorm:"column:id;primaryKey" json:"id"`
	CreatedAt         string  `gorm:"column:created_at" json:"created_at"`
	CreatedBy         int64   `gorm:"column:created_by" json:"created_by"`
	UpdatedAt         string  `gorm:"column:updated_at" json:"updated_at"`
	UpdatedBy         int64   `gorm:"column:updated_by" json:"updated_by"`
	InspectionItemID  string  `gorm:"column:inspection_item_id" json:"inspection_item_id"`
	LanguageCode      string  `gorm:"column:language_code" json:"language_code"`
	TranslationStatus string  `gorm:"column:translation_status" json:"translation_status"`
	DisplayName       string  `gorm:"column:display_name" json:"display_name"`
	Specification     *string `gorm:"column:specification" json:"specification"`
	TestMethod        *string `gorm:"column:test_method" json:"test_method"`
	ResultDisplayText *string `gorm:"column:result_display_text" json:"result_display_text"`
}

func (InspectionTranslation) TableName() string { return "inspection_item_translations" }
