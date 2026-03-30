import { ref } from 'vue'
import type { Router } from 'vue-router'

import { taskApi, workflowNodeApi } from '@/api/workflow'
import { runFlagAction } from '@/composables'
import type { PortalTaskRecord } from '@/types/portal'

import { getPortalTaskPath } from './portalTaskModel'

type TranslationFn = (key: string) => string

interface ActionNotifier {
  success: (message: string) => void
  warning: (message: string) => void
  error: (message: string) => void
}

export const usePortalTasks = (
  t: TranslationFn,
  router: Router,
  notifier: ActionNotifier,
) => {
  const loadingTasks = ref(false)
  const myTasks = ref<PortalTaskRecord[]>([])
  const taskPage = ref(1)
  const taskPageSize = ref(10)
  const taskTotal = ref(0)
  const pendingTaskCount = ref(0)

  const processingTask = ref(false)
  const rejectDialog = ref(false)
  const rejectComment = ref('')
  const rejectTargetTask = ref<PortalTaskRecord | null>(null)

  const loadMyTasks = async () => {
    loadingTasks.value = true
    try {
      const response: any = await workflowNodeApi.getMyTasks({
        page: taskPage.value,
        pageSize: taskPageSize.value,
      })
      myTasks.value = response?.results ?? []
      taskTotal.value = response?.count ?? 0
      pendingTaskCount.value = taskTotal.value
    } finally {
      loadingTasks.value = false
    }
  }

  const openTask = (task: PortalTaskRecord) => router.push(getPortalTaskPath(task.id))

  const quickApprove = async (task: PortalTaskRecord) => {
    await runFlagAction({
      loadingFlag: processingTask,
      notifier,
      messages: {
        successFallback: t('portal.tasks.approveSuccess'),
        failureFallback: t('portal.tasks.approveFailed'),
        errorFallback: t('portal.tasks.approveFailed')
      },
      invoke: async () => {
        await taskApi.approveTask(String(task.id), { comment: '' })
        return { success: true }
      },
      onSuccess: async () => {
        await loadMyTasks()
      }
    })
  }

  const openRejectDialog = (task: PortalTaskRecord) => {
    rejectTargetTask.value = task
    rejectComment.value = ''
    rejectDialog.value = true
  }

  const confirmReject = async () => {
    if (!rejectTargetTask.value) return

    await runFlagAction({
      loadingFlag: processingTask,
      notifier,
      messages: {
        successFallback: t('portal.tasks.rejectSuccess'),
        failureFallback: t('portal.tasks.rejectFailed'),
        errorFallback: t('portal.tasks.rejectFailed')
      },
      invoke: async () => {
        await taskApi.rejectTask(String(rejectTargetTask.value?.id), { comment: rejectComment.value })
        return { success: true }
      },
      onSuccess: async () => {
        rejectDialog.value = false
        await loadMyTasks()
      }
    })
  }

  return {
    confirmReject,
    loadMyTasks,
    loadingTasks,
    myTasks,
    openRejectDialog,
    openTask,
    pendingTaskCount,
    processingTask,
    quickApprove,
    rejectComment,
    rejectDialog,
    taskPage,
    taskPageSize,
    taskTotal,
  }
}
