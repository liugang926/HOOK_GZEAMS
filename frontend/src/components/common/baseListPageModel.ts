import type { ColumnItem, SearchField, TableColumn } from '@/types/common'
import { normalizeFieldType } from '@/utils/fieldType'
import { buildFieldKeyCandidates } from '@/utils/fieldKey'

export const normalizeBaseListSearchField = (field: SearchField) => {
  const prop = field.prop || field.field
  if (!prop) return null

  const rawType = (field.type || 'text') as string
  const typeMap: Record<string, SearchField['type']> = {
    input: 'text',
    text: 'text',
    daterange: 'dateRange',
    date_range: 'dateRange',
    dateRange: 'dateRange',
    month: 'month',
    year: 'year',
  }

  return {
    ...field,
    prop,
    type: typeMap[rawType] || (rawType as SearchField['type']),
  } as SearchField
}

export const getBaseListSearchFieldKey = (field: SearchField): string => {
  return field.prop || field.field || ''
}

export const buildBaseListSearchResetPatch = (fields: SearchField[]) => {
  return fields.reduce((acc, field) => {
    const key = getBaseListSearchFieldKey(field)
    if (!key) return acc
    acc[key] = undefined
    if (field.type === 'numberRange') {
      acc[`${key}_min`] = undefined
      acc[`${key}_max`] = undefined
    }
    return acc
  }, {} as Record<string, any>)
}

export const buildBaseListRequestParams = ({
  currentPage,
  pageSize,
  visibleColumns,
  searchForm,
  sortState,
}: {
  currentPage: number
  pageSize: number
  visibleColumns: TableColumn[]
  searchForm: Record<string, any>
  sortState: { prop: string; order: string } | null
}) => {
  const visibleFieldCodes = visibleColumns
    .map((column) => String(column.fieldCode || column.prop || '').trim())
    .filter(Boolean)

  const params: Record<string, any> = {
    page: currentPage,
    pageSize,
    __visibleFieldCodes: visibleFieldCodes,
  }

  Object.keys(searchForm).forEach((key) => {
    const value = searchForm[key]
    if (value !== undefined && value !== null && value !== '') {
      params[key] = value
    }
  })

  if (sortState?.prop) {
    const prefix = sortState.order === 'descending' ? '-' : ''
    params.ordering = `${prefix}${sortState.prop}`
  }

  return params
}

export const resolveBaseListResponsePayload = (response: any) => {
  if (response?.results) {
    return {
      tableData: response.results,
      total: response.count || 0,
    }
  }

  if (Array.isArray(response)) {
    return {
      tableData: response,
      total: response.length,
    }
  }

  return {
    tableData: [],
    total: 0,
  }
}

export const prepareBaseListColumns = (columns: TableColumn[]): TableColumn[] => {
  return columns.map((column) => ({
    ...column,
    fieldCode: column.fieldCode || column.prop,
    sortable: (column.sortable === undefined || column.sortable === true) ? 'custom' : column.sortable,
    visible: column.visible !== false,
  }))
}

export const normalizeBaseListColumnSaveInput = (columns: ColumnItem[]): TableColumn[] => {
  return columns
    .map((column) => ({
      ...column,
      prop: column.prop || column.fieldCode || column.field_code || '',
    }))
    .filter((column) => !!column.prop) as TableColumn[]
}

export const resolveBaseListFieldCode = (entry: any): string => {
  return entry?.fieldCode || entry?.field_code || entry?.prop || entry?.code || entry?.field || ''
}

export const applyBaseListFieldDefinitions = (columns: TableColumn[], definitions: any[]): TableColumn[] => {
  if (!Array.isArray(definitions) || definitions.length === 0) return columns

  const fieldMap = new Map<string, any>()
  definitions.forEach((field) => {
    const code = field.code || field.fieldCode || field.field_code || field.fieldName
    if (!code) return
    buildFieldKeyCandidates(String(code)).forEach((key) => fieldMap.set(key, field))
  })

  return columns.map((column) => {
    const fieldCode = resolveBaseListFieldCode(column)
    const meta = buildFieldKeyCandidates(fieldCode)
      .map((key) => fieldMap.get(key))
      .find(Boolean)

    if (!meta) return column

    const rawType = column.fieldType || column.type || meta.fieldType || meta.field_type
    const normalizedType = rawType ? normalizeFieldType(rawType) : undefined

    return {
      ...column,
      fieldCode: column.fieldCode || fieldCode,
      dataKey: column.dataKey || meta.dataKey || meta.data_key || fieldCode,
      label: column.label || meta.name || meta.label || fieldCode,
      fieldType: column.fieldType || normalizedType,
      type: column.type || normalizedType,
      options: column.options || meta.options || meta.choices,
      referenceObject: column.referenceObject || meta.referenceObject || meta.reference_object || meta.reference_model_path || meta.relatedObject,
      referenceDisplayField: column.referenceDisplayField || meta.referenceDisplayField || meta.reference_display_field || meta.displayField || meta.display_field,
      referenceSecondaryField: column.referenceSecondaryField || meta.referenceSecondaryField || meta.reference_secondary_field,
    }
  })
}

export const needsBaseListFieldDefinitions = (columns: TableColumn[]) => {
  return columns.some((column) => (!column.fieldType && !column.type) || (!column.options && !column.tagType))
}
