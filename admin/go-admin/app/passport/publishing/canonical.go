// Package publishing builds and validates the public contract independently of database models.
package publishing

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"sort"
	"strconv"
	"unicode/utf8"
)

const MaxPayloadBytes = 1024 * 1024

func Hash(data []byte) string { h := sha256.Sum256(data); return hex.EncodeToString(h[:]) }

// Decode rejects duplicate keys, invalid UTF-8 and trailing values. Numbers retain exact lexemes.
func Decode(data []byte) (interface{}, error) {
	if !utf8.Valid(data) {
		return nil, fmt.Errorf("invalid UTF-8")
	}
	d := json.NewDecoder(bytes.NewReader(data))
	d.UseNumber()
	var read func(int) (interface{}, error)
	read = func(depth int) (interface{}, error) {
		if depth > 64 {
			return nil, fmt.Errorf("JSON nesting limit")
		}
		tok, e := d.Token()
		if e != nil {
			return nil, e
		}
		if delim, ok := tok.(json.Delim); ok {
			switch delim {
			case '{':
				m := map[string]interface{}{}
				for d.More() {
					k, e := d.Token()
					if e != nil {
						return nil, e
					}
					key, ok := k.(string)
					if !ok {
						return nil, fmt.Errorf("invalid key")
					}
					if _, exists := m[key]; exists {
						return nil, fmt.Errorf("duplicate JSON key")
					}
					v, e := read(depth + 1)
					if e != nil {
						return nil, e
					}
					m[key] = v
				}
				if _, e = d.Token(); e != nil {
					return nil, e
				}
				return m, nil
			case '[':
				a := []interface{}{}
				for d.More() {
					v, e := read(depth + 1)
					if e != nil {
						return nil, e
					}
					a = append(a, v)
				}
				if _, e = d.Token(); e != nil {
					return nil, e
				}
				return a, nil
			default:
				return nil, fmt.Errorf("invalid JSON delimiter")
			}
		}
		return tok, nil
	}
	v, e := read(0)
	if e != nil {
		return nil, e
	}
	if _, e = d.Token(); e != io.EOF {
		return nil, fmt.Errorf("trailing JSON")
	}
	return v, nil
}

// Canonical sorts object keys by UTF-8 order (Unicode scalar order), preserves array order,
// writes exact safe integers, and uses one fixed JSON string escaping convention.
// Decimal business facts must be strings; floating point is deliberately not accepted.
func Canonical(v interface{}) ([]byte, error) {
	var out bytes.Buffer
	var write func(interface{}) error
	write = func(v interface{}) error {
		switch x := v.(type) {
		case nil:
			out.WriteString("null")
		case bool:
			if x {
				out.WriteString("true")
			} else {
				out.WriteString("false")
			}
		case string:
			if !utf8.ValidString(x) {
				return fmt.Errorf("invalid UTF-8 string")
			}
			var b bytes.Buffer
			encoder := json.NewEncoder(&b)
			encoder.SetEscapeHTML(false)
			if e := encoder.Encode(x); e != nil {
				return e
			}
			out.Write(bytes.TrimSuffix(b.Bytes(), []byte("\n")))
		case int:
			return write(int64(x))
		case int64:
			if x > 9007199254740991 || x < -9007199254740991 {
				return fmt.Errorf("unsafe integer")
			}
			out.WriteString(strconv.FormatInt(x, 10))
		case json.Number:
			n, e := strconv.ParseInt(string(x), 10, 64)
			if e != nil {
				return fmt.Errorf("only exact integers allowed")
			}
			return write(n)
		case []interface{}:
			out.WriteByte('[')
			for i, item := range x {
				if i > 0 {
					out.WriteByte(',')
				}
				if e := write(item); e != nil {
					return e
				}
			}
			out.WriteByte(']')
		case map[string]interface{}:
			keys := make([]string, 0, len(x))
			for k := range x {
				keys = append(keys, k)
			}
			sort.Strings(keys)
			out.WriteByte('{')
			for i, k := range keys {
				if i > 0 {
					out.WriteByte(',')
				}
				if e := write(k); e != nil {
					return e
				}
				out.WriteByte(':')
				if e := write(x[k]); e != nil {
					return e
				}
			}
			out.WriteByte('}')
		default:
			return fmt.Errorf("unsupported canonical value type %T", v)
		}
		return nil
	}
	if e := write(v); e != nil {
		return nil, e
	}
	return out.Bytes(), nil
}
