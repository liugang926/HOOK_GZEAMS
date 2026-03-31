<template>
  <div
    v-if="hasPanels"
    class="object-workbench-panel-host"
  >
    <div
      v-for="panel in renderedPanels"
      :key="panel.code"
      :ref="bindPanelAnchor(String(panel.code || ''))"
      :data-panel-code="String(panel.code || '')"
      class="object-workbench-panel-host__item"
    >
      <component
        :is="resolvePanelComponent(panel)"
        v-if="isPanelActivated(panel)"
        :panel="panel"
        :object-code="objectCode"
        :record-id="recordId"
        :record-data="recordData || null"
        :current-task="currentTask || null"
        :task-state-key="taskStateKey"
        :refresh-version="refreshVersion"
        :panel-refresh-version="resolvePanelRefreshVersion(panel)"
        :workspace-dashboard="resolveSharedWorkspaceDashboard(panel)"
        :workspace-dashboard-enabled="isSharedWorkspaceDashboardPanel(panel)"
        :workspace-dashboard-loading="sharedWorkspaceDashboardLoading"
        :start-task-polling="startTaskPolling"
        @refresh-requested="emit('refresh-requested')"
        @workbench-refresh-requested="handleWorkbenchRefreshRequest"
        @task-complete="emit('refresh-requested')"
      />
      <div
        v-else
        class="object-workbench-panel-host__placeholder"
      >
        <div class="object-workbench-panel-host__placeholder-head">
          <strong class="object-workbench-panel-host__placeholder-title">
            {{ resolvePanelTitle(panel) }}
          </strong>
        </div>
        <p class="object-workbench-panel-host__placeholder-hint">
          {{ resolvePanelHint(panel) }}
        </p>
        <p class="object-workbench-panel-host__placeholder-copy">
          {{ t('projects.messages.lazyPanelHint') }}
        </p>
        <button
          type="button"
          class="object-workbench-panel-host__placeholder-action"
          @click="activatePanel(String(panel.code || ''))"
        >
          {{ t('common.actions.loadMore') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, toRef, watch, type ComponentPublicInstance } from 'vue'
import { useI18n } from 'vue-i18n'
import { useObjectWorkbench } from '@/composables/useObjectWorkbench'
import type { RuntimeWorkbench } from '@/types/runtime'
import request from '@/utils/request'
import FinanceVoucherEntriesPanel from '@/components/finance/FinanceVoucherEntriesPanel.vue'
import FinanceVoucherIntegrationLogsPanel from '@/components/finance/FinanceVoucherIntegrationLogsPanel.vue'
import FinanceVoucherSyncStatusPanel from '@/components/finance/FinanceVoucherSyncStatusPanel.vue'
import InventoryDifferenceClosurePanel from '@/components/inventory/InventoryDifferenceClosurePanel.vue'
import InventoryTaskExecutorProgressPanel from '@/components/inventory/InventoryTaskExecutorProgressPanel.vue'
import AssetProjectAssetsPanel from '@/components/projects/AssetProjectAssetsPanel.vue'
import AssetProjectMembersPanel from '@/components/projects/AssetProjectMembersPanel.vue'
import AssetProjectOverviewPanel from '@/components/projects/AssetProjectOverviewPanel.vue'
import AssetProjectReturnHistoryPanel from '@/components/projects/AssetProjectReturnHistoryPanel.vue'
import AssetProjectReturnsPanel from '@/components/projects/AssetProjectReturnsPanel.vue'

interface SyncTaskState {
  syncTaskId: string
  status: string
  statusDisplay?: string
  done: boolean
}

interface WorkbenchRefreshRequest {
  summary?: boolean
  detail?: boolean
  panels?: string[]
}

const props = defineProps<{
  objectCode: string
  recordId: string
  recordData?: Record<string, unknown> | null
  workbench: RuntimeWorkbench | null
  currentTask?: SyncTaskState | null
  taskStateKey?: string
  refreshVersion?: number
  startTaskPolling?: (key: string, syncTaskId: string, options?: { onDone?: (state: SyncTaskState) => void | Promise<void> }) => void
}>()

const emit = defineEmits<{
  (e: 'refresh-requested'): void
  (e: 'record-patch', patch: Record<string, unknown>): void
}>()

const { t, te } = useI18n()
const assetProjectSharedPanelComponents = new Set([
  'asset-project-overview',
  'asset-project-assets',
  'asset-project-members',
  'asset-project-returns',
  'asset-project-return-history',
])
const assetProjectDeferredPanelComponents = new Set([
  'asset-project-assets',
  'asset-project-members',
  'asset-project-returns',
  'asset-project-return-history',
])
const assetProjectPanelHintKeys: Record<string, string> = {
  'asset-project-assets': 'projects.panels.assetsHint',
  'asset-project-members': 'projects.panels.membersHint',
  'asset-project-returns': 'projects.panels.returnsHint',
  'asset-project-return-history': 'projects.panels.returnHistoryHint',
}

const panelRegistry: Record<string, unknown> = {
  'finance-voucher-entries': FinanceVoucherEntriesPanel,
  'finance-voucher-integration-logs': FinanceVoucherIntegrationLogsPanel,
  'finance-voucher-sync-status': FinanceVoucherSyncStatusPanel,
  'inventory-difference-closure': InventoryDifferenceClosurePanel,
  'inventory-task-executor-progress': InventoryTaskExecutorProgressPanel,
  'asset-project-overview': AssetProjectOverviewPanel,
  'asset-project-assets': AssetProjectAssetsPanel,
  'asset-project-members': AssetProjectMembersPanel,
  'asset-project-returns': AssetProjectReturnsPanel,
  'asset-project-return-history': AssetProjectReturnHistoryPanel,
}

const { detailPanels, hasPanels } = useObjectWorkbench({
  workbench: toRef(props, 'workbench'),
  recordData: toRef(props, 'recordData'),
})

const renderedPanels = computed(() => {
  return detailPanels.value.filter((panel) => {
    const componentCode = String(panel.component || '').trim()
    return Boolean(panelRegistry[componentCode])
  })
})
const panelAnchors = new Map<string, HTMLElement>()
const panelActivationState = ref<Record<string, boolean>>({})
const panelRefreshVersions = ref<Record<string, number>>({})
let panelVisibilityObserver: IntersectionObserver | null = null

const sharedWorkspaceDashboard = ref<Record<string, unknown> | null>(null)
const sharedWorkspaceDashboardLoading = ref(false)
const shouldLoadAssetProjectWorkspaceDashboard = computed(() => {
  return props.objectCode === 'AssetProject' && Boolean(props.recordId)
})

const loadSharedWorkspaceDashboard = async () => {
  if (!shouldLoadAssetProjectWorkspaceDashboard.value) {
    sharedWorkspaceDashboard.value = null
    sharedWorkspaceDashboardLoading.value = false
    emit('record-patch', {})
    return
  }

  sharedWorkspaceDashboardLoading.value = true
  try {
    const result = await request.get<Record<string, unknown>>(
      `/system/objects/AssetProject/${props.recordId}/workspace_dashboard/`
    )
    sharedWorkspaceDashboard.value = result && typeof result === 'object' ? result : null
    emit('record-patch', buildRecordPatchFromWorkspaceDashboard(sharedWorkspaceDashboard.value))
  } catch {
    sharedWorkspaceDashboard.value = null
    emit('record-patch', {})
  } finally {
    sharedWorkspaceDashboardLoading.value = false
  }
}

watch(
  () => [props.objectCode, props.recordId, props.refreshVersion],
  () => {
    void loadSharedWorkspaceDashboard()
  },
  { immediate: true }
)

const shouldDeferPanel = (panel: Record<string, unknown>) => {
  if (props.objectCode !== 'AssetProject') {
    return false
  }
  const componentCode = String(panel.component || '').trim()
  return assetProjectDeferredPanelComponents.has(componentCode)
}

const incrementPanelRefreshVersions = (panelCodes: string[]) => {
  if (!Array.isArray(panelCodes) || panelCodes.length === 0) {
    return
  }

  const nextVersions = {
    ...panelRefreshVersions.value,
  }
  panelCodes.forEach((panelCode) => {
    const normalizedCode = String(panelCode || '').trim()
    if (!normalizedCode) {
      return
    }
    nextVersions[normalizedCode] = (nextVersions[normalizedCode] || 0) + 1
  })
  panelRefreshVersions.value = nextVersions
}

const activatePanel = (panelCode: string) => {
  const normalizedCode = String(panelCode || '').trim()
  if (!normalizedCode || panelActivationState.value[normalizedCode]) {
    return
  }

  panelActivationState.value = {
    ...panelActivationState.value,
    [normalizedCode]: true,
  }

  const target = panelAnchors.get(normalizedCode)
  if (target && panelVisibilityObserver) {
    panelVisibilityObserver.unobserve(target)
  }
}

const isPanelActivated = (panel: Record<string, unknown>) => {
  const panelCode = String(panel.code || '').trim()
  if (!panelCode) {
    return true
  }
  return Boolean(panelActivationState.value[panelCode])
}

const resolvePanelTitle = (panel: Record<string, unknown>) => {
  const titleKey = String(panel.titleKey || panel.title_key || '').trim()
  if (titleKey && te(titleKey)) {
    return t(titleKey)
  }
  return String(panel.title || panel.code || '')
}

const resolvePanelHint = (panel: Record<string, unknown>) => {
  const componentCode = String(panel.component || '').trim()
  const hintKey = assetProjectPanelHintKeys[componentCode]
  if (hintKey && te(hintKey)) {
    return t(hintKey)
  }
  return ''
}

const disconnectPanelObserver = () => {
  if (panelVisibilityObserver) {
    panelVisibilityObserver.disconnect()
    panelVisibilityObserver = null
  }
}

const ensurePanelObserver = async () => {
  disconnectPanelObserver()

  const Observer = globalThis.IntersectionObserver
  if (typeof Observer !== 'function') {
    return
  }

  panelVisibilityObserver = new Observer((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) {
        return
      }
      const target = entry.target as HTMLElement
      activatePanel(target.dataset.panelCode || '')
    })
  }, {
    rootMargin: '280px 0px',
    threshold: 0.01,
  })

  await nextTick()
  renderedPanels.value.forEach((panel) => {
    const panelCode = String(panel.code || '').trim()
    const target = panelAnchors.get(panelCode)
    if (!target || panelActivationState.value[panelCode]) {
      return
    }
    panelVisibilityObserver?.observe(target)
  })
}

const initializePanelActivation = async () => {
  const nextState: Record<string, boolean> = {}
  const nextRefreshVersions: Record<string, number> = {}
  renderedPanels.value.forEach((panel) => {
    const panelCode = String(panel.code || '').trim()
    if (!panelCode) {
      return
    }
    nextState[panelCode] = !shouldDeferPanel(panel)
    nextRefreshVersions[panelCode] = panelRefreshVersions.value[panelCode] || 0
  })
  panelActivationState.value = nextState
  panelRefreshVersions.value = nextRefreshVersions
  await ensurePanelObserver()
}

const bindPanelAnchor = (panelCode: string) => (element: Element | ComponentPublicInstance | null) => {
  const normalizedCode = String(panelCode || '').trim()
  if (!normalizedCode) {
    return
  }

  const previous = panelAnchors.get(normalizedCode)
  if (previous && panelVisibilityObserver) {
    panelVisibilityObserver.unobserve(previous)
  }

  const targetElement = element instanceof HTMLElement
    ? element
    : element && '$el' in element && element.$el instanceof HTMLElement
      ? element.$el
      : null

  if (targetElement) {
    panelAnchors.set(normalizedCode, targetElement)
    if (panelVisibilityObserver && !panelActivationState.value[normalizedCode]) {
      panelVisibilityObserver.observe(targetElement)
    }
    return
  }

  panelAnchors.delete(normalizedCode)
}

const resolvePanelRefreshVersion = (panel: Record<string, unknown>) => {
  const panelCode = String(panel.code || '').trim()
  return panelRefreshVersions.value[panelCode] || 0
}

const buildRecordPatchFromWorkspaceDashboard = (payload: Record<string, unknown> | null) => {
  if (!payload || props.objectCode !== 'AssetProject') {
    return {}
  }

  const project = payload.project && typeof payload.project === 'object'
    ? payload.project as Record<string, unknown>
    : {}
  const assets = payload.assets && typeof payload.assets === 'object'
    ? payload.assets as Record<string, unknown>
    : {}
  const members = payload.members && typeof payload.members === 'object'
    ? payload.members as Record<string, unknown>
    : {}

  const activeAssets = Number(assets.inUseCount || assets.in_use_count || 0)
  const totalAssets = Number(assets.totalCount || assets.total_count || 0)
  const memberCount = Number(members.totalCount || members.total_count || 0)
  const assetCost = project.assetCost || project.asset_cost || assets.allocationCostTotal || assets.allocation_cost_total || ''

  return {
    activeAssets,
    active_assets: activeAssets,
    totalAssets,
    total_assets: totalAssets,
    memberCount,
    member_count: memberCount,
    assetCost,
    asset_cost: assetCost,
  }
}

const handleWorkbenchRefreshRequest = async (request: WorkbenchRefreshRequest = {}) => {
  if (request.summary) {
    await loadSharedWorkspaceDashboard()
  }

  if (Array.isArray(request.panels) && request.panels.length > 0) {
    incrementPanelRefreshVersions(request.panels)
  }

  if (request.detail) {
    emit('refresh-requested')
  }
}

watch(
  () => `${props.objectCode}:${props.recordId}:${renderedPanels.value.map((panel) => String(panel.code || '')).join('|')}`,
  () => {
    void initializePanelActivation()
  },
  { immediate: true }
)

const isSharedWorkspaceDashboardPanel = (panel: Record<string, unknown>) => {
  if (!shouldLoadAssetProjectWorkspaceDashboard.value) {
    return false
  }
  const componentCode = String(panel.component || '').trim()
  return assetProjectSharedPanelComponents.has(componentCode)
}

const resolveSharedWorkspaceDashboard = (panel: Record<string, unknown>) => {
  if (!isSharedWorkspaceDashboardPanel(panel)) {
    return null
  }
  return sharedWorkspaceDashboard.value
}

const resolvePanelComponent = (panel: Record<string, unknown>) => {
  const componentCode = String(panel.component || '').trim()
  return panelRegistry[componentCode]
}

onBeforeUnmount(() => {
  disconnectPanelObserver()
})
</script>

<style scoped>
.object-workbench-panel-host {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.object-workbench-panel-host__item {
  min-width: 0;
}

.object-workbench-panel-host__placeholder {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px 20px;
  border: 1px dashed var(--el-border-color);
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(250, 250, 250, 0.96) 0%, rgba(245, 247, 250, 0.92) 100%);
}

.object-workbench-panel-host__placeholder-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.object-workbench-panel-host__placeholder-title {
  font-size: 15px;
  color: var(--el-text-color-primary);
}

.object-workbench-panel-host__placeholder-hint,
.object-workbench-panel-host__placeholder-copy {
  margin: 0;
  line-height: 1.6;
  color: var(--el-text-color-secondary);
}

.object-workbench-panel-host__placeholder-action {
  width: fit-content;
  min-width: 104px;
  padding: 8px 14px;
  border: 1px solid var(--el-color-primary-light-5);
  border-radius: 999px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  cursor: pointer;
}

.object-workbench-panel-host__placeholder-action:hover {
  background: var(--el-color-primary-light-8);
}
</style>
