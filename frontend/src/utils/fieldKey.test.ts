import { describe, expect, it } from 'vitest'
import {
  buildFieldKeyCandidates,
  resolveFieldValue,
  toDataKey
} from './fieldKey'

describe('fieldKey contract', () => {
  it('should derive camel dataKey from snake code', () => {
    expect(toDataKey('asset_code')).toBe('assetCode')
    expect(toDataKey('assetCode')).toBe('assetCode')
  })

  it('should build key candidates with snake/camel aliases', () => {
    const keys = buildFieldKeyCandidates('asset_code')
    expect(keys).toContain('asset_code')
    expect(keys).toContain('assetCode')
  })

  it('should resolve camelCase payload by snake field code', () => {
    const record = { assetCode: 'A-001' }
    const value = resolveFieldValue(record, { fieldCode: 'asset_code' })
    expect(value).toBe('A-001')
  })

  it('should resolve snake_case payload by camel field code', () => {
    const record = { asset_code: 'A-002' }
    const value = resolveFieldValue(record, { fieldCode: 'assetCode' })
    expect(value).toBe('A-002')
  })

  it('should fallback to wrapped data payload', () => {
    const record = { success: true, data: { assetCode: 'A-003' } }
    const value = resolveFieldValue(record, { fieldCode: 'asset_code', includeWrappedData: true })
    expect(value).toBe('A-003')
  })

  it('should fallback to custom fields bag', () => {
    const record = { customFields: { assetCode: 'A-004' } }
    const value = resolveFieldValue(record, { fieldCode: 'asset_code', includeCustomBags: true })
    expect(value).toBe('A-004')
  })

  it('should treat empty values as missing and continue fallback', () => {
    const record = {
      asset_code: '',
      assetCode: 'A-005'
    }
    const value = resolveFieldValue(record, {
      fieldCode: 'asset_code',
      treatEmptyAsMissing: true
    })
    expect(value).toBe('A-005')
  })

  it('should optionally return empty match when no better candidate exists', () => {
    const record = { asset_code: '' }
    const strict = resolveFieldValue(record, {
      fieldCode: 'asset_code',
      treatEmptyAsMissing: true,
      returnEmptyMatch: false
    })
    expect(strict).toBeUndefined()

    const relaxed = resolveFieldValue(record, {
      fieldCode: 'asset_code',
      treatEmptyAsMissing: true,
      returnEmptyMatch: true
    })
    expect(relaxed).toBe('')
  })
})

