import { describe, expect, it } from 'vitest'

import {
  createDashboardCategoryChartOption,
  createDashboardCategoryChartUpdate,
  createDashboardMaintenanceChartOption,
  createDashboardMaintenanceChartUpdate,
  createDashboardStatusChartOption,
  createDashboardStatusChartUpdate,
} from './dashboardChartModel'

const t = (key: string) => key

describe('dashboardChartModel', () => {
  it('creates base chart options with translated series names', () => {
    expect(createDashboardStatusChartOption(t).series[0].name).toBe('dashboard.charts.assetStatus')
    expect(createDashboardCategoryChartOption(t).series[0].name).toBe('dashboard.charts.quantity')
    expect(createDashboardMaintenanceChartOption(t).series[0].name).toBe('dashboard.lifecycle.maintenanceStatusChart')
  })

  it('creates chart update payloads from metrics and lifecycle state', () => {
    expect(createDashboardCategoryChartUpdate({ Laptop: 2, Printer: 1 })).toEqual({
      xAxis: [{ data: ['Laptop', 'Printer'] }],
      series: [{ data: [2, 1] }]
    })

    expect(createDashboardStatusChartUpdate({ idle: 3 }, t).series[0].data).toEqual([
      { value: 3, name: 'assets.status.idle', itemStyle: { color: '#67C23A' } }
    ])

    expect(createDashboardMaintenanceChartUpdate({
      activeMaintenance: 2,
      overdueTasks: 1,
      pendingPurchases: 0,
      pendingDisposals: 0,
    }, t).series[0].data).toHaveLength(2)
  })
})
