import { describe, expect, it } from 'vitest'
import type { RenderSchema } from '@/platform/layout/renderSchema'
import { projectDetailSectionsFromRenderSchema } from '@/platform/layout/detailSchemaProjector'
import { isSystemField } from '@/utils/transform'

describe('detailSchemaProjector', () => {
  it('projects render schema into detail sections with span normalization', () => {
    const schema: RenderSchema = {
      mode: 'readonly',
      fieldOrder: ['assetName', 'status'],
      sections: [
        {
          id: 'basic',
          title: 'Basic',
          kind: 'section',
          columns: 2,
          collapsible: true,
          collapsed: false,
          fields: [
            { code: 'assetName', label: 'Asset Name', fieldType: 'text', span: 1, minHeight: 120, required: false, readonly: true, visible: true },
            { code: 'status', label: 'Status', fieldType: 'select', span: 2, required: false, readonly: true, visible: true }
          ]
        }
      ]
    }

    const sections = projectDetailSectionsFromRenderSchema(
      schema,
      [
        { code: 'assetName', name: 'Asset Name', fieldType: 'text' } as any,
        { code: 'status', name: 'Status', fieldType: 'select' } as any
      ],
      {
        fieldToDetailField: (field: any) => ({
          prop: field.code,
          label: field.name,
          type: 'text',
          span: 12
        }),
        shouldSkipField: () => false
      }
    )

    expect(sections).toHaveLength(1)
    expect(sections[0].name).toBe('basic')
    expect(sections[0].fields.map((field) => field.prop)).toEqual(['assetName', 'status'])
    expect(sections[0].fields[0].span).toBe(12)
    expect((sections[0].fields[0] as any).placement).toMatchObject({
      row: 1,
      colStart: 1,
      colSpan: 1,
      rowSpan: 3,
      columns: 2,
      totalRows: 4,
      order: 1
    })
    expect((sections[0].fields[0] as any).minHeight).toBe(120)
    expect(sections[0].fields[1].span).toBe(24)
    expect(sections[0].fields[0].readonly).toBe(true)
    expect(sections[0].fields[1].readonly).toBe(true)
  })

  it('respects visibility skip rules and audit exclusion', () => {
    const schema: RenderSchema = {
      mode: 'readonly',
      fieldOrder: ['assetName', 'createdAt'],
      sections: [
        {
          id: 'basic',
          title: 'Basic',
          kind: 'section',
          columns: 2,
          collapsible: false,
          collapsed: false,
          fields: [
            { code: 'assetName', label: 'Asset Name', fieldType: 'text', span: 1, required: false, readonly: true, visible: true },
            { code: 'createdAt', label: 'Created At', fieldType: 'datetime', span: 1, required: false, readonly: true, visible: true }
          ]
        }
      ]
    }

    const sections = projectDetailSectionsFromRenderSchema(
      schema,
      [{ code: 'assetName', name: 'Asset Name', fieldType: 'text' } as any],
      {
        fieldToDetailField: (field: any) => ({
          prop: field.code,
          label: field.name,
          type: 'text'
        }),
        shouldSkipField: (field: any) => field.code === 'assetName',
        isAuditFieldCode: (code: string) => code === 'createdAt'
      }
    )

    expect(sections).toHaveLength(0)
  })

  it('skips unknown system fields injected only in layout schema', () => {
    const schema: RenderSchema = {
      mode: 'readonly',
      fieldOrder: ['id', 'assetName'],
      sections: [
        {
          id: 'basic',
          title: 'Basic',
          kind: 'section',
          columns: 2,
          collapsible: false,
          collapsed: false,
          fields: [
            { code: 'id', label: 'ID', fieldType: 'text', span: 1, required: false, readonly: true, visible: true },
            { code: 'assetName', label: 'Asset Name', fieldType: 'text', span: 1, required: false, readonly: true, visible: true }
          ]
        }
      ]
    }

    const sections = projectDetailSectionsFromRenderSchema(
      schema,
      [{ code: 'assetName', name: 'Asset Name', fieldType: 'text' } as any],
      {
        fieldToDetailField: (field: any) => ({
          prop: field.code,
          label: field.name,
          type: 'text'
        }),
        mustSkipField: (field: any) => isSystemField(field)
      }
    )

    expect(sections).toHaveLength(1)
    expect(sections[0].fields.map((field) => field.prop)).toEqual(['assetName'])
  })
})
