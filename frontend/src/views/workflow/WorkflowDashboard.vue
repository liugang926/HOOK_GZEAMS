<template>
  <div class="workflow-dashboard">
    <div class="page-header">
      <h2>{{ $t('workflow.dashboard.title') }}</h2>
      <el-button
        :icon="Refresh"
        :loading="loading"
        circle
        @click="loadAll"
      />
    </div>

    <!-- Widget 1: Status Overview -->
    <div class="widget-section">
      <h3 class="widget-title">
        <el-icon><DataAnalysis /></el-icon>
        {{ $t('workflow.dashboard.statusOverview') }}
      </h3>
      <div class="stat-cards">
        <div class="stat-card total">
          <div class="stat-value">
            {{ overview.total_instances }}
          </div>
          <div class="stat-label">
            {{ $t('workflow.dashboard.totalInstances') }}
          </div>
        </div>
        <div class="stat-card pending">
          <div class="stat-value">
            {{ overview.pending_instances }}
          </div>
          <div class="stat-label">
            {{ $t('workflow.dashboard.pendingInstances') }}
          </div>
        </div>
        <div class="stat-card completed">
          <div class="stat-value">
            {{ overview.completed_instances }}
          </div>
          <div class="stat-label">
            {{ $t('workflow.dashboard.completedInstances') }}
          </div>
        </div>
        <div class="stat-card rejected">
          <div class="stat-value">
            {{ overview.rejected_instances }}
          </div>
          <div class="stat-label">
            {{ $t('workflow.dashboard.rejectedInstances') }}
          </div>
        </div>
      </div>
      <div class="stat-cards secondary">
        <div class="stat-card rate">
          <div class="stat-value">
            {{ overview.approval_rate }}%
          </div>
          <div class="stat-label">
            {{ $t('workflow.dashboard.approvalRate') }}
          </div>
        </div>
        <div class="stat-card rate">
          <div class="stat-value">
            {{ overview.average_completion_hours }}h
          </div>
          <div class="stat-label">
            {{ $t('workflow.dashboard.avgCompletionTime') }}
          </div>
        </div>
      </div>
    </div>

    <!-- Widget 2: My Tasks Summary -->
    <div class="widget-section">
      <h3 class="widget-title">
        <el-icon><User /></el-icon>
        {{ $t('workflow.dashboard.myTasksSummary') }}
      </h3>
      <div class="stat-cards">
        <div class="stat-card my-pending">
          <div class="stat-value">
            {{ overview.my_pending_tasks }}
          </div>
          <div class="stat-label">
            {{ $t('workflow.dashboard.myPending') }}
          </div>
        </div>
        <div class="stat-card my-overdue">
          <div class="stat-value">
            {{ overview.my_overdue_tasks }}
          </div>
          <div class="stat-label">
            {{ $t('workflow.dashboard.myOverdue') }}
          </div>
        </div>
        <div class="stat-card my-completed">
          <div class="stat-value">
            {{ overview.my_completed_tasks }}
          </div>
          <div class="stat-label">
            {{ $t('workflow.dashboard.myCompleted') }}
          </div>
        </div>
      </div>
    </div>

    <!-- Widget 3: 7-Day Trends -->
    <div class="widget-section">
      <h3 class="widget-title">
        <el-icon><TrendCharts /></el-icon>
        {{ $t('workflow.dashboard.trends') }}
        <el-radio-group
          v-model="trendPeriod"
          size="small"
          class="period-selector"
          @change="loadTrends"
        >
          <el-radio-button value="7d">
            7D
          </el-radio-button>
          <el-radio-button value="14d">
            14D
          </el-radio-button>
          <el-radio-button value="30d">
            30D
          </el-radio-button>
        </el-radio-group>
      </h3>
      <div
        v-if="trendData.length"
        class="trend-chart"
      >
        <div class="trend-legend">
          <span class="legend-item started">
            <span class="legend-dot" />{{ $t('workflow.dashboard.started') }}
          </span>
          <span class="legend-item completed">
            <span class="legend-dot" />{{ $t('workflow.dashboard.completed') }}
          </span>
          <span class="legend-item rejected-leg">
            <span class="legend-dot" />{{ $t('workflow.dashboard.rejected') }}
          </span>
        </div>
        <div class="bars-container">
          <div
            v-for="point in trendData"
            :key="point.date"
            class="bar-group"
          >
            <div class="bar-stack">
              <div
                class="bar bar-started"
                :style="{ height: barHeight(point.started) + 'px' }"
                :title="`${$t('workflow.dashboard.started')}: ${point.started}`"
              />
              <div
                class="bar bar-completed"
                :style="{ height: barHeight(point.completed) + 'px' }"
                :title="`${$t('workflow.dashboard.completed')}: ${point.completed}`"
              />
              <div
                class="bar bar-rejected"
                :style="{ height: barHeight(point.rejected) + 'px' }"
                :title="`${$t('workflow.dashboard.rejected')}: ${point.rejected}`"
              />
            </div>
            <div class="bar-label">
              {{ formatTrendDate(point.date) }}
            </div>
          </div>
        </div>
      </div>
      <el-empty
        v-else
        :description="$t('common.messages.noData')"
        :image-size="60"
      />
    </div>

    <!-- Widget 4: Bottleneck Nodes -->
    <div class="widget-section">
      <h3 class="widget-title">
        <el-icon><Warning /></el-icon>
        {{ $t('workflow.dashboard.bottlenecks') }}
      </h3>
      <el-table
        v-if="bottlenecks.length"
        :data="bottlenecks"
        stripe
        size="small"
        class="bottleneck-table"
      >
        <el-table-column
          prop="node_name"
          :label="$t('workflow.dashboard.nodeName')"
          min-width="160"
        />
        <el-table-column
          prop="definition_name"
          :label="$t('workflow.dashboard.definitionName')"
          min-width="140"
        />
        <el-table-column
          prop="avg_duration_hours"
          :label="$t('workflow.dashboard.avgDuration')"
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <span :class="{ 'text-danger': row.avg_duration_hours > 24 }">
              {{ row.avg_duration_hours }}h
            </span>
          </template>
        </el-table-column>
        <el-table-column
          prop="task_count"
          :label="$t('workflow.dashboard.taskCount')"
          width="100"
          align="center"
        />
        <el-table-column
          :label="$t('workflow.dashboard.overdueRate')"
          width="140"
          align="center"
        >
          <template #default="{ row }">
            <el-progress
              :percentage="row.overdue_rate"
              :color="row.overdue_rate > 30 ? '#f56c6c' : row.overdue_rate > 10 ? '#e6a23c' : '#67c23a'"
              :stroke-width="10"
            />
          </template>
        </el-table-column>
      </el-table>
      <el-empty
        v-else
        :description="$t('common.messages.noData')"
        :image-size="60"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Refresh, DataAnalysis, User, TrendCharts, Warning } from '@element-plus/icons-vue'
import {
  workflowStatsApi,
  type OverviewStats,
  type TrendDataPoint,
  type BottleneckNode,
} from '@/api/workflowStats'

const { t } = useI18n()

// State
const loading = ref(false)
const trendPeriod = ref<'7d' | '14d' | '30d'>('7d')

const overview = ref<OverviewStats>({
  total_instances: 0,
  pending_instances: 0,
  completed_instances: 0,
  rejected_instances: 0,
  my_pending_tasks: 0,
  my_completed_tasks: 0,
  my_overdue_tasks: 0,
  average_completion_hours: 0,
  approval_rate: 0,
  overdue_rate: 0,
  instances_by_status: {},
  instances_by_definition: {},
})

const trendData = ref<TrendDataPoint[]>([])
const bottlenecks = ref<BottleneckNode[]>([])

// Compute bar height relative to max value
const maxTrendValue = () => {
  let max = 1
  for (const p of trendData.value) {
    max = Math.max(max, p.started, p.completed, p.rejected)
  }
  return max
}

const barHeight = (value: number) => {
  const max = maxTrendValue()
  return Math.max(2, (value / max) * 100)
}

const formatTrendDate = (dateStr: string) => {
  const parts = dateStr.split('-')
  return `${parts[1]}/${parts[2]}`
}

// Data loading
const loadOverview = async () => {
  try {
    const res = await workflowStatsApi.getOverview()
    const data = res?.data || res
    overview.value = { ...overview.value, ...data }
  } catch (e: any) {
    console.error('Failed to load overview:', e)
  }
}

const loadTrends = async () => {
  try {
    const res = await workflowStatsApi.getTrends(trendPeriod.value)
    const data = res?.data || res
    trendData.value = data.data || []
  } catch (e: any) {
    console.error('Failed to load trends:', e)
  }
}

const loadBottlenecks = async () => {
  try {
    const res = await workflowStatsApi.getBottlenecks()
    const data = res?.data || res
    bottlenecks.value = data.bottlenecks || []
  } catch (e: any) {
    console.error('Failed to load bottlenecks:', e)
  }
}

const loadAll = async () => {
  loading.value = true
  try {
    await Promise.all([loadOverview(), loadTrends(), loadBottlenecks()])
  } catch (e: any) {
    ElMessage.error(e.message || t('workflow.messages.loadFailed'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadAll()
})
</script>

<style scoped>
.workflow-dashboard {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.widget-section {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.widget-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 16px 0;
}

.period-selector {
  margin-left: auto;
}

/* Stat Cards */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 12px;
}

.stat-cards.secondary {
  margin-top: 12px;
}

.stat-card {
  padding: 16px;
  border-radius: 8px;
  text-align: center;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.stat-card.total { background: #ecf5ff; }
.stat-card.total .stat-value { color: #409eff; }

.stat-card.pending { background: #fdf6ec; }
.stat-card.pending .stat-value { color: #e6a23c; }

.stat-card.completed { background: #f0f9eb; }
.stat-card.completed .stat-value { color: #67c23a; }

.stat-card.rejected { background: #fef0f0; }
.stat-card.rejected .stat-value { color: #f56c6c; }

.stat-card.rate { background: #f4f4f5; }
.stat-card.rate .stat-value { color: #606266; }

.stat-card.my-pending { background: #ecf5ff; }
.stat-card.my-pending .stat-value { color: #409eff; }

.stat-card.my-overdue { background: #fef0f0; }
.stat-card.my-overdue .stat-value { color: #f56c6c; }

.stat-card.my-completed { background: #f0f9eb; }
.stat-card.my-completed .stat-value { color: #67c23a; }

/* Trend Chart */
.trend-chart {
  overflow-x: auto;
}

.trend-legend {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 12px;
  color: #606266;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  display: inline-block;
}

.legend-item.started .legend-dot { background: #409eff; }
.legend-item.completed .legend-dot { background: #67c23a; }
.legend-item.rejected-leg .legend-dot { background: #f56c6c; }

.bars-container {
  display: flex;
  gap: 6px;
  align-items: flex-end;
  min-height: 130px;
  padding-bottom: 4px;
}

.bar-group {
  flex: 1;
  min-width: 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.bar-stack {
  display: flex;
  gap: 2px;
  align-items: flex-end;
  height: 110px;
}

.bar {
  width: 8px;
  border-radius: 2px 2px 0 0;
  transition: height 0.3s ease;
  cursor: pointer;
}

.bar:hover {
  opacity: 0.8;
}

.bar-started { background: #409eff; }
.bar-completed { background: #67c23a; }
.bar-rejected { background: #f56c6c; }

.bar-label {
  font-size: 10px;
  color: #909399;
  margin-top: 4px;
  white-space: nowrap;
}

/* Bottleneck Table */
.bottleneck-table {
  width: 100%;
}

.text-danger {
  color: #f56c6c;
  font-weight: 600;
}
</style>
