import { ref, type ComputedRef } from 'vue'
import type { Router } from 'vue-router'
import { ElMessageBox } from 'element-plus'

import { runAction } from '@/composables'
import type { PortalRequestRecord } from '@/types/portal'

import {
  canCancelPortalRequest,
  canSubmitPortalRequest,
  getPortalRequestCreatePath,
  getPortalRequestDetailPath,
  portalRequestApiMap,
} from './portalRequestModel'
import type { PortalRequestType } from '@/types/portal'

type TranslationFn = (key: string) => string

interface ActionNotifier {
  success: (message: string) => void
  warning: (message: string) => void
  error: (message: string) => void
}

type UserIdRef = ComputedRef<string | number | undefined>

export const usePortalRequests = (
  t: TranslationFn,
  router: Router,
  notifier: ActionNotifier,
  userId: UserIdRef,
) => {
  const loadingRequests = ref(false)
  const myRequests = ref<PortalRequestRecord[]>([])
  const requestType = ref<PortalRequestType>('pickup')
  const requestStatusFilter = ref('')
  const requestPage = ref(1)
  const requestPageSize = ref(15)
  const requestTotal = ref(0)
  const pendingRequestCount = ref(0)

  const loadMyRequests = async () => {
    loadingRequests.value = true
    try {
      const api = portalRequestApiMap[requestType.value]
      const response: any = await api.list({
        page: requestPage.value,
        page_size: requestPageSize.value,
        status: requestStatusFilter.value || undefined,
        createdBy: userId.value,
      })
      myRequests.value = response?.results ?? []
      requestTotal.value = response?.count ?? 0
    } finally {
      loadingRequests.value = false
    }
  }

  const refreshPendingRequestCount = async () => {
    const responses = await Promise.all(
      Object.values(portalRequestApiMap).map((api) => api.list({
        page: 1,
        page_size: 1,
        status: 'pending',
        createdBy: userId.value,
      }))
    )

    pendingRequestCount.value = responses.reduce((total, response: any) => {
      return total + (response?.count ?? 0)
    }, 0)
  }

  const viewRequest = (row: Record<string, any>) => {
    return router.push(getPortalRequestDetailPath(requestType.value, row.id))
  }

  const createNewRequest = () => {
    return router.push(getPortalRequestCreatePath(requestType.value))
  }

  const canSubmitRequest = (row: Record<string, any>) =>
    canSubmitPortalRequest(requestType.value, row, portalRequestApiMap)

  const canCancelRequest = (row: Record<string, any>) =>
    canCancelPortalRequest(requestType.value, row, portalRequestApiMap)

  const submitRequest = async (row: Record<string, any>) => {
    try {
      await ElMessageBox.confirm(t('portal.requests.submitConfirm'), { type: 'info' })
    } catch {
      return
    }

    const submit = portalRequestApiMap[requestType.value].submit
    if (!submit) return

    await runAction({
      notifier,
      messages: {
        successFallback: t('portal.requests.submitSuccess'),
        failureFallback: t('portal.requests.submitFailed'),
        errorFallback: t('portal.requests.submitFailed')
      },
      invoke: async () => {
        await submit(String(row.id))
        return { success: true }
      },
      onSuccess: async () => {
        await Promise.all([
          loadMyRequests(),
          refreshPendingRequestCount(),
        ])
      }
    })
  }

  const cancelRequest = async (row: Record<string, any>) => {
    try {
      await ElMessageBox.confirm(t('portal.requests.cancelConfirm'), { type: 'warning' })
    } catch {
      return
    }

    const cancel = portalRequestApiMap[requestType.value].cancel
    if (!cancel) return

    await runAction({
      notifier,
      messages: {
        successFallback: t('common.messages.operationSuccess'),
        failureFallback: t('common.messages.operationFailed'),
        errorFallback: t('common.messages.operationFailed')
      },
      invoke: async () => {
        await cancel(String(row.id))
        return { success: true }
      },
      onSuccess: async () => {
        await Promise.all([
          loadMyRequests(),
          refreshPendingRequestCount(),
        ])
      }
    })
  }

  return {
    canCancelRequest,
    canSubmitRequest,
    cancelRequest,
    createNewRequest,
    loadMyRequests,
    loadingRequests,
    myRequests,
    pendingRequestCount,
    refreshPendingRequestCount,
    requestPage,
    requestPageSize,
    requestStatusFilter,
    requestTotal,
    requestType,
    submitRequest,
    viewRequest,
  }
}
