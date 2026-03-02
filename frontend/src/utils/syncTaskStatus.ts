export type SyncTaskTagType = 'success' | 'warning' | 'danger' | 'primary' | 'info'

export const normalizeSyncTaskStatus = (status?: string) => String(status || '').toLowerCase()

export const getSyncTaskStatusType = (status?: string): SyncTaskTagType => {
  const normalized = normalizeSyncTaskStatus(status)
  if (normalized === 'success') return 'success'
  if (normalized === 'failed') return 'danger'
  if (normalized === 'partial_success' || normalized === 'partialsuccess') return 'warning'
  if (normalized === 'running') return 'primary'
  return 'info'
}

export const isSyncTaskDone = (status?: string) => {
  const normalized = normalizeSyncTaskStatus(status)
  return ['success', 'failed', 'cancelled', 'partial_success', 'partialsuccess'].includes(normalized)
}
