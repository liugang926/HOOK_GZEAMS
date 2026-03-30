import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ClosedLoopOverview } from '@/api/closedLoopMetrics'
import { exportClosedLoopDashboardWorkbook } from '@/platform/reports/closedLoopDashboardExport'

const {
  bookNewMock,
  aoaToSheetMock,
  bookAppendSheetMock,
  writeFileMock,
} = vi.hoisted(() => ({
  bookNewMock: vi.fn(() => ({ sheets: [] })),
  aoaToSheetMock: vi.fn(() => ({})),
  bookAppendSheetMock: vi.fn(),
  writeFileMock: vi.fn(),
}))

vi.mock('@/utils/xlsxLoader', () => ({
  loadXlsx: async () => ({
    utils: {
      book_new: bookNewMock,
      aoa_to_sheet: aoaToSheetMock,
      book_append_sheet: bookAppendSheetMock,
    },
    writeFile: writeFileMock,
  }),
}))

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
    points: [{ date: '2026-03-29', opened: 1, closed: 1 }],
  },
  workflowSla: {
    activeTaskCount: 2,
    overdueTaskCount: 1,
    escalatedTaskCount: 0,
    bottleneckCount: 1,
  },
  ownerRankings: [
    {
      userId: 'user-1',
      username: 'metrics_user',
      displayName: 'Metrics User',
      openCount: 2,
      overdueCount: 1,
      topSource: 'workflow_tasks',
      sourceCounts: { workflow_tasks: 2 },
    },
  ],
  departmentRankings: [
    {
      departmentId: 'dept-1',
      departmentName: 'Operations',
      openCount: 3,
      overdueCount: 1,
      topSource: 'inventory_differences',
      sourceCounts: { inventory_differences: 3 },
    },
  ],
  objectsCovered: [],
})

describe('closedLoopDashboardExport', () => {
  beforeEach(() => {
    bookNewMock.mockClear()
    aoaToSheetMock.mockClear()
    bookAppendSheetMock.mockClear()
    writeFileMock.mockClear()
  })

  it('builds a workbook with the expected sheet set', async () => {
    await exportClosedLoopDashboardWorkbook({
      filename: 'Metrics Org / 30d',
      overview: buildOverview(),
      byObjectItems: [],
      queues: [],
      bottlenecks: [],
    })

    expect(bookNewMock).toHaveBeenCalled()
    expect(aoaToSheetMock).toHaveBeenCalledTimes(7)
    expect(bookAppendSheetMock).toHaveBeenNthCalledWith(1, expect.any(Object), expect.any(Object), 'Overview')
    expect(bookAppendSheetMock).toHaveBeenNthCalledWith(2, expect.any(Object), expect.any(Object), 'Trend')
    expect(bookAppendSheetMock).toHaveBeenNthCalledWith(7, expect.any(Object), expect.any(Object), 'Bottlenecks')
    expect(writeFileMock).toHaveBeenCalledWith(expect.any(Object), 'Metrics Org _ 30d.xlsx')
  })
})
