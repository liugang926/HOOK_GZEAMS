import type {
  ClosedLoopBottleneckItem,
  ClosedLoopByObjectItem,
  ClosedLoopOverview,
  ClosedLoopQueueItem,
  ClosedLoopWindowKey,
} from '@/api/closedLoopMetrics'
import { readStorageJson, writeStorageJson } from '@/platform/storage/browserStorage'

const CLOSED_LOOP_DASHBOARD_SNAPSHOT_STORAGE_KEY = 'reports.closed_loop.dashboard_snapshots.v1'
const CLOSED_LOOP_DASHBOARD_SNAPSHOT_LIMIT = 8

export interface ClosedLoopDashboardSnapshotFilters {
  window: ClosedLoopWindowKey
  organizationId?: string
  organizationName?: string
  objectCodes: string[]
}

export interface ClosedLoopDashboardSnapshotPayload {
  overview: ClosedLoopOverview
  byObjectItems: ClosedLoopByObjectItem[]
  queues: ClosedLoopQueueItem[]
  bottlenecks: ClosedLoopBottleneckItem[]
}

export interface ClosedLoopDashboardSnapshot {
  id: string
  label: string
  createdAt: string
  filters: ClosedLoopDashboardSnapshotFilters
  payload: ClosedLoopDashboardSnapshotPayload
}

const normalizeString = (value: unknown) => String(value || '').trim()

const normalizeStringArray = (value: unknown): string[] => {
  if (!Array.isArray(value)) return []
  return value
    .map((item) => normalizeString(item))
    .filter(Boolean)
}

const isSnapshotPayload = (value: unknown): value is ClosedLoopDashboardSnapshotPayload => {
  if (!value || typeof value !== 'object') return false
  const payload = value as Record<string, unknown>
  return Boolean(payload.overview && payload.byObjectItems && payload.queues && payload.bottlenecks)
}

const normalizeSnapshot = (value: unknown): ClosedLoopDashboardSnapshot | null => {
  if (!value || typeof value !== 'object') return null

  const candidate = value as Record<string, unknown>
  const id = normalizeString(candidate.id)
  const label = normalizeString(candidate.label)
  const createdAt = normalizeString(candidate.createdAt)
  const filters = candidate.filters as Record<string, unknown> | undefined
  const payload = candidate.payload

  if (!id || !label || !createdAt || !filters || !isSnapshotPayload(payload)) {
    return null
  }

  const window = normalizeString(filters.window) as ClosedLoopWindowKey
  if (!['7d', '30d', '90d'].includes(window)) {
    return null
  }

  return {
    id,
    label,
    createdAt,
    filters: {
      window,
      organizationId: normalizeString(filters.organizationId) || undefined,
      organizationName: normalizeString(filters.organizationName) || undefined,
      objectCodes: normalizeStringArray(filters.objectCodes),
    },
    payload,
  }
}

const persistSnapshots = (snapshots: ClosedLoopDashboardSnapshot[]) => {
  writeStorageJson(CLOSED_LOOP_DASHBOARD_SNAPSHOT_STORAGE_KEY, snapshots)
}

export const readClosedLoopDashboardSnapshots = (): ClosedLoopDashboardSnapshot[] => {
  const storedSnapshots = readStorageJson<unknown[]>(
    CLOSED_LOOP_DASHBOARD_SNAPSHOT_STORAGE_KEY,
    [],
  )

  return storedSnapshots
    .map((snapshot) => normalizeSnapshot(snapshot))
    .filter((snapshot): snapshot is ClosedLoopDashboardSnapshot => Boolean(snapshot))
    .sort((left, right) => String(right.createdAt).localeCompare(String(left.createdAt)))
}

export const saveClosedLoopDashboardSnapshot = (input: {
  label: string
  filters: ClosedLoopDashboardSnapshotFilters
  payload: ClosedLoopDashboardSnapshotPayload
}) => {
  const snapshot: ClosedLoopDashboardSnapshot = {
    id: `closed-loop-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    label: normalizeString(input.label) || 'Closed Loop Snapshot',
    createdAt: new Date().toISOString(),
    filters: {
      window: input.filters.window,
      organizationId: normalizeString(input.filters.organizationId) || undefined,
      organizationName: normalizeString(input.filters.organizationName) || undefined,
      objectCodes: normalizeStringArray(input.filters.objectCodes),
    },
    payload: input.payload,
  }

  const snapshots = [snapshot, ...readClosedLoopDashboardSnapshots()].slice(0, CLOSED_LOOP_DASHBOARD_SNAPSHOT_LIMIT)
  persistSnapshots(snapshots)
  return snapshot
}

export const deleteClosedLoopDashboardSnapshot = (snapshotId: string) => {
  const normalizedId = normalizeString(snapshotId)
  if (!normalizedId) return []

  const snapshots = readClosedLoopDashboardSnapshots().filter((snapshot) => snapshot.id !== normalizedId)
  persistSnapshots(snapshots)
  return snapshots
}
