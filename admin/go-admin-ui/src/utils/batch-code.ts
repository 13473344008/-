/** Matches backend normalization and the published test-record contract. */
export function batchCodeIssue(input: string, recordType: string): 'invalidCode' | 'testCodeHelp' | null {
  const code = input.trim().toUpperCase()
  if (!/^[A-Z0-9_-]{1,64}$/.test(code)) return 'invalidCode'
  if (recordType === 'test' && !/(^|[-_])TEST([-_]|$)/.test(code)) return 'testCodeHelp'
  return null
}
