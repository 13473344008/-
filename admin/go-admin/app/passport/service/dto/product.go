package dto

type Step struct {
	StepKey string `json:"step_key"`
}
type RevisionContent struct {
	SourceLanguage    string  `json:"source_language"`
	CategoryCode      *string `json:"category_code"`
	OriginCountryCode *string `json:"origin_country_code"`
	PackageQuantity   *string `json:"package_quantity"`
	PackageUnit       *string `json:"package_unit"`
	PackageTypeCode   *string `json:"package_type_code"`
	ShelfLifeDays     *int64  `json:"shelf_life_days"`
	ProcessSteps      []Step  `json:"process_steps"`
	InternalNote      *string `json:"internal_note"`
}
type TranslationRequest struct {
	LanguageCode           string            `json:"language_code"`
	TranslationStatus      string            `json:"translation_status"`
	ProductName            string            `json:"product_name"`
	ShortDescription       *string           `json:"short_description"`
	RawMaterialName        *string           `json:"raw_material_name"`
	RawMaterialType        *string           `json:"raw_material_type"`
	RawMaterialOrigin      *string           `json:"raw_material_origin"`
	RawMaterialDescription *string           `json:"raw_material_description"`
	PackageDescription     *string           `json:"package_description"`
	InnerMaterial          *string           `json:"inner_material"`
	StorageConditions      *string           `json:"storage_conditions"`
	ShelfLifeDescription   *string           `json:"shelf_life_description"`
	ManufacturerName       *string           `json:"manufacturer_name"`
	ManufacturerAddress    *string           `json:"manufacturer_address"`
	ProcessLabels          map[string]string `json:"process_labels"`
}
type CreateProductRequest struct {
	ProductCode  string               `json:"product_code"`
	Content      RevisionContent      `json:"content"`
	Translations []TranslationRequest `json:"translations"`
}
type UpdateRevisionRequest struct {
	ExpectedToken string          `json:"expected_token"`
	Content       RevisionContent `json:"content"`
}
type UpdateTranslationRequest struct {
	ExpectedToken string             `json:"expected_token"`
	Translation   TranslationRequest `json:"translation"`
}
type CreateRevisionRequest struct {
	SourceRevisionID string `json:"source_revision_id"`
}
type TokenRequest struct {
	ExpectedToken string `json:"expected_token"`
}
type DefaultRequest struct {
	RevisionID        string  `json:"revision_id"`
	ExpectedCurrentID *string `json:"expected_current_revision_id"`
}
type UpdateProductRequest struct {
	LifecycleStatus string `json:"lifecycle_status"`
}
type Query struct {
	PageIndex int    `form:"pageIndex"`
	PageSize  int    `form:"pageSize"`
	Search    string `form:"search"`
	Status    string `form:"status"`
}
