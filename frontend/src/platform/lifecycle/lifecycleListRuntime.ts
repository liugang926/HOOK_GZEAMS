import { computed, ref, type ComputedRef, type Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Router } from 'vue-router'

import {
  assetReceiptActionApi,
  assetWarrantyActionApi,
  disposalRequestActionApi,
  maintenanceActionApi,
  maintenancePlanActionApi,
  maintenanceTaskActionApi,
  purchaseRequestActionApi,
} from '@/api/lifecycleActionApi'
import { financeApi, integrationApi } from '@/api/finance'

import {
  getLifecycleListStatusTranslationKey,
  getLifecycleListStatusType,
  getLifecycleQuickFilterDefinitions,
  getLifecycleRowActionDefinitions,
  type LifecycleListQuickFilterDefinition,
  type LifecycleQuickFilterMode,
} from './lifecycleListModel'

interface Params {
  objectCode: Ref<string>
  router: Router
  tableRef: Ref<any>
  t: (key: string, params?: Record<string, unknown>) => string
  te: (key: string) => boolean
}

const normalizeQuickFilterResponse = (response: any) => {
  const records = Array.isArray(response)
    ? response
    : Array.isArray(response?.data)
      ? response.data
      : Array.isArray(response?.results)
        ? response.results
        : []

  return {
    results: records,
    count: records.length,
  }
}

export const useLifecycleListRuntime = ({
  objectCode,
  router,
  tableRef,
  t,
  te,
}: Params) => {
  const maintenanceTaskFilterMode = ref<LifecycleQuickFilterMode>('all')

  const quickFilters = computed(() =>
    getLifecycleQuickFilterDefinitions(objectCode.value, maintenanceTaskFilterMode.value)
  )

  const refreshTable = () => {
    tableRef.value?.refresh?.()
  }

  const withErrorHandling = async (operation: () => Promise<void> | void) => {
    try {
      await operation()
    } catch (error: any) {
      if (error === 'cancel' || error === 'close') return
      ElMessage.error(error?.message || t('common.messages.operationFailed'))
    }
  }

  const runConfirmedAction = async ({
    confirmMessage,
    confirmType = 'info',
    successMessage,
    operation,
  }: {
    confirmMessage: string
    confirmType?: 'info' | 'warning' | 'error' | 'success'
    successMessage: string
    operation: () => Promise<any>
  }) => {
    await ElMessageBox.confirm(confirmMessage, t('common.messages.confirmTitle'), { type: confirmType })
    await operation()
    ElMessage.success(successMessage)
    refreshTable()
  }

  const setQuickFilter = (key: LifecycleQuickFilterMode) => {
    maintenanceTaskFilterMode.value = key
    refreshTable()
  }

  const fetchData = async (
    params: Record<string, any>,
    defaultFetch: (params: Record<string, any>) => Promise<any>
  ) => {
    if (objectCode.value === 'MaintenanceTask' && maintenanceTaskFilterMode.value !== 'all') {
      const response =
        maintenanceTaskFilterMode.value === 'overdue'
          ? await maintenanceTaskActionApi.overdue()
          : await maintenanceTaskActionApi.today()

      return normalizeQuickFilterResponse(response)
    }

    return defaultFetch(params)
  }

  const getStatusType = (status: string, fallback: (status: string) => string) => {
    return getLifecycleListStatusType(objectCode.value, status) ?? fallback(status)
  }

  const getStatusLabel = (status: string, fallback: (status: string) => string) => {
    const translationKey = getLifecycleListStatusTranslationKey(objectCode.value, status)
    if (translationKey && te(translationKey)) {
      return t(translationKey)
    }
    return fallback(status)
  }

  const getRowActions = (row: Record<string, any>) => {
    return getLifecycleRowActionDefinitions(objectCode.value, row).map((definition) => ({
      ...definition,
      label: t(definition.labelKey),
    }))
  }

  const handleRowAction = async (actionKey: string, row: Record<string, any>) => {
    const recordId = encodeURIComponent(String(row?.id || ''))
    if (!recordId) return

    await withErrorHandling(async () => {
      switch (`${objectCode.value}:${actionKey}`) {
        case 'PurchaseRequest:submit':
          await runConfirmedAction({
            confirmMessage: t('assets.lifecycle.purchaseRequest.actions.submit'),
            successMessage: t('assets.lifecycle.purchaseRequest.messages.submitSuccess'),
            operation: () => purchaseRequestActionApi.submit(recordId),
          })
          return
        case 'PurchaseRequest:cancel':
          await runConfirmedAction({
            confirmMessage: t('assets.lifecycle.purchaseRequest.messages.cancelConfirm'),
            confirmType: 'warning',
            successMessage: t('assets.lifecycle.purchaseRequest.messages.cancelSuccess'),
            operation: () => purchaseRequestActionApi.cancel(recordId),
          })
          return
        case 'AssetReceipt:submitInspection':
          await runConfirmedAction({
            confirmMessage: t('assets.lifecycle.assetReceipt.messages.submitInspectionConfirm'),
            successMessage: t('assets.lifecycle.assetReceipt.messages.submitInspectionSuccess'),
            operation: () => assetReceiptActionApi.submitInspection(recordId),
          })
          return
        case 'AssetReceipt:cancel':
          await runConfirmedAction({
            confirmMessage: t('assets.lifecycle.assetReceipt.messages.cancelConfirm'),
            confirmType: 'warning',
            successMessage: t('assets.lifecycle.assetReceipt.messages.cancelSuccess'),
            operation: () => assetReceiptActionApi.cancel(recordId),
          })
          return
        case 'Maintenance:cancel':
          await runConfirmedAction({
            confirmMessage: t('assets.lifecycle.maintenance.messages.cancelConfirm'),
            confirmType: 'warning',
            successMessage: t('assets.lifecycle.maintenance.messages.cancelSuccess'),
            operation: () => maintenanceActionApi.cancel(recordId),
          })
          return
        case 'MaintenancePlan:activate':
          await maintenancePlanActionApi.activate(recordId)
          ElMessage.success(t('assets.lifecycle.maintenancePlan.messages.activateSuccess'))
          refreshTable()
          return
        case 'MaintenancePlan:pause':
          await maintenancePlanActionApi.pause(recordId)
          ElMessage.success(t('assets.lifecycle.maintenancePlan.messages.pauseSuccess'))
          refreshTable()
          return
        case 'MaintenancePlan:generateTasks': {
          await ElMessageBox.confirm(
            t('assets.lifecycle.maintenancePlan.messages.generateTasksConfirm'),
            t('common.messages.confirmTitle'),
            { type: 'info' }
          )
          const result: any = await maintenancePlanActionApi.generateTasks(recordId)
          ElMessage.success(
            t('assets.lifecycle.maintenancePlan.messages.generateTasksSuccess', {
              count: result?.generated_count || result?.data?.generated_count || '?',
            })
          )
          refreshTable()
          return
        }
        case 'MaintenanceTask:execute':
          router.push(`/objects/MaintenanceTask/${recordId}`)
          return
        case 'MaintenanceTask:skip': {
          const promptResult = await ElMessageBox.prompt(
            t('assets.lifecycle.maintenanceTask.dialog.skipReasonPlaceholder'),
            t('assets.lifecycle.maintenanceTask.actions.skip'),
            {
              inputType: 'textarea',
              confirmButtonText: t('common.actions.confirm'),
              cancelButtonText: t('common.actions.cancel'),
            }
          )
          await maintenanceTaskActionApi.skip(recordId, String(promptResult.value || ''))
          ElMessage.success(t('assets.lifecycle.maintenanceTask.messages.skipSuccess'))
          refreshTable()
          return
        }
        case 'DisposalRequest:submit':
          await runConfirmedAction({
            confirmMessage: t('assets.lifecycle.disposalRequest.actions.submit'),
            successMessage: t('assets.lifecycle.disposalRequest.messages.submitSuccess'),
            operation: () => disposalRequestActionApi.submit(recordId),
          })
          return
        case 'DisposalRequest:cancel':
          await runConfirmedAction({
            confirmMessage: t('assets.lifecycle.disposalRequest.messages.cancelConfirm'),
            confirmType: 'warning',
            successMessage: t('assets.lifecycle.disposalRequest.messages.cancelSuccess'),
            operation: () => disposalRequestActionApi.cancel(recordId),
          })
          return
        case 'AssetWarranty:activate':
          await runConfirmedAction({
            confirmMessage: t('assets.lifecycle.assetWarranty.messages.activateConfirm'),
            successMessage: t('assets.lifecycle.assetWarranty.messages.activateSuccess'),
            operation: () => assetWarrantyActionApi.activate(recordId),
          })
          return
        case 'AssetWarranty:renew':
          router.push(`/objects/AssetWarranty/${recordId}?action=renew`)
          return
        case 'AssetWarranty:cancel':
          await runConfirmedAction({
            confirmMessage: t('assets.lifecycle.assetWarranty.messages.cancelConfirm'),
            confirmType: 'warning',
            successMessage: t('assets.lifecycle.assetWarranty.messages.cancelSuccess'),
            operation: () => assetWarrantyActionApi.cancel(recordId),
          })
          return
        case 'FinanceVoucher:post':
          await runConfirmedAction({
            confirmMessage: t('finance.messages.confirmPost'),
            confirmType: 'warning',
            successMessage: t('common.messages.operationSuccess'),
            operation: () => financeApi.postVoucher(recordId),
          })
          return
        case 'FinanceVoucher:retryPush':
          await runConfirmedAction({
            confirmMessage: t('finance.messages.confirmRetryPush'),
            confirmType: 'warning',
            successMessage: t('common.messages.operationSuccess'),
            operation: () => integrationApi.retry(recordId),
          })
          return
        default:
          return
      }
    })
  }

  return {
    fetchData,
    getRowActions,
    getStatusLabel,
    getStatusType,
    handleRowAction,
    quickFilters: quickFilters as ComputedRef<LifecycleListQuickFilterDefinition[]>,
    setQuickFilter,
  }
}
