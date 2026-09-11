package dto

import "encoding/json"

type SectionTranslation struct {
	LanguageCode      string          `json:"language_code"`
	TranslationStatus string          `json:"translation_status"`
	Title             string          `json:"title"`
	Content           json.RawMessage `json:"content"`
}

// All translated structures are submitted together so a structural change is atomic.
type SectionContent struct {
	SectionKey   string               `json:"section_key"`
	Operation    string               `json:"operation"`
	SectionType  string               `json:"section_type"`
	SortOrder    *int                 `json:"sort_order"`
	IsVisible    bool                 `json:"is_visible"`
	IsPublic     bool                 `json:"is_public"`
	AllowHide    bool                 `json:"allow_hide"`
	Status       string               `json:"status"`
	Translations []SectionTranslation `json:"translations"`
}
type SectionWrite struct {
	ExpectedToken string         `json:"expected_token"`
	Section       SectionContent `json:"section"`
}
type SectionTranslate struct {
	ExpectedToken string             `json:"expected_token"`
	Translation   SectionTranslation `json:"translation"`
}
type SectionReorder struct {
	ExpectedToken string   `json:"expected_token"`
	Keys          []string `json:"keys"`
}
