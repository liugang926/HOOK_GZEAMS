import { describe, expect, it } from 'vitest'
import type { TableColumn } from '@/types/common'
import {
  buildBaseListRendererField,
  filterBaseListDataColumns,
  isBaseListActionColumn,
  resolveBaseListColumnDisplayValue,
  resolveBaseListColumnValue,
  resolveBaseListRowValue,
  resolveBaseListSlotName,
} from './baseListPageRenderModel'

describe('baseListPageRenderModel', () => {
  it('resolves nested row paths and display values', () => {
    const row = {
      code: 'A-001',
      asset: { name: 'Laptop' },
      owner: 'u1',
      ownerName: 'Alice',
    }

    expect(resolveBaseListRowValue(row, 'asset.name')).toBe('Laptop')
    expect(resolveBaseListColumnValue(row, {
      prop: 'code',
      label: 'Code',
    })).toBe('A-001')
    expect(resolveBaseListColumnValue(row, {
      prop: 'owner',
      label: 'Owner',
      fieldType: 'user',
    })).toEqual({
      id: 'u1',
      name: 'Alice',
    })
    expect(resolveBaseListColumnDisplayValue(row, {
      prop: 'code',
      label: 'Code',
      format: (value) => `#${value}`,
    })).toBe('#A-001')
  })

  it('builds field renderer props from table columns', () => {
    expect(buildBaseListRendererField({
      prop: 'owner',
      fieldCode: 'owner',
      label: 'Owner',
      fieldType: 'user',
      referenceObject: 'User',
      referenceDisplayField: 'fullName',
    })).toEqual({
      prop: 'owner',
      dataKey: 'owner',
      type: 'user',
      code: 'owner',
      fieldCode: 'owner',
      fieldType: 'user',
      label: 'Owner',
      options: undefined,
      referenceObject: 'User',
      targetObjectCode: 'User',
      referenceDisplayField: 'fullName',
      referenceSecondaryField: undefined,
    })
  })

  it('resolves slot names and action columns from slot registry', () => {
    const slots = {
      toolbar: true,
      'cell-status': true,
      custom: true,
      actions: true,
    }

    expect(resolveBaseListSlotName({
      prop: 'status',
      label: 'Status',
      slot: true,
    }, slots)).toBe('cell-status')

    expect(resolveBaseListSlotName({
      prop: 'owner',
      label: 'Owner',
      slot: 'custom',
    }, slots)).toBe('custom')

    expect(resolveBaseListSlotName({
      prop: 'code',
      label: 'Code',
    }, slots)).toBeNull()

    expect(isBaseListActionColumn({
      prop: 'actions',
      label: 'Actions',
    }, slots)).toBe(true)

    expect(isBaseListActionColumn({
      prop: 'status',
      label: 'Status',
      slot: true,
    }, slots)).toBe(false)
  })

  it('filters action columns out of mobile data columns', () => {
    const columns: TableColumn[] = [
      { prop: 'code', label: 'Code' },
      { prop: 'actions', label: 'Actions' },
      { prop: 'status', label: 'Status', slot: true },
    ]

    expect(filterBaseListDataColumns(columns, {
      'cell-status': true,
      actions: true,
    })).toEqual([
      { prop: 'code', label: 'Code' },
      { prop: 'status', label: 'Status', slot: true },
    ])
  })
})
