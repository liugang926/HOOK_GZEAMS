import type { PortalTaskRecord } from '@/types/portal'

export const getPortalTaskTitle = (task: PortalTaskRecord) => {
  return task.title || task.businessTitle || task.instanceTitle || '-'
}

export const getPortalTaskInitiator = (task: PortalTaskRecord) => {
  return task.initiatorDisplay || task.createdBy || '-'
}

export const getPortalTaskTime = (task: PortalTaskRecord) => {
  return String(task.createdAt || task.assignedAt || '')
}

export const getPortalTaskPath = (id: string | number) => `/workflow/approvals/${id}`

type TranslationFn = (key: string) => string

export const getPortalTaskTypeLabel = (
  task: PortalTaskRecord,
  t: TranslationFn
) => {
  return task.taskName || task.nodeName || t('portal.tasks.approvalTask')
}
