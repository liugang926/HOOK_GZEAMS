import { describe, expect, it } from 'vitest'
import { normalizeFieldType, resolveFieldType } from '@/utils/fieldType'

describe('fieldType normalization', () => {
  it('normalizes known legacy aliases to canonical runtime keys', () => {
    expect(normalizeFieldType('multiselect')).toBe('multi_select')
    expect(normalizeFieldType('multiSelect')).toBe('multi_select')
    expect(normalizeFieldType('richtext')).toBe('rich_text')
    expect(normalizeFieldType('subtable')).toBe('sub_table')
    expect(normalizeFieldType('qrCode')).toBe('qr_code')
  })

  it('normalizes separators and casing consistently', () => {
    expect(normalizeFieldType('Multi-Select')).toBe('multi_select')
    expect(normalizeFieldType('Rich Text')).toBe('rich_text')
    expect(normalizeFieldType('Sub_Table')).toBe('sub_table')
  })

  it('resolves field type from mixed payload shape', () => {
    expect(resolveFieldType({ field_type: 'multiSelect' })).toBe('multi_select')
    expect(resolveFieldType({ fieldType: 'richtext' })).toBe('rich_text')
    expect(resolveFieldType({ type: 'subtable' })).toBe('sub_table')
  })

  it('keeps canonical runtime field types stable (coverage baseline)', () => {
    const canonicalTypes = [
      'text', 'textarea', 'email', 'url', 'phone', 'password',
      'number', 'currency', 'percent',
      'date', 'datetime', 'time', 'daterange', 'year', 'month',
      'select', 'multi_select', 'radio', 'checkbox', 'boolean',
      'reference', 'user', 'department', 'location', 'asset',
      'dictionary', 'json', 'object', 'sub_table', 'formula',
      'file', 'image', 'attachment',
      'qr_code', 'barcode', 'rich_text', 'code', 'color', 'rate', 'slider', 'switch'
    ]

    canonicalTypes.forEach((type) => {
      expect(normalizeFieldType(type)).toBe(type)
    })
  })
})
