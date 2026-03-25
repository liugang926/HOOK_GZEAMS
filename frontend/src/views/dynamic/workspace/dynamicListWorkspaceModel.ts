import type { ObjectWorkspaceChip, ObjectWorkspaceStat } from '@/components/common/object-workspace/ObjectWorkspaceHero.vue'

interface DynamicListWorkspaceCopy {
  listModeLabel: string
  createEnabledLabel: string
  fieldCountLabel: string
  visibleFieldCountLabel: string
  searchableFieldCountLabel: string
  listHeroDescription: string
  listPanelTitle: string
  listPanelDescription: string
}

export const resolveDynamicListWorkspaceModuleLabel = ({
  moduleName,
  objectDisplayName,
  objectCode,
}: {
  moduleName?: string | null
  objectDisplayName?: string | null
  objectCode: string
}) => {
  return String(moduleName || '').trim() || String(objectDisplayName || '').trim() || objectCode
}

export const resolveDynamicListWorkspaceCopy = ({
  isZhLocale,
  metadataDescription,
  objectCode,
}: {
  isZhLocale: boolean
  metadataDescription?: string | null
  objectCode?: string | null
}): DynamicListWorkspaceCopy => {
  const description = String(metadataDescription || '').trim()
  const normalizedObjectCode = String(objectCode || '').trim()

  if (normalizedObjectCode === 'AssetProject') {
    if (isZhLocale) {
      return {
        listModeLabel: '项目工作区',
        createEnabledLabel: '支持立项',
        fieldCountLabel: '字段数',
        visibleFieldCountLabel: '列表列',
        searchableFieldCountLabel: '搜索字段',
        listHeroDescription: description || '集中查看项目台账、项目经理与预算执行情况。进入详情后可继续处理项目资产分配和成员协同。',
        listPanelTitle: '项目总览',
        listPanelDescription: '在这里完成项目检索、立项录入和状态跟踪。行级动作可直接跳转到项目资产与成员工作区。',
      }
    }

    return {
      listModeLabel: 'Project workspace',
      createEnabledLabel: 'Project setup enabled',
      fieldCountLabel: 'Fields',
      visibleFieldCountLabel: 'List columns',
      searchableFieldCountLabel: 'Search fields',
      listHeroDescription: description || 'Track project registers, ownership, and budget execution in one place, then drill into detail panels for assets and members.',
      listPanelTitle: 'Project overview',
      listPanelDescription: 'Handle project search, setup, and status review here. Row actions jump directly into the related asset and member workspaces.',
    }
  }

  if (isZhLocale) {
    return {
      listModeLabel: '对象列表',
      createEnabledLabel: '支持新建',
      fieldCountLabel: '字段数',
      visibleFieldCountLabel: '列表列',
      searchableFieldCountLabel: '搜索字段',
      listHeroDescription: description || '统一查看、搜索和维护当前对象记录。列表支持按字段检索、导入导出以及对象级操作。',
      listPanelTitle: '记录工作台',
      listPanelDescription: '在这里完成检索、批量处理和逐条查看。点击行即可进入详情，使用顶部操作可快速新建或调整布局。',
    }
  }

  return {
    listModeLabel: 'List view',
    createEnabledLabel: 'Create enabled',
    fieldCountLabel: 'Fields',
    visibleFieldCountLabel: 'List columns',
    searchableFieldCountLabel: 'Search fields',
    listHeroDescription: description || 'Browse, search, and manage records for this object in one place with field-based search, import/export, and object-level actions.',
    listPanelTitle: 'Record workspace',
    listPanelDescription: 'Handle search, bulk actions, and row-level review here. Click a row to open details, and use the top actions for create or layout changes.',
  }
}

export const countDynamicListVisibleColumns = (tableColumns: Array<{ visible?: boolean }>) => {
  return (tableColumns || []).filter((column) => column?.visible !== false).length
}

export const buildDynamicListHeroChips = ({
  listModeLabel,
  objectCode,
  canAdd,
  createEnabledLabel,
}: {
  listModeLabel: string
  objectCode: string
  canAdd: boolean
  createEnabledLabel: string
}): ObjectWorkspaceChip[] => {
  const chips: ObjectWorkspaceChip[] = [
    { label: listModeLabel, kind: 'primary' },
    { label: objectCode },
  ]

  if (canAdd) {
    chips.push({ label: createEnabledLabel, kind: 'muted' })
  }

  return chips
}

export const buildDynamicListHeroStats = ({
  fieldCountLabel,
  visibleFieldCountLabel,
  searchableFieldCountLabel,
  fieldCount,
  visibleFieldCount,
  searchableFieldCount,
}: {
  fieldCountLabel: string
  visibleFieldCountLabel: string
  searchableFieldCountLabel: string
  fieldCount: number
  visibleFieldCount: number
  searchableFieldCount: number
}): ObjectWorkspaceStat[] => ([
  { label: fieldCountLabel, value: fieldCount },
  { label: visibleFieldCountLabel, value: visibleFieldCount },
  { label: searchableFieldCountLabel, value: searchableFieldCount },
])
