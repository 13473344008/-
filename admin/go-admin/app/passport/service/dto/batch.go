package dto

type BatchContent struct {
	ProductionDate *string `json:"production_date"`
	ExpiryDate     *string `json:"expiry_date"`
	QualityStatus  string  `json:"quality_status"`
	InternalNote   *string `json:"internal_note"`
}
type ProcessLabel struct {
	StepKey string `json:"step_key"`
	Label   string `json:"label"`
}
type OverrideInput struct {
	FieldKey     string         `json:"field_key"`
	Operation    string         `json:"operation"`
	ValueText    *string        `json:"value_text"`
	ValueInteger *int64         `json:"value_integer"`
	Process      []ProcessLabel `json:"process"`
}
type InspectionInput struct {
	ItemCode      string  `json:"item_code"`
	Name          string  `json:"name"`
	ValueType     string  `json:"value_type"`
	NumericValue  *string `json:"numeric_value"`
	TextValue     *string `json:"text_value"`
	Unit          *string `json:"unit"`
	StandardValue *string `json:"standard_value"`
	MinLimit      *string `json:"min_limit"`
	MaxLimit      *string `json:"max_limit"`
	MinInclusive  bool    `json:"min_inclusive"`
	MaxInclusive  bool    `json:"max_inclusive"`
	Specification *string `json:"specification"`
	TestMethod    *string `json:"test_method"`
	Judgement     string  `json:"judgement"`
	SortOrder     int64   `json:"sort_order"`
	InternalNote  *string `json:"internal_note"`
	IsPublic      bool    `json:"is_public"`
	TestedOn      *string `json:"tested_on"`
}

// Full aggregate replacement: omitted child arrays are rejected, [] explicitly removes children.
type BatchWork struct {
	Content     BatchContent      `json:"content"`
	Overrides   []OverrideInput   `json:"overrides"`
	Inspections []InspectionInput `json:"inspections"`
}
type CreateBatchRequest struct {
	ProductID  string `json:"product_id"`
	BatchCode  string `json:"batch_code"`
	RecordType string `json:"record_type"`
	BatchWork
}
type UpdateBatchRequest struct {
	ExpectedEditVersion int64 `json:"expected_edit_version"`
	BatchWork
}
type CloneBatchRequest struct {
	BatchCode           string  `json:"batch_code"`
	ProductionDate      *string `json:"production_date"`
	ExpiryDate          *string `json:"expiry_date"`
	ExpectedEditVersion int64   `json:"expected_edit_version"`
}
type BatchQuery struct {
	PageIndex int    `form:"pageIndex"`
	PageSize  int    `form:"pageSize"`
	Search    string `form:"search"`
	Status    string `form:"status"`
	ProductID string `form:"product_id"`
}
