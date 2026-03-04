<template>
  <div class="dashboard">
    <!-- ── Asset Overview Row ─────────────────────────────────── -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="data-card"
        >
          <div class="card-header">
            <span>{{ $t('dashboard.metrics.assetCount') }}</span>
            <el-tag>{{ $t('common.units.piece') }}</el-tag>
          </div>
          <div class="card-value">
            {{ metrics.assetCount }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="data-card"
        >
          <div class="card-header">
            <span>{{ $t('dashboard.metrics.assetValue') }}</span>
            <el-tag type="success">
              {{ $t('common.units.yuan') }}
            </el-tag>
          </div>
          <div class="card-value">
            ¥ {{ metrics.assetValue }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="data-card"
        >
          <div class="card-header">
            <span>{{ $t('dashboard.metrics.warningCount') }}</span>
            <el-tag type="danger">
              {{ $t('common.units.item') }}
            </el-tag>
          </div>
          <div class="card-value text-danger">
            {{ metrics.warningCount }}
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="data-card"
        >
          <div class="card-header">
            <span>{{ $t('dashboard.metrics.pendingApproval') }}</span>
            <el-tag type="warning">
              {{ $t('common.units.pending') }}
            </el-tag>
          </div>
          <div class="card-value">
            {{ metrics.pendingApproval }}
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ── Asset Charts Row ───────────────────────────────────── -->
    <el-row
      :gutter="20"
      class="mt-20"
    >
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>{{ $t('dashboard.charts.statusDistribution') }}</span>
          </template>
          <div
            ref="statusChartRef"
            style="height: 300px"
          />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>{{ $t('dashboard.charts.categoryStatistics') }}</span>
          </template>
          <div
            ref="categoryChartRef"
            style="height: 300px"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- ── Lifecycle Section ─────────────────────────────────── -->
    <div class="section-title mt-20">
      <el-icon class="section-icon">
        <Refresh />
      </el-icon>
      {{ $t('dashboard.lifecycle.title') }}
    </div>

    <!-- ── Lifecycle Stat Cards ──────────────────────────────── -->
    <el-row
      :gutter="20"
      class="mt-12"
    >
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="data-card lifecycle-card clickable"
          @click="router.push('/assets/lifecycle/purchase-requests')"
        >
          <div class="card-header">
            <span>{{ $t('dashboard.lifecycle.pendingPurchases') }}</span>
            <el-icon
              class="card-icon"
              color="#409eff"
            >
              <ShoppingCart />
            </el-icon>
          </div>
          <div class="card-value text-primary">
            <span v-if="lifecycleLoading">…</span>
            <span v-else>{{ lifecycle.pendingPurchases }}</span>
          </div>
          <div class="card-footer">
            {{ $t('dashboard.lifecycle.viewAll') }} →
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="data-card lifecycle-card clickable"
          @click="router.push('/assets/lifecycle/maintenance')"
        >
          <div class="card-header">
            <span>{{ $t('dashboard.lifecycle.activeMaintenance') }}</span>
            <el-icon
              class="card-icon"
              color="#e6a23c"
            >
              <Tools />
            </el-icon>
          </div>
          <div class="card-value text-warning">
            <span v-if="lifecycleLoading">…</span>
            <span v-else>{{ lifecycle.activeMaintenance }}</span>
          </div>
          <div class="card-footer">
            {{ $t('dashboard.lifecycle.viewAll') }} →
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="data-card lifecycle-card clickable"
          @click="router.push('/assets/lifecycle/maintenance-tasks')"
        >
          <div class="card-header">
            <span>{{ $t('dashboard.lifecycle.overdueTasks') }}</span>
            <el-icon
              class="card-icon"
              color="#f56c6c"
            >
              <Warning />
            </el-icon>
          </div>
          <div class="card-value text-danger">
            <span v-if="lifecycleLoading">…</span>
            <span v-else>{{ lifecycle.overdueTasks }}</span>
          </div>
          <div class="card-footer">
            {{ $t('dashboard.lifecycle.viewAll') }} →
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card
          shadow="hover"
          class="data-card lifecycle-card clickable"
          @click="router.push('/assets/lifecycle/disposal-requests')"
        >
          <div class="card-header">
            <span>{{ $t('dashboard.lifecycle.pendingDisposals') }}</span>
            <el-icon
              class="card-icon"
              color="#909399"
            >
              <Delete />
            </el-icon>
          </div>
          <div class="card-value">
            <span v-if="lifecycleLoading">…</span>
            <span v-else>{{ lifecycle.pendingDisposals }}</span>
          </div>
          <div class="card-footer">
            {{ $t('dashboard.lifecycle.viewAll') }} →
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- ── Lifecycle Charts Row ─────────────────────────────── -->
    <el-row
      :gutter="20"
      class="mt-20"
    >
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>{{ $t('dashboard.lifecycle.maintenanceStatusChart') }}</span>
          </template>
          <div
            ref="maintenanceChartRef"
            style="height: 300px"
          />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <span>{{ $t('dashboard.lifecycle.recentActivity') }}</span>
          </template>
          <el-empty
            v-if="!lifecycleLoading && recentActivities.length === 0"
            :description="$t('common.messages.noData')"
            :image-size="60"
          />
          <el-timeline
            v-else
            class="activity-timeline"
          >
            <el-timeline-item
              v-for="item in recentActivities"
              :key="item.id"
              :type="item.type"
              :timestamp="item.time"
              placement="top"
              size="small"
            >
              <router-link
                :to="item.url"
                class="activity-link"
              >
                {{ item.title }}
              </router-link>
              <div class="activity-sub">
                {{ item.sub }}
              </div>
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ShoppingCart, Tools, Warning, Delete, Refresh } from '@element-plus/icons-vue'
import { assetApi } from '@/api/assets'
import { workflowNodeApi } from '@/api/workflow'
import { purchaseRequestApi, maintenanceApi, maintenanceTaskApi, disposalRequestApi } from '@/api/lifecycle'
import { init, type EChartsType } from '@/utils/echarts'

const { t } = useI18n()
const router = useRouter()

// ── Asset metrics ────────────────────────────────────────────────────────
const metrics = reactive({
  assetCount: 0,
  assetValue: '0',
  warningCount: 0,
  pendingApproval: 0
})

// ── Lifecycle metrics ─────────────────────────────────────────────────────
const lifecycleLoading = ref(true)
const lifecycle = reactive({
  pendingPurchases: 0,
  activeMaintenance: 0,
  overdueTasks: 0,
  pendingDisposals: 0
})

interface ActivityItem {
  id: string
  type: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  title: string
  sub: string
  time: string
  url: string
}
const recentActivities = ref<ActivityItem[]>([])

// ── Chart refs ───────────────────────────────────────────────────────────
const statusChartRef = ref<HTMLElement | null>(null)
const categoryChartRef = ref<HTMLElement | null>(null)
const maintenanceChartRef = ref<HTMLElement | null>(null)
let statusChart: EChartsType | null = null
let categoryChart: EChartsType | null = null
let maintenanceChart: EChartsType | null = null

onMounted(() => {
  initCharts()
  fetchData()
  fetchLifecycleData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  statusChart?.dispose()
  categoryChart?.dispose()
  maintenanceChart?.dispose()
})

const handleResize = () => {
  statusChart?.resize()
  categoryChart?.resize()
  maintenanceChart?.resize()
}

// ── Asset data ───────────────────────────────────────────────────────────
const fetchData = async () => {
  try {
    const stats = await assetApi.statistics()
    if (stats) {
      metrics.assetCount = stats.total || 0
      metrics.assetValue = (stats.total_value || 0).toLocaleString()
      updateStatusChart(stats.by_status || {})
      updateCategoryChart(stats.by_category || {})
    }
    const tasks = await workflowNodeApi.getMyTasks({ page: 1, pageSize: 1, status: 'pending' })
    metrics.pendingApproval = tasks?.count || 0
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  }
}

// ── Lifecycle data ────────────────────────────────────────────────────────
const fetchLifecycleData = async () => {
  lifecycleLoading.value = true
  const activities: ActivityItem[] = []

  await Promise.allSettled([
    (async () => {
      const res = await purchaseRequestApi.list({ status: 'submitted', pageSize: 5 }) as any
      lifecycle.pendingPurchases = res?.count ?? 0
      ;(res?.results ?? []).slice(0, 3).forEach((r: any) => {
        activities.push({
          id: `pr-${r.id}`, type: 'primary',
          title: `${t('assets.lifecycle.purchaseRequest.title')}：${r.requestNo || r.request_no}`,
          sub: t('assets.lifecycle.purchaseRequest.status.submitted'),
          time: r.createdAt || r.created_at || '',
          url: `/assets/lifecycle/purchase-requests/${r.id}`
        })
      })
    })(),

    (async () => {
      const [rep, proc] = await Promise.all([
        maintenanceApi.list({ status: 'reported', pageSize: 1 }) as any,
        maintenanceApi.list({ status: 'processing', pageSize: 3 }) as any
      ])
      lifecycle.activeMaintenance = (rep?.count ?? 0) + (proc?.count ?? 0)
      ;(proc?.results ?? []).slice(0, 2).forEach((r: any) => {
        activities.push({
          id: `mt-${r.id}`, type: 'warning',
          title: `${t('assets.lifecycle.maintenance.title')}：${r.maintenanceNo || r.maintenance_no}`,
          sub: t('assets.lifecycle.maintenance.status.processing'),
          time: r.createdAt || r.created_at || '',
          url: `/assets/lifecycle/maintenance/${r.id}`
        })
      })
    })(),

    (async () => {
      const res = await maintenanceTaskApi.overdue() as any
      const arr = Array.isArray(res) ? res : (res?.data ?? [])
      lifecycle.overdueTasks = arr.length
    })(),

    (async () => {
      const res = await disposalRequestApi.list({ status: 'submitted', pageSize: 5 }) as any
      lifecycle.pendingDisposals = res?.count ?? 0
      ;(res?.results ?? []).slice(0, 2).forEach((r: any) => {
        activities.push({
          id: `dr-${r.id}`, type: 'danger',
          title: `${t('assets.lifecycle.disposalRequest.title')}：${r.requestNo || r.request_no}`,
          sub: t('assets.lifecycle.disposalRequest.status.submitted'),
          time: r.createdAt || r.created_at || '',
          url: `/assets/lifecycle/disposal-requests/${r.id}`
        })
      })
    })()
  ])

  activities.sort((a, b) => (b.time > a.time ? 1 : -1))
  recentActivities.value = activities.slice(0, 6)
  updateMaintenanceChart()
  lifecycleLoading.value = false
}

// ── Chart updates ─────────────────────────────────────────────────────────
const updateStatusChart = (data: Record<string, number>) => {
  if (!statusChart) return
  const statusMap: Record<string, { label: string; color: string }> = {
    idle: { label: t('assets.status.idle'), color: '#67C23A' },
    in_use: { label: t('assets.status.inUse'), color: '#409EFF' },
    maintenance: { label: t('assets.status.maintenance'), color: '#E6A23C' },
    scrapped: { label: t('assets.status.scrapped'), color: '#909399' },
    borrowed: { label: t('assets.status.borrowed'), color: '#6f7ad3' },
    disposed: { label: t('assets.status.disposed'), color: '#F56C6C' }
  }
  statusChart.setOption({
    series: [{
      data: Object.entries(data).map(([key, value]) => ({
        value,
        name: statusMap[key]?.label || key,
        itemStyle: { color: statusMap[key]?.color }
      }))
    }]
  })
}

const updateCategoryChart = (data: Record<string, number>) => {
  if (!categoryChart) return
  categoryChart.setOption({
    xAxis: [{ data: Object.keys(data) }],
    series: [{ data: Object.values(data) }]
  })
}

const updateMaintenanceChart = () => {
  if (!maintenanceChart) return
  const seriesData = [
    { value: lifecycle.activeMaintenance, name: t('dashboard.lifecycle.activeMaintenance'), itemStyle: { color: '#E6A23C' } },
    { value: lifecycle.overdueTasks, name: t('dashboard.lifecycle.overdueTasks'), itemStyle: { color: '#F56C6C' } },
    { value: lifecycle.pendingPurchases, name: t('dashboard.lifecycle.pendingPurchases'), itemStyle: { color: '#409EFF' } },
    { value: lifecycle.pendingDisposals, name: t('dashboard.lifecycle.pendingDisposals'), itemStyle: { color: '#909399' } }
  ].filter(d => d.value > 0)
  maintenanceChart.setOption({ series: [{ data: seriesData }] })
}

// ── Chart init ────────────────────────────────────────────────────────────
const initCharts = () => {
  if (statusChartRef.value) {
    statusChart = init(statusChartRef.value)
    statusChart.setOption({
      tooltip: { trigger: 'item' },
      legend: { top: '5%', left: 'center' },
      series: [{
        name: t('dashboard.charts.assetStatus'), type: 'pie', radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 20, fontWeight: 'bold' } },
        data: []
      }]
    })
  }
  if (categoryChartRef.value) {
    categoryChart = init(categoryChartRef.value)
    categoryChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: [{ type: 'category', data: [], axisTick: { alignWithLabel: true } }],
      yAxis: [{ type: 'value' }],
      series: [{
        name: t('dashboard.charts.quantity'), type: 'bar', barWidth: '60%',
        data: [], itemStyle: { color: '#409EFF' }
      }]
    })
  }
  if (maintenanceChartRef.value) {
    maintenanceChart = init(maintenanceChartRef.value)
    maintenanceChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { top: '5%', left: 'center' },
      series: [{
        name: t('dashboard.lifecycle.maintenanceStatusChart'), type: 'pie',
        radius: ['40%', '70%'], avoidLabelOverlap: false,
        itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
        data: []
      }]
    })
  }
}
</script>

<style scoped>
.dashboard { padding: 20px; }
.mt-20 { margin-top: 20px; }
.mt-12 { margin-top: 12px; }

.data-card { height: 120px; display: flex; flex-direction: column; justify-content: center; }
.lifecycle-card { height: 130px; }
.clickable { cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; }
.clickable:hover { transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.12) !important; }

.card-header { display: flex; justify-content: space-between; align-items: center; font-size: 14px; color: #909399; }
.card-icon { font-size: 20px; }
.card-value { font-size: 28px; font-weight: bold; margin-top: 8px; color: #303133; }
.card-footer { font-size: 12px; color: #c0c4cc; margin-top: 4px; }

.text-danger { color: #F56C6C; }
.text-warning { color: #E6A23C; }
.text-primary { color: #409EFF; }

.section-title {
  font-size: 16px; font-weight: 600; color: #303133;
  display: flex; align-items: center; gap: 8px;
  padding-bottom: 4px; border-bottom: 2px solid #f0f0f0;
}
.section-icon { color: #409EFF; }

.activity-timeline { padding: 8px 16px; max-height: 270px; overflow-y: auto; }
.activity-link { font-size: 13px; color: #409EFF; text-decoration: none; }
.activity-link:hover { text-decoration: underline; }
.activity-sub { font-size: 12px; color: #909399; margin-top: 2px; }
</style>
