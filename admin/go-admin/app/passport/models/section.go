package models

import "encoding/json"

type Section struct {
	ID                string  `gorm:"primaryKey" json:"id"`
	CreatedAt         string  `json:"created_at"`
	CreatedBy         int     `json:"created_by"`
	UpdatedAt         string  `json:"updated_at"`
	UpdatedBy         int     `json:"updated_by"`
	ProductRevisionID *string `json:"product_revision_id"`
	BatchID           *string `json:"batch_id"`
	SectionKey        string  `json:"section_key"`
	Operation         string  `json:"operation"`
	SectionType       string  `json:"section_type"`
	SourceLanguage    string  `json:"source_language"`
	SortOrder         *int    `json:"sort_order"`
	IsVisible         bool    `json:"is_visible"`
	IsPublic          bool    `json:"is_public"`
	AllowHide         bool    `json:"allow_hide"`
	Status            string  `json:"status"`
}

func (Section) TableName() string { return "custom_sections" }

type SectionTranslation struct {
	ID                string `gorm:"primaryKey" json:"id"`
	CreatedAt         string `json:"created_at"`
	CreatedBy         int    `json:"created_by"`
	UpdatedAt         string `json:"updated_at"`
	UpdatedBy         int    `json:"updated_by"`
	CustomSectionID   string `json:"custom_section_id"`
	LanguageCode      string `json:"language_code"`
	TranslationStatus string `json:"translation_status"`
	Title             string `json:"title"`
	Content           string `json:"-"`
}

func (SectionTranslation) TableName() string { return "custom_section_translations" }

type SectionTranslationView struct {
	SectionTranslation
	Content json.RawMessage `json:"content"`
}
