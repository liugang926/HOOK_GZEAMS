import { describe, expect, it } from 'vitest'
import type { SearchField, TableColumn } from '@/types/common'
import {
  applyBaseListFieldDefinitions,
  buildBaseListRequestParams,
  buildBaseListSearchResetPatch,
  getBaseListSearchFieldKey,
  needsBaseListFieldDefinitions,
  normalizeBaseListColumnSaveInput,
  normalizeBaseListSearchField,
  prepareBaseListColumns,
  resolveBaseListResponsePayload,
} from './baseListPageModel'

describe('baseListPageModel', () => {
  it('normalizes search field types and resolves field keys', () => {
    expect(normalizeBaseListSearchField({
      field: 'created_at',
      label: 'Created',
      type: 'daterange',
    })).toEqual({
      field: 'created_at',
      prop: 'created_at',
      label: 'Created',
      type: 'dateRange',
    })

    expect(getBaseListSearchFieldKey({
      prop: 'status',
      label: 'Status',
      type: 'select',
    })).toBe('status')
  })

  it('builds reset patches and request params from search state, columns, and sorting', () => {
    const fields: SearchField[] = [
      { prop: 'status', label: 'Status', type: 'select' },
      { prop: 'amount', label: 'Amount', type: 'numberRange' },
    ]
    expect(buildBaseListSearchResetPatch(fields)).toEqual({
      status: undefined,
      amount: undefined,
      amount_min: undefined,
      amount_max: undefined,
    })

    expect(buildBaseListRequestParams({
      currentPage: 2,
      pageSize: 50,
      visibleColumns: [
        { prop: 'code', label: 'Code', visible: true },
        { prop: 'name', label: 'Name', visible: true },
      ] as TableColumn[],
      searchForm: {
        status: 'active',
        empty: '',
      },
      sortState: { prop: 'name', order: 'descending' },
    })).toEqual({
      page: 2,
      pageSize: 50,
      __visibleFieldCodes: ['code', 'name'],
      status: 'active',
      ordering: '-name',
    })
  })

  it('resolves paginated, array, and empty API payloads', () => {
    expect(resolveBaseListResponsePayload({
      count: 2,
      results: [{ id: 1 }, { id: 2 }],
    })).toEqual({
      tableData: [{ id: 1 }, { id: 2 }],
      total: 2,
    })

    expect(resolveBaseListResponsePayload([{ id: 1 }])).toEqual({
      tableData: [{ id: 1 }],
      total: 1,
    })

    expect(resolveBaseListResponsePayload(null)).toEqual({
      tableData: [],
      total: 0,
    })
  })

  it('normalizes columns for save and applies default sortable/visible settings', () => {
    expect(normalizeBaseListColumnSaveInput([
      { fieldCode: 'code', label: 'Code' },
      { field_code: 'name', label: 'Name' },
      { label: 'Broken' },
    ])).toEqual([
      { fieldCode: 'code', label: 'Code', prop: 'code' },
      { field_code: 'name', label: 'Name', prop: 'name' },
    ])

    expect(prepareBaseListColumns([
      { prop: 'code', label: 'Code' },
      { prop: 'name', label: 'Name', visible: false, sortable: false },
    ])).toEqual([
      { prop: 'code', label: 'Code', fieldCode: 'code', sortable: 'custom', visible: true },
      { prop: 'name', label: 'Name', fieldCode: 'name', visible: false, sortable: false },
    ])
  })

  it('detects missing field metadata and enriches columns from field definitions', () => {
    const columns: TableColumn[] = [
      { prop: 'owner', label: 'Owner' },
      { prop: 'status', label: 'Status', type: 'select' },
    ]

    expect(needsBaseListFieldDefinitions(columns)).toBe(true)

    expect(applyBaseListFieldDefinitions(columns, [
      {
        code: 'owner',
        fieldType: 'user',
        dataKey: 'owner',
        referenceObject: 'User',
        referenceDisplayField: 'fullName',
      },
    ])).toEqual([
      {
        prop: 'owner',
        label: 'Owner',
        fieldCode: 'owner',
        dataKey: 'owner',
        fieldType: 'user',
        type: 'user',
        options: undefined,
        referenceObject: 'User',
        referenceDisplayField: 'fullName',
        referenceSecondaryField: undefined,
      },
      { prop: 'status', label: 'Status', type: 'select' },
    ])
  })
})
