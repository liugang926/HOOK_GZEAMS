import { describe, expect, it } from 'vitest'

import {
  resolveReferenceDisplayField,
  resolveReferenceLabel,
  resolveReferenceObjectCode,
  resolveReferenceSecondaryField
} from '@/platform/reference/referenceFieldMeta'

describe('resolveReferenceObjectCode', () => {
  it('prefers targetObjectCode when referenceObject is absent', () => {
    expect(
      resolveReferenceObjectCode({
        fieldType: 'text',
        targetObjectCode: 'User'
      })
    ).toBe('User')
  })

  it('uses asset-specific display defaults when metadata is implicit', () => {
    expect(
      resolveReferenceDisplayField({
        fieldType: 'asset'
      })
    ).toBe('assetName')

    expect(
      resolveReferenceSecondaryField({
        fieldType: 'asset'
      })
    ).toBe('assetCode')

    expect(
      resolveReferenceLabel(
        {
          id: 'asset-1',
          assetName: 'MacBook Pro'
        },
        'name'
      )
    ).toBe('MacBook Pro')
  })
})
