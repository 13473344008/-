package publishing

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func candidate() []byte {
	return []byte(`{"schema":"review-v2","product_code":"TEST-P","batch":{"batch_code":"TEST-B","record_type":"test","content":{"production_date":"2026-09-10","expiry_date":"2027-09-10","quality_status":"pending","internal_note":"PRIVATE"}},"base":{"content":{"source_language":"en"},"translations":[]},"effective":[{"field_key":"product_name","value":"TEST RECORD"},{"field_key":"process","value":[]}],"inspections":[],"effective_sections":[],"assets":[]}`)
}
func built(t *testing.T) BuildResult {
	t.Helper()
	b, e := Build(candidate(), 1, "2026-09-10T00:00:00.000Z")
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func TestBuildDeterministic(t *testing.T) {
	a, b := built(t), built(t)
	if !bytes.Equal(a.Payload, b.Payload) || a.PayloadHash != Hash(a.Payload) {
		t.Fatal("unstable bytes")
	}
	c, e := Build(candidate(), 2, "2026-09-10T01:00:00.000Z")
	if e != nil || c.ContentHash != a.ContentHash || c.PayloadHash == a.PayloadHash {
		t.Fatal("hash domains")
	}
	if bytes.Contains(a.Payload, []byte("PRIVATE")) {
		t.Fatal("private leak")
	}
}
func TestCanonicalVectors(t *testing.T) {
	for _, tt := range []struct{ in, out string }{{`{"z":1,"a":"中文<>&"}`, `{"a":"中文<>&","z":1}`}, {`{"b":null,"a":[true,false]}`, `{"a":[true,false],"b":null}`}, {`{"x":"\u2028"}`, `{"x":"\u2028"}`}} {
		v, e := Decode([]byte(tt.in))
		if e != nil {
			t.Fatal(e)
		}
		b, e := Canonical(v)
		if e != nil || string(b) != tt.out {
			t.Fatalf("%s %v", b, e)
		}
	}
}
func TestDecodeRejects(t *testing.T) {
	for _, in := range []string{`{"x":1,"x":2}`, `{} {}`, "\xff", `[1,]`, strings.Repeat("[", 66) + strings.Repeat("]", 66)} {
		t.Run(fmt.Sprintf("%x", Hash([]byte(in))[:8]), func(t *testing.T) {
			if _, e := Decode([]byte(in)); e == nil {
				t.Fatal("accepted invalid JSON")
			}
		})
	}
}
func TestCanonicalRejectsFloatsAndUnsafeInts(t *testing.T) {
	for _, v := range []interface{}{1.2, json.Number("1.2"), json.Number("9007199254740992"), int64(-9007199254740992)} {
		if _, e := Canonical(v); e == nil {
			t.Fatal("accepted unsafe number")
		}
	}
}
func TestSchemaRejections(t *testing.T) {
	cases := []struct {
		name   string
		change func(map[string]interface{})
	}{
		{"unknown root", func(p map[string]interface{}) { p["internal_note"] = "secret" }},
		{"unknown nested", func(p map[string]interface{}) { obj(p["product"])["id"] = "uuid" }},
		{"schema version", func(p map[string]interface{}) { p["schema_version"] = "2.0" }},
		{"required", func(p map[string]interface{}) { delete(p, "inspection") }},
		{"missing marker", func(p map[string]interface{}) { p["notice"] = nil }},
		{"test batch code", func(p map[string]interface{}) { obj(p["batch"])["code"] = "NORMAL" }},
		{"traversal", func(p map[string]interface{}) { obj(p["batch"])["code"] = "../private" }},
		{"newline code", func(p map[string]interface{}) { obj(p["batch"])["code"] = "TEST-B\n" }},
		{"invalid date", func(p map[string]interface{}) { obj(p["batch"])["production_date"] = "2026-02-30" }},
		{"date order", func(p map[string]interface{}) { obj(p["batch"])["expiry_date"] = "2025-01-01" }},
		{"html text", func(p map[string]interface{}) { obj(p["product"])["name"] = "<script>x</script>" }},
		{"empty name", func(p map[string]interface{}) { obj(p["product"])["name"] = "" }},
		{"decimal number", func(p map[string]interface{}) { obj(p["packaging"])["quantity"] = json.Number("12") }},
		{"decimal trailing zero", func(p map[string]interface{}) { obj(p["packaging"])["quantity"] = "1.00" }},
		{"decimal negative zero", func(p map[string]interface{}) { obj(p["packaging"])["quantity"] = "-0" }},
		{"negative quantity", func(p map[string]interface{}) { obj(p["packaging"])["quantity"] = "-1" }},
		{"integer bound", func(p map[string]interface{}) {
			obj(p["publication"])["version_number"] = json.Number("9007199254740992")
		}},
		{"array bound", func(p map[string]interface{}) {
			a := []interface{}{}
			for i := 0; i < 101; i++ {
				a = append(a, map[string]interface{}{"step_key": fmt.Sprint(i), "label": "x"})
			}
			p["process"] = a
		}},
		{"duplicate steps", func(p map[string]interface{}) {
			p["process"] = []interface{}{map[string]interface{}{"step_key": "a", "label": "x"}, map[string]interface{}{"step_key": "a", "label": "y"}}
		}},
		{"missing language", func(p map[string]interface{}) {
			obj(p["localization"])["available_languages"] = []interface{}{"en", "fr"}
		}},
		{"duplicate languages", func(p map[string]interface{}) {
			obj(p["localization"])["available_languages"] = []interface{}{"en", "en"}
		}},
		{"source translation", func(p map[string]interface{}) {
			obj(p["localization"])["translations"] = []interface{}{map[string]interface{}{"language_code": "en"}}
		}},
		{"translated fact", func(p map[string]interface{}) {
			obj(p["localization"])["translations"] = []interface{}{map[string]interface{}{"language_code": "fr", "packaging": map[string]interface{}{"quantity": "12"}}}
		}},
		{"translated new key", func(p map[string]interface{}) {
			obj(p["localization"])["available_languages"] = []interface{}{"en", "fr"}
			obj(p["localization"])["translations"] = []interface{}{map[string]interface{}{"language_code": "fr", "inspection": []interface{}{map[string]interface{}{"code": "new", "name": "x"}}}}
		}},
		{"unreferenced asset", func(p map[string]interface{}) {
			hash := strings.Repeat("a", 64)
			p["assets"] = []interface{}{map[string]interface{}{"key": "a", "role": "attachment", "label": "x", "path": "assets/sha256/aa/" + hash + ".png", "mime_type": "image/png", "sha256": hash, "file_size": json.Number("3")}}
		}},
		{"dangling asset", func(p map[string]interface{}) {
			p["custom_sections"] = []interface{}{map[string]interface{}{"key": "s", "type": "text", "title": "x", "content": map[string]interface{}{"text": "a"}, "asset_keys": []interface{}{"absent"}}}
		}},
		{"table width", func(p map[string]interface{}) {
			p["custom_sections"] = []interface{}{map[string]interface{}{"key": "s", "type": "table", "title": "x", "content": map[string]interface{}{"columns": []interface{}{map[string]interface{}{"key": "a", "label": "A"}}, "rows": []interface{}{map[string]interface{}{"cells": []interface{}{}}}}, "asset_keys": []interface{}{}}}
		}},
	}
	for _, tt := range cases {
		t.Run(tt.name, func(t *testing.T) {
			b := built(t)
			v, _ := Decode(b.Payload)
			p := obj(v)
			tt.change(p)
			raw, e := json.Marshal(p)
			if e != nil {
				t.Fatal(e)
			}
			if ValidatePayload(raw) == nil {
				t.Fatal("accepted invalid payload")
			}
		})
	}
}
func TestMediaAndPaths(t *testing.T) {
	im := image.NewRGBA(image.Rect(0, 0, 2, 2))
	im.Set(0, 0, color.RGBA{255, 0, 0, 255})
	var b bytes.Buffer
	png.Encode(&b, im)
	source := b.Bytes()
	n, e := Normalize(source, "image/png")
	if e != nil {
		t.Fatal(e)
	}
	n2, e := Normalize(n, "image/png")
	if e != nil || !bytes.Equal(n, n2) {
		t.Fatal("unstable normalization")
	}
	for _, mime := range []string{"image/svg+xml", "text/html", "application/pdf", "image/jpeg"} {
		if _, e = Normalize(source, mime); e == nil {
			t.Fatal("accepted wrong MIME")
		}
	}
	if _, e = Normalize(make([]byte, MaxSourceBytes+1), "image/png"); e == nil {
		t.Fatal("oversize")
	}
	root, _ := filepath.EvalSymlinks(t.TempDir())
	os.WriteFile(filepath.Join(root, "source.png"), source, 0600)
	os.Symlink(filepath.Join(root, "source.png"), filepath.Join(root, "link"))
	for _, key := range []string{"../source.png", "/source.png", "link", "x\\file", "a/../source.png"} {
		if _, e := ReadPrivate(root, key); e == nil {
			t.Fatal("unsafe path", key)
		}
	}
}
func TestImmutableAndAtomicStorage(t *testing.T) {
	root, _ := filepath.EvalSymlinks(t.TempDir())
	pub, work := filepath.Join(root, "public"), filepath.Join(root, "private")
	os.Mkdir(pub, 0755)
	os.Mkdir(work, 0700)
	s, e := OpenStore(pub, work)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	if e = Immutable(s.Public, "assets/test.png", []byte("first"), 0644); e != nil {
		t.Fatal(e)
	}
	if e = Immutable(s.Public, "assets/test.png", []byte("second"), 0644); e == nil {
		t.Fatal("overwrite")
	}
	if e = Immutable(s.Public, "assets/test.png", []byte("first"), 0644); e != nil {
		t.Fatal(e)
	}
	if _, e = s.Switch("../secret", []byte("x")); e == nil {
		t.Fatal("unsafe code")
	}
	if _, e = s.Switch("TEST-B", []byte("first")); e != nil {
		t.Fatal(e)
	}
	if _, e = s.Switch("TEST-B", []byte("second")); e != nil {
		t.Fatal(e)
	}
	b, e := s.Current("TEST-B")
	if e != nil || string(b) != "second" {
		t.Fatal("head")
	}
	if _, e = OpenStore(pub, pub); e == nil {
		t.Fatal("mixed public private root")
	}
	if e = os.Symlink(work, filepath.Join(pub, "escape")); e != nil {
		t.Fatal(e)
	}
	if e = Immutable(s.Public, "escape/test", []byte("private"), 0600); e == nil {
		t.Fatal("symlink write")
	}
}
func TestApprovedTranslationsAndClear(t *testing.T) {
	v, _ := Decode(candidate())
	c := obj(v)
	base := obj(c["base"])
	base["translations"] = []interface{}{map[string]interface{}{"language_code": "fr", "translation_status": "approved", "product_name": "Produit approuvé", "raw_material_name": "NEVER FALL BACK"}, map[string]interface{}{"language_code": "de", "translation_status": "draft", "product_name": "PRIVATE DRAFT"}}
	c["effective"] = append(arr(c["effective"]), map[string]interface{}{"field_key": "raw_material_name", "value": nil})
	c["overrides"] = []interface{}{map[string]interface{}{"field_key": "raw_material_name", "operation": "clear", "id": "o"}}
	raw, e := Canonical(c)
	if e != nil {
		t.Fatal(e)
	}
	b, e := Build(raw, 1, "2026-09-10T00:00:00.000Z")
	if e != nil {
		t.Fatal(e)
	}
	if bytes.Contains(b.Payload, []byte("PRIVATE DRAFT")) || bytes.Contains(b.Payload, []byte("NEVER FALL BACK")) {
		t.Fatal("draft translation/clear leaked")
	}
	out, _ := Decode(b.Payload)
	translations := arr(obj(obj(out)["localization"])["translations"])
	if len(translations) != 1 || obj(obj(translations[0])["raw_material"])["name"] != nil {
		t.Fatal("clear not preserved")
	}
}
func TestHiddenSectionsAndUnknownPrivateFields(t *testing.T) {
	v, _ := Decode(candidate())
	c := obj(v)
	c["internal_password"] = "PRIVATE SECRET"
	c["hidden_sections"] = []interface{}{map[string]interface{}{"section_key": "hidden", "title": "PRIVATE HIDDEN"}}
	c["effective_sections"] = []interface{}{map[string]interface{}{"section_key": "private", "is_public": false, "title": "PRIVATE SECTION"}}
	raw, _ := Canonical(c)
	b, e := Build(raw, 1, "2026-09-10T00:00:00.000Z")
	if e != nil {
		t.Fatal(e)
	}
	if bytes.Contains(b.Payload, []byte("PRIVATE")) {
		t.Fatal("private whitelist leak")
	}
}
func TestEmbeddedSchemaVocabulary(t *testing.T) {
	v, e := Decode(Schema10)
	if e != nil {
		t.Fatal(e)
	}
	allowed := map[string]bool{}
	for _, k := range strings.Fields("$schema title $defs $ref type properties required additionalProperties const enum allOf anyOf oneOf if then else items minItems maxItems uniqueItems minLength maxLength pattern format minimum maximum description") {
		allowed[k] = true
	}
	var walk func(map[string]interface{})
	walk = func(m map[string]interface{}) {
		for k, v := range m {
			if !allowed[k] {
				t.Fatalf("unsupported schema keyword %s", k)
			}
			switch k {
			case "$defs", "properties":
				for _, sub := range obj(v) {
					walk(obj(sub))
				}
			case "items", "if", "then", "else":
				walk(obj(v))
			case "allOf", "anyOf", "oneOf":
				for _, sub := range arr(v) {
					walk(obj(sub))
				}
			}
		}
	}
	walk(obj(v))
}
func TestAtomicReadersNeverSeePartial(t *testing.T) {
	root, _ := filepath.EvalSymlinks(t.TempDir())
	pub, work := filepath.Join(root, "public"), filepath.Join(root, "private")
	os.Mkdir(pub, 0755)
	os.Mkdir(work, 0700)
	s, e := OpenStore(pub, work)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	a, b := bytes.Repeat([]byte("a"), 100000), bytes.Repeat([]byte("b"), 100000)
	s.Switch("TEST-RACE", a)
	done := make(chan error, 1)
	go func() {
		for i := 0; i < 50; i++ {
			if _, e := s.Switch("TEST-RACE", b); e != nil {
				done <- e
				return
			}
			if _, e := s.Switch("TEST-RACE", a); e != nil {
				done <- e
				return
			}
		}
		done <- nil
	}()
	for {
		select {
		case e := <-done:
			if e != nil {
				t.Fatal(e)
			}
			return
		default:
			raw, e := s.Current("TEST-RACE")
			if e != nil || !bytes.Equal(raw, a) && !bytes.Equal(raw, b) {
				t.Fatal("partial/torn file")
			}
		}
	}
}
func TestMalformedAndOversizedImage(t *testing.T) {
	for _, data := range [][]byte{[]byte("<html>image</html>"), []byte("<svg></svg>"), {0x7f, 'E', 'L', 'F'}} {
		if _, e := Normalize(data, "image/png"); e == nil {
			t.Fatal("non-image accepted")
		}
	}
	im := image.NewRGBA(image.Rect(0, 0, 4097, 1))
	var b bytes.Buffer
	png.Encode(&b, im)
	if _, e := Normalize(b.Bytes(), "image/png"); e == nil {
		t.Fatal("oversized dimensions accepted")
	}
}
