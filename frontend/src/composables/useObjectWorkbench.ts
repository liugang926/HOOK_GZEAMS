import { computed, type ComputedRef, type Ref } from 'vue'
import type {
  RuntimeWorkbench,
  RuntimeWorkbenchAsyncIndicator,
  RuntimeWorkbenchClosurePanel,
  RuntimeWorkbenchDetailPanel,
  RuntimeWorkbenchSurfacePriority,
  RuntimeWorkbenchQueuePanel,
  RuntimeWorkbenchRecommendedAction,
  RuntimeWorkbenchSlaIndicator,
  RuntimeWorkbenchSummaryCard,
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

const VALID_SURFACE_PRIORITIES: RuntimeWorkbenchSurfacePriority[] = [
  'primary',
  'context',
  'related',
  'activity',
  'admin',
]

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

const normalizeSurfacePriority = (value: unknown): RuntimeWorkbenchSurfacePriority | null => {
  if (typeof value !== 'string') return null
  const candidate = value.trim() as RuntimeWorkbenchSurfacePriority
  return VALID_SURFACE_PRIORITIES.includes(candidate) ? candidate : null
}

const resolveSurfacePriority = (
  definition: Record<string, unknown>,
): RuntimeWorkbenchSurfacePriority | null => {
  return normalizeSurfacePriority(definition.surfacePriority ?? definition.surface_priority)
}

const normalizeAllowedSurfacePriorities = (
  value: unknown,
): RuntimeWorkbenchSurfacePriority[] | null => {
  if (!Array.isArray(value)) return null
  const priorities = value
    .map((item) => normalizeSurfacePriority(item))
    .filter((item): item is RuntimeWorkbenchSurfacePriority => Boolean(item))
  return priorities.length > 0 ? priorities : null
}

const isVisibleForSurfacePriority = (
  definition: Record<string, unknown>,
  allowedSurfacePriorities: RuntimeWorkbenchSurfacePriority[] | null,
) => {
  if (!allowedSurfacePriorities || allowedSurfacePriorities.length === 0) {
    return true
  }
  const priority = resolveSurfacePriority(definition)
  if (!priority) {
    return true
  }
  return allowedSurfacePriorities.includes(priority)
}

const normalizePanelList = (value: unknown): RuntimeWorkbenchDetailPanel[] => {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is RuntimeWorkbenchDetailPanel => {
    return Boolean(item && typeof item === 'object' && String((item as Record<string, unknown>).code || '').trim())
  })
}

const normalizeSummaryCardList = (value: unknown): RuntimeWorkbenchSummaryCard[] => {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is RuntimeWorkbenchSummaryCard => {
    return Boolean(item && typeof item === 'object' && String((item as Record<string, unknown>).code || '').trim())
  })
}

const normalizeQueuePanelList = (value: unknown): RuntimeWorkbenchQueuePanel[] => {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is RuntimeWorkbenchQueuePanel => {
    return Boolean(item && typeof item === 'object' && String((item as Record<string, unknown>).code || '').trim())
  })
}

const normalizeIndicatorList = (value: unknown): RuntimeWorkbenchAsyncIndicator[] => {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is RuntimeWorkbenchAsyncIndicator => {
    return Boolean(item && typeof item === 'object' && String((item as Record<string, unknown>).code || '').trim())
  })
}

const normalizeSlaIndicatorList = (value: unknown): RuntimeWorkbenchSlaIndicator[] => {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is RuntimeWorkbenchSlaIndicator => {
    return Boolean(item && typeof item === 'object' && String((item as Record<string, unknown>).code || '').trim())
  })
}

const normalizeRecommendedActionList = (value: unknown): RuntimeWorkbenchRecommendedAction[] => {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is RuntimeWorkbenchRecommendedAction => {
    return Boolean(item && typeof item === 'object' && String((item as Record<string, unknown>).code || '').trim())
  })
}

const normalizeClosurePanel = (value: unknown): RuntimeWorkbenchClosurePanel | null => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return null
  }
  const candidate = value as Record<string, unknown>
  if (Object.keys(candidate).length === 0) {
    return null
  }
  return candidate as RuntimeWorkbenchClosurePanel
}

export const useObjectWorkbench = ({
  workbench,
  recordData,
  allowedSurfacePriorities,
}: {
  workbench: Ref<RuntimeWorkbench | null> | ComputedRef<RuntimeWorkbench | null>
  recordData: Ref<WorkbenchRecord> | ComputedRef<WorkbenchRecord>
  allowedSurfacePriorities?: Ref<RuntimeWorkbenchSurfacePriority[] | null> | ComputedRef<RuntimeWorkbenchSurfacePriority[] | null>
}) => {
  const activeSurfacePriorities = computed(() => normalizeAllowedSurfacePriorities(allowedSurfacePriorities?.value))

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
      isVisibleForRecord(panel as WorkbenchDefinitionBase, recordData.value) &&
      isVisibleForSurfacePriority(panel, activeSurfacePriorities.value)
    )
  })

  const asyncIndicators = computed(() => {
    return normalizeIndicatorList(workbench.value?.asyncIndicators).filter((indicator) =>
      isVisibleForRecord(indicator as WorkbenchDefinitionBase, recordData.value) &&
      isVisibleForSurfacePriority(indicator, activeSurfacePriorities.value)
    )
  })

  const summaryCards = computed(() => {
    return normalizeSummaryCardList(workbench.value?.summaryCards).filter((card) =>
      isVisibleForRecord(card as WorkbenchDefinitionBase, recordData.value) &&
      isVisibleForSurfacePriority(card, activeSurfacePriorities.value)
    )
  })

  const queuePanels = computed(() => {
    return normalizeQueuePanelList(workbench.value?.queuePanels).filter((panel) =>
      isVisibleForRecord(panel as WorkbenchDefinitionBase, recordData.value) &&
      isVisibleForSurfacePriority(panel, activeSurfacePriorities.value)
    )
  })

  const exceptionPanels = computed(() => {
    return normalizeQueuePanelList(workbench.value?.exceptionPanels).filter((panel) =>
      isVisibleForRecord(panel as WorkbenchDefinitionBase, recordData.value) &&
      isVisibleForSurfacePriority(panel, activeSurfacePriorities.value)
    )
  })

  const closurePanel = computed(() => {
    const panel = normalizeClosurePanel(workbench.value?.closurePanel)
    if (!panel) return null
    return (
      isVisibleForRecord(panel as WorkbenchDefinitionBase, recordData.value) &&
      isVisibleForSurfacePriority(panel, activeSurfacePriorities.value)
    ) ? panel : null
  })

  const slaIndicators = computed(() => {
    return normalizeSlaIndicatorList(workbench.value?.slaIndicators).filter((indicator) =>
      isVisibleForRecord(indicator as WorkbenchDefinitionBase, recordData.value) &&
      isVisibleForSurfacePriority(indicator, activeSurfacePriorities.value)
    )
  })

  const recommendedActions = computed(() => {
    return normalizeRecommendedActionList(workbench.value?.recommendedActions).filter((action) =>
      isVisibleForRecord(action as WorkbenchDefinitionBase, recordData.value) &&
      isVisibleForSurfacePriority(action, activeSurfacePriorities.value)
    )
  })

  return {
    asyncIndicators,
    closurePanel,
    detailPanels,
    exceptionPanels,
    hasActions: computed(() => primaryActions.value.length > 0 || secondaryActions.value.length > 0),
    hasInsights: computed(() =>
      summaryCards.value.length > 0 ||
      Boolean(closurePanel.value) ||
      recommendedActions.value.length > 0 ||
      slaIndicators.value.length > 0
    ),
    hasQueues: computed(() => queuePanels.value.length > 0 || exceptionPanels.value.length > 0),
    hasPanels: computed(() => detailPanels.value.length > 0),
    primaryActions,
    queuePanels,
    recommendedActions,
    slaIndicators,
    secondaryActions,
    summaryCards,
  }
}
