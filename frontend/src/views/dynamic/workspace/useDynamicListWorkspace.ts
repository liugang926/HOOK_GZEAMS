import { computed, type ComputedRef, type Ref } from 'vue'
import type { ObjectMetadata } from '@/api/dynamic'
import {
  buildDynamicListHeroChips,
  buildDynamicListHeroStats,
  countDynamicListVisibleColumns,
  resolveDynamicListWorkspaceCopy,
  resolveDynamicListWorkspaceModuleLabel,
} from './dynamicListWorkspaceModel'

interface Params {
  isZhLocale: ComputedRef<boolean>
  objectCode: Ref<string>
  objectMetadata: Ref<ObjectMetadata | null>
  objectDisplayName: ComputedRef<string>
  canAdd: ComputedRef<boolean>
  tableColumns: ComputedRef<Array<{ visible?: boolean }>>
  unifiedSearchFieldOptions: ComputedRef<Array<{ value: string }>>
}

export const useDynamicListWorkspace = ({
  isZhLocale,
  objectCode,
  objectMetadata,
  objectDisplayName,
  canAdd,
  tableColumns,
  unifiedSearchFieldOptions,
}: Params) => {
  const workspaceCopy = computed(() => resolveDynamicListWorkspaceCopy({
    isZhLocale: isZhLocale.value,
    metadataDescription: objectMetadata.value?.description,
    objectCode: objectCode.value,
  }))

  const moduleLabel = computed(() => {
    return resolveDynamicListWorkspaceModuleLabel({
      moduleName: objectMetadata.value?.module,
      objectDisplayName: objectDisplayName.value,
      objectCode: objectCode.value,
    })
  })

  const fieldCount = computed(() => {
    return Array.isArray(objectMetadata.value?.fields) ? objectMetadata.value?.fields.length || 0 : 0
  })

  const visibleFieldCount = computed(() => {
    return countDynamicListVisibleColumns(tableColumns.value || [])
  })

  const searchableFieldCount = computed(() => {
    return unifiedSearchFieldOptions.value.length
  })

  const listModeLabel = computed(() => workspaceCopy.value.listModeLabel)
  const listHeroDescription = computed(() => workspaceCopy.value.listHeroDescription)
  const listPanelTitle = computed(() => workspaceCopy.value.listPanelTitle)
  const listPanelDescription = computed(() => workspaceCopy.value.listPanelDescription)

  const heroChips = computed(() => buildDynamicListHeroChips({
    listModeLabel: workspaceCopy.value.listModeLabel,
    objectCode: objectCode.value,
    canAdd: canAdd.value,
    createEnabledLabel: workspaceCopy.value.createEnabledLabel,
  }))

  const heroStats = computed(() => buildDynamicListHeroStats({
    fieldCountLabel: workspaceCopy.value.fieldCountLabel,
    visibleFieldCountLabel: workspaceCopy.value.visibleFieldCountLabel,
    searchableFieldCountLabel: workspaceCopy.value.searchableFieldCountLabel,
    fieldCount: fieldCount.value,
    visibleFieldCount: visibleFieldCount.value,
    searchableFieldCount: searchableFieldCount.value,
  }))

  return {
    moduleLabel,
    listModeLabel,
    listHeroDescription,
    listPanelTitle,
    listPanelDescription,
    heroChips,
    heroStats,
  }
}
