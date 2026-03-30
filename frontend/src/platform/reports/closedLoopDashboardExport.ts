import type {
  ClosedLoopBottleneckItem,
  ClosedLoopByObjectItem,
  ClosedLoopOverview,
  ClosedLoopQueueItem,
} from '@/api/closedLoopMetrics'
import { loadXlsx } from '@/utils/xlsxLoader'

export interface ClosedLoopDashboardExportPayload {
  filename: string
  overview: ClosedLoopOverview
  byObjectItems: ClosedLoopByObjectItem[]
  queues: ClosedLoopQueueItem[]
  bottlenecks: ClosedLoopBottleneckItem[]
}

const normalizeFilename = (value: string) => value.replace(/[/\\?%*:|"<>]/g, '_')

const formatMetric = (value: unknown) => {
  if (typeof value === 'number') {
    if (Number.isInteger(value)) return value
    return Number(value.toFixed(2))
  }
  if (value === null || value === undefined) return ''
  return String(value)
}

const formatRate = (value: unknown) => `${Number(value || 0).toFixed(1)}%`

const buildOverviewSheet = (overview: ClosedLoopOverview) => {
  return [
    ['Metric', 'Value'],
    ['Window', `${overview.window.startDate} - ${overview.window.endDate}`],
    ['Opened Count', overview.summary.openedCount],
    ['Closed Count', overview.summary.closedCount],
    ['Backlog Count', overview.summary.backlogCount],
    ['Overdue Count', overview.summary.overdueCount],
    ['Auto Closed Count', overview.summary.autoClosedCount],
    ['Exception Backlog Count', overview.summary.exceptionBacklogCount],
    ['Average Cycle Hours', formatMetric(overview.summary.avgCycleHours)],
    ['Closure Rate', formatRate(overview.summary.closureRate)],
    ['Overdue Rate', formatRate(overview.summary.overdueRate)],
    ['Automatic Closure Rate', formatRate(overview.summary.automaticClosureRate)],
    [],
    ['Workflow SLA Metric', 'Value'],
    ['Active Task Count', overview.workflowSla.activeTaskCount],
    ['Overdue Task Count', overview.workflowSla.overdueTaskCount],
    ['Escalated Task Count', overview.workflowSla.escalatedTaskCount],
    ['Bottleneck Count', overview.workflowSla.bottleneckCount],
  ]
}

const buildTrendSheet = (overview: ClosedLoopOverview) => {
  return [
    ['Date', 'Opened', 'Closed'],
    ...overview.trend.points.map((point) => [point.date, point.opened, point.closed]),
  ]
}

const buildByObjectSheet = (items: ClosedLoopByObjectItem[]) => {
  return [
    ['Object', 'Opened', 'Closed', 'Backlog', 'Overdue', 'Auto Closed', 'Avg Cycle Hours', 'Primary Route'],
    ...items.map((item) => [
      item.objectName,
      item.summary.openedCount,
      item.summary.closedCount,
      item.summary.backlogCount,
      item.summary.overdueCount,
      item.summary.autoClosedCount,
      formatMetric(item.summary.avgCycleHours),
      item.primaryRoute,
    ]),
  ]
}

const buildOwnerSheet = (overview: ClosedLoopOverview) => {
  return [
    ['Owner', 'Username', 'Open Count', 'Overdue Count', 'Top Source'],
    ...overview.ownerRankings.map((item) => [
      item.displayName || item.username,
      item.username,
      item.openCount,
      item.overdueCount,
      item.topSource,
    ]),
  ]
}

const buildDepartmentSheet = (overview: ClosedLoopOverview) => {
  return [
    ['Department', 'Open Count', 'Overdue Count', 'Top Source'],
    ...overview.departmentRankings.map((item) => [
      item.departmentName,
      item.openCount,
      item.overdueCount,
      item.topSource,
    ]),
  ]
}

const buildQueueSheet = (queues: ClosedLoopQueueItem[]) => {
  return [
    ['Queue', 'Object', 'Count', 'Route', 'Tone'],
    ...queues.map((item) => [item.label, item.objectName, item.count, item.route, item.tone]),
  ]
}

const buildBottleneckSheet = (items: ClosedLoopBottleneckItem[]) => {
  return [
    ['Bottleneck', 'Object', 'Count', 'Severity', 'Metric Type', 'Route'],
    ...items.map((item) => [
      item.label,
      item.objectName,
      item.count,
      item.severity,
      item.metricType,
      item.route,
    ]),
  ]
}

const appendSheet = (workbook: any, xlsx: any, name: string, rows: Array<Array<string | number>>) => {
  const worksheet = xlsx.utils.aoa_to_sheet(rows)
  worksheet['!cols'] = rows[0]?.map((_, columnIndex) => {
    const maxLength = rows.reduce((max, row) => {
      const cellValue = row[columnIndex]
      return Math.max(max, String(cellValue ?? '').length)
    }, 12)
    return { wch: Math.min(maxLength + 2, 40) }
  }) || []
  xlsx.utils.book_append_sheet(workbook, worksheet, name)
}

export const exportClosedLoopDashboardWorkbook = async (payload: ClosedLoopDashboardExportPayload) => {
  const xlsx = await loadXlsx()
  const workbook = xlsx.utils.book_new()

  appendSheet(workbook, xlsx, 'Overview', buildOverviewSheet(payload.overview))
  appendSheet(workbook, xlsx, 'Trend', buildTrendSheet(payload.overview))
  appendSheet(workbook, xlsx, 'By Object', buildByObjectSheet(payload.byObjectItems))
  appendSheet(workbook, xlsx, 'Owners', buildOwnerSheet(payload.overview))
  appendSheet(workbook, xlsx, 'Departments', buildDepartmentSheet(payload.overview))
  appendSheet(workbook, xlsx, 'Queues', buildQueueSheet(payload.queues))
  appendSheet(workbook, xlsx, 'Bottlenecks', buildBottleneckSheet(payload.bottlenecks))

  xlsx.writeFile(workbook, `${normalizeFilename(payload.filename)}.xlsx`)
}
