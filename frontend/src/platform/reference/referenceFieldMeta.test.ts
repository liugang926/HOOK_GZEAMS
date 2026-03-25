import { describe, expect, it } from 'vitest'
import {
  extractReferenceIds,
  isReferenceLikeField,
  normalizeReferenceObjectCode,
  resolveReferenceDisplayField,
  resolveReferenceLabel,
  resolveReferenceObjectCode,
  resolveReferenceSecondaryField,
  resolveReferenceSecondaryText
} from '@/platform/reference/referenceFieldMeta'

describe('referenceFieldMeta', () => {
  it('normalizes object code from dotted model path', () => {
    expect(normalizeReferenceObjectCode('apps.assets.models.Asset')).toBe('Asset')
    expect(normalizeReferenceObjectCode('/api/system/objects/User/')).toBe('User')
  })

  it('resolves reference object code from field metadata and type fallback', () => {
    expect(
      resolveReferenceObjectCode({
        reference_model_path: 'apps.organizations.models.Department'
      })
    ).toBe('Department')

    expect(
      resolveReferenceObjectCode({
        fieldType: 'user'
      })
    ).toBe('User')
  })

  it('resolves display and secondary fields from explicit metadata', () => {
    expect(
      resolveReferenceDisplayField({
        referenceDisplayField: 'assetName'
      })
    ).toBe('assetName')

    expect(
      resolveReferenceSecondaryField({
        component_props: { secondary_field: 'assetCode' }
      })
    ).toBe('assetCode')
  })

  it('extracts unique reference ids from primitive and object values', () => {
    expect(extractReferenceIds('id-1')).toEqual(['id-1'])
    expect(
      extractReferenceIds([
        { id: 'id-1', name: 'A' },
        'id-2',
        { value: 'id-2' },
        { pk: 'id-3' }
      ])
    ).toEqual(['id-1', 'id-2', 'id-3'])
  })

  it('detects reference-like fields', () => {
    expect(isReferenceLikeField({ fieldType: 'reference' })).toBe(true)
    expect(isReferenceLikeField({ referenceObject: 'Asset' })).toBe(true)
    expect(isReferenceLikeField({ fieldType: 'text' })).toBe(false)
  })

  it('resolves reference label and secondary text from object values', () => {
    const value = {
      id: 'asset-1',
      assetName: 'MacBook Pro',
      assetCode: 'ASSET-001',
      name: 'Fallback Name'
    }

    expect(resolveReferenceLabel(value, 'assetName')).toBe('MacBook Pro')
    expect(resolveReferenceSecondaryText(value, 'assetCode', 'assetName')).toBe('ASSET-001')
  })
})
