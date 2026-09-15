package service

import (
	"fmt"
	"go-admin/app/passport/service/dto"
	"reflect"
	"regexp"
	"strings"
	"unicode/utf8"
)

type BusinessError struct {
	Code    int
	Message string
}

func (e *BusinessError) Error() string { return e.Message }
func invalid(s string) error           { return &BusinessError{422, s} }
func conflict(s string) error          { return &BusinessError{409, s} }

var codePattern = regexp.MustCompile(`^[A-Za-z0-9_-]{1,64}$`)
var decimalPattern = regexp.MustCompile(`^[0-9]{1,18}(\.[0-9]{1,9})?$`)
var countryPattern = regexp.MustCompile(`^[A-Z]{2}$`)
var languages = map[string]bool{"en": true, "zh-CN": true, "es": true, "ar": true, "fr": true, "de": true}

func activeLanguage(lang string) bool { return lang == "en" || lang == "zh-CN" }

func validateCode(s string) (string, error) {
	s = strings.ToUpper(strings.TrimSpace(s))
	if !codePattern.MatchString(s) {
		return "", invalid("产品编码须为 1–64 位字母、数字、下划线或连字符")
	}
	return s, nil
}
func validateContent(c *dto.RevisionContent) error {
	if c.SourceLanguage == "" {
		c.SourceLanguage = "en"
	}
	if !activeLanguage(c.SourceLanguage) {
		return invalid("请选择支持的源语言")
	}
	for _, v := range []*string{c.CategoryCode, c.PackageTypeCode} {
		if v != nil && !codePattern.MatchString(*v) {
			return invalid("分类和包装代码格式不正确")
		}
	}
	if c.OriginCountryCode != nil && !countryPattern.MatchString(*c.OriginCountryCode) {
		return invalid("原产国请填写两位大写国家代码")
	}
	if c.PackageQuantity != nil && !decimalPattern.MatchString(*c.PackageQuantity) {
		return invalid("净含量须为非负十进制数，最多 18 位整数和 9 位小数")
	}
	if c.PackageUnit != nil && utf8.RuneCountInString(*c.PackageUnit) > 32 {
		return invalid("包装单位超过 32 字符")
	}
	if c.ShelfLifeDays != nil && (*c.ShelfLifeDays < 0 || *c.ShelfLifeDays > 9007199254740991) {
		return invalid("保质期天数须为非负安全整数")
	}
	if c.InternalNote != nil && utf8.RuneCountInString(*c.InternalNote) > 2000 {
		return invalid("内部备注超过 2000 字符")
	}
	if c.ProcessSteps == nil {
		c.ProcessSteps = []dto.Step{}
	}
	if len(c.ProcessSteps) > 100 {
		return invalid("工艺步骤最多 100 项")
	}
	seen := map[string]bool{}
	for _, s := range c.ProcessSteps {
		if !codePattern.MatchString(s.StepKey) || seen[s.StepKey] {
			return invalid("工艺步骤代码须合法且不重复")
		}
		seen[s.StepKey] = true
	}
	return nil
}
func validateTranslation(t *dto.TranslationRequest, c dto.RevisionContent) error {
	if !languages[t.LanguageCode] {
		return invalid("不支持的翻译语言")
	}
	if t.TranslationStatus == "" {
		t.TranslationStatus = "draft"
	}
	if t.TranslationStatus != "draft" && t.TranslationStatus != "approved" {
		return invalid("翻译状态不正确")
	}
	t.ProductName = strings.TrimSpace(t.ProductName)
	if t.ProductName == "" || utf8.RuneCountInString(t.ProductName) > 200 {
		return invalid("产品名称须为 1–200 字符")
	}
	v := reflect.ValueOf(*t)
	for i := 0; i < v.NumField(); i++ {
		f := v.Field(i)
		if f.Kind() == reflect.Pointer && !f.IsNil() && utf8.RuneCountInString(f.Elem().String()) > 4000 {
			return invalid("翻译文字超过 4000 字符")
		}
	}
	allowed := map[string]bool{}
	for _, step := range c.ProcessSteps {
		allowed[step.StepKey] = true
	}
	if t.ProcessLabels == nil {
		t.ProcessLabels = map[string]string{}
	}
	for k, v := range t.ProcessLabels {
		if !allowed[k] || strings.TrimSpace(v) == "" || utf8.RuneCountInString(v) > 4000 {
			return invalid(fmt.Sprintf("工艺标签 %s 未对应有效步骤或文字无效", k))
		}
	}
	return nil
}
