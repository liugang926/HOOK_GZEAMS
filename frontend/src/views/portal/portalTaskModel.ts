export const getPortalTaskTitle = (task: Record<string, any>) => {
  return task.title || task.businessTitle || task.instanceTitle || '-'
}

export const getPortalTaskInitiator = (task: Record<string, any>) => {
  return task.initiatorDisplay || task.createdBy || '-'
}

export const getPortalTaskTime = (task: Record<string, any>) => {
  return String(task.createdAt || task.assignedAt || '')
}

export const getPortalTaskPath = (id: string | number) => `/workflow/tasks/${id}`

type TranslationFn = (key: string) => string

export const getPortalTaskTypeLabel = (
  task: Record<string, any>,
  t: TranslationFn
) => {
  return task.taskName || task.nodeName || t('portal.tasks.approvalTask')
}
