CREATE TABLE "t8_audit_events" (
  "id" TEXT NOT NULL PRIMARY KEY CHECK (length("id")=36 AND substr("id",15,1)='4' AND substr("id",20,1) IN ('8','9','a','b') AND "id" NOT GLOB '*[^0-9a-f-]*'),
  "batch_id" TEXT CHECK (length("batch_id")=36 AND substr("batch_id",15,1)='4' AND substr("batch_id",20,1) IN ('8','9','a','b') AND "batch_id" NOT GLOB '*[^0-9a-f-]*'),
  "passport_revision_id" TEXT CHECK (length("passport_revision_id")=36 AND substr("passport_revision_id",15,1)='4' AND substr("passport_revision_id",20,1) IN ('8','9','a','b') AND "passport_revision_id" NOT GLOB '*[^0-9a-f-]*'),
  "actor_user_id" INTEGER NOT NULL,
  "created_at" TEXT NOT NULL CHECK ("created_at" IS NULL OR (length("created_at")=24 AND substr("created_at",24,1)='Z' AND julianday("created_at") IS NOT NULL)),
  "event_type" TEXT NOT NULL CHECK ("event_type" IN ('batch_created','batch_cloned','batch_edited','override_set','override_cleared','review_submitted','review_approved','review_rejected','publish_requested','publish_succeeded','publish_failed','rollback_requested','rollback_succeeded','archived','media_replaced','inspection_changed','certification_linked','product_revision_sealed','product_created','product_updated','product_revision_created','product_revision_cloned','product_revision_updated','product_default_revision_changed','product_translation_updated','override_reset','custom_section_created','custom_section_updated','custom_section_deleted','custom_section_reordered','custom_section_translation_updated','batch_section_overridden','batch_section_hidden','batch_section_reset','batch_section_created','review_returned_to_draft','review_conflict')),
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
INSERT INTO t8_audit_events SELECT * FROM passport_audit_events;
DROP TABLE passport_audit_events;
ALTER TABLE t8_audit_events RENAME TO passport_audit_events;
CREATE INDEX "ix_passport_audit_events_batch_id" ON "passport_audit_events" ("batch_id");
CREATE INDEX "ix_passport_audit_events_passport_revision_id" ON "passport_audit_events" ("passport_revision_id");
CREATE INDEX "ix_passport_audit_events_actor_user_id" ON "passport_audit_events" ("actor_user_id");
CREATE INDEX "ix_passport_audit_events_batch_id_created_at_id" ON "passport_audit_events" ("batch_id","created_at","id");
CREATE INDEX "ix_passport_audit_events_entity_type_entity_id_created_at" ON "passport_audit_events" ("entity_type","entity_id","created_at");
CREATE TRIGGER "freeze_passport_audit_events_update" BEFORE UPDATE ON "passport_audit_events" WHEN 1 BEGIN SELECT RAISE(ABORT,'passport_audit_events frozen'); END;
CREATE TRIGGER "freeze_passport_audit_events_delete" BEFORE DELETE ON "passport_audit_events" WHEN 1 BEGIN SELECT RAISE(ABORT,'passport_audit_events frozen'); END;

CREATE TABLE review_records (
 id TEXT PRIMARY KEY NOT NULL CHECK(length(id)=36 AND substr(id,15,1)='4'),
 batch_id TEXT NOT NULL REFERENCES batches(id) ON UPDATE RESTRICT ON DELETE RESTRICT,
 attempt_number INTEGER NOT NULL CHECK(attempt_number>0),
 decision TEXT NOT NULL DEFAULT 'pending' CHECK(decision IN ('pending','approved','rejected')),
 candidate_input TEXT NOT NULL CHECK(json_valid(candidate_input) AND length(CAST(candidate_input AS BLOB))<=4194304),
 candidate_hash TEXT NOT NULL CHECK(length(candidate_hash)=64 AND candidate_hash NOT GLOB '*[^0-9a-f]*'),
 preview_hash TEXT NOT NULL CHECK(length(preview_hash)=64 AND preview_hash NOT GLOB '*[^0-9a-f]*'),
 source_edit_version INTEGER NOT NULL CHECK(source_edit_version>=0),
 schema_version TEXT NOT NULL CHECK(length(schema_version)<=16),
 builder_version TEXT NOT NULL CHECK(length(builder_version)<=64),
 submitted_by INTEGER NOT NULL REFERENCES sys_user(user_id) ON DELETE RESTRICT,
 submitted_at TEXT NOT NULL CHECK(length(submitted_at)=24 AND substr(submitted_at,24,1)='Z' AND julianday(submitted_at) IS NOT NULL),
 contributors TEXT NOT NULL CHECK(json_valid(contributors) AND json_type(contributors)='array'),
 reviewed_by INTEGER REFERENCES sys_user(user_id) ON DELETE RESTRICT,
 reviewed_at TEXT CHECK(reviewed_at IS NULL OR (length(reviewed_at)=24 AND substr(reviewed_at,24,1)='Z' AND julianday(reviewed_at) IS NOT NULL)),
 comment TEXT CHECK(length(comment)<=2000),
 rejection_reason TEXT CHECK(length(rejection_reason)<=2000),
 UNIQUE(batch_id,attempt_number), UNIQUE(batch_id,id),
 CHECK((decision='pending' AND reviewed_by IS NULL AND reviewed_at IS NULL AND comment IS NULL AND rejection_reason IS NULL) OR (decision='approved' AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL AND rejection_reason IS NULL) OR (decision='rejected' AND reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL AND length(trim(rejection_reason))>0)),
 CHECK(reviewed_by IS NULL OR reviewed_by!=submitted_by)
);
CREATE UNIQUE INDEX uq_review_pending_batch ON review_records(batch_id) WHERE decision='pending';
CREATE INDEX ix_review_decision_submitted ON review_records(decision,submitted_at,id);
ALTER TABLE batches ADD COLUMN current_review_record_id TEXT REFERENCES review_records(id) ON UPDATE RESTRICT ON DELETE RESTRICT;
CREATE INDEX ix_batches_current_review ON batches(current_review_record_id);
CREATE TRIGGER review_no_delete BEFORE DELETE ON review_records BEGIN SELECT RAISE(ABORT,'review history immutable'); END;
CREATE TRIGGER review_frozen BEFORE UPDATE ON review_records WHEN
 OLD.decision!='pending' OR NEW.decision NOT IN ('approved','rejected') OR
 NEW.id IS NOT OLD.id OR NEW.batch_id IS NOT OLD.batch_id OR NEW.attempt_number IS NOT OLD.attempt_number OR
 NEW.candidate_input IS NOT OLD.candidate_input OR NEW.candidate_hash IS NOT OLD.candidate_hash OR NEW.preview_hash IS NOT OLD.preview_hash OR NEW.source_edit_version IS NOT OLD.source_edit_version OR NEW.schema_version IS NOT OLD.schema_version OR NEW.builder_version IS NOT OLD.builder_version OR NEW.submitted_by IS NOT OLD.submitted_by OR NEW.submitted_at IS NOT OLD.submitted_at OR NEW.contributors IS NOT OLD.contributors
 BEGIN SELECT RAISE(ABORT,'review candidate frozen'); END;
CREATE TRIGGER review_no_self BEFORE UPDATE ON review_records WHEN EXISTS(SELECT 1 FROM json_each(OLD.contributors) WHERE value=NEW.reviewed_by) BEGIN SELECT RAISE(ABORT,'self review prohibited'); END;
CREATE TRIGGER review_pointer_owner BEFORE UPDATE OF current_review_record_id ON batches WHEN NEW.current_review_record_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM review_records r WHERE r.id=NEW.current_review_record_id AND r.batch_id=NEW.id) BEGIN SELECT RAISE(ABORT,'review owner mismatch'); END;
CREATE TRIGGER review_input_frozen BEFORE UPDATE ON batches WHEN OLD.workflow_status='pending_review' AND NEW.workflow_status='pending_review' AND (NEW.current_review_record_id IS NOT OLD.current_review_record_id OR NEW.submitted_input IS NOT OLD.submitted_input OR NEW.submitted_content_hash IS NOT OLD.submitted_content_hash OR NEW.submitted_preview_hash IS NOT OLD.submitted_preview_hash OR NEW.submitted_edit_version IS NOT OLD.submitted_edit_version OR NEW.submitted_schema_version IS NOT OLD.submitted_schema_version OR NEW.submitted_builder_version IS NOT OLD.submitted_builder_version OR NEW.submitted_by IS NOT OLD.submitted_by OR NEW.submitted_at IS NOT OLD.submitted_at OR NEW.edit_version IS NOT OLD.edit_version) BEGIN SELECT RAISE(ABORT,'review input frozen'); END;
