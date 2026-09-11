package apis

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/gin-gonic/gin"
	"io"
)

// Reject duplicate keys, unknown fields, trailing values and oversized requests.
func strict(c *gin.Context, out interface{}) error {
	b, e := io.ReadAll(io.LimitReader(c.Request.Body, 1048577))
	if e != nil || len(b) > 1048576 {
		return fmt.Errorf("请求内容过大或无法读取")
	}
	scan := json.NewDecoder(bytes.NewReader(b))
	var walk func() error
	walk = func() error {
		t, e := scan.Token()
		if e != nil {
			return e
		}
		if d, ok := t.(json.Delim); ok {
			switch d {
			case '{':
				keys := map[string]bool{}
				for scan.More() {
					k, e := scan.Token()
					if e != nil {
						return e
					}
					key, ok := k.(string)
					if !ok || keys[key] {
						return fmt.Errorf("重复字段")
					}
					keys[key] = true
					if e = walk(); e != nil {
						return e
					}
				}
				_, e = scan.Token()
				return e
			case '[':
				for scan.More() {
					if e = walk(); e != nil {
						return e
					}
				}
				_, e = scan.Token()
				return e
			default:
				return fmt.Errorf("无效 JSON")
			}
		}
		return nil
	}
	if e = walk(); e != nil {
		return fmt.Errorf("请求字段重复或格式不正确")
	}
	if _, e = scan.Token(); e != io.EOF {
		return fmt.Errorf("请求只能包含一个 JSON 对象")
	}
	d := json.NewDecoder(bytes.NewReader(b))
	d.DisallowUnknownFields()
	if e = d.Decode(out); e != nil {
		return fmt.Errorf("请求含不允许的字段或字段类型不正确")
	}
	return nil
}
