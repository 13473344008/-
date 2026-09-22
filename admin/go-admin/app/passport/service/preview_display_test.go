package service

import (
	"bytes"
	"encoding/json"
	"go-admin/app/passport/models"
	"go-admin/app/passport/publishing"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"image"
	"image/color"
	"image/png"
	"testing"
)

func TestDisplayPreviewPreservesFrozenRecord(t *testing.T) {
	db, e := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	if e != nil {
		t.Fatal(e)
	}
	if e = db.AutoMigrate(&models.Batch{}, &models.ReviewRecord{}); e != nil {
		t.Fatal(e)
	}
	im := image.NewRGBA(image.Rect(0, 0, 1400, 800))
	noise := uint32(12345)
	for y := 0; y < 800; y++ {
		for x := 0; x < 1400; x++ {
			noise ^= noise << 13
			noise ^= noise >> 17
			noise ^= noise << 5
			im.SetRGBA(x, y, color.RGBA{uint8(noise), uint8(noise >> 8), uint8(noise >> 16), 255})
		}
	}
	var b bytes.Buffer
	if e = png.Encode(&b, im); e != nil {
		t.Fatal(e)
	}
	a := ReviewAsset{AssetKey: "photo", AssetRole: "product_image", PublicLabel: "Test", Publish: true, NormalizedPreview: b.Bytes(), NormalizedSHA256: publishing.Hash(b.Bytes()), NormalizedSize: int64(b.Len())}
	var c map[string]interface{}
	json.Unmarshal([]byte(`{"schema":"review-v2","product_code":"TEST-P","batch":{"id":"batch","batch_code":"TEST-B","record_type":"test","content":{"production_date":"2026-09-10","expiry_date":"2027-09-10","quality_status":"pending"}},"base":{"content":{"source_language":"en"},"translations":[]},"effective":[{"field_key":"product_name","value":"TEST RECORD"},{"field_key":"process","value":[]}],"inspections":[],"effective_sections":[],"assets":[]}`), &c)
	c["assets"] = []ReviewAsset{a}
	raw, _ := json.Marshal(c)
	record := models.ReviewRecord{ID: "review", BatchID: "batch", CandidateInput: string(raw), CandidateHash: rawHash(string(raw)), SourceEditVersion: 7}
	if e = db.Create(&models.Batch{ID: "batch"}).Error; e != nil {
		t.Fatal(e)
	}
	if e = db.Create(&record).Error; e != nil {
		t.Fatal(e)
	}
	s := Reviews{}
	s.Orm = db
	s.Admin = true
	old, e := s.Preview("batch", "review", "review")
	if e != nil {
		t.Fatal(e)
	}
	display, e := s.DisplayPreview("batch", "review", "review")
	if e != nil {
		t.Fatal(e)
	}
	if display.SourceHash != old.SourceHash || display.EditVersion != 7 || !bytes.Equal(old.Assets["photo"], b.Bytes()) {
		t.Fatal("source changed")
	}
	cfg, kind, e := image.DecodeConfig(bytes.NewReader(display.Assets["photo"]))
	if e != nil || kind != "jpeg" || cfg.Width != 1200 || cfg.Height != 685 || display.AssetMimeTypes["photo"] != "image/jpeg" {
		t.Fatalf("bad display image: %v %s %v", cfg, kind, e)
	}
	if len(display.Assets["photo"]) >= len(old.Assets["photo"]) {
		t.Fatal("display not smaller")
	}
	var stored models.ReviewRecord
	db.First(&stored, "id=?", "review")
	if stored.CandidateInput != record.CandidateInput || stored.CandidateHash != record.CandidateHash {
		t.Fatal("frozen record changed")
	}
	db.Model(&stored).Update("candidate_hash", "tampered")
	if _, e = s.DisplayPreview("batch", "review", "review"); e == nil {
		t.Fatal("invalid hash accepted")
	}
}
