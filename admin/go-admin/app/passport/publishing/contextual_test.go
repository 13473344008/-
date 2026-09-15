package publishing

import (
	"strings"
	"testing"
)

func TestContextualImageVersionAndPlacement(t *testing.T) {
	v, _ := Decode(candidate())
	c := obj(v)
	c["assets"] = []interface{}{map[string]interface{}{"publish": true, "asset_key": "photo", "asset_role": "section_image", "display_target": "storage_conditions", "public_label": "Storage", "normalized_sha256": strings.Repeat("a", 64), "normalized_size": 123, "owner_id": "base"}}
	raw, _ := Canonical(c)
	b, e := Build(raw, 1, "2026-09-15T00:00:00.000Z")
	if e != nil {
		t.Fatal(e)
	}
	out, _ := Decode(b.Payload)
	if obj(out)["schema_version"] != "1.1" || b.Assets[0]["display_target"] != "storage_conditions" {
		t.Fatal("placement was lost")
	}
	if e = ValidatePayload(b.Payload); e != nil {
		t.Fatal(e)
	}
	obj(arr(c["assets"])[0])["display_target"] = "process:missing"
	raw, _ = Canonical(c)
	if _, e = Build(raw, 1, "2026-09-15T00:00:00.000Z"); e == nil {
		t.Fatal("orphaned step image accepted")
	}
	obj(arr(c["assets"])[0])["publish"] = false
	raw, _ = Canonical(c)
	b, e = Build(raw, 1, "2026-09-15T00:00:00.000Z")
	if e != nil || len(b.Assets) != 0 || FrozenSchemaVersion(raw) != "1.0" {
		t.Fatal("private image leaked or changed legacy schema")
	}
}
