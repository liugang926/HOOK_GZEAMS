<template>
  <div class="dashboard">
    <!-- KPI Summary Cards -->
    <DashboardMetricGrid :cards="metricCards" />

    <!-- New: My Tasks + Alerts Row -->
    <el-row :gutter="20" class="mt-20">
      <el-col :xs="24" :sm="12" :md="8">
        <el-card shadow="hover" class="dashboard-panel tasks-panel">
          <template #header>
            <div class="panel-header">
              <el-icon class="panel-icon tasks-icon"><Bell /></el-icon>
              <span>{{ $t('dashboard.myTasks.title', 'My Tasks') }}</span>
            </div>
          </template>
          <el-skeleton :loading="summaryLoading" :rows="3" animated>
            <template #default>
              <div class="task-items">
                <div
                  class="task-item clickable"
                  @click="router.push('/workflow/my-approvals')"
                >
                  <div class="task-count warning">{{ summaryData.myTasks.pendingApprovals }}</div>
                  <div class="task-label">{{ $t('dashboard.myTasks.pendingApprovals', 'Pending Approvals') }}</div>
                </div>
                <div
                  class="task-item clickable"
                  @click="router.push('/objects/AssetPickup?status=pending')"
                >
                  <div class="task-count primary">{{ summaryData.myTasks.pendingPickups }}</div>
                  <div class="task-label">{{ $t('dashboard.myTasks.pendingPickups', 'Pending Pickups') }}</div>
                </div>
                <div class="task-item">
                  <div class="task-count" :class="{ danger: summaryData.myTasks.overdueTasks > 0 }">
                    {{ summaryData.myTasks.overdueTasks }}
                  </div>
                  <div class="task-label">{{ $t('dashboard.myTasks.overdueTasks', 'Overdue Tasks') }}</div>
                </div>
              </div>
            </template>
          </el-skeleton>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8">
        <el-card shadow="hover" class="dashboard-panel alerts-panel">
          <template #header>
            <div class="panel-header">
              <el-icon class="panel-icon alerts-icon"><Warning /></el-icon>
              <span>{{ $t('dashboard.alerts.title', 'Alerts & Warnings') }}</span>
            </div>
          </template>
          <el-skeleton :loading="summaryLoading" :rows="3" animated>
            <template #default>
              <div v-if="summaryData.alerts.length === 0" class="empty-hint">
                {{ $t('dashboard.alerts.noAlerts', 'No alerts at this time') }}
              </div>
              <div v-else class="alert-list">
                <div
                  v-for="(alert, i) in summaryData.alerts"
                  :key="i"
                  :class="['alert-item', `alert-${alert.type}`]"
                  @click="router.push(alert.link)"
                >
                  <el-icon v-if="alert.type === 'warning'" class="alert-icon"><Warning /></el-icon>
                  <el-icon v-else class="alert-icon"><InfoFilled /></el-icon>
                  <span class="alert-text">{{ alert.title }}</span>
                </div>
              </div>
            </template>
          </el-skeleton>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="8">
        <el-card shadow="hover" class="dashboard-panel actions-panel">
          <template #header>
            <div class="panel-header">
              <el-icon class="panel-icon actions-icon"><Grid /></el-icon>
              <span>{{ $t('dashboard.quickActions.title', 'Quick Actions') }}</span>
            </div>
          </template>
          <div class="quick-actions-grid">
            <el-button
              v-for="action in summaryData.quickActions"
              :key="action.code"
              class="quick-action-btn"
              @click="router.push(action.route)"
            >
              <span class="action-label">{{ action.label }}</span>
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Existing: Charts Row -->
    <el-row :gutter="20" class="mt-20">
      <el-col :xs="24" :md="12">
        <DashboardChartCard
          :set-chart-ref="setStatusChartRef"
          :title="$t('dashboard.charts.statusDistribution')"
        />
      </el-col>
      <el-col :xs="24" :md="12">
        <DashboardChartCard
          :set-chart-ref="setCategoryChartRef"
          :title="$t('dashboard.charts.categoryStatistics')"
        />
      </el-col>
    </el-row>

    <!-- Existing: Lifecycle Section -->
    <div class="section-title mt-20">
      <el-icon class="section-icon"><Refresh /></el-icon>
      {{ $t('dashboard.lifecycle.title') }}
    </div>

    <DashboardLifecycleCards
      :cards="lifecycleCards"
      :view-all-label="$t('dashboard.lifecycle.viewAll')"
      @navigate="router.push($event)"
    />

    <el-row :gutter="20" class="mt-20">
      <el-col :xs="24" :md="12">
        <DashboardChartCard
          :set-chart-ref="setMaintenanceChartRef"
          :title="$t('dashboard.lifecycle.maintenanceStatusChart')"
        />
      </el-col>
      <el-col :xs="24" :md="12">
        <DashboardRecentActivityPanel
          :empty-description="$t('common.messages.noData')"
          :items="recentActivities"
          :loading="lifecycleLoading"
          :title="$t('dashboard.lifecycle.recentActivity')"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Bell, Grid, InfoFilled, Refresh, Warning } from '@element-plus/icons-vue'

import DashboardChartCard from './dashboard/DashboardChartCard.vue'
import DashboardLifecycleCards from './dashboard/DashboardLifecycleCards.vue'
import DashboardMetricGrid from './dashboard/DashboardMetricGrid.vue'
import DashboardRecentActivityPanel from './dashboard/DashboardRecentActivityPanel.vue'
import {
  buildDashboardLifecycleCards,
  buildDashboardMetricCards,
} from './dashboard/dashboardCardModel'
import { useDashboardData } from './dashboard/useDashboardData'
import { useDashboardCharts } from './dashboard/useDashboardCharts'
import { dashboardApi } from '@/api/dashboard'
import type { DashboardAlert, QuickAction } from '@/api/dashboard'

const { t } = useI18n()
const router = useRouter()
const {
  fetchLifecycleData,
  fetchMetrics,
  lifecycle,
  lifecycleLoading,
  metrics,
  recentActivities,
} = useDashboardData(t)
const {
  categoryChartRef,
  initCharts,
  maintenanceChartRef,
  resizeCharts,
  statusChartRef,
  updateCategoryChart,
  updateMaintenanceChart,
  updateStatusChart,
} = useDashboardCharts(t)

// New: summary data from /api/dashboard/summary/
const summaryLoading = ref(true)
const summaryData = reactive({
  myTasks: { pendingApprovals: 0, pendingPickups: 0, overdueTasks: 0 },
  alerts: [] as DashboardAlert[],
  quickActions: [] as QuickAction[],
})

const metricCards = computed(() => buildDashboardMetricCards(metrics, t))
const lifecycleCards = computed(() => buildDashboardLifecycleCards(lifecycle, lifecycleLoading.value, t))
const setStatusChartRef = (element: Element | { $el?: Element } | null) => {
  statusChartRef.value = element instanceof HTMLElement ? element : null
}
const setCategoryChartRef = (element: Element | { $el?: Element } | null) => {
  categoryChartRef.value = element instanceof HTMLElement ? element : null
}
const setMaintenanceChartRef = (element: Element | { $el?: Element } | null) => {
  maintenanceChartRef.value = element instanceof HTMLElement ? element : null
}

const fetchSummary = async () => {
  summaryLoading.value = true
  try {
    const res = await dashboardApi.getSummary()
    const data = (res as any)?.data?.data ?? (res as any)?.data ?? {}
    if (data.myTasks) {
      summaryData.myTasks = data.myTasks
    }
    if (data.alerts) {
      summaryData.alerts = data.alerts
    }
    if (data.quickActions) {
      summaryData.quickActions = data.quickActions
    }
  } catch {
    // Silently fail — panels will show defaults
  } finally {
    summaryLoading.value = false
  }
}

onMounted(() => {
  initCharts()
  void loadDashboard()
  void fetchSummary()
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeCharts)
})

const loadDashboard = async () => {
  const { byCategory, byStatus } = await fetchMetrics()
  updateStatusChart(byStatus)
  updateCategoryChart(byCategory)
  await fetchLifecycleData()
  updateMaintenanceChart(lifecycle)
}
</script>

<style scoped>
.dashboard { padding: 20px; }
.mt-20 { margin-top: 20px; }

.section-title {
  font-size: 16px; font-weight: 600; color: #303133;
  display: flex; align-items: center; gap: 8px;
  padding-bottom: 4px; border-bottom: 2px solid #f0f0f0;
}
.section-icon { color: #409EFF; }

/* --- Panel styles --- */
.dashboard-panel {
  height: 100%;
  min-height: 200px;
}
.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 15px;
}
.panel-icon { font-size: 18px; }
.tasks-icon { color: #E6A23C; }
.alerts-icon { color: #F56C6C; }
.actions-icon { color: #409EFF; }

/* --- Task items --- */
.task-items {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.task-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 8px;
  transition: background-color 0.2s;
}
.task-item.clickable {
  cursor: pointer;
}
.task-item.clickable:hover {
  background-color: #f5f7fa;
}
.task-count {
  font-size: 24px;
  font-weight: 700;
  min-width: 40px;
  text-align: center;
}
.task-count.primary { color: #409EFF; }
.task-count.warning { color: #E6A23C; }
.task-count.danger { color: #F56C6C; }
.task-label {
  font-size: 14px;
  color: #606266;
}

/* --- Alert items --- */
.empty-hint {
  text-align: center;
  color: #909399;
  padding: 20px 0;
}
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.alert-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
}
.alert-item:hover {
  transform: translateX(4px);
}
.alert-warning {
  background-color: #fdf6ec;
  color: #E6A23C;
}
.alert-info {
  background-color: #ecf5ff;
  color: #409EFF;
}
.alert-icon { font-size: 16px; flex-shrink: 0; }
.alert-text { flex: 1; }

/* --- Quick actions --- */
.quick-actions-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.quick-action-btn {
  height: 48px;
  font-size: 13px;
  border-radius: 8px;
}
.action-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
