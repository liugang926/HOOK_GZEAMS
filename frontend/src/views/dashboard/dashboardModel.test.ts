import { describe, expect, it } from 'vitest'

import {
  buildDashboardMaintenanceSeries,
  buildDashboardStatusSeries,
  buildDisposalActivities,
  buildMaintenanceActivities,
  buildPurchaseRequestActivities,
  normalizeOverdueTaskCount,
  sortDashboardActivities,
} from './dashboardModel'

const t = (key: string) => key

describe('dashboardModel', () => {
  it('builds lifecycle activity links from domain records', () => {
    expect(buildPurchaseRequestActivities([{ id: '1', request_no: 'PR-001', created_at: '2026-03-01' }], t)[0]).toMatchObject({
      id: 'pr-1',
      title: 'assets.lifecycle.purchaseRequest.title PR-001',
      url: '/objects/PurchaseRequest/1',
    })

    expect(buildMaintenanceActivities([{ id: '2', maintenanceNo: 'MO-002', createdAt: '2026-03-02' }], t)[0]).toMatchObject({
      id: 'mt-2',
      title: 'assets.lifecycle.maintenance.title MO-002',
      url: '/objects/Maintenance/2',
    })

    expect(buildDisposalActivities([{ id: '3', request_no: 'DR-003', created_at: '2026-03-03' }], t)[0]).toMatchObject({
      id: 'dr-3',
      title: 'assets.lifecycle.disposalRequest.title DR-003',
      url: '/objects/DisposalRequest/3',
    })
  })

  it('sorts recent activities in reverse time order and limits the list', () => {
    const activities = sortDashboardActivities([
      { id: 'a', type: 'info', title: 'A', sub: '', time: '2026-03-01', url: '/a' },
      { id: 'c', type: 'info', title: 'C', sub: '', time: '2026-03-03', url: '/c' },
      { id: 'b', type: 'info', title: 'B', sub: '', time: '2026-03-02', url: '/b' },
    ], 2)

    expect(activities.map((item) => item.id)).toEqual(['c', 'b'])
  })

  it('normalizes overdue task counts from array and wrapped payloads', () => {
    expect(normalizeOverdueTaskCount([{ id: 1 }, { id: 2 }])).toBe(2)
    expect(normalizeOverdueTaskCount({ data: [{ id: 1 }] })).toBe(1)
    expect(normalizeOverdueTaskCount({ results: [{ id: 1 }] })).toBe(0)
  })

  it('builds chart series from lifecycle and status summaries', () => {
    expect(buildDashboardMaintenanceSeries({
      activeMaintenance: 3,
      overdueTasks: 0,
      pendingPurchases: 2,
      pendingDisposals: 1,
    }, t).map((item) => item.value)).toEqual([3, 2, 1])

    expect(buildDashboardStatusSeries({ idle: 4, disposed: 1 }, t)).toEqual([
      { value: 4, name: 'assets.status.idle', itemStyle: { color: '#67C23A' } },
      { value: 1, name: 'assets.status.disposed', itemStyle: { color: '#F56C6C' } },
    ])
  })
})
