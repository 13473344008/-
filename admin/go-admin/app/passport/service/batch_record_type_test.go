package service

import (
	"encoding/json"
	"go-admin/app/passport/publishing"
	"go-admin/app/passport/service/dto"
	"os"
	"testing"
)

func TestBatchTestCodeContract(t *testing.T) {
	for _, tc := range []struct {
		code, kind string
		valid      bool
	}{{"POTATO-001", "test", false}, {"CONTEST-001", "test", false}, {"TESTING-001", "test", false}, {"POTATO-TEST-001", "test", true}, {"TEST_001", "test", true}, {"TEST", "test", true}, {"POTATO-001", "commercial", true}} {
		t.Run(tc.code+tc.kind, func(t *testing.T) {
			if (validateBatchRecordCode(tc.code, tc.kind) == nil) != tc.valid {
				t.Fatal("contract mismatch")
			}
		})
	}
	// A rejected create must fail before any database access, even when record_type is omitted.
	for _, kind := range []string{"test", ""} {
		s := Batches{}
		_, err := s.CreateBatch(dto.CreateBatchRequest{BatchCode: "POTATO-001", RecordType: kind})
		if err == nil {
			t.Fatal("missing TEST accepted")
		}
	}
}
func TestCapturedPublishCodeRegression(t *testing.T) {
	fixture := os.Getenv("T13_FROZEN_INPUT")
	if fixture == "" {
		t.Skip("set T13_FROZEN_INPUT to a private frozen review fixture")
	}
	b, err := os.ReadFile(fixture)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = publishing.Build(b, 1, "2026-09-11T00:00:00.000Z"); err == nil {
		t.Fatal("original malformed test code unexpectedly valid")
	}
	var v map[string]interface{}
	if err = json.Unmarshal(b, &v); err != nil {
		t.Fatal(err)
	}
	v["batch"].(map[string]interface{})["batch_code"] = "POTATO-FLAKES-TEST-20260911-001"
	b, _ = json.Marshal(v)
	if _, err = publishing.Build(b, 1, "2026-09-11T00:00:00.000Z"); err != nil {
		t.Fatal(err)
	}
}
