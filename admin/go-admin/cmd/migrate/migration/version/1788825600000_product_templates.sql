CREATE TABLE "t5_audit_events" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "batch_id" TEXT CHECK (length("batch_id")=36 AND substr("batch_id",15,1)='4' AND substr("batch_id",20,1) IN ('8','9','a','b') AND "batch_id" NOT GLOB '*[^0-9a-f-]*'),
  "passport_revision_id" TEXT CHECK (length("passport_revision_id")=36 AND substr("passport_revision_id",15,1)='4' AND substr("passport_revision_id",20,1) IN ('8','9','a','b') AND "passport_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "actor_user_id" INTEGER NOT NULL,
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "event_type" TEXT NOT NULL CHECK ("event_type" IN ('batch_created','batch_cloned','batch_edited','override_set','override_cleared','review_submitted','review_approved','review_rejected','publish_requested','publish_succeeded','publish_failed','rollback_requested','rollback_succeeded','archived','media_replaced','inspection_changed','certification_linked','product_revision_sealed','product_created','product_updated','product_revision_created','product_revision_cloned','product_revision_updated','product_default_revision_changed','product_translation_updated')),
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
INSERT INTO t5_audit_events SELECT * FROM passport_audit_events;
DROP TABLE passport_audit_events;
ALTER TABLE t5_audit_events RENAME TO passport_audit_events;
CREATE INDEX "ix_passport_audit_events_batch_id" ON "passport_audit_events" ("batch_id");
CREATE INDEX "ix_passport_audit_events_passport_revision_id" ON "passport_audit_events" ("passport_revision_id");
CREATE INDEX "ix_passport_audit_events_actor_user_id" ON "passport_audit_events" ("actor_user_id");
CREATE INDEX "ix_passport_audit_events_batch_id_created_at_id" ON "passport_audit_events" ("batch_id","created_at","id");
CREATE INDEX "ix_passport_audit_events_entity_type_entity_id_created_at" ON "passport_audit_events" ("entity_type","entity_id","created_at");
CREATE TRIGGER "freeze_passport_audit_events_update" BEFORE UPDATE ON "passport_audit_events" WHEN 1 BEGIN SELECT RAISE(ABORT,'passport_audit_events frozen'); END;
CREATE TRIGGER "freeze_passport_audit_events_delete" BEFORE DELETE ON "passport_audit_events" WHEN 1 BEGIN SELECT RAISE(ABORT,'passport_audit_events frozen'); END;