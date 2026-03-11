import { computed, type ComputedRef, type Ref } from 'vue'
import type { ObjectMetadata } from '@/api/dynamic'
import type { ObjectWorkspaceChip, ObjectWorkspaceStat } from '@/components/common/object-workspace/ObjectWorkspaceHero.vue'

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
  const moduleLabel = computed(() => {
    return String(objectMetadata.value?.module || '').trim() || objectCode.value
  })

  const listModeLabel = computed(() => {
    return isZhLocale.value ? '对象列表' : 'List view'
  })

  const createEnabledLabel = computed(() => {
    return isZhLocale.value ? '支持新建' : 'Create enabled'
  })

  const fieldCount = computed(() => {
    return Array.isArray(objectMetadata.value?.fields) ? objectMetadata.value?.fields.length || 0 : 0
  })

  const visibleFieldCount = computed(() => {
    return (tableColumns.value || []).filter((column) => column?.visible !== false).length
  })

  const searchableFieldCount = computed(() => {
    return unifiedSearchFieldOptions.value.length
  })

  const fieldCountLabel = computed(() => {
    return isZhLocale.value ? '字段数' : 'Fields'
  })

  const visibleFieldCountLabel = computed(() => {
    return isZhLocale.value ? '列表列' : 'List columns'
  })

  const searchableFieldCountLabel = computed(() => {
    return isZhLocale.value ? '搜索字段' : 'Search fields'
  })

  const listHeroDescription = computed(() => {
    const description = String(objectMetadata.value?.description || '').trim()
    if (description) return description
    return isZhLocale.value
      ? '统一查看、搜索和维护当前对象记录。列表支持按字段检索、导入导出以及对象级操作。'
      : 'Browse, search, and manage records for this object in one place with field-based search, import/export, and object-level actions.'
  })

  const listPanelTitle = computed(() => {
    return isZhLocale.value ? '记录工作台' : 'Record workspace'
  })

  const listPanelDescription = computed(() => {
    return isZhLocale.value
      ? '在这里完成检索、批量处理和逐条查看。点击行即可进入详情，使用顶部操作可快速新建或调整布局。'
      : 'Handle search, bulk actions, and row-level review here. Click a row to open details, and use the top actions for create or layout changes.'
  })

  const heroChips = computed<ObjectWorkspaceChip[]>(() => {
    const chips: ObjectWorkspaceChip[] = [
      { label: listModeLabel.value, kind: 'primary' },
      { label: objectCode.value },
    ]
    if (canAdd.value) {
      chips.push({ label: createEnabledLabel.value, kind: 'muted' })
    }
    return chips
  })

  const heroStats = computed<ObjectWorkspaceStat[]>(() => ([
    { label: fieldCountLabel.value, value: fieldCount.value },
    { label: visibleFieldCountLabel.value, value: visibleFieldCount.value },
    { label: searchableFieldCountLabel.value, value: searchableFieldCount.value },
  ]))

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
