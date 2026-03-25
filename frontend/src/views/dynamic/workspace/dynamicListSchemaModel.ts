import type { RenderSchema } from '@/platform/layout/renderSchema'
import type { SearchField, TableColumn } from '@/types/common'
import { resolveFieldType } from '@/utils/fieldType'
import { filterSystemFields } from '@/utils/transform'

export interface DynamicListSearchOption {
  label: string
  value: string
}

export const resolveDynamicListFieldCode = (field: any): string => {
  return String(field?.code || field?.fieldCode || field?.field_code || '').trim()
}

export const buildDynamicListFieldColumn = (field: any, visible = false): TableColumn | null => {
  const fieldCode = resolveDynamicListFieldCode(field)
  if (!fieldCode) return null

  const fieldType = resolveFieldType(field, 'text')
  return {
    prop: fieldCode,
    fieldCode,
    dataKey: field?.dataKey || field?.data_key || fieldCode,
    label: field?.name || field?.label || fieldCode,
    type: fieldType,
    fieldType,
    options: field?.options || field?.choices || [],
    referenceObject: field?.referenceObject || field?.reference_object || field?.targetObjectCode || field?.target_object_code || field?.reference_model_path || field?.relatedObject,
    targetObjectCode: field?.targetObjectCode || field?.target_object_code || field?.referenceObject || field?.reference_object,
    referenceDisplayField: field?.referenceDisplayField || field?.reference_display_field || field?.displayField || field?.display_field,
    referenceSecondaryField: field?.referenceSecondaryField || field?.reference_secondary_field,
    sortable: field?.sortable !== false,
    visible,
  } as TableColumn
}

export const selectDynamicListDefaultVisibleFieldCodes = (fields: any[], maxVisible = 8): Set<string> => {
  const candidates = filterSystemFields(fields || [])
    .map((field) => ({
      code: resolveDynamicListFieldCode(field),
      score: (() => {
        let score = 0
        const showInList = field?.showInList ?? field?.show_in_list
        const isIdentifier = field?.isIdentifier ?? field?.is_identifier
        const code = String(field?.code || '').trim()
        if (showInList === true) score += 100
        if (isIdentifier === true) score += 60
        if (code === 'name' || code.endsWith('_name')) score += 40
        if (code === 'code' || code.endsWith('_code')) score += 30
        if (code.includes('status')) score += 20
        if (code.includes('date')) score += 5
        return score
      })(),
      sortOrder: Number(field?.sortOrder ?? field?.sort_order ?? 9999),
    }))
    .filter((item) => item.code)

  if (!candidates.length) return new Set<string>()

  const ranked = [...candidates].sort((a, b) => {
    if (b.score !== a.score) return b.score - a.score
    return a.sortOrder - b.sortOrder
  })

  return new Set(ranked.slice(0, maxVisible).map((item) => item.code))
}

export const extractDynamicListLayoutFieldCodes = (schema: RenderSchema | null): Set<string> => {
  const layoutFieldCodes = new Set<string>()

  if (!schema?.sections?.length) return layoutFieldCodes

  for (const section of schema.sections) {
    for (const field of section.fields) {
      const code = String(field.code || '').trim()
      if (code) layoutFieldCodes.add(code)
    }
  }

  return layoutFieldCodes
}

export const buildDynamicListTableColumns = (fields: any[], schema: RenderSchema | null): TableColumn[] => {
  const businessFields = filterSystemFields(fields || [])
  if (!businessFields.length) return []

  const layoutFieldCodes = extractDynamicListLayoutFieldCodes(schema)
  const hasLayoutFields = layoutFieldCodes.size > 0
  const heuristicVisibleCodes = hasLayoutFields ? new Set<string>() : selectDynamicListDefaultVisibleFieldCodes(businessFields)

  const columns: TableColumn[] = []
  const seen = new Set<string>()

  for (const field of businessFields) {
    const code = resolveDynamicListFieldCode(field)
    if (!code || seen.has(code)) continue
    seen.add(code)

    const visible = hasLayoutFields
      ? layoutFieldCodes.has(code)
      : heuristicVisibleCodes.has(code)

    const column = buildDynamicListFieldColumn(field, visible)
    if (column) columns.push(column)
  }

  return columns
}

export const buildDynamicListSearchCandidateOptions = (fields: any[]): DynamicListSearchOption[] => {
  const candidates = filterSystemFields(fields || [])
  const seen = new Set<string>()
  const options: DynamicListSearchOption[] = []

  for (const field of candidates as any[]) {
    const value = resolveDynamicListFieldCode(field)
    if (!value || seen.has(value)) continue
    seen.add(value)
    options.push({
      label: String(field?.name || field?.label || value),
      value,
    })
  }

  return options
}

export const filterDynamicListVisibleSearchCandidateOptions = (
  tableColumns: TableColumn[],
  candidateOptions: DynamicListSearchOption[],
): DynamicListSearchOption[] => {
  const visibleCodes = new Set(
    (tableColumns || [])
      .filter((column) => column?.visible !== false)
      .map((column) => String(column?.fieldCode || column?.prop || '').trim())
      .filter(Boolean),
  )

  if (!visibleCodes.size) return candidateOptions
  return candidateOptions.filter((item) => visibleCodes.has(item.value))
}

export const resolveDynamicListSearchFieldOptions = ({
  rawSearchFields,
  tableColumns,
  orderedVisibleFields,
}: {
  rawSearchFields: SearchField[]
  tableColumns: TableColumn[]
  orderedVisibleFields: any[]
}): DynamicListSearchOption[] => {
  const allCandidateOptions = buildDynamicListSearchCandidateOptions(orderedVisibleFields)
  const candidateOptions = filterDynamicListVisibleSearchCandidateOptions(tableColumns, allCandidateOptions).length
    ? filterDynamicListVisibleSearchCandidateOptions(tableColumns, allCandidateOptions)
    : allCandidateOptions
  const candidateCodeSet = new Set(candidateOptions.map((item) => item.value))

  if (!rawSearchFields.length) return candidateOptions

  const bySearchable = rawSearchFields
    .map((field) => ({
      label: String(field?.label || field?.prop || field?.field || ''),
      value: String(field?.prop || field?.field || '').trim(),
    }))
    .filter((item) => item.value && candidateCodeSet.has(item.value))

  return bySearchable.length ? bySearchable : candidateOptions
}
