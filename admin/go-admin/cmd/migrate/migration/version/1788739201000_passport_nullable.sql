DROP TABLE "products";
DROP TABLE "product_revisions";
DROP TABLE "product_revision_translations";
DROP TABLE "batches";
DROP TABLE "batch_overrides";
DROP TABLE "batch_override_translations";
DROP TABLE "inspection_items";
DROP TABLE "inspection_item_translations";
DROP TABLE "certifications";
DROP TABLE "certification_translations";
DROP TABLE "certification_links";
DROP TABLE "media_assets";
DROP TABLE "asset_links";
DROP TABLE "custom_sections";
DROP TABLE "custom_section_translations";
DROP TABLE "passport_revisions";
DROP TABLE "published_assets";
DROP TABLE "publish_records";
DROP TABLE "passport_audit_events";
-- T4 minimal business schema, generated from approved T3 field dictionary.
-- No seed data, CRUD, or publish engine. Run via versioned Go Admin migration.


CREATE TABLE "products" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "updated_by" INTEGER NOT NULL,
  "product_code" TEXT NOT NULL CHECK (length("product_code") BETWEEN 1 AND 64 AND "product_code" NOT GLOB '*[^A-Za-z0-9_-]*') CHECK ("product_code"=upper("product_code")),
  "lifecycle_status" TEXT NOT NULL DEFAULT 'active' CHECK ("lifecycle_status" IN ('active','disabled','archived')),
  "current_revision_id" TEXT CHECK (length("current_revision_id")=36 AND substr("current_revision_id",15,1)='4' AND substr("current_revision_id",20,1) IN ('8','9','a','b') AND "current_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "archived_at" TEXT CHECK ("archived_at" IS NULL OR (length("archived_at")=24 AND substr("archived_at",24,1)='Z' AND julianday("archived_at") IS NOT NULL)),
  FOREIGN KEY ("id","current_revision_id") REFERENCES "product_revisions" ("product_id","id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("current_revision_id") REFERENCES "product_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("updated_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "product_revisions" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "updated_by" INTEGER NOT NULL,
  "product_id" TEXT NOT NULL CHECK (length("product_id")=36 AND substr("product_id",15,1)='4' AND substr("product_id",20,1) IN ('8','9','a','b') AND "product_id" NOT GLOB '*[^0-9a-f-]*'),
  "revision_number" INTEGER NOT NULL CHECK ("revision_number">0),
  "revision_status" TEXT NOT NULL DEFAULT 'draft' CHECK ("revision_status" IN ('draft','sealed','abandoned')),
  "source_revision_id" TEXT CHECK (length("source_revision_id")=36 AND substr("source_revision_id",15,1)='4' AND substr("source_revision_id",20,1) IN ('8','9','a','b') AND "source_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "source_language" TEXT NOT NULL DEFAULT 'en' CHECK ("source_language" IN ('en','zh-CN','es','ar','fr','de')),
  "category_code" TEXT CHECK (length("category_code") BETWEEN 1 AND 64 AND "category_code" NOT GLOB '*[^A-Za-z0-9_-]*'),
  "origin_country_code" TEXT CHECK (length("origin_country_code")<=2),
  "package_quantity" TEXT,
  "package_unit" TEXT CHECK (length("package_unit")<=32),
  "package_type_code" TEXT CHECK (length("package_type_code") BETWEEN 1 AND 64 AND "package_type_code" NOT GLOB '*[^A-Za-z0-9_-]*'),
  "shelf_life_days" INTEGER CHECK ("shelf_life_days">=0),
  "process_steps" TEXT NOT NULL DEFAULT '[]' CHECK (json_valid("process_steps")),
  "sealed_at" TEXT CHECK ("sealed_at" IS NULL OR (length("sealed_at")=24 AND substr("sealed_at",24,1)='Z' AND julianday("sealed_at") IS NOT NULL)),
  "sealed_by" INTEGER,
  "content_hash" TEXT CHECK (length("content_hash")=64 AND "content_hash" NOT GLOB '*[^0-9a-f]*'),
  "internal_note" TEXT CHECK (length("internal_note")<=2000),
  CHECK (revision_status!='sealed' OR (sealed_at IS NOT NULL AND sealed_by IS NOT NULL AND content_hash IS NOT NULL)),
  FOREIGN KEY ("product_id") REFERENCES "products" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("source_revision_id") REFERENCES "product_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("updated_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("sealed_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "product_revision_translations" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "updated_by" INTEGER NOT NULL,
  "product_revision_id" TEXT NOT NULL CHECK (length("product_revision_id")=36 AND substr("product_revision_id",15,1)='4' AND substr("product_revision_id",20,1) IN ('8','9','a','b') AND "product_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "language_code" TEXT NOT NULL CHECK ("language_code" IN ('en','zh-CN','es','ar','fr','de')),
  "translation_status" TEXT NOT NULL DEFAULT 'draft' CHECK ("translation_status" IN ('draft','approved')),
  "product_name" TEXT NOT NULL CHECK (length("product_name")<=200),
  "short_description" TEXT CHECK (length("short_description")<=4000),
  "raw_material_name" TEXT CHECK (length("raw_material_name")<=4000),
  "raw_material_type" TEXT CHECK (length("raw_material_type")<=4000),
  "raw_material_origin" TEXT CHECK (length("raw_material_origin")<=4000),
  "raw_material_description" TEXT CHECK (length("raw_material_description")<=4000),
  "package_description" TEXT CHECK (length("package_description")<=4000),
  "inner_material" TEXT CHECK (length("inner_material")<=4000),
  "storage_conditions" TEXT CHECK (length("storage_conditions")<=4000),
  "shelf_life_description" TEXT CHECK (length("shelf_life_description")<=4000),
  "manufacturer_name" TEXT CHECK (length("manufacturer_name")<=4000),
  "manufacturer_address" TEXT CHECK (length("manufacturer_address")<=4000),
  "process_labels" TEXT NOT NULL DEFAULT '{}' CHECK (json_valid("process_labels")),
  FOREIGN KEY ("product_revision_id") REFERENCES "product_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("updated_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "batches" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "updated_by" INTEGER NOT NULL,
  "batch_code" TEXT NOT NULL CHECK (length("batch_code") BETWEEN 1 AND 64 AND "batch_code" NOT GLOB '*[^A-Za-z0-9_-]*') CHECK ("batch_code"=upper("batch_code")),
  "product_id" TEXT NOT NULL CHECK (length("product_id")=36 AND substr("product_id",15,1)='4' AND substr("product_id",20,1) IN ('8','9','a','b') AND "product_id" NOT GLOB '*[^0-9a-f-]*'),
  "base_product_revision_id" TEXT NOT NULL CHECK (length("base_product_revision_id")=36 AND substr("base_product_revision_id",15,1)='4' AND substr("base_product_revision_id",20,1) IN ('8','9','a','b') AND "base_product_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "record_type" TEXT NOT NULL DEFAULT 'test' CHECK ("record_type" IN ('test','commercial')),
  "production_date" TEXT CHECK (length("production_date")=10 AND "production_date" GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date("production_date") IS "production_date"),
  "expiry_date" TEXT CHECK (length("expiry_date")=10 AND "expiry_date" GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date("expiry_date") IS "expiry_date"),
  "quality_status" TEXT NOT NULL DEFAULT 'pending' CHECK ("quality_status" IN ('pending','released','hold','rejected')),
  "workflow_status" TEXT NOT NULL DEFAULT 'draft' CHECK ("workflow_status" IN ('draft','pending_review','published','archived')),
  "edit_version" INTEGER NOT NULL DEFAULT 1 CHECK ("edit_version">0),
  "submitted_edit_version" INTEGER CHECK ("submitted_edit_version">=0),
  "submitted_content_hash" TEXT CHECK (length("submitted_content_hash")=64 AND "submitted_content_hash" NOT GLOB '*[^0-9a-f]*'),
  "submitted_input" TEXT CHECK (json_valid("submitted_input")),
  "submitted_schema_version" TEXT CHECK (length("submitted_schema_version")<=16),
  "submitted_builder_version" TEXT CHECK (length("submitted_builder_version")<=64),
  "submitted_preview_hash" TEXT CHECK (length("submitted_preview_hash")=64 AND "submitted_preview_hash" NOT GLOB '*[^0-9a-f]*'),
  "submitted_at" TEXT CHECK ("submitted_at" IS NULL OR (length("submitted_at")=24 AND substr("submitted_at",24,1)='Z' AND julianday("submitted_at") IS NOT NULL)),
  "submitted_by" INTEGER,
  "reviewed_at" TEXT CHECK ("reviewed_at" IS NULL OR (length("reviewed_at")=24 AND substr("reviewed_at",24,1)='Z' AND julianday("reviewed_at") IS NOT NULL)),
  "reviewed_by" INTEGER,
  "rejection_reason" TEXT CHECK (length("rejection_reason")<=2000),
  "current_passport_revision_id" TEXT CHECK (length("current_passport_revision_id")=36 AND substr("current_passport_revision_id",15,1)='4' AND substr("current_passport_revision_id",20,1) IN ('8','9','a','b') AND "current_passport_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "active_publish_record_id" TEXT CHECK (length("active_publish_record_id")=36 AND substr("active_publish_record_id",15,1)='4' AND substr("active_publish_record_id",20,1) IN ('8','9','a','b') AND "active_publish_record_id" NOT GLOB '*[^0-9a-f-]*'),
  "next_version_number" INTEGER NOT NULL DEFAULT 1 CHECK ("next_version_number">0),
  "cloned_from_batch_id" TEXT CHECK (length("cloned_from_batch_id")=36 AND substr("cloned_from_batch_id",15,1)='4' AND substr("cloned_from_batch_id",20,1) IN ('8','9','a','b') AND "cloned_from_batch_id" NOT GLOB '*[^0-9a-f-]*'),
  "archived_at" TEXT CHECK ("archived_at" IS NULL OR (length("archived_at")=24 AND substr("archived_at",24,1)='Z' AND julianday("archived_at") IS NOT NULL)),
  "archived_by" INTEGER,
  "internal_note" TEXT CHECK (length("internal_note")<=4000),
  FOREIGN KEY ("product_id","base_product_revision_id") REFERENCES "product_revisions" ("product_id","id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("id","current_passport_revision_id") REFERENCES "passport_revisions" ("batch_id","id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("id","active_publish_record_id") REFERENCES "publish_records" ("batch_id","id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  CHECK (expiry_date IS NULL OR production_date IS NULL OR expiry_date>=production_date),
  CHECK (workflow_status!='published' OR current_passport_revision_id IS NOT NULL),
  FOREIGN KEY ("product_id") REFERENCES "products" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("base_product_revision_id") REFERENCES "product_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("current_passport_revision_id") REFERENCES "passport_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("active_publish_record_id") REFERENCES "publish_records" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("cloned_from_batch_id") REFERENCES "batches" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("updated_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("submitted_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("reviewed_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("archived_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "batch_overrides" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "updated_by" INTEGER NOT NULL,
  "batch_id" TEXT NOT NULL CHECK (length("batch_id")=36 AND substr("batch_id",15,1)='4' AND substr("batch_id",20,1) IN ('8','9','a','b') AND "batch_id" NOT GLOB '*[^0-9a-f-]*'),
  "field_key" TEXT NOT NULL,
  "value_kind" TEXT NOT NULL CHECK ("value_kind" IN ('text','decimal','integer','json','asset')),
  "operation" TEXT NOT NULL DEFAULT 'set' CHECK ("operation" IN ('set','clear')),
  "value_text" TEXT CHECK (length("value_text")<=4000),
  "value_integer" INTEGER CHECK ("value_integer">=0),
  "value_json" TEXT CHECK (json_valid("value_json")),
  "value_media_asset_id" TEXT CHECK (length("value_media_asset_id")=36 AND substr("value_media_asset_id",15,1)='4' AND substr("value_media_asset_id",20,1) IN ('8','9','a','b') AND "value_media_asset_id" NOT GLOB '*[^0-9a-f-]*'),
  "public_asset_label" TEXT CHECK (length("public_asset_label")<=200),
  "source_language" TEXT NOT NULL DEFAULT 'en' CHECK ("source_language" IN ('en','zh-CN','es','ar','fr','de')),
  CHECK ((field_key='raw_material_name' AND value_kind='text') OR (field_key='raw_material_type' AND value_kind='text') OR (field_key='raw_material_origin' AND value_kind='text') OR (field_key='raw_material_description' AND value_kind='text') OR (field_key='package_description' AND value_kind='text') OR (field_key='inner_material' AND value_kind='text') OR (field_key='package_unit' AND value_kind='text') OR (field_key='package_type_code' AND value_kind='text') OR (field_key='storage_conditions' AND value_kind='text') OR (field_key='shelf_life_description' AND value_kind='text') OR (field_key='package_quantity' AND value_kind='decimal') OR (field_key='shelf_life_days' AND value_kind='integer') OR (field_key='process' AND value_kind='json') OR (field_key='product_image_asset' AND value_kind='asset')),
  CHECK ((operation='clear' AND value_text IS NULL AND value_integer IS NULL AND value_json IS NULL AND value_media_asset_id IS NULL AND public_asset_label IS NULL) OR (operation='set' AND ((value_kind IN ('text','decimal') AND value_text IS NOT NULL AND value_integer IS NULL AND value_json IS NULL AND value_media_asset_id IS NULL AND public_asset_label IS NULL) OR (value_kind='integer' AND value_integer IS NOT NULL AND value_text IS NULL AND value_json IS NULL AND value_media_asset_id IS NULL AND public_asset_label IS NULL) OR (value_kind='json' AND value_json IS NOT NULL AND value_text IS NULL AND value_integer IS NULL AND value_media_asset_id IS NULL AND public_asset_label IS NULL) OR (value_kind='asset' AND value_media_asset_id IS NOT NULL AND public_asset_label IS NOT NULL AND value_text IS NULL AND value_integer IS NULL AND value_json IS NULL)))),
  FOREIGN KEY ("batch_id") REFERENCES "batches" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("value_media_asset_id") REFERENCES "media_assets" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("updated_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "batch_override_translations" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "updated_by" INTEGER NOT NULL,
  "batch_override_id" TEXT NOT NULL CHECK (length("batch_override_id")=36 AND substr("batch_override_id",15,1)='4' AND substr("batch_override_id",20,1) IN ('8','9','a','b') AND "batch_override_id" NOT GLOB '*[^0-9a-f-]*'),
  "language_code" TEXT NOT NULL CHECK ("language_code" IN ('en','zh-CN','es','ar','fr','de')),
  "translation_status" TEXT NOT NULL DEFAULT 'draft' CHECK ("translation_status" IN ('draft','approved')),
  "translated_value" TEXT CHECK (length("translated_value")<=4000),
  "translated_process" TEXT CHECK (json_valid("translated_process")),
  CHECK ((translated_value IS NOT NULL)+(translated_process IS NOT NULL)=1),
  FOREIGN KEY ("batch_override_id") REFERENCES "batch_overrides" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("updated_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "inspection_items" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "updated_by" INTEGER NOT NULL,
  "batch_id" TEXT NOT NULL CHECK (length("batch_id")=36 AND substr("batch_id",15,1)='4' AND substr("batch_id",20,1) IN ('8','9','a','b') AND "batch_id" NOT GLOB '*[^0-9a-f-]*'),
  "item_code" TEXT NOT NULL CHECK (length("item_code") BETWEEN 1 AND 64 AND "item_code" NOT GLOB '*[^A-Za-z0-9_-]*'),
  "name" TEXT NOT NULL CHECK (length("name")<=200),
  "source_language" TEXT NOT NULL DEFAULT 'en' CHECK ("source_language" IN ('en','zh-CN','es','ar','fr','de')),
  "value_type" TEXT NOT NULL DEFAULT 'text' CHECK ("value_type" IN ('decimal','integer','text','none')),
  "numeric_value" TEXT,
  "text_value" TEXT CHECK (length("text_value")<=2000),
  "unit" TEXT CHECK (length("unit")<=32),
  "standard_value" TEXT,
  "min_limit" TEXT,
  "max_limit" TEXT,
  "min_inclusive" INTEGER NOT NULL DEFAULT 1 CHECK ("min_inclusive" IN(0,1)),
  "max_inclusive" INTEGER NOT NULL DEFAULT 1 CHECK ("max_inclusive" IN(0,1)),
  "specification" TEXT CHECK (length("specification")<=2000),
  "test_method" TEXT CHECK (length("test_method")<=500),
  "judgement" TEXT NOT NULL DEFAULT 'not_tested' CHECK ("judgement" IN ('pass','fail','not_tested','not_applicable','pending','informational')),
  "sort_order" INTEGER NOT NULL DEFAULT 0 CHECK ("sort_order">=0),
  "internal_note" TEXT CHECK (length("internal_note")<=2000),
  "is_public" INTEGER NOT NULL DEFAULT 0 CHECK ("is_public" IN(0,1)),
  "tested_on" TEXT CHECK (length("tested_on")=10 AND "tested_on" GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date("tested_on") IS "tested_on"),
  CHECK ((value_type IN ('decimal','integer') AND text_value IS NULL) OR (value_type='text' AND numeric_value IS NULL) OR (value_type='none' AND numeric_value IS NULL AND text_value IS NULL)),
  CHECK (judgement NOT IN ('not_tested','not_applicable') OR (numeric_value IS NULL AND text_value IS NULL)),
  CHECK (judgement NOT IN ('pass','fail','informational') OR numeric_value IS NOT NULL OR COALESCE(length(text_value),0)>0),
  FOREIGN KEY ("batch_id") REFERENCES "batches" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("updated_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "inspection_item_translations" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "updated_by" INTEGER NOT NULL,
  "inspection_item_id" TEXT NOT NULL CHECK (length("inspection_item_id")=36 AND substr("inspection_item_id",15,1)='4' AND substr("inspection_item_id",20,1) IN ('8','9','a','b') AND "inspection_item_id" NOT GLOB '*[^0-9a-f-]*'),
  "language_code" TEXT NOT NULL CHECK ("language_code" IN ('en','zh-CN','es','ar','fr','de')),
  "translation_status" TEXT NOT NULL DEFAULT 'draft' CHECK ("translation_status" IN ('draft','approved')),
  "display_name" TEXT NOT NULL CHECK (length("display_name")<=200),
  "specification" TEXT CHECK (length("specification")<=2000),
  "test_method" TEXT CHECK (length("test_method")<=500),
  "result_display_text" TEXT CHECK (length("result_display_text")<=2000),
  FOREIGN KEY ("inspection_item_id") REFERENCES "inspection_items" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("updated_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "certifications" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "family_key" TEXT NOT NULL CHECK (length("family_key")=36 AND substr("family_key",15,1)='4' AND substr("family_key",20,1) IN ('8','9','a','b') AND "family_key" NOT GLOB '*[^0-9a-f-]*'),
  "revision_number" INTEGER NOT NULL DEFAULT 1 CHECK ("revision_number">0),
  "supersedes_id" TEXT CHECK (length("supersedes_id")=36 AND substr("supersedes_id",15,1)='4' AND substr("supersedes_id",20,1) IN ('8','9','a','b') AND "supersedes_id" NOT GLOB '*[^0-9a-f-]*'),
  "name" TEXT NOT NULL CHECK (length("name")<=200),
  "source_language" TEXT NOT NULL DEFAULT 'en' CHECK ("source_language" IN ('en','zh-CN','es','ar','fr','de')),
  "certification_type" TEXT NOT NULL DEFAULT 'OTHER' CHECK (length("certification_type") BETWEEN 1 AND 64 AND "certification_type" NOT GLOB '*[^A-Za-z0-9_-]*'),
  "certificate_number" TEXT CHECK (length("certificate_number")<=200),
  "issuer" TEXT CHECK (length("issuer")<=500),
  "valid_from" TEXT CHECK (length("valid_from")=10 AND "valid_from" GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date("valid_from") IS "valid_from"),
  "valid_until" TEXT CHECK (length("valid_until")=10 AND "valid_until" GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date("valid_until") IS "valid_until"),
  "status" TEXT NOT NULL DEFAULT 'unverified' CHECK ("status" IN ('unverified','valid','expired','suspended','revoked')),
  "is_public" INTEGER NOT NULL DEFAULT 0 CHECK ("is_public" IN(0,1)),
  "internal_note" TEXT CHECK (length("internal_note")<=4000),
  "sealed_at" TEXT CHECK ("sealed_at" IS NULL OR (length("sealed_at")=24 AND substr("sealed_at",24,1)='Z' AND julianday("sealed_at") IS NOT NULL)),
  CHECK (valid_from IS NULL OR valid_until IS NULL OR valid_from<=valid_until),
  FOREIGN KEY ("supersedes_id") REFERENCES "certifications" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "certification_translations" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "updated_by" INTEGER NOT NULL,
  "certification_id" TEXT NOT NULL CHECK (length("certification_id")=36 AND substr("certification_id",15,1)='4' AND substr("certification_id",20,1) IN ('8','9','a','b') AND "certification_id" NOT GLOB '*[^0-9a-f-]*'),
  "language_code" TEXT NOT NULL CHECK ("language_code" IN ('en','zh-CN','es','ar','fr','de')),
  "translation_status" TEXT NOT NULL DEFAULT 'draft' CHECK ("translation_status" IN ('draft','approved')),
  "name" TEXT NOT NULL CHECK (length("name")<=200),
  "issuer_display_name" TEXT CHECK (length("issuer_display_name")<=500),
  FOREIGN KEY ("certification_id") REFERENCES "certifications" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("updated_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "certification_links" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "updated_by" INTEGER NOT NULL,
  "product_revision_id" TEXT CHECK (length("product_revision_id")=36 AND substr("product_revision_id",15,1)='4' AND substr("product_revision_id",20,1) IN ('8','9','a','b') AND "product_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "batch_id" TEXT CHECK (length("batch_id")=36 AND substr("batch_id",15,1)='4' AND substr("batch_id",20,1) IN ('8','9','a','b') AND "batch_id" NOT GLOB '*[^0-9a-f-]*'),
  "link_key" TEXT NOT NULL CHECK (length("link_key") BETWEEN 1 AND 64 AND "link_key" NOT GLOB '*[^A-Za-z0-9_-]*'),
  "operation" TEXT NOT NULL DEFAULT 'include' CHECK ("operation" IN ('include','exclude')),
  "certification_id" TEXT CHECK (length("certification_id")=36 AND substr("certification_id",15,1)='4' AND substr("certification_id",20,1) IN ('8','9','a','b') AND "certification_id" NOT GLOB '*[^0-9a-f-]*'),
  "sort_order" INTEGER NOT NULL DEFAULT 0 CHECK ("sort_order">=0),
  "is_public" INTEGER NOT NULL DEFAULT 0 CHECK ("is_public" IN(0,1)),
  CHECK ((product_revision_id IS NOT NULL)+(batch_id IS NOT NULL)=1),
  CHECK ((operation='include' AND certification_id IS NOT NULL) OR (operation='exclude' AND batch_id IS NOT NULL AND certification_id IS NULL)),
  FOREIGN KEY ("product_revision_id") REFERENCES "product_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("batch_id") REFERENCES "batches" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("certification_id") REFERENCES "certifications" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("updated_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "media_assets" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "storage_key" TEXT NOT NULL CHECK (length("storage_key")>0 AND substr("storage_key",1,1)!='/' AND instr("storage_key",'..')=0 AND instr("storage_key",char(92))=0 AND instr("storage_key",':')=0),
  "original_filename" TEXT NOT NULL CHECK (length("original_filename")<=255),
  "mime_type" TEXT NOT NULL CHECK ("mime_type" IN ('image/jpeg','image/png','image/webp','application/pdf')),
  "file_size" INTEGER NOT NULL CHECK ("file_size">0),
  "sha256" TEXT NOT NULL CHECK (length("sha256")=64 AND "sha256" NOT GLOB '*[^0-9a-f]*'),
  "availability_status" TEXT NOT NULL DEFAULT 'ready' CHECK ("availability_status" IN ('ready','disabled','purged')),
  "is_public_eligible" INTEGER NOT NULL DEFAULT 0 CHECK ("is_public_eligible" IN(0,1)),
  "replaces_media_asset_id" TEXT CHECK (length("replaces_media_asset_id")=36 AND substr("replaces_media_asset_id",15,1)='4' AND substr("replaces_media_asset_id",20,1) IN ('8','9','a','b') AND "replaces_media_asset_id" NOT GLOB '*[^0-9a-f-]*'),
  "internal_note" TEXT CHECK (length("internal_note")<=2000),
  "purged_at" TEXT CHECK ("purged_at" IS NULL OR (length("purged_at")=24 AND substr("purged_at",24,1)='Z' AND julianday("purged_at") IS NOT NULL)),
  FOREIGN KEY ("replaces_media_asset_id") REFERENCES "media_assets" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "asset_links" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "updated_by" INTEGER NOT NULL,
  "product_revision_id" TEXT CHECK (length("product_revision_id")=36 AND substr("product_revision_id",15,1)='4' AND substr("product_revision_id",20,1) IN ('8','9','a','b') AND "product_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "certification_id" TEXT CHECK (length("certification_id")=36 AND substr("certification_id",15,1)='4' AND substr("certification_id",20,1) IN ('8','9','a','b') AND "certification_id" NOT GLOB '*[^0-9a-f-]*'),
  "inspection_item_id" TEXT CHECK (length("inspection_item_id")=36 AND substr("inspection_item_id",15,1)='4' AND substr("inspection_item_id",20,1) IN ('8','9','a','b') AND "inspection_item_id" NOT GLOB '*[^0-9a-f-]*'),
  "custom_section_id" TEXT CHECK (length("custom_section_id")=36 AND substr("custom_section_id",15,1)='4' AND substr("custom_section_id",20,1) IN ('8','9','a','b') AND "custom_section_id" NOT GLOB '*[^0-9a-f-]*'),
  "media_asset_id" TEXT NOT NULL CHECK (length("media_asset_id")=36 AND substr("media_asset_id",15,1)='4' AND substr("media_asset_id",20,1) IN ('8','9','a','b') AND "media_asset_id" NOT GLOB '*[^0-9a-f-]*'),
  "asset_key" TEXT NOT NULL CHECK (length("asset_key") BETWEEN 1 AND 64 AND "asset_key" NOT GLOB '*[^A-Za-z0-9_-]*'),
  "asset_role" TEXT NOT NULL DEFAULT 'attachment' CHECK ("asset_role" IN ('product_image','certificate','inspection_report','section_image','attachment')),
  "public_label" TEXT NOT NULL CHECK (length("public_label")<=200),
  "sort_order" INTEGER NOT NULL DEFAULT 0 CHECK ("sort_order">=0),
  "is_public" INTEGER NOT NULL DEFAULT 0 CHECK ("is_public" IN(0,1)),
  CHECK ((product_revision_id IS NOT NULL)+(certification_id IS NOT NULL)+(inspection_item_id IS NOT NULL)+(custom_section_id IS NOT NULL)=1),
  FOREIGN KEY ("product_revision_id") REFERENCES "product_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("certification_id") REFERENCES "certifications" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("inspection_item_id") REFERENCES "inspection_items" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("custom_section_id") REFERENCES "custom_sections" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("media_asset_id") REFERENCES "media_assets" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("updated_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "custom_sections" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "updated_by" INTEGER NOT NULL,
  "product_revision_id" TEXT CHECK (length("product_revision_id")=36 AND substr("product_revision_id",15,1)='4' AND substr("product_revision_id",20,1) IN ('8','9','a','b') AND "product_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "batch_id" TEXT CHECK (length("batch_id")=36 AND substr("batch_id",15,1)='4' AND substr("batch_id",20,1) IN ('8','9','a','b') AND "batch_id" NOT GLOB '*[^0-9a-f-]*'),
  "section_key" TEXT NOT NULL CHECK (length("section_key") BETWEEN 1 AND 64 AND "section_key" NOT GLOB '*[^A-Za-z0-9_-]*'),
  "operation" TEXT NOT NULL DEFAULT 'add' CHECK ("operation" IN ('add','replace','hide','inherit')),
  "section_type" TEXT NOT NULL DEFAULT 'text' CHECK ("section_type" IN ('text','key_value','table','asset_gallery')),
  "source_language" TEXT NOT NULL DEFAULT 'en' CHECK ("source_language" IN ('en','zh-CN','es','ar','fr','de')),
  "sort_order" INTEGER CHECK ("sort_order">=0),
  "is_visible" INTEGER NOT NULL DEFAULT 1 CHECK ("is_visible" IN(0,1)),
  "is_public" INTEGER NOT NULL DEFAULT 0 CHECK ("is_public" IN(0,1)),
  "status" TEXT NOT NULL DEFAULT 'draft' CHECK ("status" IN ('draft','ready','disabled')),
  CHECK ((product_revision_id IS NOT NULL)+(batch_id IS NOT NULL)=1),
  CHECK (product_revision_id IS NULL OR operation='add'),
  CHECK (operation NOT IN ('add','replace') OR sort_order IS NOT NULL),
  CHECK (operation!='hide' OR is_visible=0),
  FOREIGN KEY ("product_revision_id") REFERENCES "product_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("batch_id") REFERENCES "batches" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("updated_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "custom_section_translations" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "updated_by" INTEGER NOT NULL,
  "custom_section_id" TEXT NOT NULL CHECK (length("custom_section_id")=36 AND substr("custom_section_id",15,1)='4' AND substr("custom_section_id",20,1) IN ('8','9','a','b') AND "custom_section_id" NOT GLOB '*[^0-9a-f-]*'),
  "language_code" TEXT NOT NULL CHECK ("language_code" IN ('en','zh-CN','es','ar','fr','de')),
  "translation_status" TEXT NOT NULL DEFAULT 'draft' CHECK ("translation_status" IN ('draft','approved')),
  "title" TEXT NOT NULL CHECK (length("title")<=200),
  "content" TEXT NOT NULL CHECK (json_valid("content")),
  FOREIGN KEY ("custom_section_id") REFERENCES "custom_sections" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("updated_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "passport_revisions" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "batch_id" TEXT NOT NULL CHECK (length("batch_id")=36 AND substr("batch_id",15,1)='4' AND substr("batch_id",20,1) IN ('8','9','a','b') AND "batch_id" NOT GLOB '*[^0-9a-f-]*'),
  "version_number" INTEGER NOT NULL CHECK ("version_number">0),
  "base_product_revision_id" TEXT NOT NULL CHECK (length("base_product_revision_id")=36 AND substr("base_product_revision_id",15,1)='4' AND substr("base_product_revision_id",20,1) IN ('8','9','a','b') AND "base_product_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "source_revision_id" TEXT CHECK (length("source_revision_id")=36 AND substr("source_revision_id",15,1)='4' AND substr("source_revision_id",20,1) IN ('8','9','a','b') AND "source_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "rollback_source_revision_id" TEXT CHECK (length("rollback_source_revision_id")=36 AND substr("rollback_source_revision_id",15,1)='4' AND substr("rollback_source_revision_id",20,1) IN ('8','9','a','b') AND "rollback_source_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "source_edit_version" INTEGER CHECK ("source_edit_version">=0),
  "source_content_hash" TEXT NOT NULL CHECK (length("source_content_hash")=64 AND "source_content_hash" NOT GLOB '*[^0-9a-f]*'),
  "frozen_input" TEXT NOT NULL CHECK (json_valid("frozen_input")),
  "schema_version" TEXT NOT NULL CHECK (length("schema_version")<=16),
  "builder_version" TEXT NOT NULL CHECK (length("builder_version")<=64),
  "payload" TEXT CHECK (json_valid("payload")),
  "payload_hash" TEXT CHECK (length("payload_hash")=64 AND "payload_hash" NOT GLOB '*[^0-9a-f]*'),
  "content_hash" TEXT CHECK (length("content_hash")=64 AND "content_hash" NOT GLOB '*[^0-9a-f]*'),
  "snapshot_path" TEXT CHECK (length("snapshot_path")>0 AND substr("snapshot_path",1,1)!='/' AND instr("snapshot_path",'..')=0 AND instr("snapshot_path",char(92))=0 AND instr("snapshot_path",':')=0),
  "asset_manifest_hash" TEXT CHECK (length("asset_manifest_hash")=64 AND "asset_manifest_hash" NOT GLOB '*[^0-9a-f]*'),
  "sealed_at" TEXT CHECK ("sealed_at" IS NULL OR (length("sealed_at")=24 AND substr("sealed_at",24,1)='Z' AND julianday("sealed_at") IS NOT NULL)),
  "published_at" TEXT CHECK ("published_at" IS NULL OR (length("published_at")=24 AND substr("published_at",24,1)='Z' AND julianday("published_at") IS NOT NULL)),
  "published_by" INTEGER NOT NULL,
  "reviewed_by" INTEGER NOT NULL,
  "reviewed_at" TEXT NOT NULL CHECK ("reviewed_at" IS NULL OR (length("reviewed_at")=24 AND substr("reviewed_at",24,1)='Z' AND julianday("reviewed_at") IS NOT NULL)),
  "release_identifier" TEXT NOT NULL CHECK (length("release_identifier")=36 AND substr("release_identifier",15,1)='4' AND substr("release_identifier",20,1) IN ('8','9','a','b') AND "release_identifier" NOT GLOB '*[^0-9a-f-]*'),
  FOREIGN KEY ("batch_id","base_product_revision_id") REFERENCES "batches" ("id","base_product_revision_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("batch_id","source_revision_id") REFERENCES "passport_revisions" ("batch_id","id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("batch_id","rollback_source_revision_id") REFERENCES "passport_revisions" ("batch_id","id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  CHECK (sealed_at IS NULL OR (payload IS NOT NULL AND payload_hash IS NOT NULL AND content_hash IS NOT NULL AND snapshot_path IS NOT NULL AND asset_manifest_hash IS NOT NULL)),
  CHECK (published_at IS NULL OR sealed_at IS NOT NULL),
  FOREIGN KEY ("batch_id") REFERENCES "batches" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("base_product_revision_id") REFERENCES "product_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("source_revision_id") REFERENCES "passport_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("rollback_source_revision_id") REFERENCES "passport_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("published_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("reviewed_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "published_assets" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "passport_revision_id" TEXT NOT NULL CHECK (length("passport_revision_id")=36 AND substr("passport_revision_id",15,1)='4' AND substr("passport_revision_id",20,1) IN ('8','9','a','b') AND "passport_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "source_media_asset_id" TEXT NOT NULL CHECK (length("source_media_asset_id")=36 AND substr("source_media_asset_id",15,1)='4' AND substr("source_media_asset_id",20,1) IN ('8','9','a','b') AND "source_media_asset_id" NOT GLOB '*[^0-9a-f-]*'),
  "asset_key" TEXT NOT NULL CHECK (length("asset_key") BETWEEN 1 AND 64 AND "asset_key" NOT GLOB '*[^A-Za-z0-9_-]*'),
  "asset_role" TEXT NOT NULL CHECK ("asset_role" IN ('product_image','certificate','inspection_report','section_image','attachment')),
  "original_filename" TEXT NOT NULL CHECK (length("original_filename")<=255),
  "public_label" TEXT NOT NULL CHECK (length("public_label")<=200),
  "published_filename" TEXT NOT NULL CHECK (length("published_filename")<=80),
  "mime_type" TEXT NOT NULL CHECK ("mime_type" IN ('image/jpeg','image/png','image/webp','application/pdf')),
  "file_size" INTEGER NOT NULL CHECK ("file_size">0),
  "sha256" TEXT NOT NULL CHECK (length("sha256")=64 AND "sha256" NOT GLOB '*[^0-9a-f]*'),
  "published_path" TEXT NOT NULL CHECK (length("published_path")>0 AND substr("published_path",1,1)!='/' AND instr("published_path",'..')=0 AND instr("published_path",char(92))=0 AND instr("published_path",':')=0),
  "transform_version" TEXT NOT NULL CHECK (length("transform_version")<=64),
  "source_asset_sha256" TEXT NOT NULL CHECK (length("source_asset_sha256")=64 AND "source_asset_sha256" NOT GLOB '*[^0-9a-f]*'),
  FOREIGN KEY ("passport_revision_id") REFERENCES "passport_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("source_media_asset_id") REFERENCES "media_assets" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "publish_records" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "created_by" INTEGER NOT NULL,
  "batch_id" TEXT NOT NULL CHECK (length("batch_id")=36 AND substr("batch_id",15,1)='4' AND substr("batch_id",20,1) IN ('8','9','a','b') AND "batch_id" NOT GLOB '*[^0-9a-f-]*'),
  "passport_revision_id" TEXT NOT NULL CHECK (length("passport_revision_id")=36 AND substr("passport_revision_id",15,1)='4' AND substr("passport_revision_id",20,1) IN ('8','9','a','b') AND "passport_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "operation_type" TEXT NOT NULL DEFAULT 'publish' CHECK ("operation_type" IN ('publish','rollback')),
  "publish_status" TEXT NOT NULL DEFAULT 'pending' CHECK ("publish_status" IN ('pending','building','validating','prepared','switching','published','failed','recovery_required')),
  "idempotency_key" TEXT NOT NULL CHECK (length("idempotency_key")<=128),
  "release_identifier" TEXT NOT NULL CHECK (length("release_identifier")=36 AND substr("release_identifier",15,1)='4' AND substr("release_identifier",20,1) IN ('8','9','a','b') AND "release_identifier" NOT GLOB '*[^0-9a-f-]*'),
  "expected_current_revision_id" TEXT CHECK (length("expected_current_revision_id")=36 AND substr("expected_current_revision_id",15,1)='4' AND substr("expected_current_revision_id",20,1) IN ('8','9','a','b') AND "expected_current_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "started_at" TEXT CHECK ("started_at" IS NULL OR (length("started_at")=24 AND substr("started_at",24,1)='Z' AND julianday("started_at") IS NOT NULL)),
  "completed_at" TEXT CHECK ("completed_at" IS NULL OR (length("completed_at")=24 AND substr("completed_at",24,1)='Z' AND julianday("completed_at") IS NOT NULL)),
  "switched_at" TEXT CHECK ("switched_at" IS NULL OR (length("switched_at")=24 AND substr("switched_at",24,1)='Z' AND julianday("switched_at") IS NOT NULL)),
  "updated_at" TEXT NOT NULL CHECK ("updated_at" IS NULL OR (length("updated_at")=24 AND substr("updated_at",24,1)='Z' AND julianday("updated_at") IS NOT NULL)),
  "attempt_count" INTEGER NOT NULL DEFAULT 0 CHECK ("attempt_count">=0),
  "asset_count" INTEGER CHECK ("asset_count">=0),
  "error_code" TEXT CHECK (length("error_code") BETWEEN 1 AND 64 AND "error_code" NOT GLOB '*[^A-Za-z0-9_-]*'),
  "error_message" TEXT CHECK (length("error_message")<=2000),
  "state_version" INTEGER NOT NULL DEFAULT 1 CHECK ("state_version">0),
  FOREIGN KEY ("batch_id","passport_revision_id") REFERENCES "passport_revisions" ("batch_id","id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("batch_id","expected_current_revision_id") REFERENCES "passport_revisions" ("batch_id","id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("passport_revision_id","release_identifier") REFERENCES "passport_revisions" ("id","release_identifier") ON UPDATE RESTRICT ON DELETE RESTRICT,
  CHECK (publish_status NOT IN ('published','failed') OR completed_at IS NOT NULL),
  FOREIGN KEY ("batch_id") REFERENCES "batches" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("passport_revision_id") REFERENCES "passport_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("expected_current_revision_id") REFERENCES "passport_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("created_by") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE "passport_audit_events" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "batch_id" TEXT CHECK (length("batch_id")=36 AND substr("batch_id",15,1)='4' AND substr("batch_id",20,1) IN ('8','9','a','b') AND "batch_id" NOT GLOB '*[^0-9a-f-]*'),
  "passport_revision_id" TEXT CHECK (length("passport_revision_id")=36 AND substr("passport_revision_id",15,1)='4' AND substr("passport_revision_id",20,1) IN ('8','9','a','b') AND "passport_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "actor_user_id" INTEGER NOT NULL,
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "event_type" TEXT NOT NULL CHECK ("event_type" IN ('batch_created','batch_cloned','batch_edited','override_set','override_cleared','review_submitted','review_approved','review_rejected','publish_requested','publish_succeeded','publish_failed','rollback_requested','rollback_succeeded','archived','media_replaced','inspection_changed','certification_linked','product_revision_sealed')),
  "entity_type" TEXT NOT NULL CHECK ("entity_type" IN ('products','product_revisions','product_revision_translations','batches','batch_overrides','batch_override_translations','inspection_items','inspection_item_translations','certifications','certification_translations','certification_links','media_assets','asset_links','custom_sections','custom_section_translations','passport_revisions','published_assets','publish_records','passport_audit_events')),
  "entity_id" TEXT NOT NULL CHECK (length("entity_id")=36 AND substr("entity_id",15,1)='4' AND substr("entity_id",20,1) IN ('8','9','a','b') AND "entity_id" NOT GLOB '*[^0-9a-f-]*'),
  "summary" TEXT NOT NULL CHECK (length("summary")<=500),
  "before_data" TEXT CHECK (json_valid("before_data")),
  "after_data" TEXT CHECK (json_valid("after_data")),
  "metadata" TEXT NOT NULL DEFAULT '{}' CHECK (json_valid("metadata")),
  FOREIGN KEY ("batch_id","passport_revision_id") REFERENCES "passport_revisions" ("batch_id","id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  CHECK (passport_revision_id IS NULL OR batch_id IS NOT NULL),
  FOREIGN KEY ("batch_id") REFERENCES "batches" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("passport_revision_id") REFERENCES "passport_revisions" ("id") ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY ("actor_user_id") REFERENCES "sys_user" ("user_id") ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE UNIQUE INDEX "uq_products_product_code" ON "products" ("product_code");

CREATE UNIQUE INDEX "uq_products_id_product_code" ON "products" ("id","product_code");

CREATE UNIQUE INDEX "uq_product_revisions_product_id_revision_number" ON "product_revisions" ("product_id","revision_number");

CREATE UNIQUE INDEX "uq_product_revisions_product_id_id" ON "product_revisions" ("product_id","id");

CREATE UNIQUE INDEX "uq_batches_batch_code" ON "batches" ("batch_code");

CREATE UNIQUE INDEX "uq_batches_id_product_id" ON "batches" ("id","product_id");

CREATE UNIQUE INDEX "uq_batches_id_base_product_revision_id" ON "batches" ("id","base_product_revision_id");

CREATE UNIQUE INDEX "uq_batch_overrides_batch_id_field_key" ON "batch_overrides" ("batch_id","field_key");

CREATE UNIQUE INDEX "uq_inspection_items_batch_id_item_code" ON "inspection_items" ("batch_id","item_code");

CREATE UNIQUE INDEX "uq_certifications_family_key_revision_number" ON "certifications" ("family_key","revision_number");

CREATE UNIQUE INDEX "uq_media_assets_storage_key" ON "media_assets" ("storage_key");

CREATE UNIQUE INDEX "uq_passport_revisions_batch_id_version_number" ON "passport_revisions" ("batch_id","version_number");

CREATE UNIQUE INDEX "uq_passport_revisions_batch_id_id" ON "passport_revisions" ("batch_id","id");

CREATE UNIQUE INDEX "uq_passport_revisions_release_identifier" ON "passport_revisions" ("release_identifier");

CREATE UNIQUE INDEX "uq_passport_revisions_id_release_identifier" ON "passport_revisions" ("id","release_identifier");

CREATE UNIQUE INDEX "uq_published_assets_passport_revision_id_asset_key" ON "published_assets" ("passport_revision_id","asset_key");

CREATE UNIQUE INDEX "uq_publish_records_passport_revision_id" ON "publish_records" ("passport_revision_id");

CREATE UNIQUE INDEX "uq_publish_records_batch_id_id" ON "publish_records" ("batch_id","id");

CREATE UNIQUE INDEX "uq_publish_records_batch_id_idempotency_key" ON "publish_records" ("batch_id","idempotency_key");

CREATE UNIQUE INDEX "uq_publish_records_release_identifier" ON "publish_records" ("release_identifier");

CREATE UNIQUE INDEX "uq_product_revision_translations_product_revision_id_language_code" ON "product_revision_translations" ("product_revision_id","language_code");

CREATE UNIQUE INDEX "uq_batch_override_translations_batch_override_id_language_code" ON "batch_override_translations" ("batch_override_id","language_code");

CREATE UNIQUE INDEX "uq_inspection_item_translations_inspection_item_id_language_code" ON "inspection_item_translations" ("inspection_item_id","language_code");

CREATE UNIQUE INDEX "uq_certification_translations_certification_id_language_code" ON "certification_translations" ("certification_id","language_code");

CREATE UNIQUE INDEX "uq_custom_section_translations_custom_section_id_language_code" ON "custom_section_translations" ("custom_section_id","language_code");

CREATE UNIQUE INDEX "uq_custom_sections_product_revision_id_section_key" ON "custom_sections" ("product_revision_id","section_key") WHERE "product_revision_id" IS NOT NULL;

CREATE UNIQUE INDEX "uq_custom_sections_batch_id_section_key" ON "custom_sections" ("batch_id","section_key") WHERE "batch_id" IS NOT NULL;

CREATE UNIQUE INDEX "uq_certification_links_product_revision_id_link_key" ON "certification_links" ("product_revision_id","link_key") WHERE "product_revision_id" IS NOT NULL;

CREATE UNIQUE INDEX "uq_certification_links_batch_id_link_key" ON "certification_links" ("batch_id","link_key") WHERE "batch_id" IS NOT NULL;

CREATE UNIQUE INDEX "uq_asset_links_product_revision_id_asset_key" ON "asset_links" ("product_revision_id","asset_key") WHERE "product_revision_id" IS NOT NULL;

CREATE UNIQUE INDEX "uq_asset_links_certification_id_asset_key" ON "asset_links" ("certification_id","asset_key") WHERE "certification_id" IS NOT NULL;

CREATE UNIQUE INDEX "uq_asset_links_inspection_item_id_asset_key" ON "asset_links" ("inspection_item_id","asset_key") WHERE "inspection_item_id" IS NOT NULL;

CREATE UNIQUE INDEX "uq_asset_links_custom_section_id_asset_key" ON "asset_links" ("custom_section_id","asset_key") WHERE "custom_section_id" IS NOT NULL;

CREATE UNIQUE INDEX "uq_asset_links_product_revision_id_asset_role" ON "asset_links" ("product_revision_id","asset_role") WHERE product_revision_id IS NOT NULL AND asset_role='product_image';

CREATE UNIQUE INDEX "uq_publish_records_batch_id" ON "publish_records" ("batch_id") WHERE publish_status IN ('pending','building','validating','prepared','switching','recovery_required');

CREATE INDEX "ix_products_current_revision_id" ON "products" ("current_revision_id");

CREATE INDEX "ix_products_created_by" ON "products" ("created_by");

CREATE INDEX "ix_products_updated_by" ON "products" ("updated_by");

CREATE INDEX "ix_product_revisions_product_id" ON "product_revisions" ("product_id");

CREATE INDEX "ix_product_revisions_source_revision_id" ON "product_revisions" ("source_revision_id");

CREATE INDEX "ix_product_revisions_created_by" ON "product_revisions" ("created_by");

CREATE INDEX "ix_product_revisions_updated_by" ON "product_revisions" ("updated_by");

CREATE INDEX "ix_product_revisions_sealed_by" ON "product_revisions" ("sealed_by");

CREATE INDEX "ix_product_revision_translations_product_revision_id" ON "product_revision_translations" ("product_revision_id");

CREATE INDEX "ix_product_revision_translations_created_by" ON "product_revision_translations" ("created_by");

CREATE INDEX "ix_product_revision_translations_updated_by" ON "product_revision_translations" ("updated_by");

CREATE INDEX "ix_batches_product_id" ON "batches" ("product_id");

CREATE INDEX "ix_batches_base_product_revision_id" ON "batches" ("base_product_revision_id");

CREATE INDEX "ix_batches_current_passport_revision_id" ON "batches" ("current_passport_revision_id");

CREATE INDEX "ix_batches_active_publish_record_id" ON "batches" ("active_publish_record_id");

CREATE INDEX "ix_batches_cloned_from_batch_id" ON "batches" ("cloned_from_batch_id");

CREATE INDEX "ix_batches_created_by" ON "batches" ("created_by");

CREATE INDEX "ix_batches_updated_by" ON "batches" ("updated_by");

CREATE INDEX "ix_batches_submitted_by" ON "batches" ("submitted_by");

CREATE INDEX "ix_batches_reviewed_by" ON "batches" ("reviewed_by");

CREATE INDEX "ix_batches_archived_by" ON "batches" ("archived_by");

CREATE INDEX "ix_batch_overrides_batch_id" ON "batch_overrides" ("batch_id");

CREATE INDEX "ix_batch_overrides_value_media_asset_id" ON "batch_overrides" ("value_media_asset_id");

CREATE INDEX "ix_batch_overrides_created_by" ON "batch_overrides" ("created_by");

CREATE INDEX "ix_batch_overrides_updated_by" ON "batch_overrides" ("updated_by");

CREATE INDEX "ix_batch_override_translations_batch_override_id" ON "batch_override_translations" ("batch_override_id");

CREATE INDEX "ix_batch_override_translations_created_by" ON "batch_override_translations" ("created_by");

CREATE INDEX "ix_batch_override_translations_updated_by" ON "batch_override_translations" ("updated_by");

CREATE INDEX "ix_inspection_items_batch_id" ON "inspection_items" ("batch_id");

CREATE INDEX "ix_inspection_items_created_by" ON "inspection_items" ("created_by");

CREATE INDEX "ix_inspection_items_updated_by" ON "inspection_items" ("updated_by");

CREATE INDEX "ix_inspection_item_translations_inspection_item_id" ON "inspection_item_translations" ("inspection_item_id");

CREATE INDEX "ix_inspection_item_translations_created_by" ON "inspection_item_translations" ("created_by");

CREATE INDEX "ix_inspection_item_translations_updated_by" ON "inspection_item_translations" ("updated_by");

CREATE INDEX "ix_certifications_supersedes_id" ON "certifications" ("supersedes_id");

CREATE INDEX "ix_certifications_created_by" ON "certifications" ("created_by");

CREATE INDEX "ix_certification_translations_certification_id" ON "certification_translations" ("certification_id");

CREATE INDEX "ix_certification_translations_created_by" ON "certification_translations" ("created_by");

CREATE INDEX "ix_certification_translations_updated_by" ON "certification_translations" ("updated_by");

CREATE INDEX "ix_certification_links_product_revision_id" ON "certification_links" ("product_revision_id");

CREATE INDEX "ix_certification_links_batch_id" ON "certification_links" ("batch_id");

CREATE INDEX "ix_certification_links_certification_id" ON "certification_links" ("certification_id");

CREATE INDEX "ix_certification_links_created_by" ON "certification_links" ("created_by");

CREATE INDEX "ix_certification_links_updated_by" ON "certification_links" ("updated_by");

CREATE INDEX "ix_media_assets_replaces_media_asset_id" ON "media_assets" ("replaces_media_asset_id");

CREATE INDEX "ix_media_assets_created_by" ON "media_assets" ("created_by");

CREATE INDEX "ix_asset_links_product_revision_id" ON "asset_links" ("product_revision_id");

CREATE INDEX "ix_asset_links_certification_id" ON "asset_links" ("certification_id");

CREATE INDEX "ix_asset_links_inspection_item_id" ON "asset_links" ("inspection_item_id");

CREATE INDEX "ix_asset_links_custom_section_id" ON "asset_links" ("custom_section_id");

CREATE INDEX "ix_asset_links_media_asset_id" ON "asset_links" ("media_asset_id");

CREATE INDEX "ix_asset_links_created_by" ON "asset_links" ("created_by");

CREATE INDEX "ix_asset_links_updated_by" ON "asset_links" ("updated_by");

CREATE INDEX "ix_custom_sections_product_revision_id" ON "custom_sections" ("product_revision_id");

CREATE INDEX "ix_custom_sections_batch_id" ON "custom_sections" ("batch_id");

CREATE INDEX "ix_custom_sections_created_by" ON "custom_sections" ("created_by");

CREATE INDEX "ix_custom_sections_updated_by" ON "custom_sections" ("updated_by");

CREATE INDEX "ix_custom_section_translations_custom_section_id" ON "custom_section_translations" ("custom_section_id");

CREATE INDEX "ix_custom_section_translations_created_by" ON "custom_section_translations" ("created_by");

CREATE INDEX "ix_custom_section_translations_updated_by" ON "custom_section_translations" ("updated_by");

CREATE INDEX "ix_passport_revisions_batch_id" ON "passport_revisions" ("batch_id");

CREATE INDEX "ix_passport_revisions_base_product_revision_id" ON "passport_revisions" ("base_product_revision_id");

CREATE INDEX "ix_passport_revisions_source_revision_id" ON "passport_revisions" ("source_revision_id");

CREATE INDEX "ix_passport_revisions_rollback_source_revision_id" ON "passport_revisions" ("rollback_source_revision_id");

CREATE INDEX "ix_passport_revisions_created_by" ON "passport_revisions" ("created_by");

CREATE INDEX "ix_passport_revisions_published_by" ON "passport_revisions" ("published_by");

CREATE INDEX "ix_passport_revisions_reviewed_by" ON "passport_revisions" ("reviewed_by");

CREATE INDEX "ix_published_assets_passport_revision_id" ON "published_assets" ("passport_revision_id");

CREATE INDEX "ix_published_assets_source_media_asset_id" ON "published_assets" ("source_media_asset_id");

CREATE INDEX "ix_published_assets_created_by" ON "published_assets" ("created_by");

CREATE INDEX "ix_publish_records_batch_id" ON "publish_records" ("batch_id");

CREATE INDEX "ix_publish_records_passport_revision_id" ON "publish_records" ("passport_revision_id");

CREATE INDEX "ix_publish_records_expected_current_revision_id" ON "publish_records" ("expected_current_revision_id");

CREATE INDEX "ix_publish_records_created_by" ON "publish_records" ("created_by");

CREATE INDEX "ix_passport_audit_events_batch_id" ON "passport_audit_events" ("batch_id");

CREATE INDEX "ix_passport_audit_events_passport_revision_id" ON "passport_audit_events" ("passport_revision_id");

CREATE INDEX "ix_passport_audit_events_actor_user_id" ON "passport_audit_events" ("actor_user_id");

CREATE INDEX "ix_products_lifecycle_status_updated_at" ON "products" ("lifecycle_status","updated_at");

CREATE INDEX "ix_product_revisions_product_id_revision_status_revision_number" ON "product_revisions" ("product_id","revision_status","revision_number");

CREATE INDEX "ix_batches_product_id_created_at" ON "batches" ("product_id","created_at");

CREATE INDEX "ix_batches_workflow_status_submitted_at" ON "batches" ("workflow_status","submitted_at");

CREATE INDEX "ix_inspection_items_batch_id_sort_order_item_code" ON "inspection_items" ("batch_id","sort_order","item_code");

CREATE INDEX "ix_passport_revisions_published_at" ON "passport_revisions" ("published_at");

CREATE INDEX "ix_publish_records_publish_status_updated_at" ON "publish_records" ("publish_status","updated_at");

CREATE INDEX "ix_passport_audit_events_batch_id_created_at_id" ON "passport_audit_events" ("batch_id","created_at","id");

CREATE INDEX "ix_passport_audit_events_entity_type_entity_id_created_at" ON "passport_audit_events" ("entity_type","entity_id","created_at");

CREATE INDEX "ix_published_assets_published_path" ON "published_assets" ("published_path");

CREATE INDEX "ix_published_assets_sha256" ON "published_assets" ("sha256");

CREATE TRIGGER "freeze_product_revisions_update" BEFORE UPDATE ON "product_revisions" WHEN OLD.revision_status IN ('sealed','abandoned') BEGIN SELECT RAISE(ABORT,'product_revisions frozen'); END;

CREATE TRIGGER "freeze_product_revisions_delete" BEFORE DELETE ON "product_revisions" WHEN OLD.revision_status IN ('sealed','abandoned') BEGIN SELECT RAISE(ABORT,'product_revisions frozen'); END;

CREATE TRIGGER "freeze_certifications_update" BEFORE UPDATE ON "certifications" WHEN OLD.sealed_at IS NOT NULL BEGIN SELECT RAISE(ABORT,'certifications frozen'); END;

CREATE TRIGGER "freeze_certifications_delete" BEFORE DELETE ON "certifications" WHEN OLD.sealed_at IS NOT NULL BEGIN SELECT RAISE(ABORT,'certifications frozen'); END;

CREATE TRIGGER "freeze_passport_audit_events_update" BEFORE UPDATE ON "passport_audit_events" WHEN 1 BEGIN SELECT RAISE(ABORT,'passport_audit_events frozen'); END;

CREATE TRIGGER "freeze_passport_audit_events_delete" BEFORE DELETE ON "passport_audit_events" WHEN 1 BEGIN SELECT RAISE(ABORT,'passport_audit_events frozen'); END;

CREATE TRIGGER "freeze_publish_records_update" BEFORE UPDATE ON "publish_records" WHEN OLD.publish_status IN ('published','failed') BEGIN SELECT RAISE(ABORT,'publish_records frozen'); END;

CREATE TRIGGER "freeze_publish_records_delete" BEFORE DELETE ON "publish_records" WHEN OLD.publish_status IN ('published','failed') BEGIN SELECT RAISE(ABORT,'publish_records frozen'); END;

CREATE TRIGGER "passport_sealed_update" BEFORE UPDATE ON "passport_revisions" WHEN OLD.published_at IS NOT NULL OR (OLD.sealed_at IS NOT NULL AND (NEW."id" IS NOT OLD."id" OR NEW."created_at" IS NOT OLD."created_at" OR NEW."created_by" IS NOT OLD."created_by" OR NEW."batch_id" IS NOT OLD."batch_id" OR NEW."version_number" IS NOT OLD."version_number" OR NEW."base_product_revision_id" IS NOT OLD."base_product_revision_id" OR NEW."source_revision_id" IS NOT OLD."source_revision_id" OR NEW."rollback_source_revision_id" IS NOT OLD."rollback_source_revision_id" OR NEW."source_edit_version" IS NOT OLD."source_edit_version" OR NEW."source_content_hash" IS NOT OLD."source_content_hash" OR NEW."frozen_input" IS NOT OLD."frozen_input" OR NEW."schema_version" IS NOT OLD."schema_version" OR NEW."builder_version" IS NOT OLD."builder_version" OR NEW."payload" IS NOT OLD."payload" OR NEW."payload_hash" IS NOT OLD."payload_hash" OR NEW."content_hash" IS NOT OLD."content_hash" OR NEW."snapshot_path" IS NOT OLD."snapshot_path" OR NEW."asset_manifest_hash" IS NOT OLD."asset_manifest_hash" OR NEW."sealed_at" IS NOT OLD."sealed_at" OR NEW."published_by" IS NOT OLD."published_by" OR NEW."reviewed_by" IS NOT OLD."reviewed_by" OR NEW."reviewed_at" IS NOT OLD."reviewed_at" OR NEW."release_identifier" IS NOT OLD."release_identifier")) BEGIN SELECT RAISE(ABORT,'passport revision frozen'); END;

CREATE TRIGGER "passport_no_delete" BEFORE DELETE ON "passport_revisions" WHEN OLD.sealed_at IS NOT NULL OR OLD.published_at IS NOT NULL BEGIN SELECT RAISE(ABORT,'passport revision frozen'); END;

CREATE TRIGGER "passport_publish_once" BEFORE UPDATE ON "passport_revisions" WHEN NEW.published_at IS NOT OLD.published_at AND (OLD.published_at IS NOT NULL OR NEW.published_at IS NULL OR NOT EXISTS(SELECT 1 FROM publish_records r JOIN batches b ON b.active_publish_record_id=r.id WHERE r.passport_revision_id=OLD.id AND r.publish_status IN ('switching','recovery_required'))) BEGIN SELECT RAISE(ABORT,'publication requires active switching record'); END;

CREATE TRIGGER "passport_insert_unpublished" BEFORE INSERT ON "passport_revisions" WHEN NEW.published_at IS NOT NULL BEGIN SELECT RAISE(ABORT,'prepare before publish'); END;

CREATE TRIGGER "products_identity" BEFORE UPDATE ON "products" WHEN NEW."id" IS NOT OLD."id" OR NEW."product_code" IS NOT OLD."product_code" BEGIN SELECT RAISE(ABORT,'identity or bytes immutable'); END;

CREATE TRIGGER "batches_identity" BEFORE UPDATE ON "batches" WHEN NEW."id" IS NOT OLD."id" OR NEW."batch_code" IS NOT OLD."batch_code" OR NEW."product_id" IS NOT OLD."product_id" OR NEW."base_product_revision_id" IS NOT OLD."base_product_revision_id" OR NEW."record_type" IS NOT OLD."record_type" BEGIN SELECT RAISE(ABORT,'identity or bytes immutable'); END;

CREATE TRIGGER "product_revisions_identity" BEFORE UPDATE ON "product_revisions" WHEN NEW."id" IS NOT OLD."id" OR NEW."product_id" IS NOT OLD."product_id" OR NEW."revision_number" IS NOT OLD."revision_number" BEGIN SELECT RAISE(ABORT,'identity or bytes immutable'); END;

CREATE TRIGGER "media_assets_identity" BEFORE UPDATE ON "media_assets" WHEN NEW."id" IS NOT OLD."id" OR NEW."created_at" IS NOT OLD."created_at" OR NEW."created_by" IS NOT OLD."created_by" OR NEW."storage_key" IS NOT OLD."storage_key" OR NEW."original_filename" IS NOT OLD."original_filename" OR NEW."mime_type" IS NOT OLD."mime_type" OR NEW."file_size" IS NOT OLD."file_size" OR NEW."sha256" IS NOT OLD."sha256" OR NEW."is_public_eligible" IS NOT OLD."is_public_eligible" OR NEW."replaces_media_asset_id" IS NOT OLD."replaces_media_asset_id" OR NEW."internal_note" IS NOT OLD."internal_note" BEGIN SELECT RAISE(ABORT,'identity or bytes immutable'); END;

CREATE TRIGGER "batch_sealed_base_INSERT" BEFORE INSERT ON "batches" WHEN NOT EXISTS(SELECT 1 FROM product_revisions p WHERE p.id=NEW.base_product_revision_id AND p.product_id=NEW.product_id AND p.revision_status='sealed') BEGIN SELECT RAISE(ABORT,'batch requires sealed matching template'); END;

CREATE TRIGGER "product_current_INSERT" BEFORE INSERT ON "products" WHEN NEW.current_revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM product_revisions p WHERE p.id=NEW.current_revision_id AND p.product_id=NEW.id AND p.revision_status='sealed') BEGIN SELECT RAISE(ABORT,'current template must be sealed'); END;

CREATE TRIGGER "batch_current_INSERT" BEFORE INSERT ON "batches" WHEN NEW.current_passport_revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM passport_revisions p WHERE p.id=NEW.current_passport_revision_id AND p.batch_id=NEW.id AND p.published_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'current passport must be published'); END;

CREATE TRIGGER "cert_link_sealed_INSERT" BEFORE INSERT ON "certification_links" WHEN NEW.operation='include' AND NOT EXISTS(SELECT 1 FROM certifications c WHERE c.id=NEW.certification_id AND c.sealed_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'certification must be sealed'); END;

CREATE TRIGGER "product_revisions_source_revision_id_INSERT" BEFORE INSERT ON "product_revisions" WHEN NEW.source_revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM product_revisions s WHERE s.id=NEW.source_revision_id AND s.product_id=NEW.product_id AND s.revision_number<NEW.revision_number) BEGIN SELECT RAISE(ABORT,'invalid revision source'); END;

CREATE TRIGGER "certifications_supersedes_id_INSERT" BEFORE INSERT ON "certifications" WHEN NEW.supersedes_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM certifications s WHERE s.id=NEW.supersedes_id AND s.family_key=NEW.family_key AND s.revision_number<NEW.revision_number) BEGIN SELECT RAISE(ABORT,'invalid revision source'); END;

CREATE TRIGGER "passport_revisions_source_revision_id_INSERT" BEFORE INSERT ON "passport_revisions" WHEN NEW.source_revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM passport_revisions s WHERE s.id=NEW.source_revision_id AND s.batch_id=NEW.batch_id AND s.version_number<NEW.version_number AND s.published_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'invalid revision source'); END;

CREATE TRIGGER "passport_revisions_rollback_source_revision_id_INSERT" BEFORE INSERT ON "passport_revisions" WHEN NEW.rollback_source_revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM passport_revisions s WHERE s.id=NEW.rollback_source_revision_id AND s.batch_id=NEW.batch_id AND s.version_number<NEW.version_number AND s.published_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'invalid revision source'); END;

CREATE TRIGGER "batch_sealed_base_UPDATE" BEFORE UPDATE ON "batches" WHEN NOT EXISTS(SELECT 1 FROM product_revisions p WHERE p.id=NEW.base_product_revision_id AND p.product_id=NEW.product_id AND p.revision_status='sealed') BEGIN SELECT RAISE(ABORT,'batch requires sealed matching template'); END;

CREATE TRIGGER "product_current_UPDATE" BEFORE UPDATE ON "products" WHEN NEW.current_revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM product_revisions p WHERE p.id=NEW.current_revision_id AND p.product_id=NEW.id AND p.revision_status='sealed') BEGIN SELECT RAISE(ABORT,'current template must be sealed'); END;

CREATE TRIGGER "batch_current_UPDATE" BEFORE UPDATE ON "batches" WHEN NEW.current_passport_revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM passport_revisions p WHERE p.id=NEW.current_passport_revision_id AND p.batch_id=NEW.id AND p.published_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'current passport must be published'); END;

CREATE TRIGGER "cert_link_sealed_UPDATE" BEFORE UPDATE ON "certification_links" WHEN NEW.operation='include' AND NOT EXISTS(SELECT 1 FROM certifications c WHERE c.id=NEW.certification_id AND c.sealed_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'certification must be sealed'); END;

CREATE TRIGGER "product_revisions_source_revision_id_UPDATE" BEFORE UPDATE ON "product_revisions" WHEN NEW.source_revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM product_revisions s WHERE s.id=NEW.source_revision_id AND s.product_id=NEW.product_id AND s.revision_number<NEW.revision_number) BEGIN SELECT RAISE(ABORT,'invalid revision source'); END;

CREATE TRIGGER "certifications_supersedes_id_UPDATE" BEFORE UPDATE ON "certifications" WHEN NEW.supersedes_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM certifications s WHERE s.id=NEW.supersedes_id AND s.family_key=NEW.family_key AND s.revision_number<NEW.revision_number) BEGIN SELECT RAISE(ABORT,'invalid revision source'); END;

CREATE TRIGGER "passport_revisions_source_revision_id_UPDATE" BEFORE UPDATE ON "passport_revisions" WHEN NEW.source_revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM passport_revisions s WHERE s.id=NEW.source_revision_id AND s.batch_id=NEW.batch_id AND s.version_number<NEW.version_number AND s.published_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'invalid revision source'); END;

CREATE TRIGGER "passport_revisions_rollback_source_revision_id_UPDATE" BEFORE UPDATE ON "passport_revisions" WHEN NEW.rollback_source_revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM passport_revisions s WHERE s.id=NEW.rollback_source_revision_id AND s.batch_id=NEW.batch_id AND s.version_number<NEW.version_number AND s.published_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'invalid revision source'); END;

CREATE TRIGGER "parent_freeze_certification_links_INSERT" BEFORE INSERT ON "certification_links" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT NEW.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT NEW.product_revision_id) AND p.revision_status!='draft') BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_certification_links_INSERT" AFTER INSERT ON "certification_links" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT NEW.batch_id); END;

CREATE TRIGGER "parent_freeze_certification_links_UPDATE" BEFORE UPDATE ON "certification_links" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT OLD.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT OLD.product_revision_id) AND p.revision_status!='draft') OR EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT NEW.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT NEW.product_revision_id) AND p.revision_status!='draft') BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_certification_links_UPDATE" AFTER UPDATE ON "certification_links" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT NEW.batch_id); END;

CREATE TRIGGER "parent_freeze_certification_links_DELETE" BEFORE DELETE ON "certification_links" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT OLD.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT OLD.product_revision_id) AND p.revision_status!='draft') BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_certification_links_DELETE" AFTER DELETE ON "certification_links" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT OLD.batch_id); END;

CREATE TRIGGER "owner_fixed_certification_links" BEFORE UPDATE ON "certification_links" WHEN NEW."product_revision_id" IS NOT OLD."product_revision_id" OR NEW."batch_id" IS NOT OLD."batch_id" OR NEW."certification_id" IS NOT OLD."certification_id" BEGIN SELECT RAISE(ABORT,'owner immutable'); END;

CREATE TRIGGER "parent_freeze_custom_sections_INSERT" BEFORE INSERT ON "custom_sections" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT NEW.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT NEW.product_revision_id) AND p.revision_status!='draft') BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_custom_sections_INSERT" AFTER INSERT ON "custom_sections" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT NEW.batch_id); END;

CREATE TRIGGER "parent_freeze_custom_sections_UPDATE" BEFORE UPDATE ON "custom_sections" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT OLD.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT OLD.product_revision_id) AND p.revision_status!='draft') OR EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT NEW.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT NEW.product_revision_id) AND p.revision_status!='draft') BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_custom_sections_UPDATE" AFTER UPDATE ON "custom_sections" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT NEW.batch_id); END;

CREATE TRIGGER "parent_freeze_custom_sections_DELETE" BEFORE DELETE ON "custom_sections" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT OLD.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT OLD.product_revision_id) AND p.revision_status!='draft') BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_custom_sections_DELETE" AFTER DELETE ON "custom_sections" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT OLD.batch_id); END;

CREATE TRIGGER "owner_fixed_custom_sections" BEFORE UPDATE ON "custom_sections" WHEN NEW."product_revision_id" IS NOT OLD."product_revision_id" OR NEW."batch_id" IS NOT OLD."batch_id" BEGIN SELECT RAISE(ABORT,'owner immutable'); END;

CREATE TRIGGER "parent_freeze_inspection_item_translations_INSERT" BEFORE INSERT ON "inspection_item_translations" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM inspection_items WHERE id=NEW.inspection_item_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_inspection_item_translations_INSERT" AFTER INSERT ON "inspection_item_translations" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT batch_id FROM inspection_items WHERE id=NEW.inspection_item_id); END;

CREATE TRIGGER "parent_freeze_inspection_item_translations_UPDATE" BEFORE UPDATE ON "inspection_item_translations" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM inspection_items WHERE id=OLD.inspection_item_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM inspection_items WHERE id=NEW.inspection_item_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_inspection_item_translations_UPDATE" AFTER UPDATE ON "inspection_item_translations" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT batch_id FROM inspection_items WHERE id=NEW.inspection_item_id); END;

CREATE TRIGGER "parent_freeze_inspection_item_translations_DELETE" BEFORE DELETE ON "inspection_item_translations" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM inspection_items WHERE id=OLD.inspection_item_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_inspection_item_translations_DELETE" AFTER DELETE ON "inspection_item_translations" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT batch_id FROM inspection_items WHERE id=OLD.inspection_item_id); END;

CREATE TRIGGER "owner_fixed_inspection_item_translations" BEFORE UPDATE ON "inspection_item_translations" WHEN NEW."inspection_item_id" IS NOT OLD."inspection_item_id" BEGIN SELECT RAISE(ABORT,'owner immutable'); END;

CREATE TRIGGER "parent_freeze_custom_section_translations_INSERT" BEFORE INSERT ON "custom_section_translations" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM custom_sections WHERE id=NEW.custom_section_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT product_revision_id FROM custom_sections WHERE id=NEW.custom_section_id) AND p.revision_status!='draft') BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_custom_section_translations_INSERT" AFTER INSERT ON "custom_section_translations" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT batch_id FROM custom_sections WHERE id=NEW.custom_section_id); END;

CREATE TRIGGER "parent_freeze_custom_section_translations_UPDATE" BEFORE UPDATE ON "custom_section_translations" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM custom_sections WHERE id=OLD.custom_section_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT product_revision_id FROM custom_sections WHERE id=OLD.custom_section_id) AND p.revision_status!='draft') OR EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM custom_sections WHERE id=NEW.custom_section_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT product_revision_id FROM custom_sections WHERE id=NEW.custom_section_id) AND p.revision_status!='draft') BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_custom_section_translations_UPDATE" AFTER UPDATE ON "custom_section_translations" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT batch_id FROM custom_sections WHERE id=NEW.custom_section_id); END;

CREATE TRIGGER "parent_freeze_custom_section_translations_DELETE" BEFORE DELETE ON "custom_section_translations" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM custom_sections WHERE id=OLD.custom_section_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT product_revision_id FROM custom_sections WHERE id=OLD.custom_section_id) AND p.revision_status!='draft') BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_custom_section_translations_DELETE" AFTER DELETE ON "custom_section_translations" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT batch_id FROM custom_sections WHERE id=OLD.custom_section_id); END;

CREATE TRIGGER "owner_fixed_custom_section_translations" BEFORE UPDATE ON "custom_section_translations" WHEN NEW."custom_section_id" IS NOT OLD."custom_section_id" BEGIN SELECT RAISE(ABORT,'owner immutable'); END;

CREATE TRIGGER "parent_freeze_asset_links_INSERT" BEFORE INSERT ON "asset_links" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM inspection_items WHERE id=NEW.inspection_item_id UNION SELECT batch_id FROM custom_sections WHERE id=NEW.custom_section_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT NEW.product_revision_id UNION SELECT product_revision_id FROM custom_sections WHERE id=NEW.custom_section_id) AND p.revision_status!='draft') OR EXISTS(SELECT 1 FROM certifications c WHERE c.id IN (SELECT NEW.certification_id) AND c.sealed_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_asset_links_INSERT" AFTER INSERT ON "asset_links" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT batch_id FROM inspection_items WHERE id=NEW.inspection_item_id UNION SELECT batch_id FROM custom_sections WHERE id=NEW.custom_section_id); END;

CREATE TRIGGER "parent_freeze_asset_links_UPDATE" BEFORE UPDATE ON "asset_links" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM inspection_items WHERE id=OLD.inspection_item_id UNION SELECT batch_id FROM custom_sections WHERE id=OLD.custom_section_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT OLD.product_revision_id UNION SELECT product_revision_id FROM custom_sections WHERE id=OLD.custom_section_id) AND p.revision_status!='draft') OR EXISTS(SELECT 1 FROM certifications c WHERE c.id IN (SELECT OLD.certification_id) AND c.sealed_at IS NOT NULL) OR EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM inspection_items WHERE id=NEW.inspection_item_id UNION SELECT batch_id FROM custom_sections WHERE id=NEW.custom_section_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT NEW.product_revision_id UNION SELECT product_revision_id FROM custom_sections WHERE id=NEW.custom_section_id) AND p.revision_status!='draft') OR EXISTS(SELECT 1 FROM certifications c WHERE c.id IN (SELECT NEW.certification_id) AND c.sealed_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_asset_links_UPDATE" AFTER UPDATE ON "asset_links" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT batch_id FROM inspection_items WHERE id=NEW.inspection_item_id UNION SELECT batch_id FROM custom_sections WHERE id=NEW.custom_section_id); END;

CREATE TRIGGER "parent_freeze_asset_links_DELETE" BEFORE DELETE ON "asset_links" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM inspection_items WHERE id=OLD.inspection_item_id UNION SELECT batch_id FROM custom_sections WHERE id=OLD.custom_section_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT OLD.product_revision_id UNION SELECT product_revision_id FROM custom_sections WHERE id=OLD.custom_section_id) AND p.revision_status!='draft') OR EXISTS(SELECT 1 FROM certifications c WHERE c.id IN (SELECT OLD.certification_id) AND c.sealed_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_asset_links_DELETE" AFTER DELETE ON "asset_links" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT batch_id FROM inspection_items WHERE id=OLD.inspection_item_id UNION SELECT batch_id FROM custom_sections WHERE id=OLD.custom_section_id); END;

CREATE TRIGGER "owner_fixed_asset_links" BEFORE UPDATE ON "asset_links" WHEN NEW."product_revision_id" IS NOT OLD."product_revision_id" OR NEW."certification_id" IS NOT OLD."certification_id" OR NEW."inspection_item_id" IS NOT OLD."inspection_item_id" OR NEW."custom_section_id" IS NOT OLD."custom_section_id" BEGIN SELECT RAISE(ABORT,'owner immutable'); END;

CREATE TRIGGER "parent_freeze_batch_overrides_INSERT" BEFORE INSERT ON "batch_overrides" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT NEW.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_batch_overrides_INSERT" AFTER INSERT ON "batch_overrides" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT NEW.batch_id); END;

CREATE TRIGGER "parent_freeze_batch_overrides_UPDATE" BEFORE UPDATE ON "batch_overrides" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT OLD.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT NEW.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_batch_overrides_UPDATE" AFTER UPDATE ON "batch_overrides" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT NEW.batch_id); END;

CREATE TRIGGER "parent_freeze_batch_overrides_DELETE" BEFORE DELETE ON "batch_overrides" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT OLD.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_batch_overrides_DELETE" AFTER DELETE ON "batch_overrides" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT OLD.batch_id); END;

CREATE TRIGGER "owner_fixed_batch_overrides" BEFORE UPDATE ON "batch_overrides" WHEN NEW."batch_id" IS NOT OLD."batch_id" BEGIN SELECT RAISE(ABORT,'owner immutable'); END;

CREATE TRIGGER "parent_freeze_inspection_items_INSERT" BEFORE INSERT ON "inspection_items" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT NEW.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_inspection_items_INSERT" AFTER INSERT ON "inspection_items" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT NEW.batch_id); END;

CREATE TRIGGER "parent_freeze_inspection_items_UPDATE" BEFORE UPDATE ON "inspection_items" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT OLD.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT NEW.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_inspection_items_UPDATE" AFTER UPDATE ON "inspection_items" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT NEW.batch_id); END;

CREATE TRIGGER "parent_freeze_inspection_items_DELETE" BEFORE DELETE ON "inspection_items" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT OLD.batch_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_inspection_items_DELETE" AFTER DELETE ON "inspection_items" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT OLD.batch_id); END;

CREATE TRIGGER "owner_fixed_inspection_items" BEFORE UPDATE ON "inspection_items" WHEN NEW."batch_id" IS NOT OLD."batch_id" BEGIN SELECT RAISE(ABORT,'owner immutable'); END;

CREATE TRIGGER "parent_freeze_batch_override_translations_INSERT" BEFORE INSERT ON "batch_override_translations" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM batch_overrides WHERE id=NEW.batch_override_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_batch_override_translations_INSERT" AFTER INSERT ON "batch_override_translations" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT batch_id FROM batch_overrides WHERE id=NEW.batch_override_id); END;

CREATE TRIGGER "parent_freeze_batch_override_translations_UPDATE" BEFORE UPDATE ON "batch_override_translations" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM batch_overrides WHERE id=OLD.batch_override_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) OR EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM batch_overrides WHERE id=NEW.batch_override_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_batch_override_translations_UPDATE" AFTER UPDATE ON "batch_override_translations" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT batch_id FROM batch_overrides WHERE id=NEW.batch_override_id); END;

CREATE TRIGGER "parent_freeze_batch_override_translations_DELETE" BEFORE DELETE ON "batch_override_translations" WHEN EXISTS(SELECT 1 FROM batches b WHERE b.id IN (SELECT batch_id FROM batch_overrides WHERE id=OLD.batch_override_id) AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL)) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "bump_batch_override_translations_DELETE" AFTER DELETE ON "batch_override_translations" BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN (SELECT batch_id FROM batch_overrides WHERE id=OLD.batch_override_id); END;

CREATE TRIGGER "owner_fixed_batch_override_translations" BEFORE UPDATE ON "batch_override_translations" WHEN NEW."batch_override_id" IS NOT OLD."batch_override_id" BEGIN SELECT RAISE(ABORT,'owner immutable'); END;

CREATE TRIGGER "parent_freeze_certification_translations_INSERT" BEFORE INSERT ON "certification_translations" WHEN EXISTS(SELECT 1 FROM certifications c WHERE c.id IN (SELECT NEW.certification_id) AND c.sealed_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "parent_freeze_certification_translations_UPDATE" BEFORE UPDATE ON "certification_translations" WHEN EXISTS(SELECT 1 FROM certifications c WHERE c.id IN (SELECT OLD.certification_id) AND c.sealed_at IS NOT NULL) OR EXISTS(SELECT 1 FROM certifications c WHERE c.id IN (SELECT NEW.certification_id) AND c.sealed_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "parent_freeze_certification_translations_DELETE" BEFORE DELETE ON "certification_translations" WHEN EXISTS(SELECT 1 FROM certifications c WHERE c.id IN (SELECT OLD.certification_id) AND c.sealed_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "owner_fixed_certification_translations" BEFORE UPDATE ON "certification_translations" WHEN NEW."certification_id" IS NOT OLD."certification_id" BEGIN SELECT RAISE(ABORT,'owner immutable'); END;

CREATE TRIGGER "parent_freeze_published_assets_INSERT" BEFORE INSERT ON "published_assets" WHEN EXISTS(SELECT 1 FROM passport_revisions p WHERE p.id=NEW.passport_revision_id AND p.sealed_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "parent_freeze_published_assets_UPDATE" BEFORE UPDATE ON "published_assets" WHEN EXISTS(SELECT 1 FROM passport_revisions p WHERE p.id=OLD.passport_revision_id AND p.sealed_at IS NOT NULL) OR EXISTS(SELECT 1 FROM passport_revisions p WHERE p.id=NEW.passport_revision_id AND p.sealed_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "parent_freeze_published_assets_DELETE" BEFORE DELETE ON "published_assets" WHEN EXISTS(SELECT 1 FROM passport_revisions p WHERE p.id=OLD.passport_revision_id AND p.sealed_at IS NOT NULL) BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "owner_fixed_published_assets" BEFORE UPDATE ON "published_assets" WHEN NEW."passport_revision_id" IS NOT OLD."passport_revision_id" BEGIN SELECT RAISE(ABORT,'owner immutable'); END;

CREATE TRIGGER "parent_freeze_product_revision_translations_INSERT" BEFORE INSERT ON "product_revision_translations" WHEN EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT NEW.product_revision_id) AND p.revision_status!='draft') BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "parent_freeze_product_revision_translations_UPDATE" BEFORE UPDATE ON "product_revision_translations" WHEN EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT OLD.product_revision_id) AND p.revision_status!='draft') OR EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT NEW.product_revision_id) AND p.revision_status!='draft') BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "parent_freeze_product_revision_translations_DELETE" BEFORE DELETE ON "product_revision_translations" WHEN EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN (SELECT OLD.product_revision_id) AND p.revision_status!='draft') BEGIN SELECT RAISE(ABORT,'parent frozen'); END;

CREATE TRIGGER "owner_fixed_product_revision_translations" BEFORE UPDATE ON "product_revision_translations" WHEN NEW."product_revision_id" IS NOT OLD."product_revision_id" BEGIN SELECT RAISE(ABORT,'owner immutable'); END;

CREATE TRIGGER "batch_work_freeze" BEFORE UPDATE ON "batches" WHEN (OLD.workflow_status!='draft' OR OLD.active_publish_record_id IS NOT NULL) AND (NEW.production_date IS NOT OLD.production_date OR NEW.expiry_date IS NOT OLD.expiry_date OR NEW.quality_status IS NOT OLD.quality_status OR NEW.internal_note IS NOT OLD.internal_note) BEGIN SELECT RAISE(ABORT,'batch working data frozen'); END;

CREATE TRIGGER "batch_active_workflow" BEFORE UPDATE ON "batches" WHEN OLD.active_publish_record_id IS NOT NULL AND NEW.workflow_status IS NOT OLD.workflow_status AND NOT (NEW.workflow_status='published' AND EXISTS(SELECT 1 FROM publish_records r WHERE r.id=OLD.active_publish_record_id AND r.publish_status='published')) BEGIN SELECT RAISE(ABORT,'unresolved publish'); END;

CREATE TRIGGER "product_seal_translation" BEFORE UPDATE ON "product_revisions" WHEN NEW.revision_status='sealed' AND OLD.revision_status='draft' AND NOT EXISTS(SELECT 1 FROM product_revision_translations t WHERE t.product_revision_id=NEW.id AND t.language_code=NEW.source_language AND t.translation_status='approved' AND length(t.product_name)>0) BEGIN SELECT RAISE(ABORT,'approved source translation required'); END;

CREATE TRIGGER "batch_history_delete" BEFORE DELETE ON "batches" WHEN EXISTS(SELECT 1 FROM passport_revisions p WHERE p.batch_id=OLD.id) BEGIN SELECT RAISE(ABORT,'batch history retained'); END;
