import { describe, expect, it } from 'vitest'
import { buildAndOrderFields, getFieldCode, mergeFieldSources, orderFieldsWithSchema } from './unifiedFieldOrder'
import type { RenderSchema } from '@/platform/layout/renderSchema'

describe('unifiedFieldOrder', () => {
  it('resolves field code from mixed naming styles', () => {
    expect(getFieldCode({ code: 'asset_name' })).toBe('asset_name')
    expect(getFieldCode({ fieldCode: 'asset_code' })).toBe('asset_code')
    expect(getFieldCode({ fieldName: 'purchase_date' })).toBe('purchase_date')
  })

  it('merges runtime and metadata fields by code and keeps runtime as primary', () => {
    const merged = mergeFieldSources(
      [
        { code: 'asset_name', name: 'Runtime Name', fieldType: 'text' }
      ],
      [
        { code: 'asset_name', name: 'Metadata Name', fieldType: 'textarea' },
        { code: 'purchase_date', name: 'Purchase Date', fieldType: 'date' }
      ]
    )

    const map = new Map(merged.map((item) => [item.code, item]))
    expect(map.get('asset_name')?.name).toBe('Runtime Name')
    expect(map.get('asset_name')?.fieldType).toBe('text')
    expect(map.get('purchase_date')?.name).toBe('Purchase Date')
  })

  it('applies schema order first and keeps runtime order for remaining fields', () => {
    const schema: RenderSchema = {
      mode: 'list',
      fieldOrder: ['asset_name', 'asset_code'],
      sections: []
    }

    const ordered = orderFieldsWithSchema(
      [
        { code: 'status', sortOrder: 3 },
        { code: 'asset_code', sortOrder: 2 },
        { code: 'asset_name', sortOrder: 1 },
        { code: 'purchase_date', sortOrder: 4 }
      ],
      schema
    )

    expect(ordered.map((item) => item.code)).toEqual([
      'asset_name',
      'asset_code',
      'status',
      'purchase_date'
    ])
  })

  it('builds schema fallback ordering when layout config is missing', () => {
    const ordered = buildAndOrderFields({
      fields: [
        { code: 'asset_code', sort_order: 2 },
        { code: 'asset_name', sort_order: 1 }
      ],
      layoutConfig: null,
      mode: 'edit'
    })

    expect(ordered.map((item) => item.code)).toEqual(['asset_name', 'asset_code'])
  })
})

