import { describe, expect, it } from 'vitest'
import { batchCodeIssue } from '@/utils/batch-code'

describe('batch creation and clone code validation', () => {
  it.each(['PRODUCT-TEST-001', 'TEST', ' test_001 ', 'PRODUCT_TEST'])('accepts test codes: %s', code => {
    expect(batchCodeIssue(code, 'test')).toBeNull()
  })
  it.each(['PRODUCT-001', 'CONTEST-001', 'TESTING-001'])('rejects missing independent TEST: %s', code => {
    expect(batchCodeIssue(code, 'test')).toBe('testCodeHelp')
  })
  it('does not impose the marker on commercial records', () => {
    expect(batchCodeIssue('PRODUCT-001', 'commercial')).toBeNull()
  })
  it.each(['', 'a/b', 'A'.repeat(65), '产品'])('rejects invalid code syntax', code => {
    expect(batchCodeIssue(code, 'commercial')).toBe('invalidCode')
  })
})
