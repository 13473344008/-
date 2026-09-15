/** Stable keys are never derived from translated names or row positions. */
export function nextStepKey(keys: string[]): string {
  const used = new Set(keys)
  let n = 1
  while (used.has(`STEP_${String(n).padStart(3, '0')}`)) n++
  return `STEP_${String(n).padStart(3, '0')}`
}
