import { computed, type Ref } from 'vue'
import type { TableColumn, SearchField } from '@/types/common'
import { filterSystemFields } from '@/utils/transform'
import { buildSearchFields } from '@/platform/layout/searchFieldBuilder'
import {
  projectListLayoutConfigForRenderSchema,
  projectSearchFieldsFromRenderSchema,
} from '@/platform/layout/renderSchemaProjector'
import { mergeFieldSources, orderFieldsWithSchema } from '@/platform/layout/unifiedFieldOrder'
import { compileLayoutSchema } from '@/platform/layout/layoutCompiler'
import {
  buildDynamicListTableColumns,
  resolveDynamicListSearchFieldOptions,
} from './dynamicListSchemaModel'

interface Params {
  objectMetadata: Ref<any>
  runtimeColumns: Ref<any[]>
  runtimeFields: Ref<any[]>
  runtimeLayoutConfig: Ref<Record<string, any> | null>
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
    return buildDynamicListTableColumns(
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

  const unifiedSearchFieldOptions = computed(() => {
    return resolveDynamicListSearchFieldOptions({
      rawSearchFields: rawSearchFields.value,
      tableColumns: tableColumns.value,
      orderedVisibleFields: orderedVisibleFieldsSource.value,
    })
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
