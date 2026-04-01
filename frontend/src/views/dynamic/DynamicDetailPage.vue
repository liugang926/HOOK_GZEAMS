<template>
  <div
    v-loading="loading"
    class="dynamic-detail-page"
  >
    <DynamicDetailStatePanel
      v-if="loadError"
      icon="error"
      :title="t('common.messages.loadFailed')"
      :sub-title="loadError"
      :refresh-label="t('common.actions.refresh')"
      :back-label="t('common.actions.back')"
      show-refresh
      @refresh="retryLoad"
      @back="$router.back()"
    />

    <DynamicDetailStatePanel
      v-else-if="!canView"
      icon="warning"
      :title="t('common.messages.permissionDenied')"
      :sub-title="t('common.messages.permissionDeniedHint')"
      :back-label="t('common.actions.back')"
      @back="$router.back()"
    />

    <div
      v-else
      class="dynamic-detail-page__shell"
    >
      <ObjectWorkspaceHero
        variant="detail"
        :object-code="objectCode"
        :icon="objectMetadata?.icon || ''"
        :eyebrow="moduleLabel"
        :title="heroTitle"
        :description="heroDescription"
        :chips="heroChips"
        :stats="detailHeroStats"
        :show-back="true"
        :back-label="t('common.actions.back')"
        :back-icon="ArrowLeft"
        @back="handleBackToList"
      />

      <div class="detail-layout">
        <section class="detail-panel detail-panel--main">
          <header class="detail-panel__header">
            <div class="detail-panel__header-copy">
              <p class="detail-panel__kicker">
                {{ detailModeLabel }}
              </p>
              <h2 class="detail-panel__title">
                {{ detailPanelTitle }}
              </h2>
            </div>
            <div class="detail-panel__header-meta">
              <el-segmented
                v-if="supportsPageModeSwitch"
                v-model="detailPageModeModel"
                :options="detailPageModeOptions"
                class="detail-panel__mode-toggle"
              />
              <p class="detail-panel__text">
                {{ detailPanelDescription }}
              </p>
            </div>
          </header>

          <div
            v-if="usesWorkspaceWorkbench"
            id="detail-activity"
            class="detail-workbench"
          >
            <DocumentWorkbench
              :object-code="objectCode"
              :record-id="recordId"
              mode="readonly"
              :model-value="loadedRecord || {}"
              :document="documentPayload"
              :workbench="runtimeWorkbench"
              :status-actions="aggregateStatusActions"
              readonly
              @action-success="handleDetailRefresh"
            />
          </div>

          <CommonDynamicDetailPage
            v-else
            ref="detailPageRef"
            :object-code="objectCode"
            :record-id="recordId"
            :show-edit="canEdit"
            :show-delete="canDelete"
            :object-name="objectMetadata?.name || objectMetadata?.nameEn"
            :object-icon="objectMetadata?.icon"
            @related-record-click="handleRelatedRecordClick"
            @related-record-edit="handleRelatedRecordEdit"
            @loaded="handleRecordLoaded"
          >
            <template
              #action-bar
            >
              <div class="detail-action-stack">
                <StatusActionBar
                  v-if="isLifecycle"
                  :actions="lifecycleRendererRef?.workflowActions || []"
                  :status="lifecycleRecordData?.status || ''"
                  @action-success="handleDetailRefresh"
                />
                <ObjectActionBar
                  :object-code="objectCode"
                  :record-id="recordId"
                  @action-success="handleDetailRefresh"
                />
                <ObjectWorkbenchActionBar
                  v-if="hasWorkbenchActions"
                  :object-code="objectCode"
                  :record-id="recordId"
                  :record-data="workbenchRecordData"
                  :workbench="runtimeWorkbench"
                  :task-state-key="detailTaskStateKey"
                  :start-task-polling="startTaskPolling"
                  @refresh-requested="handleWorkbenchRefresh"
                />
              </div>
            </template>

            <template
              v-if="isLifecycle && lifecycleExtension?.workflowSteps"
              #header-extra
            >
              <el-card
                class="lifecycle-steps-card"
                shadow="never"
              >
                <el-steps
                  :active="lifecycleRendererRef?.getStepIndex(lifecycleRecordData?.status || '') || 0"
                  finish-status="success"
                >
                  <el-step
                    v-for="step in lifecycleExtension.workflowSteps.steps"
                    :key="step"
                    :title="t(`${lifecycleExtension.workflowSteps.i18nPrefix}.${step}`)"
                  />
                </el-steps>
              </el-card>
            </template>

            <template
              v-if="hasWorkbenchExtensionArea"
              #after-sections
            >
              <el-tabs
                v-model="activeDetailSurfaceTab"
                class="detail-surface-tabs"
              >
                <el-tab-pane
                  v-if="hasProcessSurface"
                  :label="t('common.detailWorkspace.tabs.process')"
                  name="process"
                >
                  <div
                    id="detail-process"
                    class="detail-extension-stack"
                  >
                    <LifecycleDetailRenderer
                      v-if="isLifecycle"
                      ref="lifecycleRendererRef"
                      :object-code="objectCode"
                      :record-id="recordId"
                      :record-data="lifecycleRecordData"
                      @refresh="handleDetailRefresh"
                    />

                    <WorkbenchSummaryCards
                      v-if="summaryCards.length > 0"
                      :cards="summaryCards"
                      :record-data="workbenchRecordData"
                    />

                    <WorkbenchQueuePanel
                      v-if="queuePanels.length > 0"
                      :panels="queuePanels"
                      :record-data="workbenchRecordData"
                      variant="queue"
                    />

                    <WorkbenchQueuePanel
                      v-if="exceptionPanels.length > 0"
                      :panels="exceptionPanels"
                      :record-data="workbenchRecordData"
                      variant="exception"
                    />

                    <ProcessSummaryPanel
                      v-if="showProcessSummaryPanel"
                      :stats="processSummaryStats"
                      :panel="closurePanel"
                      :record-data="workbenchRecordData"
                      :extra-rows="closureRows"
                      :navigation-section="showDetailNavigationSection ? detailNavigationSection : null"
                      @select="handleDetailNavigationSelect"
                    />

                    <SlaIndicatorBar
                      v-if="slaIndicators.length > 0"
                      :indicators="slaIndicators"
                      :record-data="workbenchRecordData"
                      :sla-data="objectSla"
                    />

                    <RecommendedActionPanel
                      v-if="recommendedActions.length > 0"
                      :actions="recommendedActions"
                      :object-code="objectCode"
                      :record-id="recordId"
                      :task-state-key="detailTaskStateKey"
                      :start-task-polling="startTaskPolling"
                      @refresh-requested="handleWorkbenchRefresh"
                    />

                    <ObjectWorkbenchPanelHost
                      v-if="showWorkbenchPanelHost"
                      :object-code="objectCode"
                      :record-id="recordId"
                      :record-data="workbenchRecordData"
                      :workbench="runtimeWorkbench"
                      :current-task="currentTask"
                      :task-state-key="detailTaskStateKey"
                      :refresh-version="workbenchRefreshVersion"
                      :start-task-polling="startTaskPolling"
                      @record-patch="handleWorkbenchRecordPatch"
                      @refresh-requested="handleWorkbenchRefresh"
                    />
                  </div>
                </el-tab-pane>

                <el-tab-pane
                  v-if="detailTimelineConfig"
                  :label="t('common.detailWorkspace.tabs.activity')"
                  name="activity"
                >
                  <el-card
                    id="detail-activity"
                    class="detail-timeline-card"
                    shadow="never"
                  >
                    <ActivityTimeline
                      :object-code="detailTimelineConfig.objectCode"
                      :record-id="detailTimelineConfig.recordId"
                      :fetch-url="detailTimelineConfig.fetchUrl"
                    />
                  </el-card>
                </el-tab-pane>
              </el-tabs>
            </template>
          </CommonDynamicDetailPage>
        </section>

        <DynamicDetailSidebar
          :summary-label="summaryLabel"
          :tips-label="tipsLabel"
          :object-display-name="objectDisplayName"
          :info-rows="infoRows"
          :tips="tips"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import ActivityTimeline from '@/components/common/ActivityTimeline.vue'
import DocumentWorkbench from '@/components/common/DocumentWorkbench.vue'
import CommonDynamicDetailPage from '@/components/common/DynamicDetailPage.vue'
import ObjectActionBar from '@/components/common/ObjectActionBar.vue'
import ObjectWorkbenchActionBar from '@/components/common/ObjectWorkbenchActionBar.vue'
import ObjectWorkbenchPanelHost from '@/components/common/ObjectWorkbenchPanelHost.vue'
import ObjectWorkspaceHero from '@/components/common/object-workspace/ObjectWorkspaceHero.vue'
import ProcessSummaryPanel from '@/components/common/ProcessSummaryPanel.vue'
import RecommendedActionPanel from '@/components/common/RecommendedActionPanel.vue'
import SlaIndicatorBar from '@/components/common/SlaIndicatorBar.vue'
import StatusActionBar from '@/components/common/StatusActionBar.vue'
import WorkbenchQueuePanel from '@/components/common/WorkbenchQueuePanel.vue'
import WorkbenchSummaryCards from '@/components/common/WorkbenchSummaryCards.vue'
import LifecycleDetailRenderer from '@/components/lifecycle/LifecycleDetailRenderer.vue'
import { useClosedLoopNavigation } from '@/composables/useClosedLoopNavigation'
import { useObjectWorkbench } from '@/composables/useObjectWorkbench'
import { useSyncTaskPolling } from '@/composables/useSyncTaskPolling'
import DynamicDetailSidebar from '@/views/dynamic/DynamicDetailSidebar.vue'
import DynamicDetailStatePanel from '@/views/dynamic/DynamicDetailStatePanel.vue'
import {
  useDynamicDetailController,
} from '@/views/dynamic/workspace'
import { useDynamicDetailEnhancements } from '@/views/dynamic/workspace/useDynamicDetailEnhancements'
import { useDynamicDetailShell } from '@/views/dynamic/workspace/useDynamicDetailShell'

const route = useRoute()
const router = useRouter()
const { t, te, locale } = useI18n()
const { handleClosedLoopNavigation } = useClosedLoopNavigation()
const objectCode = ref<string>((route.params.code as string) || '')
const recordId = ref<string>((route.params.id as string) || '')
type DetailPageMode = 'record' | 'workspace'
type WorkbenchSurfacePriority = 'primary' | 'context' | 'related' | 'activity' | 'admin'
const lifecycleRendererRef = ref<InstanceType<typeof LifecycleDetailRenderer> | null>(null)
const {
  detailPageRef,
  documentPayload,
  handleBackToList,
  handleLifecycleRefresh,
  handleRecordLoaded,
  handleRelatedRecordClick,
  handleRelatedRecordEdit,
  lifecycleRecordData,
  loadError,
  loadedRecord,
  loading,
  loadMetadata,
  metadataPermissions,
  objectClosure,
  objectMetadata,
  objectSla,
  retryLoad,
  runtimePermissions,
  runtimeWorkbench,
  usesAggregateDocument,
} = useDynamicDetailController({
  objectCode,
  recordId,
  router,
  t: t as (key: string) => string,
})
const { detailNavigationSection, detailTimelineConfig } = useDynamicDetailEnhancements({
  objectCode,
  recordId,
  loadedRecord,
  t: t as (key: string, params?: Record<string, unknown>) => string,
})
const {
  aggregateStatusActions,
  canDelete,
  canEdit,
  canView,
  isLifecycle,
  lifecycleExtension,
  objectDisplayName,
  moduleLabel,
  detailModeLabel,
  detailPanelTitle,
  detailPanelDescription,
  summaryLabel,
  tipsLabel,
  heroTitle,
  heroDescription,
  heroChips,
  detailHeroStats,
  processSummaryStats,
  infoRows,
  closureRows,
  tips,
} = useDynamicDetailShell({
  objectCode,
  recordId,
  objectMetadata,
  metadataPermissions,
  runtimePermissions,
  documentPayload,
  loadedRecord,
  detailNavigationSection,
  detailTimelineConfig,
  t: t as (key: string, params?: Record<string, unknown>) => string,
  te: (te || (() => false)) as (key: string) => boolean,
  locale,
})
const {
  getState: getTaskState,
  start: startTaskPolling,
  stopAll: stopAllTaskPolling,
} = useSyncTaskPolling()
const detailTaskStateKey = computed(() => `${objectCode.value}:${recordId.value}`)
const currentTask = computed(() => getTaskState(detailTaskStateKey.value) || null)
const workbenchRefreshVersion = ref(0)
const workbenchRecordPatch = ref<Record<string, unknown>>({})
const activeDetailSurfaceTab = ref('')
const RECORD_SURFACE_PRIORITIES: WorkbenchSurfacePriority[] = ['primary', 'context']
const WORKSPACE_ONLY_SURFACE_PRIORITIES: WorkbenchSurfacePriority[] = ['related', 'activity', 'admin']
const normalizeDetailPageMode = (value: unknown): DetailPageMode => (
  value === 'workspace' ? 'workspace' : 'record'
)
const normalizeWorkbenchSurfacePriority = (value: unknown): WorkbenchSurfacePriority | null => {
  if (typeof value !== 'string') {
    return null
  }
  const candidate = value.trim() as WorkbenchSurfacePriority
  return (
    candidate === 'primary' ||
    candidate === 'context' ||
    candidate === 'related' ||
    candidate === 'activity' ||
    candidate === 'admin'
  ) ? candidate : null
}
const resolveWorkbenchSurfacePriority = (definition: unknown): WorkbenchSurfacePriority | null => {
  if (!definition || typeof definition !== 'object') {
    return null
  }
  const candidate = definition as Record<string, unknown>
  return normalizeWorkbenchSurfacePriority(candidate.surfacePriority ?? candidate.surface_priority)
}
const collectionHasWorkspaceOnlySurfacePriority = (collection: unknown) => {
  if (!Array.isArray(collection)) {
    return false
  }
  return collection.some((item) => {
    const priority = resolveWorkbenchSurfacePriority(item)
    return Boolean(priority && WORKSPACE_ONLY_SURFACE_PRIORITIES.includes(priority))
  })
}
const readRouteQueryString = (value: unknown): string => {
  if (Array.isArray(value)) {
    return String(value[0] || '').trim()
  }
  return String(value || '').trim()
}
const workbenchHasWorkspaceOnlySurfaces = computed(() => {
  const workbench = runtimeWorkbench.value
  if (!workbench || workbench.workspaceMode !== 'extended') {
    return false
  }
  const closurePriority = resolveWorkbenchSurfacePriority(workbench.closurePanel)
  return (
    collectionHasWorkspaceOnlySurfacePriority(workbench.detailPanels) ||
    collectionHasWorkspaceOnlySurfacePriority(workbench.asyncIndicators) ||
    collectionHasWorkspaceOnlySurfacePriority(workbench.summaryCards) ||
    collectionHasWorkspaceOnlySurfacePriority(workbench.queuePanels) ||
    collectionHasWorkspaceOnlySurfacePriority(workbench.exceptionPanels) ||
    collectionHasWorkspaceOnlySurfacePriority(workbench.slaIndicators) ||
    collectionHasWorkspaceOnlySurfacePriority(workbench.recommendedActions) ||
    Boolean(closurePriority && WORKSPACE_ONLY_SURFACE_PRIORITIES.includes(closurePriority))
  )
})
const supportsPageModeSwitch = computed(() => {
  return usesAggregateDocument.value || workbenchHasWorkspaceOnlySurfaces.value
})
const preferredDetailPageMode = computed<DetailPageMode>(() => {
  return normalizeDetailPageMode(runtimeWorkbench.value?.defaultPageMode)
})
const requestedDetailPageMode = computed<DetailPageMode | null>(() => {
  const candidate = readRouteQueryString(route.query.page_mode)
  if (candidate === 'record' || candidate === 'workspace') {
    return candidate
  }
  return null
})
const effectiveDetailPageMode = computed<DetailPageMode>(() => {
  if (!supportsPageModeSwitch.value) {
    return 'record'
  }
  return requestedDetailPageMode.value || preferredDetailPageMode.value
})
const usesWorkspaceWorkbench = computed(() => {
  return usesAggregateDocument.value && effectiveDetailPageMode.value === 'workspace'
})
const detailPageModeOptions = computed(() => ([
  {
    label: t('common.detailWorkspace.pageModes.record'),
    value: 'record',
  },
  {
    label: t('common.detailWorkspace.pageModes.workspace'),
    value: 'workspace',
  },
]))
const detailPageModeModel = computed<DetailPageMode>({
  get: () => effectiveDetailPageMode.value,
  set: (value) => {
    if (!supportsPageModeSwitch.value) {
      return
    }
    const nextMode = normalizeDetailPageMode(value)
    const nextQuery = { ...route.query }
    if (nextMode === preferredDetailPageMode.value) {
      delete nextQuery.page_mode
    } else {
      nextQuery.page_mode = nextMode
    }
    void router.replace({
      query: nextQuery,
    })
  },
})
const toSnakeCase = (value: string) => value.replace(/([A-Z])/g, '_$1').toLowerCase()
const toSnakeCaseRecord = (value: unknown): unknown => {
  if (Array.isArray(value)) {
    return value.map((item) => toSnakeCaseRecord(item))
  }
  if (!value || typeof value !== 'object') {
    return value
  }
  return Object.entries(value as Record<string, unknown>).reduce<Record<string, unknown>>((result, [key, item]) => {
    result[toSnakeCase(key)] = toSnakeCaseRecord(item)
    return result
  }, {})
}
const workbenchRecordData = computed(() => {
  const baseRecord = loadedRecord.value || lifecycleRecordData.value || null
  const closurePatch = objectClosure.value
    ? {
        closureSummary: objectClosure.value,
        closure_summary: toSnakeCaseRecord(objectClosure.value) as Record<string, unknown>,
      }
    : {}
  if (!baseRecord) {
    const mergedPatch = {
      ...closurePatch,
      ...workbenchRecordPatch.value,
    }
    return Object.keys(mergedPatch).length > 0 ? mergedPatch : null
  }
  return {
    ...baseRecord,
    ...closurePatch,
    ...workbenchRecordPatch.value,
  }
})
const allowedSurfacePriorities = computed<WorkbenchSurfacePriority[] | null>(() => {
  if (!supportsPageModeSwitch.value || effectiveDetailPageMode.value !== 'record') {
    return null
  }
  return RECORD_SURFACE_PRIORITIES
})
const {
  hasActions: hasWorkbenchActions,
  hasPanels: hasWorkbenchPanels,
  closurePanel,
  exceptionPanels,
  queuePanels,
  recommendedActions,
  slaIndicators,
  summaryCards,
} = useObjectWorkbench({
  workbench: runtimeWorkbench,
  recordData: workbenchRecordData,
  allowedSurfacePriorities,
})
const showDetailNavigationSection = computed(() => {
  return Boolean(detailNavigationSection.value)
})
const showWorkbenchPanelHost = computed(() => {
  if (!hasWorkbenchPanels.value) {
    return false
  }
  if (!supportsPageModeSwitch.value) {
    return true
  }
  return effectiveDetailPageMode.value === 'workspace'
})
const showProcessSummaryPanel = computed(() => {
  return (
    processSummaryStats.value.length > 0 ||
    Boolean(closurePanel.value) ||
    closureRows.value.length > 0 ||
    showDetailNavigationSection.value
  )
})
const hasWorkbenchExtensionArea = computed(() => {
  return hasProcessSurface.value || Boolean(detailTimelineConfig.value)
})
const hasProcessSurface = computed(() => {
  return (
    isLifecycle.value ||
    summaryCards.value.length > 0 ||
    queuePanels.value.length > 0 ||
    exceptionPanels.value.length > 0 ||
    showProcessSummaryPanel.value ||
    slaIndicators.value.length > 0 ||
    recommendedActions.value.length > 0 ||
    showWorkbenchPanelHost.value
  )
})
const preferredDetailSurfaceTab = computed(() => {
  const candidate = runtimeWorkbench.value?.defaultDetailSurfaceTab
  return candidate === 'activity' ? 'activity' : 'process'
})

const handleDetailRefresh = async () => {
  if (usesWorkspaceWorkbench.value) {
    await handleLifecycleRefresh()
    return
  }
  if (detailPageRef.value?.refresh) {
    await detailPageRef.value.refresh()
    return
  }
  await handleLifecycleRefresh()
}

const syncDetailSurfaceTab = () => {
  const availableTabs = [
    ...(hasProcessSurface.value ? ['process'] : []),
    ...(detailTimelineConfig.value ? ['activity'] : []),
  ]
  if (availableTabs.length === 0) return

  const currentHash = typeof window !== 'undefined' ? window.location.hash : ''
  if (currentHash === '#detail-activity' && detailTimelineConfig.value) {
    activeDetailSurfaceTab.value = 'activity'
    return
  }
  if (currentHash === '#detail-process' && hasProcessSurface.value) {
    activeDetailSurfaceTab.value = 'process'
    return
  }
  if (!availableTabs.includes(activeDetailSurfaceTab.value)) {
    const defaultTab = preferredDetailSurfaceTab.value
    activeDetailSurfaceTab.value = availableTabs.includes(defaultTab) ? defaultTab : (availableTabs[0] || 'process')
  }
}

const handleWorkbenchRefresh = async () => {
  await handleDetailRefresh()
  workbenchRecordPatch.value = {}
  workbenchRefreshVersion.value += 1
}

const handleWorkbenchRecordPatch = (patch: Record<string, unknown>) => {
  workbenchRecordPatch.value = patch && typeof patch === 'object' ? patch : {}
}

watch(
  () => `${objectCode.value}:${recordId.value}`,
  () => {
    workbenchRecordPatch.value = {}
    syncDetailSurfaceTab()
  },
)

watch(
  () => [
    hasProcessSurface.value,
    Boolean(detailTimelineConfig.value),
    preferredDetailSurfaceTab.value,
  ],
  () => {
    syncDetailSurfaceTab()
  },
  { immediate: true },
)

const handleDetailNavigationSelect = (item: Parameters<typeof handleClosedLoopNavigation>[0]) => {
  handleClosedLoopNavigation(item)
}

onMounted(() => {
  loadMetadata()
  if (typeof window !== 'undefined') {
    window.addEventListener('hashchange', syncDetailSurfaceTab)
  }
})

onUnmounted(() => {
  stopAllTaskPolling()
  if (typeof window !== 'undefined') {
    window.removeEventListener('hashchange', syncDetailSurfaceTab)
  }
})
</script>

<style scoped lang="scss">
@use '@/views/dynamic/styles/dynamic-detail-page' as detailPage;

@include detailPage.dynamic-detail-page-styles();

.detail-action-stack {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 12px;
}

.detail-workbench {
  display: flex;
  flex-direction: column;
}

.detail-extension-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-panel__header-copy,
.detail-panel__header-meta {
  min-width: 0;
}

.detail-panel__header-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.detail-panel__mode-toggle {
  align-self: flex-end;
}

.detail-surface-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 16px;
  }
}

@media (max-width: 1200px) {
  .detail-panel__header-meta {
    width: 100%;
    align-items: flex-start;
  }

  .detail-panel__mode-toggle {
    align-self: flex-start;
  }
}
</style>
