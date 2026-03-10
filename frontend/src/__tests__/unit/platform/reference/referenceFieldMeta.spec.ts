import { describe, expect, it } from 'vitest'

import { resolveReferenceObjectCode } from '@/platform/reference/referenceFieldMeta'

describe('resolveReferenceObjectCode', () => {
  it('prefers targetObjectCode when referenceObject is absent', () => {
    expect(
      resolveReferenceObjectCode({
        fieldType: 'text',
        targetObjectCode: 'User'
      })
    ).toBe('User')
  })
})
