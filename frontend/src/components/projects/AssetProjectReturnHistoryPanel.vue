<template>
  <el-card
    class="asset-project-panel"
    shadow="never"
  >
    <template #header>
      <div class="asset-project-panel__header">
        <div class="asset-project-panel__heading">
          <div class="asset-project-panel__title-row">
            <span>{{ title }}</span>
            <span class="asset-project-panel__meta">{{ historyCount }}</span>
          </div>
          <p class="asset-project-panel__hint">
            {{ t('projects.panels.returnHistoryHint') }}
          </p>
        </div>

        <div class="asset-project-panel__actions">
          <div class="asset-project-panel__range-switch">
            <el-button
              v-for="option in rangeOptions"
              :key="option.value"
              size="small"
              :type="selectedRangeKey === option.value ? 'primary' : 'default'"
              @click="handleRangeChange(option.value)"
            >
              {{ option.label }}
            </el-button>
          </div>
          <el-button
            size="small"
            @click="loadHistory"
          >
            {{ t('common.actions.refresh') }}
          </el-button>
          <el-button
            size="small"
            @click="handleViewAll"
          >
            {{ t('projects.actions.viewAllReturns') }}
          </el-button>
        </div>
      </div>
    </template>

    <div class="asset-project-panel__summary">
      <div class="asset-project-panel__summary-card">
        <span class="asset-project-panel__summary-label">{{ t('projects.summary.pendingReturns') }}</span>
        <strong class="asset-project-panel__summary-value">{{ displayPendingCount }}</strong>
      </div>
      <div class="asset-project-panel__summary-card">
        <span class="asset-project-panel__summary-label">{{ t('projects.summary.completedReturns') }}</span>
        <strong class="asset-project-panel__summary-value">{{ displayCompletedCount }}</strong>
      </div>
      <div class="asset-project-panel__summary-card">
        <span class="asset-project-panel__summary-label">{{ t('projects.summary.rejectedReturns') }}</span>
        <strong class="asset-project-panel__summary-value">{{ displayRejectedCount }}</strong>
      </div>
    </div>

    <div class="asset-project-panel__trend">
      <div class="asset-project-panel__trend-header">
        <span class="asset-project-panel__trend-title">{{ t('projects.panels.returnTrend') }}</span>
        <span class="asset-project-panel__trend-window">
          {{ t('projects.messages.returnTrendWindow', { start: windowStartDate || '--', end: windowEndDate || '--' }) }}
        </span>
      </div>
      <div
        v-if="trendPoints.length === 0"
        class="asset-project-panel__trend-empty"
      >
        {{ t('projects.messages.emptyReturnTrend') }}
      </div>
      <div
        v-else
        class="asset-project-panel__trend-list"
      >
        <div
          v-for="point in trendPoints"
          :key="point.date"
          class="asset-project-panel__trend-row"
        >
          <span class="asset-project-panel__trend-label">{{ point.label || point.date }}</span>
          <div class="asset-project-panel__trend-track">
            <div
              class="asset-project-panel__trend-stack"
              :style="{ width: `${resolveTrendWidth(point)}%` }"
            >
              <span
                v-if="point.completedCount > 0"
                class="asset-project-panel__trend-segment asset-project-panel__trend-segment--completed"
                :style="{ flexGrow: point.completedCount }"
              />
              <span
                v-if="point.rejectedCount > 0"
                class="asset-project-panel__trend-segment asset-project-panel__trend-segment--rejected"
                :style="{ flexGrow: point.rejectedCount }"
              />
            </div>
          </div>
          <span class="asset-project-panel__trend-metrics">
            {{ point.completedCount }}/{{ point.rejectedCount }}/{{ point.totalCount }}
          </span>
        </div>
      </div>
    </div>

    <el-empty
      v-if="!loading && historyRows.length === 0"
      :description="t('projects.messages.emptyReturnHistory')"
    />

    <el-table
      v-else
      v-loading="loading"
      :data="historyRows"
      border
      stripe
      @row-click="handleOpenReturn"
    >
      <el-table-column
        :label="t('projects.columns.returnNo')"
        min-width="160"
      >
        <template #default="{ row }">
          <el-button
            link
            type="primary"
            class="asset-project-panel__return-link"
            @click.stop="handleOpenReturn(row)"
          >
            {{ resolveText(row, ['returnNo', 'return_no']) || '--' }}
          </el-button>
        </template>
      </el-table-column>
      <el-table-column
        :label="t('common.columns.status')"
        width="120"
      >
        <template #default="{ row }">
          <el-tag :type="resolveStatusType(resolveText(row, ['status']))">
            {{ resolveText(row, ['statusLabel', 'status_label']) || resolveText(row, ['status']) || '--' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.returnDate')"
        width="130"
      >
        <template #default="{ row }">
          {{ formatDate(resolveText(row, ['returnDate', 'return_date'])) || '--' }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.itemsCount')"
        width="110"
        align="center"
      >
        <template #default="{ row }">
          {{ Number(row.itemsCount || row.items_count || 0) }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.processingNote')"
        min-width="260"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          {{ resolveProcessingNote(row) || '--' }}
        </template>
      </el-table-column>
      <el-table-column
        :label="t('projects.columns.processedAt')"
        width="150"
      >
        <template #default="{ row }">
          {{ formatDate(resolveEventAt(row)) || '--' }}
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { formatDate } from '@/utils/dateFormat'
import request from '@/utils/request'

const props = defineProps<{
  panel: Record<string, unknown>
  recordId: string
  refreshVersion?: number
  panelRefreshVersion?: number
  workspaceDashboard?: Record<string, unknown> | null
  workspaceDashboardEnabled?: boolean
}>()

interface ReturnOrderRecord extends Record<string, unknown> {
  id?: string
}

interface TrendPoint {
  date: string
  label: string
  completedCount: number
  rejectedCount: number
  totalCount: number
}

interface ReturnDashboardPayload {
  summary?: {
    pendingCount?: number
    pending_count?: number
    completedCount?: number
    completed_count?: number
    rejectedCount?: number
    rejected_count?: number
    processedCount?: number
    processed_count?: number
  }
  history?: {
    totalCount?: number
    total_count?: number
    rows?: ReturnOrderRecord[]
  }
  trend?: {
    maxTotalCount?: number
    max_total_count?: number
    points?: Array<Record<string, unknown>>
  }
  window?: {
    rangeKey?: string
    range_key?: string
    startDate?: string
    start_date?: string
    endDate?: string
    end_date?: string
  }
}

const { t, te } = useI18n()
const router = useRouter()
const loading = ref(false)
const pendingCount = ref(0)
const completedCount = ref(0)
const rejectedCount = ref(0)
const processedCount = ref(0)
const historyRows = ref<ReturnOrderRecord[]>([])
const trendPoints = ref<TrendPoint[]>([])
const trendMaxTotal = ref(0)
const selectedRangeKey = ref('30d')
const windowStartDate = ref('')
const windowEndDate = ref('')

const historyCount = computed(() => processedCount.value)

const rangeOptions = computed(() => [
  { value: '7d', label: t('projects.ranges.last7Days') },
  { value: '30d', label: t('projects.ranges.last30Days') },
  { value: '90d', label: t('projects.ranges.last90Days') },
])

const title = computed(() => {
  const titleKey = String(props.panel.titleKey || props.panel.title_key || '').trim()
  if (titleKey && te(titleKey)) {
    return t(titleKey)
  }
  return String(props.panel.title || t('projects.panels.returnHistory'))
})

const resolveText = (row: Record<string, unknown>, keys: string[]) => {
  for (const key of keys) {
    const value = String(row[key] || '').trim()
    if (value) return value
  }
  return ''
}

const resolveEventAt = (row: Record<string, unknown>) => {
  return resolveText(row, ['completedAt', 'completed_at', 'confirmedAt', 'confirmed_at', 'updatedAt', 'updated_at', 'createdAt', 'created_at'])
}

const resolveProcessingNote = (row: Record<string, unknown>) => {
  return resolveText(row, ['rejectReason', 'reject_reason', 'returnReason', 'return_reason'])
}

const resolveStatusType = (value: string) => {
  if (value === 'completed') return 'success'
  if (value === 'rejected') return 'danger'
  if (value === 'pending') return 'warning'
  return 'info'
}

const resolveDashboardCount = (
  segmentKey: string,
  countKeys: string[],
): number | null => {
  if (!props.workspaceDashboard || typeof props.workspaceDashboard !== 'object') {
    return null
  }
  const segment = props.workspaceDashboard[segmentKey]
  if (!segment || typeof segment !== 'object') {
    return null
  }
  const candidate = segment as Record<string, unknown>
  for (const key of countKeys) {
    const value = candidate[key]
    if (value === null || value === undefined || value === '') {
      continue
    }
    const normalized = Number(value)
    if (Number.isFinite(normalized)) {
      return normalized
    }
  }
  return null
}

const sortHistoryRows = (rows: ReturnOrderRecord[]) => {
  return [...rows].sort((left, right) => {
    const leftTime = Date.parse(resolveEventAt(left) || resolveText(left, ['returnDate', 'return_date']) || '') || 0
    const rightTime = Date.parse(resolveEventAt(right) || resolveText(right, ['returnDate', 'return_date']) || '') || 0
    return rightTime - leftTime
  })
}

const normalizeTrendPoints = (points: Array<Record<string, unknown>>) => {
  return points.map((point) => ({
    date: String(point.date || '').trim(),
    label: String(point.label || '').trim(),
    completedCount: Number(point.completedCount || point.completed_count || 0),
    rejectedCount: Number(point.rejectedCount || point.rejected_count || 0),
    totalCount: Number(point.totalCount || point.total_count || 0),
  }))
}

const resolveTrendWidth = (point: TrendPoint) => {
  const maxTotal = Math.max(trendMaxTotal.value, 1)
  return Math.max((point.totalCount / maxTotal) * 100, point.totalCount > 0 ? 8 : 0)
}

const sharedPendingCount = computed(() => resolveDashboardCount('returns', ['pendingCount', 'pending_count']))
const sharedCompletedCount = computed(() => resolveDashboardCount('returns', ['completedCount', 'completed_count']))
const sharedRejectedCount = computed(() => resolveDashboardCount('returns', ['rejectedCount', 'rejected_count']))
const displayPendingCount = computed(() => sharedPendingCount.value ?? pendingCount.value)
const displayCompletedCount = computed(() => sharedCompletedCount.value ?? completedCount.value)
const displayRejectedCount = computed(() => sharedRejectedCount.value ?? rejectedCount.value)

const loadHistory = async () => {
  if (!props.recordId) return
  loading.value = true
  try {
    const result = await request.get<ReturnDashboardPayload>(
      `/system/objects/AssetProject/${props.recordId}/return_dashboard/`,
      {
        params: {
          range_key: selectedRangeKey.value,
        },
      }
    )

    const summary = result.summary || {}
    const history = result.history || {}
    const trend = result.trend || {}
    const window = result.window || {}
    pendingCount.value = Number(summary.pendingCount || summary.pending_count || 0)
    completedCount.value = Number(summary.completedCount || summary.completed_count || 0)
    rejectedCount.value = Number(summary.rejectedCount || summary.rejected_count || 0)
    processedCount.value = Number(summary.processedCount || summary.processed_count || 0)
    historyRows.value = sortHistoryRows(Array.isArray(history.rows) ? history.rows : [])
    trendPoints.value = normalizeTrendPoints(Array.isArray(trend.points) ? trend.points : [])
    trendMaxTotal.value = Number(trend.maxTotalCount || trend.max_total_count || 0)
    windowStartDate.value = String(window.startDate || window.start_date || '').trim()
    windowEndDate.value = String(window.endDate || window.end_date || '').trim()
  } catch (error: unknown) {
    pendingCount.value = 0
    completedCount.value = 0
    rejectedCount.value = 0
    processedCount.value = 0
    historyRows.value = []
    trendPoints.value = []
    trendMaxTotal.value = 0
    windowStartDate.value = ''
    windowEndDate.value = ''
    ElMessage.error(error instanceof Error ? error.message : t('projects.messages.loadReturnHistoryFailed'))
  } finally {
    loading.value = false
  }
}

const handleRangeChange = (rangeKey: string) => {
  if (!rangeKey || rangeKey === selectedRangeKey.value) return
  selectedRangeKey.value = rangeKey
  void loadHistory()
}

const handleViewAll = () => {
  router.push({
    path: '/objects/AssetReturn',
    query: { project: props.recordId },
  })
}

const handleOpenReturn = (row: ReturnOrderRecord) => {
  const recordId = String(row.id || '').trim()
  if (!recordId) return
  router.push(`/objects/AssetReturn/${encodeURIComponent(recordId)}`)
}

watch(
  () => [props.recordId, props.refreshVersion, props.panelRefreshVersion],
  () => {
    void loadHistory()
  },
  { immediate: true }
)
</script>

<style scoped>
.asset-project-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.asset-project-panel__heading {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.asset-project-panel__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.asset-project-panel__meta {
  font-size: 12px;
  color: #606266;
}

.asset-project-panel__hint {
  margin: 0;
  font-size: 12px;
  color: #909399;
}

.asset-project-panel__actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.asset-project-panel__range-switch {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.asset-project-panel__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.asset-project-panel__summary-card {
  padding: 12px 14px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fafafa;
}

.asset-project-panel__summary-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}

.asset-project-panel__summary-value {
  font-size: 22px;
  line-height: 1;
  color: #303133;
}

.asset-project-panel__trend {
  padding: 12px 14px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
  margin-bottom: 16px;
}

.asset-project-panel__trend-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.asset-project-panel__trend-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}

.asset-project-panel__trend-window {
  font-size: 12px;
  color: #909399;
}

.asset-project-panel__trend-empty {
  font-size: 12px;
  color: #909399;
}

.asset-project-panel__trend-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.asset-project-panel__trend-row {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr) 72px;
  align-items: center;
  gap: 12px;
}

.asset-project-panel__trend-label,
.asset-project-panel__trend-metrics {
  font-size: 12px;
  color: #606266;
}

.asset-project-panel__trend-track {
  height: 10px;
  border-radius: 999px;
  background: #f0f2f5;
  overflow: hidden;
}

.asset-project-panel__trend-stack {
  display: flex;
  height: 100%;
  min-width: 0;
}

.asset-project-panel__trend-segment {
  height: 100%;
}

.asset-project-panel__trend-segment--completed {
  background: #67c23a;
}

.asset-project-panel__trend-segment--rejected {
  background: #f56c6c;
}

.asset-project-panel__return-link {
  justify-content: flex-start;
  padding: 0;
}

@media (max-width: 768px) {
  .asset-project-panel__summary {
    grid-template-columns: 1fr;
  }

  .asset-project-panel__trend-row {
    grid-template-columns: 48px minmax(0, 1fr) 64px;
  }
}
</style>
