import {
  buildDashboardMaintenanceSeries,
  buildDashboardStatusSeries,
  type DashboardLifecycleState,
} from './dashboardModel'

type TranslationFn = (key: string) => string

export const createDashboardStatusChartOption = (t: TranslationFn) => ({
  tooltip: { trigger: 'item' },
  legend: { top: '5%', left: 'center' },
  series: [{
    name: t('dashboard.charts.assetStatus'),
    type: 'pie',
    radius: ['40%', '70%'],
    avoidLabelOverlap: false,
    itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
    label: { show: false, position: 'center' },
    emphasis: { label: { show: true, fontSize: 20, fontWeight: 'bold' } },
    data: [],
  }]
})

export const createDashboardCategoryChartOption = (t: TranslationFn) => ({
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: [{ type: 'category', data: [], axisTick: { alignWithLabel: true } }],
  yAxis: [{ type: 'value' }],
  series: [{
    name: t('dashboard.charts.quantity'),
    type: 'bar',
    barWidth: '60%',
    data: [],
    itemStyle: { color: '#409EFF' },
  }]
})

export const createDashboardMaintenanceChartOption = (t: TranslationFn) => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { top: '5%', left: 'center' },
  series: [{
    name: t('dashboard.lifecycle.maintenanceStatusChart'),
    type: 'pie',
    radius: ['40%', '70%'],
    avoidLabelOverlap: false,
    itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
    label: { show: false, position: 'center' },
    emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
    data: [],
  }]
})

export const createDashboardStatusChartUpdate = (
  data: Record<string, number>,
  t: TranslationFn
) => ({
  series: [{
    data: buildDashboardStatusSeries(data, t)
  }]
})

export const createDashboardCategoryChartUpdate = (data: Record<string, number>) => ({
  xAxis: [{ data: Object.keys(data) }],
  series: [{ data: Object.values(data) }]
})

export const createDashboardMaintenanceChartUpdate = (
  lifecycle: DashboardLifecycleState,
  t: TranslationFn
) => ({
  series: [{
    data: buildDashboardMaintenanceSeries(lifecycle, t)
  }]
})
