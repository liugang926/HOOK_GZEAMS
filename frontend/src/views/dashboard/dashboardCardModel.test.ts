import { describe, expect, it } from 'vitest'

import {
  buildDashboardLifecycleCards,
  buildDashboardMetricCards,
} from './dashboardCardModel'

const t = (key: string) => key

describe('dashboardCardModel', () => {
  it('builds metric cards from dashboard state', () => {
    const cards = buildDashboardMetricCards({
      assetCount: 10,
      assetValue: '12,345',
      warningCount: 3,
      pendingApproval: 2,
    }, t)

    expect(cards[0]).toMatchObject({
      id: 'assetCount',
      label: 'dashboard.metrics.assetCount',
      value: 10,
    })
    expect(cards[1].value).toBe('common.units.yuan 12,345')
    expect(cards[2].valueClass).toBe('text-danger')
  })

  it('builds lifecycle cards with loading-safe values and routes', () => {
    const loadingCards = buildDashboardLifecycleCards({
      pendingPurchases: 5,
      activeMaintenance: 2,
      overdueTasks: 1,
      pendingDisposals: 4,
    }, true, t)
    const loadedCards = buildDashboardLifecycleCards({
      pendingPurchases: 5,
      activeMaintenance: 2,
      overdueTasks: 1,
      pendingDisposals: 4,
    }, false, t)

    expect(loadingCards[0].value).toBe('-')
    expect(loadedCards[2]).toMatchObject({
      route: '/objects/MaintenanceTask',
      icon: 'task',
      value: '1',
    })
  })
})
