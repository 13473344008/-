package service

import (
	"encoding/json"
	"go-admin/app/passport/models"
	"go-admin/app/passport/service/dto"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"strings"
	"testing"
)

func TestBatchResponseExcludesFrozenInput(t *testing.T) {
	db, e := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	if e != nil {
		t.Fatal(e)
	}
	if e = db.AutoMigrate(&models.Batch{}); e != nil {
		t.Fatal(e)
	}
	for _, q := range []string{"CREATE TABLE products(id TEXT, product_code TEXT)", "CREATE TABLE product_revisions(id TEXT, revision_number INTEGER)", "CREATE TABLE review_records(id TEXT, decision TEXT)", "CREATE TABLE batch_overrides(batch_id TEXT)", "CREATE TABLE inspection_items(batch_id TEXT)"} {
		if e = db.Exec(q).Error; e != nil {
			t.Fatal(e)
		}
	}
	raw := `{"image":"` + strings.Repeat("x", 5*1024*1024) + `"}`
	b := models.Batch{ID: "batch", BatchCode: "PF-TEST", WorkflowStatus: "pending_review", SubmittedInput: &raw}
	if e = db.Create(&b).Error; e != nil {
		t.Fatal(e)
	}
	s := Batches{}
	s.Orm = db
	s.Admin = true
	rows, n, e := s.ListBatches(dto.BatchQuery{})
	if e != nil || n != 1 || len(rows) != 1 {
		t.Fatalf("list: %v %d", e, n)
	}
	if rows[0].SubmittedInput != nil {
		t.Fatal("list reads frozen image snapshot")
	}
	encoded, e := json.Marshal(rows)
	if e != nil || len(encoded) > 4096 || strings.Contains(string(encoded), "submitted_input") {
		t.Fatal("oversized list response")
	}
	encoded, e = json.Marshal(BatchView{Batch: BatchRow{Batch: b}})
	if e != nil || len(encoded) > 4096 || strings.Contains(string(encoded), "submitted_input") {
		t.Fatal("snapshot exposed by batch detail")
	}
	var stored models.Batch
	if e = db.First(&stored, "id=?", b.ID).Error; e != nil || stored.SubmittedInput == nil || *stored.SubmittedInput != raw {
		t.Fatal("stored review snapshot changed")
	}
}
