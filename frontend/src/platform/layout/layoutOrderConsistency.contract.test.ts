import { describe, expect, it } from 'vitest'
import { buildRenderSchema } from '@/platform/layout/renderSchema'
import { orderFieldsByRenderSchema } from '@/platform/layout/renderSchemaProjector'
import { buildAndOrderFields } from '@/platform/layout/unifiedFieldOrder'
import { normalizeLayoutType, toRuntimeMode } from '@/utils/layoutMode'

type AnyRecord = Record<string, any>

const toCode = (field: AnyRecord): string =>
  String(field?.code || field?.fieldCode || field?.field_code || field?.fieldName || '').trim()

const toCodes = (fields: AnyRecord[]): string[] =>
  (fields || []).map((field) => toCode(field)).filter(Boolean)

const assertPreviewRuntimeOrderConsistency = (input: {
  mode: string
  fields: AnyRecord[]
  layoutConfig: AnyRecord | null
  expectedOrder: string[]
}) => {
  const runtimeMode = toRuntimeMode(input.mode)
  const schema = buildRenderSchema({
    mode: runtimeMode,
    fields: input.fields,
    layoutConfig: input.layoutConfig
  })

  const previewOrder = schema.fieldOrder
  const runtimeOrdered = orderFieldsByRenderSchema(input.fields, schema)
  const runtimeOrder = toCodes(runtimeOrdered)
  const modeAlignedOrder = toCodes(
    buildAndOrderFields({
      fields: input.fields,
      layoutConfig: input.layoutConfig,
      mode: runtimeMode
    })
  )

  expect(previewOrder).toEqual(input.expectedOrder)
  expect(runtimeOrder).toEqual(previewOrder)
  expect(modeAlignedOrder).toEqual(previewOrder)
}

describe('layout order consistency contract', () => {
  it('keeps section field order consistent between preview and runtime for form mode', () => {
    assertPreviewRuntimeOrderConsistency({
      mode: 'edit',
      fields: [
        { code: 'asset_code', name: 'Asset Code', sortOrder: 2 },
        { code: 'asset_name', name: 'Asset Name', sortOrder: 1 },
        { code: 'status', name: 'Status', sortOrder: 3 }
      ],
      layoutConfig: {
        sections: [
          {
            id: 'basic',
            type: 'section',
            columns: 2,
            fields: [
              { fieldCode: 'asset_name' },
              { fieldCode: 'asset_code' },
              { fieldCode: 'status' }
            ]
          }
        ]
      },
      expectedOrder: ['asset_name', 'asset_code', 'status']
    })
  })

  it('keeps tab and collapse field order consistent between preview and runtime', () => {
    assertPreviewRuntimeOrderConsistency({
      mode: 'edit',
      fields: [
        { code: 'asset_name', name: 'Asset Name', sortOrder: 1 },
        { code: 'owner', name: 'Owner', sortOrder: 2 },
        { code: 'memo', name: 'Memo', sortOrder: 3 }
      ],
      layoutConfig: {
        sections: [
          {
            id: 'basic',
            type: 'section',
            fields: [{ fieldCode: 'asset_name' }]
          },
          {
            id: 'ops',
            type: 'tab',
            tabs: [
              { id: 'main', fields: [{ fieldCode: 'owner' }] }
            ]
          },
          {
            id: 'notes',
            type: 'collapse',
            items: [
              { id: 'memo-item', fields: [{ fieldCode: 'memo' }] }
            ]
          }
        ]
      },
      expectedOrder: ['asset_name', 'owner', 'memo']
    })
  })

  it('keeps list-column order consistent between preview and runtime', () => {
    const mode = 'list'
    const runtimeMode = toRuntimeMode(mode)
    const fields = [
      { code: 'asset_name', name: 'Asset Name', showInList: true, sortOrder: 2 },
      { code: 'asset_code', name: 'Asset Code', showInList: true, sortOrder: 1 },
      { code: 'status', name: 'Status', showInList: true, sortOrder: 3 }
    ]
    const layoutConfig = {
      sections: [
        {
          id: 'list_default',
          type: 'section',
          columns: 1,
          fields: [
            { fieldCode: 'asset_code' },
            { fieldCode: 'asset_name' },
            { fieldCode: 'status' }
          ]
        }
      ]
    }

    const schema = buildRenderSchema({
      mode: runtimeMode,
      fields,
      layoutConfig
    })
    const previewOrder = schema.fieldOrder
    const runtimeOrder = toCodes(orderFieldsByRenderSchema(fields, schema))
    const modeAlignedOrder = toCodes(
      buildAndOrderFields({
        fields,
        layoutConfig,
        mode: runtimeMode
      })
    )

    expect(normalizeLayoutType(mode)).toBe('list')
    expect(previewOrder).toEqual(['asset_code', 'asset_name', 'status'])
    expect(runtimeOrder).toEqual(previewOrder)
    expect(modeAlignedOrder).toEqual(previewOrder)
  })

  it('falls back to metadata sort order consistently when layout sections are missing', () => {
    assertPreviewRuntimeOrderConsistency({
      mode: 'edit',
      fields: [
        { code: 'status', name: 'Status', sortOrder: 3 },
        { code: 'asset_name', name: 'Asset Name', sortOrder: 1 },
        { code: 'asset_code', name: 'Asset Code', sortOrder: 2 }
      ],
      layoutConfig: null,
      expectedOrder: ['asset_name', 'asset_code', 'status']
    })
  })

  it('keeps order stable when fields mix code naming styles', () => {
    assertPreviewRuntimeOrderConsistency({
      mode: 'edit',
      fields: [
        { fieldName: 'asset_name', name: 'Asset Name', sort_order: 1 },
        { fieldCode: 'asset_code', name: 'Asset Code', sort_order: 2 },
        { code: 'status', name: 'Status', sort_order: 3 }
      ],
      layoutConfig: {
        sections: [
          {
            id: 'basic',
            type: 'section',
            fields: [
              { fieldCode: 'asset_name' },
              { fieldCode: 'asset_code' },
              { fieldCode: 'status' }
            ]
          }
        ]
      },
      expectedOrder: ['asset_name', 'asset_code', 'status']
    })
  })
})
