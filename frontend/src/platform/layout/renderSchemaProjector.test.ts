import { describe, expect, it } from 'vitest'
import type { RenderSchema } from '@/platform/layout/renderSchema'
import {
  orderFieldsByRenderSchema,
  projectListLayoutConfigForRenderSchema,
  projectListColumnsFromRenderSchema,
  projectRuntimeLayoutFromRenderSchema,
  projectSearchFieldsFromRenderSchema,
} from './renderSchemaProjector'

const baseSchema: RenderSchema = {
  mode: 'list',
  fieldOrder: ['assetName', 'assetCode', 'status'],
  sections: [
    {
      id: 'basic',
      title: 'Basic',
      kind: 'section',
      columns: 2,
      collapsible: false,
      collapsed: false,
      fields: [
        { code: 'assetName', label: 'Asset Name', fieldType: 'text', span: 1, required: false, readonly: false, visible: true },
        { code: 'assetCode', label: 'Asset Code', fieldType: 'text', span: 1, required: false, readonly: false, visible: true },
        { code: 'status', label: 'Status', fieldType: 'select', span: 1, required: false, readonly: false, visible: true },
      ]
    }
  ]
}

describe('renderSchemaProjector', () => {
  it('projects runtime layout for DynamicFormRenderer', () => {
    const runtime = projectRuntimeLayoutFromRenderSchema(baseSchema)
    expect(runtime.sections).toHaveLength(1)
    expect(runtime.sections[0].fields?.[0].code).toBe('assetName')
  })

  it('keeps render field minHeight in runtime projection', () => {
    const schema: RenderSchema = {
      ...baseSchema,
      sections: [
        {
          ...baseSchema.sections[0],
          fields: [
            {
              ...baseSchema.sections[0].fields[0],
              minHeight: 172
            }
          ]
        }
      ]
    }

    const runtime = projectRuntimeLayoutFromRenderSchema(schema)
    expect(runtime.sections[0].fields?.[0].minHeight).toBe(172)
  })

  it('prefers persisted layout placement snapshot for runtime fields', () => {
    const schema: RenderSchema = {
      ...baseSchema,
      sections: [
        {
          ...baseSchema.sections[0],
          fields: [
            {
              ...baseSchema.sections[0].fields[0],
              layoutPlacement: {
                row: 1,
                colStart: 2,
                colSpan: 1,
                rowSpan: 1,
                columns: 2,
                totalRows: 1,
                order: 1,
                canvas: { x: 0.5, y: 0, width: 0.5, height: 1 }
              }
            },
            {
              ...baseSchema.sections[0].fields[1]
            }
          ]
        }
      ]
    }

    const runtime = projectRuntimeLayoutFromRenderSchema(schema)
    expect(runtime.sections[0].fields?.[0].placement?.colStart).toBe(2)
    expect(runtime.sections[0].fields?.[1].placement?.colStart).toBe(1)
  })

  it('projects ordered list columns', () => {
    const fields = [
      { code: 'assetCode', name: 'Asset Code' },
      { code: 'assetName', name: 'Asset Name' },
      { code: 'status', name: 'Status' }
    ]
    const cols = projectListColumnsFromRenderSchema(baseSchema, fields)
    expect(cols.map((item) => item.prop)).toEqual(['assetName', 'assetCode', 'status'])
  })

  it('orders metadata fields by schema field order', () => {
    const ordered = orderFieldsByRenderSchema(
      [{ code: 'status' }, { code: 'assetCode' }, { code: 'assetName' }],
      baseSchema
    )
    expect(ordered.map((item) => item.code)).toEqual(['assetName', 'assetCode', 'status'])
  })

  it('projects search fields by schema order', () => {
    const search = projectSearchFieldsFromRenderSchema(baseSchema, [
      { code: 'status', name: 'Status', isSearchable: true, fieldType: 'select', options: [{ label: 'Active', value: 'active' }] },
      { code: 'assetName', name: 'Asset Name', isSearchable: true, fieldType: 'text' },
      { code: 'assetCode', name: 'Asset Code', isSearchable: true, fieldType: 'text' }
    ])
    expect(search.map((item) => item.prop)).toEqual(['assetName', 'assetCode', 'status'])
  })

  it('projects list columns layout config into sections for render schema builder', () => {
    const layout = projectListLayoutConfigForRenderSchema({
      columns: [
        { fieldCode: 'assetName', label: 'Asset Name' },
        { prop: 'assetCode', label: 'Asset Code' }
      ]
    })

    expect(Array.isArray(layout?.sections)).toBe(true)
    expect(layout?.sections?.[0]?.fields?.map((item: any) => item.fieldCode)).toEqual([
      'assetName',
      'assetCode'
    ])
  })

  it('projects tab and collapse sections into runtime container structures', () => {
    const schema: RenderSchema = {
      mode: 'edit',
      fieldOrder: ['name', 'owner', 'memo'],
      sections: [
        {
          id: 'basic',
          title: 'Basic',
          kind: 'section',
          columns: 2,
          collapsible: false,
          collapsed: false,
          fields: [{ code: 'name', label: 'Name', fieldType: 'text', span: 1, required: false, readonly: false, visible: true }]
        },
        {
          id: 'extra::tab::main',
          title: 'Extra / Main',
          kind: 'tab',
          containerId: 'extra',
          containerTitle: 'Extra',
          itemId: 'main',
          itemTitle: 'Main',
          columns: 2,
          collapsible: false,
          collapsed: false,
          fields: [{ code: 'owner', label: 'Owner', fieldType: 'user', span: 1, required: false, readonly: false, visible: true }]
        },
        {
          id: 'notes::collapse::memo',
          title: 'Notes / Memo',
          kind: 'collapse',
          containerId: 'notes',
          containerTitle: 'Notes',
          itemId: 'memo',
          itemTitle: 'Memo',
          columns: 2,
          collapsible: true,
          collapsed: true,
          fields: [{ code: 'memo', label: 'Memo', fieldType: 'textarea', span: 1, required: false, readonly: false, visible: true }]
        }
      ]
    }

    const runtime = projectRuntimeLayoutFromRenderSchema(schema)
    expect(runtime.sections).toHaveLength(3)
    expect(runtime.sections[1].type).toBe('tab')
    expect(runtime.sections[1].tabs?.[0].title).toBe('Main')
    expect(runtime.sections[2].type).toBe('collapse')
    expect(runtime.sections[2].items?.[0].title).toBe('Memo')
  })

  it('preserves section position from render schema', () => {
    const schema: RenderSchema = {
      mode: 'edit',
      fieldOrder: ['left_field', 'right_field'],
      sections: [
        {
          id: 'main_section',
          title: 'Main',
          kind: 'section',
          position: 'main',
          columns: 2,
          collapsible: false,
          collapsed: false,
          fields: [{ code: 'left_field', label: 'Left', fieldType: 'text', span: 1, required: false, readonly: false, visible: true }]
        },
        {
          id: 'sidebar_section',
          title: 'Sidebar',
          kind: 'section',
          position: 'sidebar',
          columns: 1,
          collapsible: false,
          collapsed: false,
          fields: [{ code: 'right_field', label: 'Right', fieldType: 'text', span: 1, required: false, readonly: false, visible: true }]
        }
      ]
    }

    const runtime = projectRuntimeLayoutFromRenderSchema(schema)
    expect(runtime.sections[0].position).toBe('main')
    expect(runtime.sections[1].position).toBe('sidebar')
  })
})
