package models

type Product struct {
	ID                string  `gorm:"column:id;primaryKey" json:"id"`
	CreatedAt         string  `gorm:"column:created_at" json:"created_at"`
	CreatedBy         int     `gorm:"column:created_by" json:"created_by"`
	UpdatedAt         string  `gorm:"column:updated_at" json:"updated_at"`
	UpdatedBy         int     `gorm:"column:updated_by" json:"updated_by"`
	ProductCode       string  `gorm:"column:product_code" json:"product_code"`
	LifecycleStatus   string  `gorm:"column:lifecycle_status" json:"lifecycle_status"`
	CurrentRevisionID *string `gorm:"column:current_revision_id" json:"current_revision_id"`
	ArchivedAt        *string `gorm:"column:archived_at" json:"archived_at"`
}

func (Product) TableName() string { return "products" }

type Revision struct {
	ID                string  `gorm:"column:id;primaryKey" json:"id"`
	CreatedAt         string  `gorm:"column:created_at" json:"created_at"`
	CreatedBy         int     `gorm:"column:created_by" json:"created_by"`
	UpdatedAt         string  `gorm:"column:updated_at" json:"updated_at"`
	UpdatedBy         int     `gorm:"column:updated_by" json:"updated_by"`
	ProductID         string  `gorm:"column:product_id" json:"product_id"`
	RevisionNumber    int64   `gorm:"column:revision_number" json:"revision_number"`
	RevisionStatus    string  `gorm:"column:revision_status" json:"revision_status"`
	SourceRevisionID  *string `gorm:"column:source_revision_id" json:"source_revision_id"`
	SourceLanguage    string  `gorm:"column:source_language" json:"source_language"`
	CategoryCode      *string `gorm:"column:category_code" json:"category_code"`
	OriginCountryCode *string `gorm:"column:origin_country_code" json:"origin_country_code"`
	PackageQuantity   *string `gorm:"column:package_quantity" json:"package_quantity"`
	PackageUnit       *string `gorm:"column:package_unit" json:"package_unit"`
	PackageTypeCode   *string `gorm:"column:package_type_code" json:"package_type_code"`
	ShelfLifeDays     *int64  `gorm:"column:shelf_life_days" json:"shelf_life_days"`
	ProcessSteps      string  `gorm:"column:process_steps" json:"-"`
	SealedAt          *string `gorm:"column:sealed_at" json:"sealed_at"`
	SealedBy          *int    `gorm:"column:sealed_by" json:"sealed_by"`
	ContentHash       *string `gorm:"column:content_hash" json:"content_hash"`
	InternalNote      *string `gorm:"column:internal_note" json:"internal_note"`
}

func (Revision) TableName() string { return "product_revisions" }

type Translation struct {
	ID                     string  `gorm:"column:id;primaryKey" json:"id"`
	CreatedAt              string  `gorm:"column:created_at" json:"created_at"`
	CreatedBy              int     `gorm:"column:created_by" json:"created_by"`
	UpdatedAt              string  `gorm:"column:updated_at" json:"updated_at"`
	UpdatedBy              int     `gorm:"column:updated_by" json:"updated_by"`
	ProductRevisionID      string  `gorm:"column:product_revision_id" json:"product_revision_id"`
	LanguageCode           string  `gorm:"column:language_code" json:"language_code"`
	TranslationStatus      string  `gorm:"column:translation_status" json:"translation_status"`
	ProductName            string  `gorm:"column:product_name" json:"product_name"`
	ShortDescription       *string `gorm:"column:short_description" json:"short_description"`
	RawMaterialName        *string `gorm:"column:raw_material_name" json:"raw_material_name"`
	RawMaterialType        *string `gorm:"column:raw_material_type" json:"raw_material_type"`
	RawMaterialOrigin      *string `gorm:"column:raw_material_origin" json:"raw_material_origin"`
	RawMaterialDescription *string `gorm:"column:raw_material_description" json:"raw_material_description"`
	PackageDescription     *string `gorm:"column:package_description" json:"package_description"`
	InnerMaterial          *string `gorm:"column:inner_material" json:"inner_material"`
	StorageConditions      *string `gorm:"column:storage_conditions" json:"storage_conditions"`
	ShelfLifeDescription   *string `gorm:"column:shelf_life_description" json:"shelf_life_description"`
	ManufacturerName       *string `gorm:"column:manufacturer_name" json:"manufacturer_name"`
	ManufacturerAddress    *string `gorm:"column:manufacturer_address" json:"manufacturer_address"`
	ProcessLabels          string  `gorm:"column:process_labels" json:"-"`
}

func (Translation) TableName() string { return "product_revision_translations" }
