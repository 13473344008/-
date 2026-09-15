import { describe, expect, it } from 'vitest'
import { nextStepKey } from '@/utils/process-steps'
describe('stable process keys', () => {
  it('avoids existing legacy and previously issued keys after deletion', () => {
    expect(nextStepKey(['washing', 'STEP_001', 'STEP_002'])).toBe('STEP_003')
  })
  it('does not use translated names as identifiers', () => {
    const keys: string[] = []
    Array.from({ length: 3 }).forEach(() => keys.push(nextStepKey(keys)))
    expect(new Set(keys).size).toBe(3)
    expect(keys.every(x => /^[A-Za-z0-9_-]{1,64}$/.test(x))).toBe(true)
  })
})
