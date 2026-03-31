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
        :stats="heroStats"
        :show-back="true"
        :back-label="t('common.actions.back')"
        :back-icon="ArrowLeft"
        @back="handleBackToList"
      />

      <div class="detail-layout">
        <section class="detail-panel detail-panel--main">
          <header class="detail-panel__header">
            <div>
              <p class="detail-panel__kicker">
                {{ detailModeLabel }}
              </p>
              <h2 class="detail-panel__title">
                {{ detailPanelTitle }}
              </h2>
            </div>
            <p class="detail-panel__text">
              {{ detailPanelDescription }}
            </p>
          </header>

          <div
            v-if="usesAggregateDocument"
            class="detail-workbench"
          >
            <DocumentWorkbench
              :object-code="objectCode"
              :record-id="recordId"
              mode="readonly"
              :model-value="loadedRecord || {}"
              :document="documentPayload"
              :status-actions="aggregateStatusActions"
              readonly
              @action-success="handleLifecycleRefresh"
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
                  @action-success="handleLifecycleRefresh"
                />
                <ObjectActionBar
                  :object-code="objectCode"
                  :record-id="recordId"
                  @action-success="handleLifecycleRefresh"
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
              <div class="detail-extension-stack">
                <LifecycleDetailRenderer
                  v-if="isLifecycle"
                  ref="lifecycleRendererRef"
                  :object-code="objectCode"
                  :record-id="recordId"
                  :record-data="lifecycleRecordData"
                  @refresh="handleLifecycleRefresh"
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

                <ClosureStatusPanel
                  v-if="closurePanel"
                  :panel="closurePanel"
                  :record-data="workbenchRecordData"
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

                <ClosedLoopNavigationCard
                  v-if="detailNavigationSection"
                  class="detail-navigation-card"
                  :title="detailNavigationSection.title"
                  :hint="detailNavigationSection.hint"
                  :items="detailNavigationSection.items"
                  @select="handleDetailNavigationSelect"
                />

                <el-card
                  v-if="detailTimelineConfig"
                  class="detail-timeline-card"
                  shadow="never"
                >
                  <ActivityTimeline
                    :object-code="detailTimelineConfig.objectCode"
                    :record-id="detailTimelineConfig.recordId"
                    :fetch-url="detailTimelineConfig.fetchUrl"
                  />
                </el-card>

                <ObjectWorkbenchPanelHost
                  v-if="hasWorkbenchPanels"
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
import ClosedLoopNavigationCard from '@/components/common/ClosedLoopNavigationCard.vue'
import ClosureStatusPanel from '@/components/common/ClosureStatusPanel.vue'
import DocumentWorkbench from '@/components/common/DocumentWorkbench.vue'
import CommonDynamicDetailPage from '@/components/common/DynamicDetailPage.vue'
import ObjectActionBar from '@/components/common/ObjectActionBar.vue'
import ObjectWorkbenchActionBar from '@/components/common/ObjectWorkbenchActionBar.vue'
import ObjectWorkbenchPanelHost from '@/components/common/ObjectWorkbenchPanelHost.vue'
import ObjectWorkspaceHero from '@/components/common/object-workspace/ObjectWorkspaceHero.vue'
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
  hasDetailEnhancements,
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
  heroStats,
  infoRows,
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
const {
  hasActions: hasWorkbenchActions,
  hasInsights: hasWorkbenchInsights,
  hasQueues: hasWorkbenchQueues,
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
})
const hasWorkbenchExtensionArea = computed(() => {
  return (
    hasDetailEnhancements.value ||
    hasWorkbenchPanels.value ||
    hasWorkbenchInsights.value ||
    hasWorkbenchQueues.value
  )
})

const handleWorkbenchRefresh = async () => {
  await handleLifecycleRefresh()
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
  },
)

const handleDetailNavigationSelect = (item: Parameters<typeof handleClosedLoopNavigation>[0]) => {
  handleClosedLoopNavigation(item)
}

onMounted(() => {
  loadMetadata()
})

onUnmounted(() => {
  stopAllTaskPolling()
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
</style>
