package service

import "regexp"

var testBatchSegment = regexp.MustCompile(`(^|[-_])TEST([-_]|$)`)

// The code has already been normalized by validateCode. Match the public 1.0 contract.
func validateBatchRecordCode(code, recordType string) error {
	if recordType == "test" && !testBatchSegment.MatchString(code) {
		return invalid("测试记录的批次编码必须包含独立的 TEST 段，例如 PRODUCT-TEST-20260911-001；请使用新编码创建批次")
	}
	return nil
}
