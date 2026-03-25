import type { SearchField, TableColumn } from '@/types/common'
import { compileLayoutSchema } from '@/platform/layout/layoutCompiler'
import {
  projectListColumnsFromRenderSchema,
  projectListLayoutConfigForRenderSchema,
  projectSearchFieldsFromRenderSchema,
} from '@/platform/layout/renderSchemaProjector'
import { buildSearchFields } from '@/platform/layout/searchFieldBuilder'
import { resolveTranslatableText } from '@/utils/localeText'
import { filterSystemFields } from '@/utils/transform'
import { resolveListFieldValue } from '@/utils/listFieldValue'

type AnyRecord = Record<string, any>

export interface RelatedObjectRecord {
  id: string
  [key: string]: unknown
}

export type RelatedTablePosition = 'main' | 'sidebar'

export type RelatedObjectRendererFieldConfig = {
  prop: string
  label: string
  type: string
  [key: string]: unknown
}

type TranslateFn = (key: string, params?: Record<string, unknown>) => string

const toPositiveNumber = (value: unknown): number | undefined => {
  const num = Number(value)
  return Number.isFinite(num) && num > 0 ? num : undefined
}

export function resolveDisplayText(value: unknown, fallback = ''): string {
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (trimmed) return trimmed
  }

  const localized = resolveTranslatableText(value)
  if (localized) {
    const trimmed = localized.trim()
    if (trimmed) return trimmed
  }

  return fallback
}

function resolveFieldLabel(field: AnyRecord, fallback = ''): string {
  return resolveDisplayText(field?.label, resolveDisplayText(field?.name, fallback))
}

export function getRelatedTableFieldCode(field: AnyRecord): string {
  return String(field?.fieldCode || field?.field_code || field?.code || field?.field || '').trim()
}

export function normalizeRelatedTableFieldProp(column: TableColumn): string {
  return String(column.fieldCode || column.prop || '').trim()
}

export function normalizeRelatedTableColumn(column: TableColumn): TableColumn {
  const fallback = normalizeRelatedTableFieldProp(column) || String(column.dataKey || '').trim() || 'field'
  return {
    ...column,
    label: resolveDisplayText(column.label, fallback)
  }
}

function limitColumns(columns: TableColumn[], position: RelatedTablePosition): TableColumn[] {
  const maxColumns = position === 'sidebar' ? 2 : 8
  return columns.slice(0, maxColumns)
}

function shouldDisplayInRelatedTable(field: AnyRecord): boolean {
  const hidden = field?.isHidden ?? field?.is_hidden
  if (hidden === true) return false
  const showInList = field?.showInList ?? field?.show_in_list
  return showInList !== false
}

export function buildColumnsFromMetadata(
  fields: AnyRecord[],
  position: RelatedTablePosition
): TableColumn[] {
  const candidates: Array<{ code: string; sortOrder: number; column: TableColumn }> = []

  fields
    .filter((field) => shouldDisplayInRelatedTable(field))
    .forEach((field) => {
      const code = getRelatedTableFieldCode(field)
      if (!code) return

      candidates.push({
        code,
        sortOrder: Number(field?.sortOrder ?? field?.sort_order ?? 9999),
        column: {
          prop: code,
          fieldCode: code,
          dataKey: String(field?.dataKey || field?.data_key || code),
          label: resolveFieldLabel(field, code),
          fieldType: String(field?.fieldType || field?.field_type || field?.type || 'text'),
          type: String(field?.fieldType || field?.field_type || field?.type || 'text'),
          options: field?.options || field?.choices || [],
          referenceObject: field?.referenceObject || field?.reference_object || field?.targetObjectCode || field?.target_object_code || field?.reference_model_path || field?.relatedObject,
          targetObjectCode: field?.targetObjectCode || field?.target_object_code || field?.referenceObject || field?.reference_object,
          referenceDisplayField: field?.referenceDisplayField || field?.reference_display_field || field?.displayField || field?.display_field,
          referenceSecondaryField: field?.referenceSecondaryField || field?.reference_secondary_field,
          width: toPositiveNumber(field?.columnWidth ?? field?.column_width),
          minWidth: toPositiveNumber(field?.minColumnWidth ?? field?.min_column_width),
          sortable: field?.sortable !== false,
          visible: true
        }
      })
    })

  candidates.sort((a, b) => {
    if (a.sortOrder !== b.sortOrder) return a.sortOrder - b.sortOrder
    return a.code.localeCompare(b.code)
  })

  const filtered = candidates
    .map((item) => item.column)
    .filter((column) => normalizeRelatedTableFieldProp(column) !== 'id')

  return limitColumns(filtered, position)
}

export function buildFallbackColumnsFromRecords(
  dataRows: RelatedObjectRecord[],
  position: RelatedTablePosition,
  t: TranslateFn
): TableColumn[] {
  const first = Array.isArray(dataRows) && dataRows.length > 0 ? (dataRows[0] as AnyRecord) : null
  const allKeys = first
    ? Object.keys(first).filter((key) => key !== 'id' && typeof first[key] !== 'object')
    : []

  const preferredKeys = ['code', 'name', 'status', 'createdAt']
  const prioritizedKeys = [
    ...preferredKeys.filter((key) => allKeys.includes(key)),
    ...allKeys.filter((key) => !preferredKeys.includes(key))
  ]

  return limitColumns(
    prioritizedKeys.map((key) => {
      const labelByKey: Record<string, string> = {
        code: t('common.relatedObject.code'),
        name: t('common.relatedObject.name'),
        status: t('common.relatedObject.status'),
        createdAt: t('common.relatedObject.createdAt')
      }

      return {
        prop: key,
        fieldCode: key,
        label: labelByKey[key] || key,
        minWidth: 120,
        sortable: true
      } as TableColumn
    }),
    position
  )
}

export function extractEditableFields(payload: unknown): AnyRecord[] {
  if (!payload || typeof payload !== 'object') return []
  const raw = payload as AnyRecord
  const source = (raw.data && typeof raw.data === 'object' ? raw.data : raw) as AnyRecord
  const fieldSource = (source.fields && typeof source.fields === 'object' ? source.fields : source) as AnyRecord
  const editableFields = Array.isArray(fieldSource.editableFields)
    ? fieldSource.editableFields
    : Array.isArray(fieldSource.editable_fields)
      ? fieldSource.editable_fields
      : Array.isArray(fieldSource.fields)
        ? fieldSource.fields
        : []

  return editableFields.filter((field: AnyRecord) => {
    const isReverse = field?.isReverseRelation ?? field?.is_reverse_relation
    return isReverse !== true
  })
}

export function extractRecordPageFromResponse(payload: unknown): {
  results: RelatedObjectRecord[]
  count: number
  targetObjectCode: string
} {
  if (!payload || typeof payload !== 'object') {
    return { results: [], count: 0, targetObjectCode: '' }
  }
  const unwrapped = payload as AnyRecord
  const source =
    unwrapped.success === true && unwrapped.data && typeof unwrapped.data === 'object'
      ? (unwrapped.data as AnyRecord)
      : unwrapped
  const results = Array.isArray(source.results) ? (source.results as RelatedObjectRecord[]) : []
  const count = Number(source.count)
  const targetObjectCode = String(
    source.targetObjectCode ||
    source.target_object_code ||
    ((source.relation as AnyRecord | undefined)?.targetObjectCode) ||
    ''
  ).trim()
  return {
    results,
    count: Number.isFinite(count) ? count : results.length,
    targetObjectCode
  }
}

export function buildColumnsFromListModel(
  fields: AnyRecord[],
  layoutPayload: AnyRecord | null,
  position: RelatedTablePosition
): TableColumn[] {
  const businessFields = filterSystemFields(fields)
  if (!businessFields.length) return []

  const schemaLayout = projectListLayoutConfigForRenderSchema(layoutPayload)
  if (!schemaLayout) {
    return buildColumnsFromMetadata(businessFields, position)
  }

  const { renderSchema } = compileLayoutSchema({
    layoutConfig: schemaLayout,
    fields: businessFields,
    mode: 'list',
    keepUnknownFields: true
  })

  const projectedColumns = projectListColumnsFromRenderSchema(renderSchema, businessFields)
  const visibleColumns = projectedColumns.filter((column) => column.visible !== false)
  const sourceColumns = visibleColumns.length > 0 ? visibleColumns : projectedColumns

  const filtered = sourceColumns.filter((column) => normalizeRelatedTableFieldProp(column) !== 'id')
  if (filtered.length > 0) {
    return limitColumns(filtered, position)
  }

  return buildColumnsFromMetadata(businessFields, position)
}

export function buildSearchFieldsFromListModel(
  fields: AnyRecord[],
  layoutPayload: AnyRecord | null
): SearchField[] {
  const businessFields = filterSystemFields(fields)
  if (!businessFields.length) return []

  const schemaLayout = projectListLayoutConfigForRenderSchema(layoutPayload)
  if (!schemaLayout) {
    return buildSearchFields(businessFields)
  }

  const { renderSchema } = compileLayoutSchema({
    layoutConfig: schemaLayout,
    fields: businessFields,
    mode: 'list',
    keepUnknownFields: true
  })

  const projected = projectSearchFieldsFromRenderSchema(renderSchema, businessFields)
  return projected.length > 0 ? projected : buildSearchFields(businessFields)
}

export function getRelatedTableColumnValue(
  row: RelatedObjectRecord,
  column: TableColumn
): unknown {
  const fieldCode = normalizeRelatedTableFieldProp(column)
  if (!fieldCode) return undefined

  if (fieldCode.includes('.')) {
    return fieldCode.split('.').reduce((acc: any, key) => acc?.[key], row as AnyRecord)
  }

  const resolved = resolveListFieldValue(row, {
    fieldCode,
    prop: column.prop || fieldCode,
    dataKey: column.dataKey || column.prop || fieldCode,
    fieldType: column.fieldType || column.type,
    referenceObject: column.referenceObject || column.targetObjectCode,
    referenceDisplayField: column.referenceDisplayField
  })

  if (resolved !== undefined) return resolved
  return (row as AnyRecord)?.[column.prop]
}

export function getRelatedTableRendererField(
  column: TableColumn,
  modelFieldMap: Map<string, AnyRecord>
): RelatedObjectRendererFieldConfig {
  const fieldCode = normalizeRelatedTableFieldProp(column)
  const field = modelFieldMap.get(fieldCode) || {}
  const fieldType = String(
    column.fieldType ||
    column.type ||
    field.fieldType ||
    field.field_type ||
    field.type ||
    'text'
  )

  return {
    prop: column.prop,
    dataKey: column.dataKey || column.prop,
    fieldCode,
    code: fieldCode,
    label: column.label,
    type: fieldType,
    fieldType,
    options: column.options || field.options || field.choices || [],
    referenceObject: column.referenceObject || column.targetObjectCode || field.referenceObject || field.reference_object || field.targetObjectCode || field.target_object_code || field.reference_model_path || field.relatedObject,
    targetObjectCode: column.targetObjectCode || column.referenceObject || field.targetObjectCode || field.target_object_code || field.referenceObject || field.reference_object,
    referenceRoute: field.referenceRoute || field.reference_route,
    referenceDisplayField:
      column.referenceDisplayField ||
      field.referenceDisplayField ||
      field.reference_display_field ||
      field.displayField ||
      field.display_field,
    referenceSecondaryField:
      column.referenceSecondaryField ||
      field.referenceSecondaryField ||
      field.reference_secondary_field
  }
}
