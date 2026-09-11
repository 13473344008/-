package service

import (
	"bytes"
	"encoding/json"
	"fmt"
	"go-admin/app/passport/service/dto"
	"io"
	"regexp"
	"strings"
	"unicode/utf8"
)

const MaxSections = 100
const MaxSectionBytes = 262144

var sectionKey = regexp.MustCompile(`^[a-z][a-z0-9_-]{0,63}$`)
var contentKey = regexp.MustCompile(`^[A-Za-z0-9_-]{1,64}$`)
var unsafeText = regexp.MustCompile(`(?i)<\s*/?\s*[a-z!]|javascript\s*:|vbscript\s*:|data\s*:\s*text/html|on[a-z]+\s*=`)

func safeSectionText(s string, max int, required bool) bool {
	return utf8.ValidString(s) && utf8.RuneCountInString(s) <= max && (!required || strings.TrimSpace(s) != "") && !strings.ContainsRune(s, 0) && !unsafeText.MatchString(s)
}
func validSectionKey(s string) bool {
	if !sectionKey.MatchString(s) {
		return false
	}
	for _, k := range []string{"id", "product_code", "batch_code", "product_name", "base_product_revision_id", "product", "batch", "publication", "assets", "sections", "schema_version", "translations", "inspection", "inspections", "certifications", "constructor", "prototype", "__proto__", "created_by", "updated_by", "workflow_status", "content_hash"} {
		if s == k {
			return false
		}
	}
	for _, r := range OverrideRules {
		if s == r.FieldKey {
			return false
		}
	}
	return !strings.HasPrefix(s, "sys_") && !strings.HasPrefix(s, "internal_") && !strings.HasPrefix(s, "published_")
}

// Pointer fields distinguish missing/null properties from intentionally empty text.
type textSection struct {
	Text *string `json:"text"`
}
type gallerySection struct {
	Caption *string `json:"caption"`
}
type sectionPair struct {
	Key   string  `json:"key"`
	Label *string `json:"label"`
	Value *string `json:"value"`
}
type pairsSection struct {
	Items *[]sectionPair `json:"items"`
}
type sectionColumn struct {
	Key   string  `json:"key"`
	Label *string `json:"label"`
}
type sectionRow struct {
	Cells *[]*string `json:"cells"`
}
type tableSection struct {
	Columns *[]sectionColumn `json:"columns"`
	Rows    *[]sectionRow    `json:"rows"`
}

func decodeSection(raw json.RawMessage, v interface{}) error {
	if len(raw) == 0 || len(raw) > MaxSectionBytes || bytes.Equal(bytes.TrimSpace(raw), []byte("null")) {
		return invalid("模块 JSON 缺失或超过 256 KiB")
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.DisallowUnknownFields()
	if e := d.Decode(v); e != nil {
		return invalid("模块内容结构或字段不正确")
	}
	if d.Decode(new(interface{})) != io.EOF {
		return invalid("模块内容包含额外数据")
	}
	return nil
}
func validateSectionContent(kind string, raw json.RawMessage) (string, error) {
	bad := func() (string, error) {
		return "", invalid("模块内容缺少字段、超限、包含危险文本或重复键")
	}
	switch kind {
	case "text":
		var v textSection
		if e := decodeSection(raw, &v); e != nil {
			return "", e
		}
		if v.Text == nil || !safeSectionText(*v.Text, 10000, false) {
			return bad()
		}
		return "text", nil
	case "asset_gallery":
		var v gallerySection
		if e := decodeSection(raw, &v); e != nil {
			return "", e
		}
		if v.Caption == nil || !safeSectionText(*v.Caption, 4000, false) {
			return bad()
		}
		return "asset_gallery", nil
	case "key_value":
		var v pairsSection
		if e := decodeSection(raw, &v); e != nil {
			return "", e
		}
		if v.Items == nil || len(*v.Items) > 100 {
			return bad()
		}
		keys := []string{}
		seen := map[string]bool{}
		for _, p := range *v.Items {
			if !contentKey.MatchString(p.Key) || seen[p.Key] || p.Label == nil || p.Value == nil || !safeSectionText(*p.Label, 200, true) || !safeSectionText(*p.Value, 2000, false) {
				return bad()
			}
			seen[p.Key] = true
			keys = append(keys, p.Key)
		}
		return encode(keys), nil
	case "table":
		var v tableSection
		if e := decodeSection(raw, &v); e != nil {
			return "", e
		}
		if v.Columns == nil || v.Rows == nil || len(*v.Columns) < 1 || len(*v.Columns) > 20 || len(*v.Rows) > 200 {
			return bad()
		}
		keys := []string{}
		seen := map[string]bool{}
		for _, p := range *v.Columns {
			if !contentKey.MatchString(p.Key) || seen[p.Key] || p.Label == nil || !safeSectionText(*p.Label, 200, true) {
				return bad()
			}
			seen[p.Key] = true
			keys = append(keys, p.Key)
		}
		for _, r := range *v.Rows {
			if r.Cells == nil || len(*r.Cells) != len(keys) {
				return bad()
			}
			for _, c := range *r.Cells {
				if c == nil || !safeSectionText(*c, 2000, false) {
					return bad()
				}
			}
		}
		return fmt.Sprint(len(*v.Rows)) + encode(keys), nil
	default:
		return "", invalid("不支持的模块类型")
	}
}
func validateSection(d dto.SectionContent, source string) error {
	if !validSectionKey(d.SectionKey) {
		return invalid("模块键须为小写字母开头的 1–64 位字母、数字、下划线或连字符，且不能使用保留键")
	}
	if d.Status != "draft" && d.Status != "ready" && d.Status != "disabled" {
		return invalid("模块状态不正确")
	}
	if d.SortOrder != nil && (*d.SortOrder < 0 || *d.SortOrder > 100000) {
		return invalid("排序须为 0–100000")
	}
	if d.SectionType != "text" && d.SectionType != "key_value" && d.SectionType != "table" && d.SectionType != "asset_gallery" {
		return invalid("不支持的模块类型")
	}
	if d.Operation == "hide" || d.Operation == "inherit" {
		if len(d.Translations) != 0 || (d.Operation == "hide" && d.IsVisible) {
			return invalid("隐藏/继承操作不能携带内容，隐藏必须关闭显示")
		}
		return nil
	}
	if d.Operation != "add" && d.Operation != "replace" {
		return invalid("模块操作不正确")
	}
	if d.SortOrder == nil || len(d.Translations) < 1 || len(d.Translations) > 6 {
		return invalid("请设置排序及源语言翻译")
	}
	seen := map[string]bool{}
	shape := ""
	size := 0
	for _, t := range d.Translations {
		if !languages[t.LanguageCode] || seen[t.LanguageCode] || (t.TranslationStatus != "draft" && t.TranslationStatus != "approved") || !safeSectionText(t.Title, 200, true) {
			return invalid("翻译语言、唯一性、标题或状态不正确")
		}
		seen[t.LanguageCode] = true
		v, e := validateSectionContent(d.SectionType, t.Content)
		if e != nil {
			return e
		}
		if shape != "" && shape != v {
			return invalid("各语言须保持项目键、行列数量和顺序一致")
		}
		shape = v
		size += len(t.Content)
	}
	if !seen[source] {
		return invalid("源语言翻译必填")
	}
	if size > MaxSectionBytes {
		return invalid("模块所有译文内容合计不得超过 256 KiB")
	}
	return nil
}
