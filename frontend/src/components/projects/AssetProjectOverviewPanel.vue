<template>
  <el-card
    class="asset-project-panel asset-project-overview"
    shadow="never"
  >
    <template #header>
      <div class="asset-project-panel__header">
        <div class="asset-project-panel__heading">
          <div class="asset-project-panel__title-row">
            <span>{{ title }}</span>
            <el-tag :type="statusTagType">
              {{ projectStatusLabel || '--' }}
            </el-tag>
          </div>
          <p class="asset-project-panel__hint">
            {{ t('projects.panels.overviewHint') }}
          </p>
        </div>

        <div class="asset-project-panel__actions">
          <el-button
            size="small"
            @click="loadDashboard"
          >
            {{ t('common.actions.refresh') }}
          </el-button>
        </div>
      </div>
    </template>

    <div
      v-loading="isPanelLoading"
      class="asset-project-overview__body"
    >
      <div class="asset-project-overview__hero">
        <div class="asset-project-overview__identity">
          <h3 class="asset-project-overview__name">
            {{ projectName || '--' }}
          </h3>
          <p class="asset-project-overview__code">
            {{ projectCode || '--' }}
          </p>
          <p
            v-if="projectAlias"
            class="asset-project-overview__alias"
          >
            {{ projectAlias }}
          </p>
        </div>

        <div class="asset-project-overview__finance">
          <div class="asset-project-overview__finance-card">
            <span class="asset-project-overview__finance-label">{{ t('projects.summary.plannedBudget') }}</span>
            <strong class="asset-project-overview__finance-value">{{ formatMoney(plannedBudget) }}</strong>
          </div>
          <div class="asset-project-overview__finance-card">
            <span class="asset-project-overview__finance-label">{{ t('projects.summary.actualCost') }}</span>
            <strong class="asset-project-overview__finance-value">{{ formatMoney(actualCost) }}</strong>
          </div>
          <div class="asset-project-overview__finance-card">
            <span class="asset-project-overview__finance-label">{{ t('projects.summary.assetCost') }}</span>
            <strong class="asset-project-overview__finance-value">{{ formatMoney(assetCost) }}</strong>
          </div>
        </div>
      </div>

      <div class="asset-project-overview__info-grid">
        <div class="asset-project-overview__info-item">
          <span class="asset-project-overview__info-label">{{ t('projects.overview.projectManager') }}</span>
          <strong class="asset-project-overview__info-value">{{ projectManagerName || '--' }}</strong>
        </div>
        <div class="asset-project-overview__info-item">
          <span class="asset-project-overview__info-label">{{ t('projects.overview.department') }}</span>
          <strong class="asset-project-overview__info-value">{{ departmentName || '--' }}</strong>
        </div>
        <div class="asset-project-overview__info-item">
          <span class="asset-project-overview__info-label">{{ t('projects.overview.projectType') }}</span>
          <strong class="asset-project-overview__info-value">{{ projectTypeLabel || '--' }}</strong>
        </div>
        <div class="asset-project-overview__info-item">
          <span class="asset-project-overview__info-label">{{ t('projects.overview.timeline') }}</span>
          <strong class="asset-project-overview__info-value">{{ timelineLabel }}</strong>
        </div>
        <div class="asset-project-overview__info-item">
          <span class="asset-project-overview__info-label">{{ t('projects.overview.actualClosure') }}</span>
          <strong class="asset-project-overview__info-value">{{ actualClosureLabel }}</strong>
        </div>
        <div class="asset-project-overview__info-item">
          <span class="asset-project-overview__info-label">{{ t('projects.overview.milestones') }}</span>
          <strong class="asset-project-overview__info-value">{{ milestoneLabel }}</strong>
        </div>
      </div>

      <div class="asset-project-overview__summary-grid">
        <div class="asset-project-overview__summary-card">
          <span class="asset-project-overview__summary-title">{{ t('projects.panels.assets') }}</span>
          <strong class="asset-project-overview__summary-value">{{ assetTotalCount }}</strong>
          <p class="asset-project-overview__summary-meta">
            {{ t('projects.summary.inUseAssets') }} {{ assetInUseCount }} ·
            {{ t('projects.summary.returnedAssets') }} {{ assetReturnedCount }} ·
            {{ t('projects.summary.transferredAssets') }} {{ assetTransferredCount }}
          </p>
        </div>

        <div class="asset-project-overview__summary-card">
          <span class="asset-project-overview__summary-title">{{ t('projects.panels.members') }}</span>
          <strong class="asset-project-overview__summary-value">{{ memberTotalCount }}</strong>
          <p class="asset-project-overview__summary-meta">
            {{ t('projects.summary.activeMembers') }} {{ memberActiveCount }} ·
            {{ t('projects.summary.primaryMembers') }} {{ memberPrimaryCount }} ·
            {{ t('projects.summary.allocators') }} {{ memberAllocatorsCount }}
          </p>
        </div>

        <div class="asset-project-overview__summary-card">
          <span class="asset-project-overview__summary-title">{{ t('projects.panels.returnHistory') }}</span>
          <strong class="asset-project-overview__summary-value">{{ returnPendingCount }}</strong>
          <p class="asset-project-overview__summary-meta">
            {{ t('projects.summary.processedReturns') }} {{ returnProcessedCount }} ·
            {{ t('projects.summary.completedReturns') }} {{ returnCompletedCount }} ·
            {{ t('projects.summary.rejectedReturns') }} {{ returnRejectedCount }}
          </p>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { formatDate } from '@/utils/dateFormat'
import { formatMoney } from '@/utils/numberFormat'
import request from '@/utils/request'

const props = defineProps<{
  panel: Record<string, unknown>
  recordId: string
  recordData?: Record<string, unknown> | null
  refreshVersion?: number
  workspaceDashboard?: Record<string, unknown> | null
  workspaceDashboardEnabled?: boolean
  workspaceDashboardLoading?: boolean
}>()

const emit = defineEmits<{
  (e: 'workbench-refresh-requested', payload: { summary?: boolean; detail?: boolean; panels?: string[] }): void
}>()

interface DashboardSegment extends Record<string, unknown> {}

interface WorkspaceDashboardPayload {
  project?: DashboardSegment
  assets?: DashboardSegment
  members?: DashboardSegment
  returns?: DashboardSegment
}

const { t, te } = useI18n()
const loading = ref(false)
const localDashboard = ref<WorkspaceDashboardPayload>({})

const title = computed(() => {
  const titleKey = String(props.panel.titleKey || props.panel.title_key || '').trim()
  if (titleKey && te(titleKey)) {
    return t(titleKey)
  }
  return String(props.panel.title || t('projects.panels.overview'))
})

const resolveText = (source: Record<string, unknown> | null | undefined, keys: string[]) => {
  if (!source) return ''
  for (const key of keys) {
    const value = String(source[key] || '').trim()
    if (value) {
      return value
    }
  }
  return ''
}

const resolveNumber = (source: Record<string, unknown> | null | undefined, keys: string[]) => {
  if (!source) return 0
  for (const key of keys) {
    const raw = source[key]
    if (raw === null || raw === undefined || raw === '') {
      continue
    }
    const value = Number(raw)
    if (Number.isFinite(value)) {
      return value
    }
  }
  return 0
}

const resolveBoolean = (source: Record<string, unknown> | null | undefined, keys: string[]) => {
  if (!source) return false
  for (const key of keys) {
    if (typeof source[key] === 'boolean') {
      return Boolean(source[key])
    }
  }
  return false
}

const resolvedDashboard = computed<WorkspaceDashboardPayload>(() => {
  if (props.workspaceDashboard && typeof props.workspaceDashboard === 'object') {
    return props.workspaceDashboard as WorkspaceDashboardPayload
  }
  return localDashboard.value
})
const isSharedDashboardEnabled = computed(() => Boolean(props.workspaceDashboardEnabled))
const isPanelLoading = computed(() => {
  return Boolean((isSharedDashboardEnabled.value && props.workspaceDashboardLoading) || loading.value)
})
const projectSummary = computed(() => resolvedDashboard.value.project ?? {})
const assetSummary = computed(() => resolvedDashboard.value.assets ?? {})
const memberSummary = computed(() => resolvedDashboard.value.members ?? {})
const returnSummary = computed(() => resolvedDashboard.value.returns ?? {})
const recordFallback = computed(() => props.recordData ?? {})

const projectName = computed(() => (
  resolveText(projectSummary.value, ['projectName', 'project_name'])
  || resolveText(recordFallback.value, ['projectName', 'project_name'])
))
const projectCode = computed(() => (
  resolveText(projectSummary.value, ['projectCode', 'project_code'])
  || resolveText(recordFallback.value, ['projectCode', 'project_code'])
))
const projectAlias = computed(() => (
  resolveText(projectSummary.value, ['projectAlias', 'project_alias'])
  || resolveText(recordFallback.value, ['projectAlias', 'project_alias'])
))
const projectStatus = computed(() => (
  resolveText(projectSummary.value, ['status'])
  || resolveText(recordFallback.value, ['status'])
))
const projectStatusLabel = computed(() => (
  resolveText(projectSummary.value, ['statusLabel', 'status_label'])
  || projectStatus.value
))
const projectTypeLabel = computed(() => (
  resolveText(projectSummary.value, ['projectTypeLabel', 'project_type_label'])
  || resolveText(projectSummary.value, ['projectType', 'project_type'])
  || resolveText(recordFallback.value, ['projectTypeLabel', 'project_type_label', 'projectType', 'project_type'])
))
const projectManagerName = computed(() => (
  resolveText(projectSummary.value, ['projectManagerName', 'project_manager_name'])
  || resolveText(recordFallback.value, ['projectManagerName', 'project_manager_name'])
))
const departmentName = computed(() => (
  resolveText(projectSummary.value, ['departmentName', 'department_name'])
  || resolveText(recordFallback.value, ['departmentName', 'department_name'])
))
const plannedBudget = computed(() => resolveNumber(projectSummary.value, ['plannedBudget', 'planned_budget']))
const actualCost = computed(() => resolveNumber(projectSummary.value, ['actualCost', 'actual_cost']))
const assetCost = computed(() => resolveNumber(projectSummary.value, ['assetCost', 'asset_cost']))
const projectStartDate = computed(() => (
  resolveText(projectSummary.value, ['startDate', 'start_date'])
  || resolveText(recordFallback.value, ['startDate', 'start_date'])
))
const projectEndDate = computed(() => (
  resolveText(projectSummary.value, ['endDate', 'end_date'])
  || resolveText(recordFallback.value, ['endDate', 'end_date'])
))
const actualEndDate = computed(() => (
  resolveText(projectSummary.value, ['actualEndDate', 'actual_end_date'])
  || resolveText(recordFallback.value, ['actualEndDate', 'actual_end_date'])
))
const completedMilestones = computed(() => resolveNumber(projectSummary.value, ['completedMilestones', 'completed_milestones']))
const totalMilestones = computed(() => resolveNumber(projectSummary.value, ['totalMilestones', 'total_milestones']))
const progress = computed(() => resolveNumber(projectSummary.value, ['progress']))

const assetTotalCount = computed(() => resolveNumber(assetSummary.value, ['totalCount', 'total_count']))
const assetInUseCount = computed(() => resolveNumber(assetSummary.value, ['inUseCount', 'in_use_count']))
const assetReturnedCount = computed(() => resolveNumber(assetSummary.value, ['returnedCount', 'returned_count']))
const assetTransferredCount = computed(() => resolveNumber(assetSummary.value, ['transferredCount', 'transferred_count']))
const memberTotalCount = computed(() => resolveNumber(memberSummary.value, ['totalCount', 'total_count']))
const memberActiveCount = computed(() => resolveNumber(memberSummary.value, ['activeCount', 'active_count']))
const memberPrimaryCount = computed(() => resolveNumber(memberSummary.value, ['primaryCount', 'primary_count']))
const memberAllocatorsCount = computed(() => resolveNumber(memberSummary.value, ['allocatorsCount', 'allocators_count']))
const returnPendingCount = computed(() => resolveNumber(returnSummary.value, ['pendingCount', 'pending_count']))
const returnCompletedCount = computed(() => resolveNumber(returnSummary.value, ['completedCount', 'completed_count']))
const returnRejectedCount = computed(() => resolveNumber(returnSummary.value, ['rejectedCount', 'rejected_count']))
const returnProcessedCount = computed(() => resolveNumber(returnSummary.value, ['processedCount', 'processed_count']))

const statusTagType = computed(() => {
  if (projectStatus.value === 'active') return 'success'
  if (projectStatus.value === 'suspended') return 'warning'
  if (projectStatus.value === 'cancelled') return 'danger'
  return 'info'
})

const timelineLabel = computed(() => {
  const startLabel = formatDate(projectStartDate.value) || '--'
  const endLabel = formatDate(projectEndDate.value) || '--'
  return `${startLabel} ~ ${endLabel}`
})

const actualClosureLabel = computed(() => {
  const actualLabel = formatDate(actualEndDate.value)
  if (actualLabel) {
    return actualLabel
  }
  return resolveBoolean(projectSummary.value, ['isOverdue', 'is_overdue'])
    ? t('projects.overview.overdue')
    : '--'
})

const milestoneLabel = computed(() => {
  if (totalMilestones.value <= 0) {
    return '--'
  }
  return `${completedMilestones.value}/${totalMilestones.value} (${progress.value}%)`
})

const loadDashboard = async () => {
  if (isSharedDashboardEnabled.value) {
    emit('workbench-refresh-requested', { summary: true })
    return
  }
  if (!props.recordId) return
  loading.value = true
  try {
    const result = await request.get<WorkspaceDashboardPayload>(
      `/system/objects/AssetProject/${props.recordId}/workspace_dashboard/`
    )
    localDashboard.value = result || {}
  } catch (error: unknown) {
    localDashboard.value = {}
    ElMessage.error(error instanceof Error ? error.message : t('projects.messages.loadOverviewFailed'))
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.recordId, props.refreshVersion, props.workspaceDashboardEnabled],
  () => {
    if (isSharedDashboardEnabled.value) {
      return
    }
    void loadDashboard()
  },
  { immediate: true }
)
</script>

<style scoped>
.asset-project-overview__body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.asset-project-overview__hero {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(280px, 420px);
  gap: 16px;
}

.asset-project-overview__identity,
.asset-project-overview__finance,
.asset-project-overview__summary-card,
.asset-project-overview__info-item {
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  background: var(--el-fill-color-blank);
}

.asset-project-overview__identity {
  padding: 18px 20px;
}

.asset-project-overview__name {
  margin: 0;
  font-size: 20px;
  line-height: 1.4;
}

.asset-project-overview__code,
.asset-project-overview__alias {
  margin: 6px 0 0;
  color: var(--el-text-color-secondary);
}

.asset-project-overview__finance {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  padding: 16px;
}

.asset-project-overview__finance-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.asset-project-overview__finance-label,
.asset-project-overview__info-label,
.asset-project-overview__summary-title {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.asset-project-overview__finance-value,
.asset-project-overview__summary-value,
.asset-project-overview__info-value {
  font-size: 18px;
  color: var(--el-text-color-primary);
}

.asset-project-overview__info-grid,
.asset-project-overview__summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.asset-project-overview__info-item,
.asset-project-overview__summary-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
}

.asset-project-overview__summary-meta {
  margin: 0;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

@media (max-width: 960px) {
  .asset-project-overview__hero,
  .asset-project-overview__finance,
  .asset-project-overview__info-grid,
  .asset-project-overview__summary-grid {
    grid-template-columns: 1fr;
  }
}
</style>
