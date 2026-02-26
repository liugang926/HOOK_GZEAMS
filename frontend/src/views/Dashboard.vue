<template>
  <div class="dashboard">
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

    <el-row
      :gutter="20"
      class="mt-20"
    >
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div 
              class="clearfix"
            >
              <span>{{ $t('dashboard.charts.statusDistribution') }}</span>
            </div>
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
            <div 
              class="clearfix"
            >
              <span>{{ $t('dashboard.charts.categoryStatistics') }}</span>
            </div>
          </template>
          <div
            ref="categoryChartRef"
            style="height: 300px"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { assetApi } from '@/api/assets'
import { workflowNodeApi } from '@/api/workflow'

const { t } = useI18n()

const metrics = reactive({
    assetCount: 0,
    assetValue: '0',
    warningCount: 0,
    pendingApproval: 0
})

const statusChartRef = ref<HTMLElement | null>(null)
const categoryChartRef = ref<HTMLElement | null>(null)
let statusChart: any = null
let categoryChart: any = null

onMounted(() => {
    initCharts()
    fetchData()
    window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    statusChart?.dispose()
    categoryChart?.dispose()
})

const handleResize = () => {
    statusChart?.resize()
    categoryChart?.resize()
}

const fetchData = async () => {
    try {
        // Fetch Asset Statistics
        const stats = await assetApi.statistics()
        if (stats) {
            metrics.assetCount = stats.total || 0
            metrics.assetValue = (stats.total_value || 0).toLocaleString()

            // Update Status Chart
            updateStatusChart(stats.by_status || {})

            // Update Category Chart
            updateCategoryChart(stats.by_category || {})
        }

        // Fetch Pending Approvals
        const tasks = await workflowNodeApi.getMyTasks({ page: 1, pageSize: 1, status: 'pending' })
        metrics.pendingApproval = tasks?.count || 0
    } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
        // Set default values on error
        metrics.assetCount = 0
        metrics.assetValue = '0'
        metrics.pendingApproval = 0
    }
}

const updateStatusChart = (data: Record<string, number>) => {
    if (!statusChart) return

    // Map status to translated labels and colors
    const statusMap: Record<string, { label: string, color: string }> = {
        'idle': { label: t('assets.status.idle'), color: '#67C23A' },
        'in_use': { label: t('assets.status.inUse'), color: '#409EFF' },
        'maintenance': { label: t('assets.status.maintenance'), color: '#E6A23C' },
        'scrapped': { label: t('assets.status.scrapped'), color: '#909399' },
        'borrowed': { label: t('assets.status.borrowed'), color: '#409EFF' },
        'disposed': { label: t('assets.status.disposed'), color: '#909399' }
    }

    const chartData = Object.entries(data).map(([key, value]) => ({
        value,
        name: statusMap[key]?.label || key,
        itemStyle: { color: statusMap[key]?.color }
    }))

    statusChart.setOption({
        series: [{
            data: chartData
        }]
    })
}

const updateCategoryChart = (data: Record<string, number>) => {
    if (!categoryChart) return

    const categories = Object.keys(data)
    const values = Object.values(data)

    categoryChart.setOption({
        xAxis: [{ data: categories }],
        series: [{
            data: values
        }]
    })
}

const initCharts = () => {
    if (statusChartRef.value) {
        statusChart = echarts.init(statusChartRef.value)
        statusChart.setOption({
            tooltip: { trigger: 'item' },
            legend: { top: '5%', left: 'center' },
            series: [{
                name: t('dashboard.charts.assetStatus'),
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
                label: { show: false, position: 'center' },
                emphasis: {
                    label: { show: true, fontSize: 20, fontWeight: 'bold' }
                },
                data: [] // Initial empty data
            }]
        })
    }

    if (categoryChartRef.value) {
        categoryChart = echarts.init(categoryChartRef.value)
        categoryChart.setOption({
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
            grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
            xAxis: [{ type: 'category', data: [], axisTick: { alignWithLabel: true } }],
            yAxis: [{ type: 'value' }],
            series: [{
                name: t('dashboard.charts.quantity'),
                type: 'bar',
                barWidth: '60%',
                data: [],
                itemStyle: { color: '#409EFF' }
            }]
        })
    }
}
</script>

<style scoped>
.dashboard { padding: 20px; }
.data-card {
    height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    color: #909399;
}
.card-value {
    font-size: 28px;
    font-weight: bold;
    margin-top: 10px;
    color: #303133;
}
.text-danger { color: #F56C6C; }
.mt-20 { margin-top: 20px; }
</style>
