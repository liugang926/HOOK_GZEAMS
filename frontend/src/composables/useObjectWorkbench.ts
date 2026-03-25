import { computed, type ComputedRef, type Ref } from 'vue'
import type {
  RuntimeWorkbench,
  RuntimeWorkbenchAsyncIndicator,
  RuntimeWorkbenchDetailPanel,
} from '@/types/runtime'

type WorkbenchRecord = Record<string, unknown> | null | undefined

interface WorkbenchVisibilityRule {
  statuses?: string[]
  statusIn?: string[]
  statusNotIn?: string[]
}

interface ResolvedWorkbenchVisibilityRule {
  statuses: string[]
  statusIn: string[]
  statusNotIn: string[]
}

interface WorkbenchDefinitionBase {
  visibleWhen?: WorkbenchVisibilityRule | Record<string, unknown>
  visible_when?: WorkbenchVisibilityRule | Record<string, unknown>
}

interface WorkbenchActionDefinition extends WorkbenchDefinitionBase, Record<string, unknown> {
  code: string
}

const toNormalizedStatus = (recordData: WorkbenchRecord) => {
  if (!recordData || typeof recordData !== 'object') return ''
  return String((recordData as Record<string, unknown>).status || '').trim()
}

const normalizeStatusList = (value: unknown) => {
  if (!Array.isArray(value)) return []
  return value
    .map((item) => String(item || '').trim())
    .filter(Boolean)
}

const resolveVisibilityRule = (definition: WorkbenchDefinitionBase): ResolvedWorkbenchVisibilityRule => {
  const rule = definition.visibleWhen || definition.visible_when
  if (!rule || typeof rule !== 'object') {
    return {
      statuses: [],
      statusIn: [],
      statusNotIn: [],
    }
  }

  const candidate = rule as Record<string, unknown>
  return {
    statuses: normalizeStatusList(candidate.statuses),
    statusIn: normalizeStatusList(candidate.statusIn || candidate.status_in),
    statusNotIn: normalizeStatusList(candidate.statusNotIn || candidate.status_not_in),
  }
}

const isVisibleForRecord = (definition: WorkbenchDefinitionBase, recordData: WorkbenchRecord) => {
  const status = toNormalizedStatus(recordData)
  const rule = resolveVisibilityRule(definition)
  const allowStatuses = rule.statuses.length > 0 ? rule.statuses : rule.statusIn

  if (allowStatuses.length > 0 && !allowStatuses.includes(status)) {
    return false
  }

  if (rule.statusNotIn && rule.statusNotIn.includes(status)) {
    return false
  }

  return true
}

const normalizeActionList = (value: unknown): WorkbenchActionDefinition[] => {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is WorkbenchActionDefinition => {
    return Boolean(item && typeof item === 'object' && String((item as Record<string, unknown>).code || '').trim())
  })
}

const normalizePanelList = (value: unknown): RuntimeWorkbenchDetailPanel[] => {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is RuntimeWorkbenchDetailPanel => {
    return Boolean(item && typeof item === 'object' && String((item as Record<string, unknown>).code || '').trim())
  })
}

const normalizeIndicatorList = (value: unknown): RuntimeWorkbenchAsyncIndicator[] => {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is RuntimeWorkbenchAsyncIndicator => {
    return Boolean(item && typeof item === 'object' && String((item as Record<string, unknown>).code || '').trim())
  })
}

export const useObjectWorkbench = ({
  workbench,
  recordData,
}: {
  workbench: Ref<RuntimeWorkbench | null> | ComputedRef<RuntimeWorkbench | null>
  recordData: Ref<WorkbenchRecord> | ComputedRef<WorkbenchRecord>
}) => {
  const primaryActions = computed(() => {
    return normalizeActionList(workbench.value?.toolbar?.primaryActions).filter((action) =>
      isVisibleForRecord(action, recordData.value)
    )
  })

  const secondaryActions = computed(() => {
    return normalizeActionList(workbench.value?.toolbar?.secondaryActions).filter((action) =>
      isVisibleForRecord(action, recordData.value)
    )
  })

  const detailPanels = computed(() => {
    return normalizePanelList(workbench.value?.detailPanels).filter((panel) =>
      isVisibleForRecord(panel as WorkbenchDefinitionBase, recordData.value)
    )
  })

  const asyncIndicators = computed(() => {
    return normalizeIndicatorList(workbench.value?.asyncIndicators).filter((indicator) =>
      isVisibleForRecord(indicator as WorkbenchDefinitionBase, recordData.value)
    )
  })

  return {
    asyncIndicators,
    detailPanels,
    hasActions: computed(() => primaryActions.value.length > 0 || secondaryActions.value.length > 0),
    hasPanels: computed(() => detailPanels.value.length > 0),
    primaryActions,
    secondaryActions,
  }
}
