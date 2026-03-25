import { describe, expect, it } from 'vitest'
import type { TableColumn } from '@/types/common'
import {
  applyBaseListColumnWidth,
  reorderBaseListColumnsAfterDrag,
} from './baseListPageColumnModel'

describe('baseListPageColumnModel', () => {
  it('reorders visible columns after drag while preserving hidden columns at the end', () => {
    const activeColumns: TableColumn[] = [
      { prop: 'code', label: 'Code', visible: true },
      { prop: 'name', label: 'Name', visible: true },
      { prop: 'status', label: 'Status', visible: true },
      { prop: 'hidden', label: 'Hidden', visible: false },
    ]

    expect(reorderBaseListColumnsAfterDrag({
      activeColumns,
      visibleColumns: activeColumns.filter((column) => column.visible !== false),
      oldIndex: 4,
      newIndex: 2,
      selectable: true,
      showIndex: true,
    })).toEqual([
      { prop: 'status', label: 'Status', visible: true },
      { prop: 'code', label: 'Code', visible: true },
      { prop: 'name', label: 'Name', visible: true },
      { prop: 'hidden', label: 'Hidden', visible: false },
    ])
  })

  it('returns null for invalid drag ranges and applies resized widths immutably', () => {
    const columns: TableColumn[] = [
      { prop: 'code', label: 'Code', width: 120 },
      { prop: 'name', label: 'Name', width: 180 },
    ]

    expect(reorderBaseListColumnsAfterDrag({
      activeColumns: columns,
      visibleColumns: columns,
      oldIndex: 0,
      newIndex: 1,
      selectable: true,
      showIndex: false,
    })).toBeNull()

    expect(applyBaseListColumnWidth(columns, 'name', 240)).toEqual([
      { prop: 'code', label: 'Code', width: 120 },
      { prop: 'name', label: 'Name', width: 240 },
    ])
    expect(applyBaseListColumnWidth(columns, 'missing', 240)).toBe(columns)
  })
})
