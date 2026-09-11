package service

import (
	"go-admin/app/passport/service/dto"
	"math/big"
	"regexp"
	"strings"
	"time"
	"unicode/utf8"
)

type OverrideRule struct {
	FieldKey     string `json:"field_key"`
	Kind         string `json:"kind"`
	AllowClear   bool   `json:"allow_clear"`
	Translatable bool   `json:"translatable"`
}

// The DATA_MODEL closed registry. Asset editing remains outside T6; it is never accepted as arbitrary text.
var OverrideRules = []OverrideRule{
	{"raw_material_name", "text", true, true}, {"raw_material_type", "text", true, true}, {"raw_material_origin", "text", true, true}, {"raw_material_description", "text", true, true},
	{"package_description", "text", true, true}, {"inner_material", "text", true, true}, {"package_quantity", "decimal", true, false}, {"package_unit", "text", true, false}, {"package_type_code", "text", true, false},
	{"storage_conditions", "text", true, true}, {"shelf_life_description", "text", true, true}, {"shelf_life_days", "integer", true, false}, {"process", "json", true, true},
}

func overrideRule(key string) (OverrideRule, bool) {
	for _, r := range OverrideRules {
		if r.FieldKey == key {
			return r, true
		}
	}
	return OverrideRule{}, false
}

var signedDecimal = regexp.MustCompile(`^-?[0-9]{1,18}(\.[0-9]{1,9})?$`)

func validDate(v *string) bool {
	if v == nil {
		return true
	}
	d, e := time.Parse("2006-01-02", *v)
	return e == nil && d.Format("2006-01-02") == *v && d.Year() > 0
}
func textLimit(v *string, n int) bool { return v == nil || utf8.RuneCountInString(*v) <= n }
func validateBatchContent(c *dto.BatchContent) error {
	if !validDate(c.ProductionDate) || !validDate(c.ExpiryDate) {
		return invalid("日期格式或日历日期不正确")
	}
	if c.ProductionDate != nil && c.ExpiryDate != nil && *c.ProductionDate > *c.ExpiryDate {
		return invalid("有效期不能早于生产日期")
	}
	if c.QualityStatus == "" {
		c.QualityStatus = "pending"
	}
	switch c.QualityStatus {
	case "pending", "released", "hold", "rejected":
	default:
		return invalid("批次质量状态不正确")
	}
	if !textLimit(c.InternalNote, 4000) {
		return invalid("批次备注超过 4000 字符")
	}
	return nil
}
func validateOverride(o *dto.OverrideInput) error {
	r, ok := overrideRule(o.FieldKey)
	if !ok {
		return invalid("该字段不允许批次覆盖，图片管理尚未开放")
	}
	if o.Operation != "set" && o.Operation != "clear" {
		return invalid("覆盖操作只允许 set/clear；恢复继承请移除覆盖")
	}
	if o.Operation == "clear" {
		if !r.AllowClear {
			return invalid("该字段不允许清空")
		}
		if o.ValueText != nil || o.ValueInteger != nil || o.Process != nil {
			return invalid("主动清空不能附带值")
		}
		return nil
	}
	switch r.Kind {
	case "text", "decimal":
		if o.ValueText == nil || o.ValueInteger != nil || o.Process != nil {
			return invalid("覆盖值类型不正确")
		}
		if strings.TrimSpace(*o.ValueText) == "" || !textLimit(o.ValueText, 4000) {
			return invalid("覆盖文字不能为空或超过长度")
		}
		if r.Kind == "decimal" && !decimalPattern.MatchString(*o.ValueText) {
			return invalid("净含量须为非负十进制数")
		}
		if o.FieldKey == "package_unit" && !textLimit(o.ValueText, 32) {
			return invalid("包装单位超过 32 字符")
		}
		if o.FieldKey == "package_type_code" && !codePattern.MatchString(*o.ValueText) {
			return invalid("包装代码不正确")
		}
	case "integer":
		if o.ValueInteger == nil || *o.ValueInteger < 0 || *o.ValueInteger > 9007199254740991 || o.ValueText != nil || o.Process != nil {
			return invalid("保质期天数须为非负安全整数")
		}
	case "json":
		if o.Process == nil || len(o.Process) > 100 || o.ValueText != nil || o.ValueInteger != nil {
			return invalid("请填写结构化工艺步骤，最多 100 项")
		}
		seen := map[string]bool{}
		for _, p := range o.Process {
			if !codePattern.MatchString(p.StepKey) || seen[p.StepKey] || strings.TrimSpace(p.Label) == "" || utf8.RuneCountInString(p.Label) > 4000 {
				return invalid("工艺步骤代码或说明不正确")
			}
			seen[p.StepKey] = true
		}
	}
	return nil
}
func validateInspection(i *dto.InspectionInput) error {
	var e error
	i.ItemCode, e = validateCode(i.ItemCode)
	if e != nil {
		return invalid("检测项目代码须为 1–64 位字母、数字、下划线或连字符")
	}
	i.Name = strings.TrimSpace(i.Name)
	if i.Name == "" || utf8.RuneCountInString(i.Name) > 200 {
		return invalid("检测项目名称须为 1–200 字符")
	}
	for _, v := range []*string{i.NumericValue, i.StandardValue, i.MinLimit, i.MaxLimit} {
		if v != nil && !signedDecimal.MatchString(*v) {
			return invalid("检测数值须为十进制字符串，不能使用指数或非数值")
		}
	}
	if i.MinLimit != nil && i.MaxLimit != nil {
		lo, _ := new(big.Rat).SetString(*i.MinLimit)
		hi, _ := new(big.Rat).SetString(*i.MaxLimit)
		if lo.Cmp(hi) > 0 {
			return invalid("检测下限不能超过上限")
		}
	}
	has := i.NumericValue != nil || i.TextValue != nil
	switch i.ValueType {
	case "decimal", "integer":
		if i.TextValue != nil {
			return invalid("数值检测不能提交文本结果")
		}
		if i.ValueType == "integer" && i.NumericValue != nil && strings.Contains(*i.NumericValue, ".") {
			return invalid("整数检测不能提交小数")
		}
	case "text":
		if i.NumericValue != nil {
			return invalid("文本检测不能提交数值列")
		}
		if i.TextValue != nil && strings.TrimSpace(*i.TextValue) == "" {
			return invalid("结果为空请使用未检测状态")
		}
	case "none":
		if has {
			return invalid("无结果类型不能携带检测值")
		}
	default:
		return invalid("检测值类型不正确")
	}
	switch i.Judgement {
	case "not_tested", "not_applicable":
		if has {
			return invalid("未检测或不适用时必须清空结果")
		}
	case "pass", "fail", "informational":
		if !has {
			return invalid("此判定需要填写实际结果")
		}
	case "pending":
	default:
		return invalid("检测判定状态不正确")
	}
	if !validDate(i.TestedOn) || i.SortOrder < 0 || i.SortOrder > 9007199254740991 {
		return invalid("检测日期或排序不正确")
	}
	if !textLimit(i.TextValue, 2000) || !textLimit(i.Unit, 32) || !textLimit(i.Specification, 2000) || !textLimit(i.TestMethod, 500) || !textLimit(i.InternalNote, 2000) {
		return invalid("检测文字超过字段长度")
	}
	return nil
}
func validateBatchWork(w *dto.BatchWork) error {
	if e := validateBatchContent(&w.Content); e != nil {
		return e
	}
	if w.Overrides == nil || w.Inspections == nil {
		return invalid("保存必须包含完整覆盖和检测列表，空列表请显式提交 []")
	}
	if len(w.Overrides) > len(OverrideRules) || len(w.Inspections) > 100 {
		return invalid("覆盖或检测项目超出本阶段容量上限（检测最多 100 项）")
	}
	seen := map[string]bool{}
	for n := range w.Overrides {
		o := &w.Overrides[n]
		if e := validateOverride(o); e != nil {
			return e
		}
		if seen[o.FieldKey] {
			return invalid("同字段覆盖不能重复")
		}
		seen[o.FieldKey] = true
	}
	seen = map[string]bool{}
	for n := range w.Inspections {
		i := &w.Inspections[n]
		if e := validateInspection(i); e != nil {
			return e
		}
		if seen[i.ItemCode] {
			return invalid("检测项目代码不能重复")
		}
		seen[i.ItemCode] = true
	}
	return nil
}
