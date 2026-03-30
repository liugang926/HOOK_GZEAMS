import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ClosedLoopOverview } from '@/api/closedLoopMetrics'
import {
  deleteClosedLoopDashboardSnapshot,
  readClosedLoopDashboardSnapshots,
  saveClosedLoopDashboardSnapshot,
} from '@/platform/reports/closedLoopDashboardSnapshots'

const storageState = new Map<string, string>()

const buildOverview = (): ClosedLoopOverview => ({
  window: {
    key: '30d',
    days: 30,
    startDate: '2026-03-01',
    endDate: '2026-03-30',
  },
  metricContract: {},
  summary: {
    openedCount: 10,
    closedCount: 8,
    backlogCount: 2,
    overdueCount: 1,
    autoClosedCount: 3,
    exceptionBacklogCount: 1,
    avgCycleHours: 12.5,
    closureRate: 80,
    overdueRate: 50,
    automaticClosureRate: 37.5,
  },
  trend: {
    bucket: 'day',
    points: [
      { date: '2026-03-29', opened: 1, closed: 1 },
    ],
  },
  workflowSla: {
    activeTaskCount: 2,
    overdueTaskCount: 1,
    escalatedTaskCount: 0,
    bottleneckCount: 1,
  },
  ownerRankings: [],
  departmentRankings: [],
  objectsCovered: [],
})

describe('closedLoopDashboardSnapshots', () => {
  beforeEach(() => {
    storageState.clear()
    vi.mocked(localStorage.getItem).mockImplementation((key: string) => storageState.get(key) ?? null)
    vi.mocked(localStorage.setItem).mockImplementation((key: string, value: string) => {
      storageState.set(key, String(value))
    })
    vi.mocked(localStorage.removeItem).mockImplementation((key: string) => {
      storageState.delete(key)
    })
  })

  it('saves and reads snapshots in reverse chronological order', () => {
    saveClosedLoopDashboardSnapshot({
      label: 'Snapshot A',
      filters: {
        window: '30d',
        organizationId: 'org-1',
        organizationName: 'Metrics Org',
        objectCodes: ['InventoryTask'],
      },
      payload: {
        overview: buildOverview(),
        byObjectItems: [],
        queues: [],
        bottlenecks: [],
      },
    })

    saveClosedLoopDashboardSnapshot({
      label: 'Snapshot B',
      filters: {
        window: '7d',
        organizationId: 'org-2',
        organizationName: 'Branch Org',
        objectCodes: ['FinanceVoucher'],
      },
      payload: {
        overview: buildOverview(),
        byObjectItems: [],
        queues: [],
        bottlenecks: [],
      },
    })

    const snapshots = readClosedLoopDashboardSnapshots()

    expect(snapshots).toHaveLength(2)
    expect(snapshots[0].label).toBe('Snapshot B')
    expect(snapshots[1].label).toBe('Snapshot A')
    expect(snapshots[0].filters.objectCodes).toEqual(['FinanceVoucher'])
  })

  it('deletes snapshots by id', () => {
    const snapshot = saveClosedLoopDashboardSnapshot({
      label: 'Snapshot A',
      filters: {
        window: '30d',
        objectCodes: [],
      },
      payload: {
        overview: buildOverview(),
        byObjectItems: [],
        queues: [],
        bottlenecks: [],
      },
    })

    expect(readClosedLoopDashboardSnapshots()).toHaveLength(1)

    deleteClosedLoopDashboardSnapshot(snapshot.id)

    expect(readClosedLoopDashboardSnapshots()).toEqual([])
  })
})
