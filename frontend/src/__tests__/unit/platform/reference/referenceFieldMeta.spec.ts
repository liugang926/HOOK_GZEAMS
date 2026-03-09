import { describe, expect, it } from 'vitest'
import { normalizeReferenceObjectCode } from '@/platform/reference/referenceFieldMeta'

describe('normalizeReferenceObjectCode', () => {
  it('canonicalizes built-in reference object codes', () => {
    expect(normalizeReferenceObjectCode('user')).toBe('User')
    expect(normalizeReferenceObjectCode('accounts.user')).toBe('User')
    expect(normalizeReferenceObjectCode('/api/system/objects/department/')).toBe('Department')
  })
})
