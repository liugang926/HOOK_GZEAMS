import { describe, expect, it } from 'vitest'
import { checkRuntimeContract } from '@/contracts/runtimeContract'
import { buildRenderSchema } from '@/platform/layout/renderSchema'
import {
  projectListColumnsFromRenderSchema,
  projectListLayoutConfigForRenderSchema,
  projectRuntimeLayoutFromRenderSchema,
  projectSearchFieldsFromRenderSchema,
} from '@/platform/layout/renderSchemaProjector'

describe('runtime render contract', () => {
  it('supports runtime section/tab/collapse payload end-to-end', () => {
    const payload = {
      runtimeVersion: 1,
      fields: {
        editableFields: [
          { code: 'assetName', name: 'Asset Name', fieldType: 'text', isSearchable: true, sortOrder: 1 },
          { code: 'assetCode', name: 'Asset Code', fieldType: 'text', isSearchable: true, sortOrder: 2 },
          { code: 'status', name: 'Status', fieldType: 'select', isSearchable: true, options: [{ label: 'Active', value: 'active' }], sortOrder: 3 },
          { code: 'memo', name: 'Memo', fieldType: 'textarea', isSearchable: false, sortOrder: 4 },
        ],
        reverseRelations: []
      },
      layout: {
        layoutConfig: {
          sections: [
            {
              id: 'basic',
              type: 'section',
              title: 'Basic',
              fields: [{ fieldCode: 'assetName' }, { fieldCode: 'assetCode' }]
            },
            {
              id: 'ops',
              type: 'tab',
              title: 'Operations',
              tabs: [
                { id: 'overview', title: 'Overview', fields: [{ fieldCode: 'status' }] }
              ]
            },
            {
              id: 'notes',
              type: 'collapse',
              title: 'Notes',
              items: [
                { id: 'memo-item', title: 'Memo', collapsed: true, fields: [{ fieldCode: 'memo' }] }
              ]
            }
          ]
        }
      },
      permissions: { view: true, add: true, change: true, delete: true }
    }

    const check = checkRuntimeContract(payload)
    expect(check.ok).toBe(true)
    expect(check.errors).toEqual([])

    const fields = payload.fields.editableFields
    const schema = buildRenderSchema({
      mode: 'edit',
      fields,
      layoutConfig: payload.layout.layoutConfig
    })
    expect(schema.fieldOrder).toEqual(['assetName', 'assetCode', 'status', 'memo'])

    const runtimeLayout = projectRuntimeLayoutFromRenderSchema(schema)
    expect(runtimeLayout.sections).toHaveLength(3)
    expect(runtimeLayout.sections[1].type).toBe('tab')
    expect(runtimeLayout.sections[1].tabs?.[0].id).toBe('overview')
    expect(runtimeLayout.sections[2].type).toBe('collapse')
    expect(runtimeLayout.sections[2].items?.[0].collapsed).toBe(true)

    const listColumns = projectListColumnsFromRenderSchema(schema, fields)
    expect(listColumns.map((item) => item.prop)).toEqual(['assetName', 'assetCode', 'status', 'memo'])

    const searchFields = projectSearchFieldsFromRenderSchema(schema, fields)
    expect(searchFields.map((item) => item.prop)).toEqual(['assetName', 'assetCode', 'status'])
  })

  it('supports list-column-only payload via schema layout projection', () => {
    const listLayout = {
      columns: [
        { fieldCode: 'assetCode', label: 'Asset Code', visible: true },
        { fieldCode: 'assetName', label: 'Asset Name', visible: true },
        { fieldCode: 'status', label: 'Status', visible: true }
      ]
    }
    const fields = [
      { code: 'assetName', name: 'Asset Name', fieldType: 'text', isSearchable: true },
      { code: 'assetCode', name: 'Asset Code', fieldType: 'text', isSearchable: true },
      { code: 'status', name: 'Status', fieldType: 'select', isSearchable: true, options: [{ label: 'Active', value: 'active' }] },
    ]

    const projectedLayout = projectListLayoutConfigForRenderSchema(listLayout)
    const schema = buildRenderSchema({
      mode: 'list',
      fields,
      layoutConfig: projectedLayout
    })

    expect(schema.fieldOrder).toEqual(['assetCode', 'assetName', 'status'])
    const columns = projectListColumnsFromRenderSchema(schema, fields)
    expect(columns.map((item) => item.prop)).toEqual(['assetCode', 'assetName', 'status'])
  })

  it('fails contract checks for malformed runtime payloads', () => {
    const malformed = {
      runtimeVersion: 2,
      fields: {
        editableFields: {}
      },
      layout: {
        layoutConfig: []
      },
      permissions: {
        view: true,
        add: 'yes',
        change: true,
        delete: true
      }
    }

    const check = checkRuntimeContract(malformed)
    expect(check.ok).toBe(false)
    expect(check.errors).toEqual(expect.arrayContaining([
      'unsupported runtimeVersion: 2',
      'fields.editableFields is not an array',
      'layout.layoutConfig is not an object',
      'permissions.add is not a boolean'
    ]))
  })
})
