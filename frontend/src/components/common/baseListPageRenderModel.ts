import type { TableColumn } from '@/types/common'
import { resolveListFieldValue } from '@/utils/listFieldValue'

type SlotRegistry = Record<string, unknown>

export interface BaseListRendererField {
  prop: string
  dataKey?: string
  type: string
  code: string
  fieldCode: string
  fieldType: string
  label: string
  options?: TableColumn['options']
  referenceObject?: string
  targetObjectCode?: string
  referenceDisplayField?: string
  referenceSecondaryField?: string
}

const hasSlot = (slots: SlotRegistry, name?: string | null) => {
  if (!name) return false
  return Boolean(slots[name])
}

export const resolveBaseListRowValue = (row: any, prop?: string) => {
  if (!row || !prop) return undefined
  if (!prop.includes('.')) return row[prop]
  return prop.split('.').reduce((acc, key) => (acc ? acc[key] : undefined), row)
}

export const resolveBaseListColumnValue = (row: any, column: TableColumn) => {
  const prop = column.prop || column.fieldCode
  if (!prop) return undefined
  if (prop.includes('.')) return resolveBaseListRowValue(row, prop)

  const resolved = resolveListFieldValue(row, {
    fieldCode: column.fieldCode || prop,
    prop,
    dataKey: column.dataKey || prop,
    fieldType: column.fieldType || column.type,
    referenceObject: column.referenceObject || column.targetObjectCode,
    referenceDisplayField: column.referenceDisplayField,
  })

  if (resolved !== undefined) return resolved
  return resolveBaseListRowValue(row, prop)
}

export const resolveBaseListColumnDisplayValue = (row: any, column: TableColumn) => {
  const value = resolveBaseListColumnValue(row, column)
  return column.format ? column.format(value, row) : value
}

export const buildBaseListRendererField = (column: TableColumn): BaseListRendererField => {
  const prop = String(column.fieldCode || column.prop || '').trim()
  const fieldType = column.fieldType || column.type || 'text'
  return {
    prop,
    dataKey: column.dataKey || column.prop,
    type: fieldType,
    code: prop,
    fieldCode: prop,
    fieldType,
    label: column.label,
    options: column.options,
    referenceObject: column.referenceObject || column.targetObjectCode,
    targetObjectCode: column.targetObjectCode || column.referenceObject,
    referenceDisplayField: column.referenceDisplayField,
    referenceSecondaryField: column.referenceSecondaryField,
  }
}

export const resolveBaseListSlotName = (column: TableColumn, slots: SlotRegistry) => {
  if (typeof column.slot === 'string') {
    return hasSlot(slots, column.slot) ? column.slot : null
  }

  const prop = column.prop || column.fieldCode
  if (!prop) return null

  const cellSlot = `cell-${prop}`
  if (column.slot === true) {
    if (hasSlot(slots, cellSlot)) return cellSlot
    if (hasSlot(slots, prop)) return prop
    return null
  }

  if (hasSlot(slots, cellSlot)) return cellSlot
  if (hasSlot(slots, prop)) return prop
  return null
}

export const isBaseListActionColumn = (column: TableColumn, slots: SlotRegistry) => {
  const prop = column.prop || column.fieldCode
  const slotName = resolveBaseListSlotName(column, slots)
  return prop === 'actions' || slotName === 'actions'
}

export const filterBaseListDataColumns = (columns: TableColumn[], slots: SlotRegistry) => {
  return columns.filter((column) => !isBaseListActionColumn(column, slots))
}
