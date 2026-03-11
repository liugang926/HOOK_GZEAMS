import { computed, type ComputedRef, type Ref } from 'vue'
import type { TableColumn, SearchField } from '@/types/common'
import { filterSystemFields } from '@/utils/transform'
import { buildSearchFields } from '@/platform/layout/searchFieldBuilder'
import type { RenderSchema } from '@/platform/layout/renderSchema'
import { resolveFieldType } from '@/utils/fieldType'
import {
  projectListLayoutConfigForRenderSchema,
  projectSearchFieldsFromRenderSchema,
} from '@/platform/layout/renderSchemaProjector'
import { mergeFieldSources, orderFieldsWithSchema } from '@/platform/layout/unifiedFieldOrder'
import { compileLayoutSchema } from '@/platform/layout/layoutCompiler'

interface Params {
  objectMetadata: Ref<any>
  runtimeColumns: Ref<any[]>
  runtimeFields: Ref<any[]>
  runtimeLayoutConfig: Ref<Record<string, any> | null>
}

const buildFieldColumn = (field: any, visible = false): TableColumn | null => {
  const fieldCode = String(field?.code || field?.fieldCode || field?.field_code || '').trim()
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

const selectDefaultVisibleFieldCodes = (fields: any[], maxVisible = 8): Set<string> => {
  const candidates = filterSystemFields(fields || [])
    .map((field) => ({
      code: String(field?.code || field?.fieldCode || field?.field_code || '').trim(),
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

const buildAllFieldColumns = (fields: any[], schema: RenderSchema | null): TableColumn[] => {
  const businessFields = filterSystemFields(fields || [])
  if (!businessFields.length) return []

  const layoutFieldCodes = new Set<string>()
  if (schema?.sections?.length) {
    for (const section of schema.sections) {
      for (const field of section.fields) {
        const code = String(field.code || '').trim()
        if (code) layoutFieldCodes.add(code)
      }
    }
  }

  const hasLayoutFields = layoutFieldCodes.size > 0
  const heuristicVisibleCodes = hasLayoutFields ? new Set<string>() : selectDefaultVisibleFieldCodes(businessFields)

  const columns: TableColumn[] = []
  const seen = new Set<string>()

  for (const field of businessFields) {
    const code = String(field?.code || field?.fieldCode || field?.field_code || '').trim()
    if (!code || seen.has(code)) continue
    seen.add(code)

    const visible = hasLayoutFields
      ? layoutFieldCodes.has(code)
      : heuristicVisibleCodes.has(code)

    const column = buildFieldColumn(field, visible)
    if (column) columns.push(column)
  }

  return columns
}

export const useDynamicListSchema = ({
  objectMetadata,
  runtimeColumns,
  runtimeFields,
  runtimeLayoutConfig,
}: Params) => {
  const visibleFieldsSource = computed<any[]>(() => {
    const runtime = Array.isArray(runtimeFields.value) ? runtimeFields.value : []
    const metadata = Array.isArray(objectMetadata.value?.fields) ? objectMetadata.value?.fields || [] : []
    return mergeFieldSources(runtime, metadata)
  })

  const effectiveListLayoutConfig = computed<Record<string, any> | null>(() => {
    if (runtimeLayoutConfig.value) return runtimeLayoutConfig.value
    const metadataListLayout = (objectMetadata.value as any)?.layouts?.list
    return metadataListLayout && typeof metadataListLayout === 'object' ? metadataListLayout : null
  })

  const schemaLayoutConfig = computed<Record<string, any> | null>(() => {
    return projectListLayoutConfigForRenderSchema(effectiveListLayoutConfig.value, runtimeColumns.value)
  })

  const listRenderSchema = computed(() => {
    if (!visibleFieldsSource.value.length) return null
    return compileLayoutSchema({
      layoutConfig: schemaLayoutConfig.value,
      fields: visibleFieldsSource.value as Record<string, unknown>[],
      mode: 'list',
    }).renderSchema
  })

  const orderedVisibleFieldsSource = computed<any[]>(() => {
    if (!visibleFieldsSource.value.length) return []
    return orderFieldsWithSchema(
      visibleFieldsSource.value as Record<string, unknown>[],
      listRenderSchema.value
    )
  })

  const businessFieldCandidates = computed<any[]>(() => {
    return filterSystemFields(orderedVisibleFieldsSource.value || [])
  })

  const hasNoBusinessFields = computed(() => {
    return businessFieldCandidates.value.length === 0
  })

  const tableColumns = computed<TableColumn[]>(() => {
    return buildAllFieldColumns(
      orderedVisibleFieldsSource.value,
      listRenderSchema.value
    )
  })

  const rawSearchFields = computed<SearchField[]>(() => {
    if (!visibleFieldsSource.value.length) return []

    if (listRenderSchema.value) {
      return projectSearchFieldsFromRenderSchema(
        listRenderSchema.value,
        filterSystemFields(orderedVisibleFieldsSource.value) as Record<string, unknown>[]
      ) as SearchField[]
    }

    return buildSearchFields(
      filterSystemFields(orderedVisibleFieldsSource.value) as Record<string, unknown>[]
    ) as SearchField[]
  })

  const unifiedSearchFieldCandidates = computed(() => {
    const candidates = filterSystemFields(orderedVisibleFieldsSource.value || [])
    const seen = new Set<string>()
    const options: Array<{ label: string; value: string }> = []
    for (const field of candidates as any[]) {
      const value = String(field?.code || field?.fieldCode || field?.field_code || '').trim()
      if (!value || seen.has(value)) continue
      seen.add(value)
      options.push({
        label: String(field?.name || field?.label || value),
        value,
      })
    }
    return options
  })

  const visibleUnifiedSearchFieldCandidates = computed(() => {
    const visibleCodes = new Set(
      (tableColumns.value || [])
        .filter((column) => column?.visible !== false)
        .map((column) => String(column?.fieldCode || column?.prop || '').trim())
        .filter(Boolean)
    )

    if (!visibleCodes.size) return unifiedSearchFieldCandidates.value
    return unifiedSearchFieldCandidates.value.filter((item) => visibleCodes.has(item.value))
  })

  const unifiedSearchFieldOptions = computed(() => {
    const candidateOptions = visibleUnifiedSearchFieldCandidates.value.length
      ? visibleUnifiedSearchFieldCandidates.value
      : unifiedSearchFieldCandidates.value
    const candidateCodeSet = new Set(candidateOptions.map((item) => item.value))

    if (!rawSearchFields.value.length) return candidateOptions

    const bySearchable = rawSearchFields.value
      .map((field) => ({
        label: String(field?.label || field?.prop || field?.field || ''),
        value: String(field?.prop || field?.field || '').trim(),
      }))
      .filter((item) => item.value && candidateCodeSet.has(item.value))

    return bySearchable.length ? bySearchable : candidateOptions
  })

  return {
    businessFieldCandidates,
    hasNoBusinessFields,
    listRenderSchema,
    orderedVisibleFieldsSource,
    rawSearchFields,
    tableColumns,
    unifiedSearchFieldOptions,
    visibleFieldsSource,
  }
}
