package publishing

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"math/big"
	"reflect"
	"regexp"
	"strings"
	"sync"
	"time"
	"unicode/utf8"
)

//go:embed schema-1.0.json
var Schema10 []byte
var schemaOnce sync.Once
var schemaRoot map[string]interface{}
var schemaLoadError error

// ValidatePayload implements the closed keyword vocabulary used by the embedded 1.0 contract.
// It is not advertised as a general-purpose JSON Schema implementation. External schemas are not loaded.
func ValidatePayload(data []byte) error {
	if len(data) > MaxPayloadBytes {
		return fmt.Errorf("public payload exceeds 1 MiB")
	}
	value, e := Decode(data)
	if e != nil {
		return e
	}
	schemaOnce.Do(func() {
		v, e := Decode(Schema10)
		if e != nil {
			schemaLoadError = e
			return
		}
		schemaRoot = v.(map[string]interface{})
	})
	if schemaLoadError != nil {
		return schemaLoadError
	}
	if e = validateNode(schemaRoot, value, "$"); e != nil {
		return e
	}
	return validateSemantics(value.(map[string]interface{}))
}
func validateNode(schema map[string]interface{}, value interface{}, path string) error {
	fail := func(rule string) error { return fmt.Errorf("public schema %s: %s", path, rule) }
	if ref, ok := schema["$ref"].(string); ok {
		if !strings.HasPrefix(ref, "#/$defs/") {
			return fail("unsupported reference")
		}
		defs := schemaRoot["$defs"].(map[string]interface{})
		target, ok := defs[strings.TrimPrefix(ref, "#/$defs/")].(map[string]interface{})
		if !ok {
			return fail("missing definition")
		}
		if e := validateNode(target, value, path); e != nil {
			return e
		}
	}
	if want, ok := schema["const"]; ok && !reflect.DeepEqual(want, value) {
		return fail("const")
	}
	if list, ok := schema["enum"].([]interface{}); ok {
		found := false
		for _, v := range list {
			found = found || reflect.DeepEqual(v, value)
		}
		if !found {
			return fail("enum")
		}
	}
	for _, kind := range []string{"allOf", "anyOf", "oneOf"} {
		if list, ok := schema[kind].([]interface{}); ok {
			n := 0
			for _, s := range list {
				if validateNode(s.(map[string]interface{}), value, path) == nil {
					n++
				}
			}
			if kind == "allOf" && n != len(list) || kind == "anyOf" && n == 0 || kind == "oneOf" && n != 1 {
				return fail(kind)
			}
		}
	}
	if cond, ok := schema["if"].(map[string]interface{}); ok {
		key := "else"
		if validateNode(cond, value, path) == nil {
			key = "then"
		}
		if next, ok := schema[key].(map[string]interface{}); ok {
			if e := validateNode(next, value, path); e != nil {
				return e
			}
		}
	}
	if typ, ok := schema["type"].(string); ok {
		valid := false
		switch typ {
		case "null":
			valid = value == nil
		case "object":
			_, valid = value.(map[string]interface{})
		case "array":
			_, valid = value.([]interface{})
		case "string":
			_, valid = value.(string)
		case "boolean":
			_, valid = value.(bool)
		case "integer":
			if n, ok := value.(json.Number); ok {
				rat, ok := new(big.Rat).SetString(string(n))
				valid = ok && rat.IsInt()
			}
		default:
			return fail("unsupported type")
		}
		if !valid {
			return fail("type " + typ)
		}
	}
	if obj, ok := value.(map[string]interface{}); ok {
		if required, ok := schema["required"].([]interface{}); ok {
			for _, k := range required {
				if _, ok := obj[k.(string)]; !ok {
					return fail("required " + k.(string))
				}
			}
		}
		props, _ := schema["properties"].(map[string]interface{})
		for k, v := range obj {
			if sub, ok := props[k].(map[string]interface{}); ok {
				if e := validateNode(sub, v, path+"."+k); e != nil {
					return e
				}
			} else if schema["additionalProperties"] == false {
				return fail("unknown field " + k)
			}
		}
	}
	if arr, ok := value.([]interface{}); ok {
		if n, ok := schema["minItems"].(json.Number); ok && int64(len(arr)) < number(n) {
			return fail("minItems")
		}
		if n, ok := schema["maxItems"].(json.Number); ok && int64(len(arr)) > number(n) {
			return fail("maxItems")
		}
		seen := map[string]bool{}
		for i, v := range arr {
			if sub, ok := schema["items"].(map[string]interface{}); ok {
				if e := validateNode(sub, v, fmt.Sprintf("%s[%d]", path, i)); e != nil {
					return e
				}
			}
			if schema["uniqueItems"] == true {
				raw, e := Canonical(v)
				if e != nil {
					return e
				}
				if seen[string(raw)] {
					return fail("uniqueItems")
				}
				seen[string(raw)] = true
			}
		}
	}
	if s, ok := value.(string); ok {
		n := int64(utf8.RuneCountInString(s))
		if min, ok := schema["minLength"].(json.Number); ok && n < number(min) {
			return fail("minLength")
		}
		if max, ok := schema["maxLength"].(json.Number); ok && n > number(max) {
			return fail("maxLength")
		}
		if pattern, ok := schema["pattern"].(string); ok {
			pattern = strings.ReplaceAll(pattern, `(?![\s\S])`, `$`)
			re, e := regexp.Compile(pattern)
			if e != nil {
				return fail("unsupported pattern")
			}
			if !re.MatchString(s) {
				return fail("pattern")
			}
		}
		if format, ok := schema["format"].(string); ok {
			layout := "2006-01-02"
			if format == "date-time" {
				layout = time.RFC3339Nano
			}
			t, e := time.Parse(layout, s)
			if e != nil || t.Year() < 1 {
				return fail("format")
			}
		}
	}
	if n, ok := value.(json.Number); ok {
		rat, valid := new(big.Rat).SetString(string(n))
		if !valid {
			return fail("number")
		}
		for _, key := range []string{"minimum", "maximum"} {
			if limit, ok := schema[key].(json.Number); ok {
				bound, _ := new(big.Rat).SetString(string(limit))
				cmp := rat.Cmp(bound)
				if key == "minimum" && cmp < 0 || key == "maximum" && cmp > 0 {
					return fail(key)
				}
			}
		}
	}
	return nil
}
func number(n json.Number) int64 { v, _ := n.Int64(); return v }
