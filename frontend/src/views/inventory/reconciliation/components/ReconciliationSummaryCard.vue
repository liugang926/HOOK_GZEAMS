<template>
  <el-card
    class="reconciliation-summary-card"
    shadow="never"
  >
    <template #header>
      <div class="reconciliation-summary-card__header">
        <div>
          <div class="reconciliation-summary-card__title">
            {{ title || t('inventory.reconciliationSummary.title') }}
          </div>
          <p class="reconciliation-summary-card__hint">
            {{ t('inventory.reconciliationSummary.hint') }}
          </p>
        </div>
        <el-tag
          size="small"
          type="info"
          effect="plain"
        >
          {{ t('inventory.reconciliationSummary.tags.currentList') }}
        </el-tag>
      </div>
    </template>

    <div
      v-loading="loading"
      class="reconciliation-summary-card__body"
    >
      <div class="reconciliation-summary-card__stats">
        <div class="reconciliation-summary-card__stat reconciliation-summary-card__stat--slate">
          <span class="reconciliation-summary-card__stat-label">
            {{ t('inventory.reconciliationSummary.stats.total') }}
          </span>
          <strong class="reconciliation-summary-card__stat-value">
            {{ formatNumber(totalRecords) }}
          </strong>
        </div>
        <div class="reconciliation-summary-card__stat reconciliation-summary-card__stat--green">
          <span class="reconciliation-summary-card__stat-label">
            {{ t('inventory.reconciliationSummary.stats.approved') }}
          </span>
          <strong class="reconciliation-summary-card__stat-value">
            {{ formatNumber(approvedCount) }}
          </strong>
        </div>
        <div class="reconciliation-summary-card__stat reconciliation-summary-card__stat--amber">
          <span class="reconciliation-summary-card__stat-label">
            {{ t('inventory.reconciliationSummary.stats.submitted') }}
          </span>
          <strong class="reconciliation-summary-card__stat-value">
            {{ formatNumber(submittedCount) }}
          </strong>
        </div>
        <div class="reconciliation-summary-card__stat reconciliation-summary-card__stat--rose">
          <span class="reconciliation-summary-card__stat-label">
            {{ t('inventory.reconciliationSummary.stats.adjustments') }}
          </span>
          <strong class="reconciliation-summary-card__stat-value">
            {{ formatNumber(totalAdjustments) }}
          </strong>
        </div>
      </div>

      <div class="reconciliation-summary-card__content">
        <section class="reconciliation-summary-card__panel">
          <div class="reconciliation-summary-card__panel-header">
            <span>{{ t('inventory.reconciliationSummary.progress.title') }}</span>
            <strong>{{ t('inventory.reconciliationSummary.progress.summary', { percent: `${completionRate}%` }) }}</strong>
          </div>

          <div class="reconciliation-summary-card__progress-list">
            <div class="reconciliation-summary-card__progress-item">
              <div class="reconciliation-summary-card__progress-meta">
                <span>{{ t('inventory.reconciliationSummary.progress.completion') }}</span>
                <strong>{{ completionRate }}%</strong>
              </div>
              <el-progress
                :percentage="completionRate"
                :show-text="false"
                color="#1f8f5f"
              />
            </div>

            <div class="reconciliation-summary-card__progress-item">
              <div class="reconciliation-summary-card__progress-meta">
                <span>{{ t('inventory.reconciliationSummary.progress.approval') }}</span>
                <strong>{{ approvalRate }}%</strong>
              </div>
              <el-progress
                :percentage="approvalRate"
                :show-text="false"
                color="#2563eb"
              />
            </div>

            <div class="reconciliation-summary-card__progress-item">
              <div class="reconciliation-summary-card__progress-meta">
                <span>{{ t('inventory.reconciliationSummary.progress.adjustmentCoverage') }}</span>
                <strong>{{ adjustmentCoverageRate }}%</strong>
              </div>
              <el-progress
                :percentage="adjustmentCoverageRate"
                :show-text="false"
                color="#d97706"
              />
            </div>
          </div>

          <div class="reconciliation-summary-card__metric-row">
            <div class="reconciliation-summary-card__metric">
              <span>{{ t('inventory.reconciliationSummary.metrics.differences') }}</span>
              <strong>{{ formatNumber(totalDifferences) }}</strong>
            </div>
            <div class="reconciliation-summary-card__metric">
              <span>{{ t('inventory.reconciliationSummary.metrics.rejected') }}</span>
              <strong>{{ formatNumber(rejectedCount) }}</strong>
            </div>
            <div class="reconciliation-summary-card__metric">
              <span>{{ t('inventory.reconciliationSummary.metrics.pending') }}</span>
              <strong>{{ formatNumber(pendingCount) }}</strong>
            </div>
          </div>
        </section>

        <section class="reconciliation-summary-card__panel">
          <div class="reconciliation-summary-card__panel-header">
            <span>{{ t('inventory.reconciliationSummary.trend.title') }}</span>
            <strong>{{ t('inventory.reconciliationSummary.trend.window', { count: trendPoints.length }) }}</strong>
          </div>

          <div
            v-if="trendPoints.length === 0"
            class="reconciliation-summary-card__empty"
          >
            {{ t('inventory.reconciliationSummary.trend.empty') }}
          </div>

          <div
            v-else
            class="reconciliation-summary-card__trend"
          >
            <div class="reconciliation-summary-card__legend">
              <span class="reconciliation-summary-card__legend-item">
                <i class="reconciliation-summary-card__legend-dot reconciliation-summary-card__legend-dot--difference" />
                {{ t('inventory.reconciliationSummary.trend.differences') }}
              </span>
              <span class="reconciliation-summary-card__legend-item">
                <i class="reconciliation-summary-card__legend-dot reconciliation-summary-card__legend-dot--adjustment" />
                {{ t('inventory.reconciliationSummary.trend.adjustments') }}
              </span>
            </div>

            <div class="reconciliation-summary-card__trend-list">
              <div
                v-for="point in trendPoints"
                :key="point.key"
                class="reconciliation-summary-card__trend-row"
              >
                <span class="reconciliation-summary-card__trend-label">
                  {{ point.label }}
                </span>

                <div class="reconciliation-summary-card__trend-track">
                  <span
                    class="reconciliation-summary-card__trend-bar reconciliation-summary-card__trend-bar--difference"
                    :style="{ width: `${resolveTrendWidth(point.differences)}%` }"
                  />
                  <span
                    class="reconciliation-summary-card__trend-bar reconciliation-summary-card__trend-bar--adjustment"
                    :style="{ width: `${resolveTrendWidth(point.adjustments)}%` }"
                  />
                </div>

                <span class="reconciliation-summary-card__trend-value">
                  {{ point.differences }}/{{ point.adjustments }}
                </span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import dayjs from 'dayjs'
import type { InventoryReconciliation } from '@/types/inventory'

interface TrendPoint {
  key: string
  label: string
  differences: number
  adjustments: number
}

const props = withDefaults(defineProps<{
  records?: InventoryReconciliation[]
  loading?: boolean
  title?: string
}>(), {
  records: () => [],
  loading: false,
  title: ''
})

const { t } = useI18n()

const safeRecords = computed<InventoryReconciliation[]>(() => {
  return Array.isArray(props.records) ? props.records : []
})

const totalRecords = computed(() => safeRecords.value.length)

const approvedCount = computed(() => {
  return safeRecords.value.filter((record) => record.status === 'approved').length
})

const submittedCount = computed(() => {
  return safeRecords.value.filter((record) => record.status === 'submitted').length
})

const rejectedCount = computed(() => {
  return safeRecords.value.filter((record) => record.status === 'rejected').length
})

const pendingCount = computed(() => {
  return safeRecords.value.filter((record) => record.status === 'draft').length
})

const totalAdjustments = computed(() => {
  return safeRecords.value.reduce((sum, record) => sum + Number(record.adjustmentCount || 0), 0)
})

const totalDifferences = computed(() => {
  return safeRecords.value.reduce((sum, record) => {
    const rawValue = record.differenceCount ?? record.abnormalCount ?? 0
    return sum + Number(rawValue)
  }, 0)
})

const completionRate = computed(() => {
  if (totalRecords.value === 0) return 0
  return Math.round(((approvedCount.value + rejectedCount.value) / totalRecords.value) * 100)
})

const approvalRate = computed(() => {
  if (totalRecords.value === 0) return 0
  return Math.round((approvedCount.value / totalRecords.value) * 100)
})

const adjustmentCoverageRate = computed(() => {
  if (totalDifferences.value === 0) return 0
  return Math.min(100, Math.round((totalAdjustments.value / totalDifferences.value) * 100))
})

const trendPoints = computed<TrendPoint[]>(() => {
  return [...safeRecords.value]
    .sort((left, right) => {
      const leftValue = dayjs(left.reconciledAt || left.createdAt || '').valueOf()
      const rightValue = dayjs(right.reconciledAt || right.createdAt || '').valueOf()
      return leftValue - rightValue
    })
    .slice(-6)
    .map((record, index) => {
      const sourceDate = record.reconciledAt || record.createdAt || ''
      return {
        key: `${record.id}-${index}`,
        label: sourceDate ? dayjs(sourceDate).format('MM-DD') : t('inventory.reconciliationSummary.trend.noDate'),
        differences: Number(record.differenceCount ?? record.abnormalCount ?? 0),
        adjustments: Number(record.adjustmentCount || 0)
      }
    })
})

const trendMaxValue = computed(() => {
  return Math.max(
    1,
    ...trendPoints.value.flatMap((point) => [point.differences, point.adjustments])
  )
})

const resolveTrendWidth = (value: number) => {
  return Math.max(10, Math.round((Math.max(value, 0) / trendMaxValue.value) * 100))
}

const formatNumber = (value: number) => {
  return Number(value || 0).toLocaleString()
}
</script>

<style scoped lang="scss">
.reconciliation-summary-card {
  border: 1px solid #dce3ef;
  border-radius: 20px;
  background:
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.08), transparent 32%),
    linear-gradient(135deg, #f8fbff 0%, #ffffff 52%, #f9f6ef 100%);
}

.reconciliation-summary-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.reconciliation-summary-card__title {
  font-size: 18px;
  font-weight: 700;
  color: #16324f;
}

.reconciliation-summary-card__hint {
  margin: 6px 0 0;
  color: #5f7085;
  font-size: 13px;
}

.reconciliation-summary-card__body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.reconciliation-summary-card__stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.reconciliation-summary-card__stat {
  padding: 16px;
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.88);
}

.reconciliation-summary-card__stat--slate {
  box-shadow: inset 0 0 0 1px rgba(51, 65, 85, 0.04);
}

.reconciliation-summary-card__stat--green {
  background: linear-gradient(180deg, rgba(236, 253, 245, 0.95), rgba(255, 255, 255, 0.92));
}

.reconciliation-summary-card__stat--amber {
  background: linear-gradient(180deg, rgba(255, 251, 235, 0.95), rgba(255, 255, 255, 0.92));
}

.reconciliation-summary-card__stat--rose {
  background: linear-gradient(180deg, rgba(255, 241, 242, 0.95), rgba(255, 255, 255, 0.92));
}

.reconciliation-summary-card__stat-label {
  display: block;
  color: #64748b;
  font-size: 12px;
  margin-bottom: 10px;
}

.reconciliation-summary-card__stat-value {
  display: block;
  color: #0f172a;
  font-size: 28px;
  line-height: 1;
}

.reconciliation-summary-card__content {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr);
  gap: 16px;
}

.reconciliation-summary-card__panel {
  padding: 18px;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.9);
}

.reconciliation-summary-card__panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  color: #1e293b;
  font-size: 14px;
  font-weight: 600;
}

.reconciliation-summary-card__progress-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.reconciliation-summary-card__progress-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reconciliation-summary-card__progress-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #475569;
  font-size: 13px;
}

.reconciliation-summary-card__metric-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.reconciliation-summary-card__metric {
  padding: 12px 14px;
  border-radius: 14px;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  gap: 8px;
  color: #64748b;
  font-size: 12px;
}

.reconciliation-summary-card__metric strong {
  color: #0f172a;
  font-size: 20px;
}

.reconciliation-summary-card__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}

.reconciliation-summary-card__legend-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #475569;
  font-size: 12px;
}

.reconciliation-summary-card__legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
}

.reconciliation-summary-card__legend-dot--difference,
.reconciliation-summary-card__trend-bar--difference {
  background: linear-gradient(90deg, #2563eb, #60a5fa);
}

.reconciliation-summary-card__legend-dot--adjustment,
.reconciliation-summary-card__trend-bar--adjustment {
  background: linear-gradient(90deg, #d97706, #fbbf24);
}

.reconciliation-summary-card__trend-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reconciliation-summary-card__trend-row {
  display: grid;
  grid-template-columns: 56px minmax(0, 1fr) 64px;
  align-items: center;
  gap: 12px;
}

.reconciliation-summary-card__trend-label,
.reconciliation-summary-card__trend-value {
  color: #64748b;
  font-size: 12px;
}

.reconciliation-summary-card__trend-value {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.reconciliation-summary-card__trend-track {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.reconciliation-summary-card__trend-bar {
  display: block;
  height: 10px;
  border-radius: 999px;
  min-width: 10%;
}

.reconciliation-summary-card__empty {
  min-height: 168px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #94a3b8;
  font-size: 13px;
  border-radius: 14px;
  background: #f8fafc;
}

@media (max-width: 1080px) {
  .reconciliation-summary-card__stats,
  .reconciliation-summary-card__metric-row,
  .reconciliation-summary-card__content {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .reconciliation-summary-card__header,
  .reconciliation-summary-card__panel-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .reconciliation-summary-card__stats,
  .reconciliation-summary-card__metric-row,
  .reconciliation-summary-card__content {
    grid-template-columns: minmax(0, 1fr);
  }

  .reconciliation-summary-card__trend-row {
    grid-template-columns: 44px minmax(0, 1fr) 52px;
    gap: 8px;
  }

  .reconciliation-summary-card__stat-value {
    font-size: 24px;
  }
}
</style>
