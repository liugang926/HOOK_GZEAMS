<template>
  <div class="dashboard">
    <DashboardMetricGrid :cards="metricCards" />

    <el-row
      :gutter="20"
      class="mt-20"
    >
      <el-col :span="12">
        <DashboardChartCard
          :set-chart-ref="setStatusChartRef"
          :title="$t('dashboard.charts.statusDistribution')"
        />
      </el-col>
      <el-col :span="12">
        <DashboardChartCard
          :set-chart-ref="setCategoryChartRef"
          :title="$t('dashboard.charts.categoryStatistics')"
        />
      </el-col>
    </el-row>

    <div class="section-title mt-20">
      <el-icon class="section-icon">
        <Refresh />
      </el-icon>
      {{ $t('dashboard.lifecycle.title') }}
    </div>

    <DashboardLifecycleCards
      :cards="lifecycleCards"
      :view-all-label="$t('dashboard.lifecycle.viewAll')"
      @navigate="router.push($event)"
    />

    <el-row
      :gutter="20"
      class="mt-20"
    >
      <el-col :span="12">
        <DashboardChartCard
          :set-chart-ref="setMaintenanceChartRef"
          :title="$t('dashboard.lifecycle.maintenanceStatusChart')"
        />
      </el-col>
      <el-col :span="12">
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
import { computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'

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

onMounted(() => {
  initCharts()
  void loadDashboard()
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
</style>
