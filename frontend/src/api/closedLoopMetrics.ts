import request from '@/utils/request'

export type ClosedLoopWindowKey = '7d' | '30d' | '90d'

export interface ClosedLoopWindow {
  key: ClosedLoopWindowKey
  days: number
  startDate: string
  endDate: string
}

export interface ClosedLoopMetricContract {
  [key: string]: string
}

export interface ClosedLoopSummary {
  openedCount: number
  closedCount: number
  backlogCount: number
  overdueCount: number
  autoClosedCount: number
  exceptionBacklogCount: number
  avgCycleHours: number
  closureRate: number
  overdueRate: number
  automaticClosureRate: number
}

export interface ClosedLoopTrendPoint {
  date: string
  opened: number
  closed: number
}

export interface ClosedLoopTrend {
  bucket: string
  points: ClosedLoopTrendPoint[]
}

export interface ClosedLoopCoverageObject {
  objectCode: string
  objectName: string
  primaryRoute: string
}

export interface ClosedLoopWorkflowSlaSummary {
  activeTaskCount: number
  overdueTaskCount: number
  escalatedTaskCount: number
  bottleneckCount: number
}

export interface ClosedLoopOwnerRanking {
  userId: string
  username: string
  displayName: string
  openCount: number
  overdueCount: number
  topSource: string
  sourceCounts: Record<string, number>
}

export interface ClosedLoopDepartmentRanking {
  departmentId: string
  departmentName: string
  openCount: number
  overdueCount: number
  topSource: string
  sourceCounts: Record<string, number>
}

export interface ClosedLoopOverview {
  window: ClosedLoopWindow
  metricContract: ClosedLoopMetricContract
  summary: ClosedLoopSummary
  trend: ClosedLoopTrend
  workflowSla: ClosedLoopWorkflowSlaSummary
  ownerRankings: ClosedLoopOwnerRanking[]
  departmentRankings: ClosedLoopDepartmentRanking[]
  objectsCovered: ClosedLoopCoverageObject[]
}

export interface ClosedLoopDashboardSnapshotPayload {
  overview: ClosedLoopOverview
  byObjectItems: ClosedLoopByObjectItem[]
  queues: ClosedLoopQueueItem[]
  bottlenecks: ClosedLoopBottleneckItem[]
}

export interface ClosedLoopDashboardSnapshotSummary {
  id: string
  label: string
  dashboardCode: string
  windowKey: ClosedLoopWindowKey
  objectCodes: string[]
  createdAt: string
  organization?: {
    id: string
    name: string
    code?: string
  } | null
  createdBy?: {
    id: string
    username: string
  } | null
}

export interface ClosedLoopDashboardSnapshotDetail extends ClosedLoopDashboardSnapshotSummary {
  payload: ClosedLoopDashboardSnapshotPayload
}

export interface ClosedLoopQueueItem {
  sourceType: 'object' | 'workflow'
  objectCode: string
  objectName: string
  code: string
  label: string
  count: number
  route: string
  tone: string
}

export interface ClosedLoopBottleneckItem {
  sourceType: 'object' | 'workflow'
  objectCode: string
  objectName: string
  code: string
  label: string
  count: number
  route: string
  severity: string
  metricType: string
  avgDurationHours?: number
  workflowName?: string
}

export interface ClosedLoopByObjectItem {
  objectCode: string
  objectName: string
  primaryRoute: string
  summary: ClosedLoopSummary
  trend: ClosedLoopTrend
  queues: ClosedLoopQueueItem[]
  bottlenecks: ClosedLoopBottleneckItem[]
}

export interface ClosedLoopByObjectResponse {
  window: ClosedLoopWindow
  results: ClosedLoopByObjectItem[]
}

export interface ClosedLoopQueueResponse {
  window: ClosedLoopWindow
  results: ClosedLoopQueueItem[]
}

export interface ClosedLoopBottleneckResponse {
  window: ClosedLoopWindow
  results: ClosedLoopBottleneckItem[]
}

export interface ClosedLoopDashboardSnapshotListResponse {
  results: ClosedLoopDashboardSnapshotSummary[]
}

interface ClosedLoopMetricsParams {
  window?: ClosedLoopWindowKey
  objectCodes?: string[]
  organizationId?: string
}

interface ClosedLoopSnapshotCreateParams {
  label: string
  window: ClosedLoopWindowKey
  objectCodes?: string[]
  organizationId?: string
}

const buildParams = (params?: ClosedLoopMetricsParams) => {
  const nextParams: Record<string, string> = {}
  if (params?.window) nextParams.window = params.window
  if (params?.objectCodes?.length) nextParams.object_codes = params.objectCodes.join(',')
  if (params?.organizationId) nextParams.organization_id = params.organizationId
  return { params: nextParams }
}

export const closedLoopMetricsApi = {
  getOverview(params?: ClosedLoopMetricsParams): Promise<ClosedLoopOverview> {
    return request.get('/system/metrics/closed-loop/overview/', buildParams(params))
  },

  getByObject(params?: ClosedLoopMetricsParams): Promise<ClosedLoopByObjectResponse> {
    return request.get('/system/metrics/closed-loop/by-object/', buildParams(params))
  },

  getQueues(params?: ClosedLoopMetricsParams): Promise<ClosedLoopQueueResponse> {
    return request.get('/system/metrics/closed-loop/queues/', buildParams(params))
  },

  getBottlenecks(params?: ClosedLoopMetricsParams): Promise<ClosedLoopBottleneckResponse> {
    return request.get('/system/metrics/closed-loop/bottlenecks/', buildParams(params))
  },

  listSnapshots(params?: ClosedLoopMetricsParams): Promise<ClosedLoopDashboardSnapshotListResponse> {
    return request.get('/system/metrics/closed-loop/snapshots/', buildParams(params))
  },

  createSnapshot(params: ClosedLoopSnapshotCreateParams): Promise<ClosedLoopDashboardSnapshotDetail> {
    return request.post('/system/metrics/closed-loop/snapshots/', {
      label: params.label,
      window: params.window,
      objectCodes: params.objectCodes || [],
      organizationId: params.organizationId,
    })
  },

  getSnapshot(snapshotId: string, params?: Pick<ClosedLoopMetricsParams, 'organizationId'>): Promise<ClosedLoopDashboardSnapshotDetail> {
    return request.get(`/system/metrics/closed-loop/snapshots/${snapshotId}/`, buildParams(params))
  },

  deleteSnapshot(snapshotId: string, params?: Pick<ClosedLoopMetricsParams, 'organizationId'>): Promise<void> {
    return request.delete(`/system/metrics/closed-loop/snapshots/${snapshotId}/`, buildParams(params))
  },
}
