package publishing

import (
	"encoding/json"
	"fmt"
	"math/big"
	"strings"
)

func arr(v interface{}) []interface{}          { a, _ := v.([]interface{}); return a }
func obj(v interface{}) map[string]interface{} { m, _ := v.(map[string]interface{}); return m }
func str(v interface{}) string                 { s, _ := v.(string); return s }
func Decimal(s string) string {
	neg := strings.HasPrefix(s, "-")
	s = strings.TrimPrefix(s, "-")
	parts := strings.SplitN(s, ".", 2)
	whole := strings.TrimLeft(parts[0], "0")
	if whole == "" {
		whole = "0"
	}
	if len(parts) == 2 {
		fraction := strings.TrimRight(parts[1], "0")
		if fraction != "" {
			whole += "." + fraction
		}
	}
	if neg && whole != "0" {
		whole = "-" + whole
	}
	return whole
}

func rat(v interface{}) *big.Rat {
	if v == nil {
		return nil
	}
	r, _ := new(big.Rat).SetString(str(v))
	return r
}
func validateSemantics(p map[string]interface{}) error {
	fail := func(s string) error { return fmt.Errorf("public semantics: %s", s) }
	b := obj(p["batch"])
	if str(b["expiry_date"]) < str(b["production_date"]) {
		return fail("date order")
	}
	if p["record_type"] == "test" && !hasTestSegment(str(b["code"])) {
		return fail("test code")
	}
	var walk func(interface{}) error
	walk = func(v interface{}) error {
		switch x := v.(type) {
		case string:
			if strings.ContainsAny(x, "<>\x00") {
				return fail("unsafe plain text")
			}
		case []interface{}:
			for _, i := range x {
				if e := walk(i); e != nil {
					return e
				}
			}
		case map[string]interface{}:
			for k, i := range x {
				switch k {
				case "quantity", "numeric_value", "standard_value", "min_limit", "max_limit":
					if i != nil && str(i) != Decimal(str(i)) {
						return fail("noncanonical decimal")
					}
				}
				if e := walk(i); e != nil {
					return e
				}
			}
		}
		return nil
	}
	if e := walk(p); e != nil {
		return e
	}
	if q := rat(obj(p["packaging"])["quantity"]); q != nil && q.Sign() <= 0 {
		return fail("quantity must be positive")
	}
	sets := map[string]map[string]map[string]interface{}{}
	for group, key := range map[string]string{"process": "step_key", "inspection": "code", "certifications": "key", "custom_sections": "key", "assets": "key"} {
		seen := map[string]map[string]interface{}{}
		for _, v := range arr(p[group]) {
			m := obj(v)
			k := str(m[key])
			if seen[k] != nil {
				return fail("duplicate " + group + " key")
			}
			seen[k] = m
		}
		sets[group] = seen
	}
	refs := map[string]bool{}
	productImages := 0
	for key, a := range sets["assets"] {
		hash := str(a["sha256"])
		ext := map[string]string{"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp", "application/pdf": "pdf"}[str(a["mime_type"])]
		if len(hash) != 64 || str(a["path"]) != "assets/sha256/"+hash[:2]+"/"+hash+"."+ext {
			return fail("asset hash path")
		}
		if a["role"] == "product_image" {
			productImages++
			refs[key] = true
		}
	}
	if productImages > 1 {
		return fail("multiple primary images")
	}
	for _, group := range []string{"inspection", "certifications", "custom_sections"} {
		for _, m := range sets[group] {
			for _, k := range arr(m["asset_keys"]) {
				if sets["assets"][str(k)] == nil {
					return fail("dangling asset")
				}
				refs[str(k)] = true
			}
		}
	}
	for k := range sets["assets"] {
		if !refs[k] {
			return fail("unreferenced asset")
		}
	}
	for _, i := range sets["inspection"] {
		lo, hi, val := rat(i["min_limit"]), rat(i["max_limit"]), rat(i["numeric_value"])
		if lo != nil && hi != nil && lo.Cmp(hi) > 0 {
			return fail("inspection limits")
		}
		if val != nil && (lo != nil || hi != nil) && (i["judgement"] == "pass" || i["judgement"] == "fail") {
			pass := true
			if lo != nil {
				c := val.Cmp(lo)
				pass = pass && (c > 0 || c == 0 && i["min_inclusive"] == true)
			}
			if hi != nil {
				c := val.Cmp(hi)
				pass = pass && (c < 0 || c == 0 && i["max_inclusive"] == true)
			}
			if pass != (i["judgement"] == "pass") {
				return fail("numeric judgement contradiction")
			}
		}
	}
	for _, c := range sets["certifications"] {
		if c["valid_from"] != nil && c["valid_until"] != nil && str(c["valid_from"]) > str(c["valid_until"]) {
			return fail("certificate dates")
		}
	}
	for _, s := range sets["custom_sections"] {
		if e := sectionStructure(s); e != nil {
			return e
		}
	}
	loc := obj(p["localization"])
	langs := map[string]bool{str(loc["source_language"]): true}
	for _, v := range arr(loc["translations"]) {
		tr := obj(v)
		l := str(tr["language_code"])
		if langs[l] {
			return fail("duplicate/source translation")
		}
		langs[l] = true
		for group, key := range map[string]string{"process": "step_key", "inspection": "code", "certifications": "key", "custom_sections": "key"} {
			seen := map[string]bool{}
			for _, x := range arr(tr[group]) {
				m := obj(x)
				k := str(m[key])
				source := sets[group][k]
				if source == nil || seen[k] {
					return fail("translation adds/duplicates structural key")
				}
				seen[k] = true
				if group == "custom_sections" {
					if source["type"] != m["type"] {
						return fail("translated section type")
					}
					if e := sectionStructure(m); e != nil {
						return e
					}
					for _, part := range []string{"items", "columns"} {
						a, c := arr(obj(source["content"])[part]), arr(obj(m["content"])[part])
						if len(a) != len(c) {
							return fail("translated section structure")
						}
						for j := range a {
							if obj(a[j])["key"] != obj(c[j])["key"] {
								return fail("translated section key")
							}
						}
					}
					if len(arr(obj(source["content"])["rows"])) != len(arr(obj(m["content"])["rows"])) {
						return fail("translated row count")
					}
				}
			}
		}
	}
	available := arr(loc["available_languages"])
	if len(langs) != len(available) {
		return fail("available languages")
	}
	for _, l := range available {
		if !langs[str(l)] {
			return fail("unapproved language")
		}
	}
	pub := obj(p["publication"])
	if pub["kind"] == "rollback" {
		n := number(pub["version_number"].(json.Number))
		s, ok := pub["source_version_number"].(json.Number)
		if !ok || number(s) >= n {
			return fail("rollback source")
		}
	}
	return nil
}
func sectionStructure(s map[string]interface{}) error {
	c := obj(s["content"])
	for _, part := range []string{"items", "columns"} {
		seen := map[string]bool{}
		for _, v := range arr(c[part]) {
			k := str(obj(v)["key"])
			if seen[k] {
				return fmt.Errorf("duplicate section key")
			}
			seen[k] = true
		}
	}
	if s["type"] == "table" {
		cols := arr(c["columns"])
		if len(cols) == 0 {
			return fmt.Errorf("empty table columns")
		}
		for _, v := range arr(c["rows"]) {
			if len(arr(obj(v)["cells"])) != len(cols) {
				return fmt.Errorf("table row width")
			}
		}
	}
	return nil
}

// Match the approved Public Payload 1.0 TEST segment contract.
func hasTestSegment(code string) bool {
	for _, part := range strings.FieldsFunc(code, func(r rune) bool { return r == '-' || r == '_' }) {
		if part == "TEST" {
			return true
		}
	}
	return false
}
