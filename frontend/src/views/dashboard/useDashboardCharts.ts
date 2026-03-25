import { onUnmounted, ref } from 'vue'

import { init, type EChartsType } from '@/utils/echarts'

import {
  createDashboardCategoryChartOption,
  createDashboardCategoryChartUpdate,
  createDashboardMaintenanceChartOption,
  createDashboardMaintenanceChartUpdate,
  createDashboardStatusChartOption,
  createDashboardStatusChartUpdate,
} from './dashboardChartModel'
import type { DashboardLifecycleState } from './dashboardModel'

type TranslationFn = (key: string) => string

export const useDashboardCharts = (t: TranslationFn) => {
  const statusChartRef = ref<HTMLElement | null>(null)
  const categoryChartRef = ref<HTMLElement | null>(null)
  const maintenanceChartRef = ref<HTMLElement | null>(null)

  let statusChart: EChartsType | null = null
  let categoryChart: EChartsType | null = null
  let maintenanceChart: EChartsType | null = null

  const initCharts = () => {
    if (statusChartRef.value) {
      statusChart = init(statusChartRef.value)
      statusChart.setOption(createDashboardStatusChartOption(t))
    }
    if (categoryChartRef.value) {
      categoryChart = init(categoryChartRef.value)
      categoryChart.setOption(createDashboardCategoryChartOption(t))
    }
    if (maintenanceChartRef.value) {
      maintenanceChart = init(maintenanceChartRef.value)
      maintenanceChart.setOption(createDashboardMaintenanceChartOption(t))
    }
  }

  const updateStatusChart = (data: Record<string, number>) => {
    statusChart?.setOption(createDashboardStatusChartUpdate(data, t))
  }

  const updateCategoryChart = (data: Record<string, number>) => {
    categoryChart?.setOption(createDashboardCategoryChartUpdate(data))
  }

  const updateMaintenanceChart = (lifecycle: DashboardLifecycleState) => {
    maintenanceChart?.setOption(createDashboardMaintenanceChartUpdate(lifecycle, t))
  }

  const resizeCharts = () => {
    statusChart?.resize()
    categoryChart?.resize()
    maintenanceChart?.resize()
  }

  const disposeCharts = () => {
    statusChart?.dispose()
    categoryChart?.dispose()
    maintenanceChart?.dispose()
    statusChart = null
    categoryChart = null
    maintenanceChart = null
  }

  onUnmounted(() => {
    disposeCharts()
  })

  return {
    categoryChartRef,
    initCharts,
    maintenanceChartRef,
    resizeCharts,
    statusChartRef,
    updateCategoryChart,
    updateMaintenanceChart,
    updateStatusChart,
  }
}
