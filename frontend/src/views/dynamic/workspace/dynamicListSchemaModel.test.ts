import { describe, expect, it } from 'vitest'
import type { RenderSchema } from '@/platform/layout/renderSchema'
import {
  buildDynamicListFieldColumn,
  buildDynamicListSearchCandidateOptions,
  buildDynamicListTableColumns,
  resolveDynamicListSearchFieldOptions,
  selectDynamicListDefaultVisibleFieldCodes,
} from './dynamicListSchemaModel'

const schema = {
  sections: [
    {
      id: 'main',
      title: 'Main',
      fields: [
        { code: 'asset_name' },
        { code: 'status' },
      ],
    },
  ],
} as unknown as RenderSchema

describe('dynamicListSchemaModel', () => {
  it('builds normalized table columns from field definitions', () => {
    expect(buildDynamicListFieldColumn({
      code: 'owner',
      name: 'Owner',
      fieldType: 'user',
      targetObjectCode: 'User',
      referenceDisplayField: 'fullName',
    }, true)).toEqual(expect.objectContaining({
      prop: 'owner',
      fieldCode: 'owner',
      label: 'Owner',
      fieldType: 'user',
      targetObjectCode: 'User',
      referenceDisplayField: 'fullName',
      visible: true,
    }))
  })

  it('prefers showInList and identifiers when selecting fallback visible fields', () => {
    const visibleCodes = selectDynamicListDefaultVisibleFieldCodes([
      { code: 'asset_code', showInList: true, sortOrder: 20 },
      { code: 'asset_name', isIdentifier: true, sortOrder: 10 },
      { code: 'purchase_date', sortOrder: 30 },
      { code: 'status', sortOrder: 40 },
    ], 2)

    expect([...visibleCodes]).toEqual(['asset_code', 'asset_name'])
  })

  it('uses schema field order visibility when runtime layout exists and deduplicates columns', () => {
    const columns = buildDynamicListTableColumns([
      { code: 'asset_name', name: 'Asset name' },
      { code: 'status', name: 'Status' },
      { code: 'asset_code', name: 'Asset code' },
      { code: 'asset_name', name: 'Duplicate asset name' },
    ], schema)

    expect(columns).toEqual([
      expect.objectContaining({ fieldCode: 'asset_name', visible: true }),
      expect.objectContaining({ fieldCode: 'status', visible: true }),
      expect.objectContaining({ fieldCode: 'asset_code', visible: false }),
    ])
  })

  it('prefers searchable fields that remain visible in the list', () => {
    const tableColumns = buildDynamicListTableColumns([
      { code: 'asset_name', name: 'Asset name' },
      { code: 'status', name: 'Status' },
      { code: 'asset_code', name: 'Asset code' },
    ], schema)

    expect(buildDynamicListSearchCandidateOptions([
      { code: 'asset_name', name: 'Asset name' },
      { code: 'status', name: 'Status' },
      { code: 'asset_code', name: 'Asset code' },
    ])).toEqual([
      { label: 'Asset name', value: 'asset_name' },
      { label: 'Status', value: 'status' },
      { label: 'Asset code', value: 'asset_code' },
    ])

    expect(resolveDynamicListSearchFieldOptions({
      rawSearchFields: [
        { prop: 'asset_name', label: 'Asset name', type: 'text' },
        { prop: 'asset_code', label: 'Asset code', type: 'text' },
      ],
      tableColumns,
      orderedVisibleFields: [
        { code: 'asset_name', name: 'Asset name' },
        { code: 'status', name: 'Status' },
        { code: 'asset_code', name: 'Asset code' },
      ],
    })).toEqual([
      { label: 'Asset name', value: 'asset_name' },
    ])
  })
})
