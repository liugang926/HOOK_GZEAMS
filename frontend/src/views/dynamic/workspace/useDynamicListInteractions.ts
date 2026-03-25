import { computed, ref, type ComputedRef, type Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Router } from 'vue-router'
import { financeApi } from '@/api/finance'
import { exportAllPages, type ExportColumn } from '@/utils/exportService'
import type { ImportResult } from '@/utils/importService'
import { filterSystemFields } from '@/utils/transform'
import { resolveListFieldValue } from '@/utils/listFieldValue'
import { isReferenceLikeFieldType } from '@/platform/reference/referenceFieldMeta'
import { useLifecycleListExtensions } from '@/platform/lifecycle/lifecycleListExtensions'
import { executeDynamicListDeleteOperation } from './dynamicListDeleteActions'
import {
  pushDynamicListCreate,
  pushDynamicListEdit,
  pushDynamicListLayoutSettings,
  pushDynamicListView,
  resolveDynamicListRowId,
} from './dynamicListNavigation'
import { buildDynamicListRequestParams } from './dynamicListQuery'

interface BatchAction {
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  icon?: any
  action: (selectedRows: any[]) => void | Promise<void>
  confirm?: boolean
  confirmMessage?: string
}

interface RowActionDefinition {
  key: string
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
}

interface DynamicListInteractionsOptions {
  t: (key: string, params?: Record<string, unknown>) => string
  te: (key: string) => boolean
  router: Router
  objectCode: Ref<string>
  objectDisplayName: ComputedRef<string>
  apiClient: ComputedRef<any>
  tableRef: Ref<any>
  canDelete: ComputedRef<boolean>
  unifiedSearchFieldOptions: ComputedRef<Array<{ label: string; value: string }>>
  visibleFieldsSource: ComputedRef<any[]>
  orderedVisibleFieldsSource: ComputedRef<any[]>
  buildExportColumns: (selectedCodes: string[]) => ExportColumn[]
  routeFilters: ComputedRef<Record<string, any>>
}

export const useDynamicListInteractions = ({
  t,
  te,
  router,
  objectCode,
  objectDisplayName,
  apiClient,
  tableRef,
  canDelete,
  unifiedSearchFieldOptions,
  visibleFieldsSource,
  orderedVisibleFieldsSource,
  buildExportColumns,
  routeFilters,
}: DynamicListInteractionsOptions) => {
  const drawerVisible = ref(false)
  const activeRecordId = ref('')
  const showFieldSelector = ref(false)
  const showImportConfig = ref(false)
  const importParseResult = ref<ImportResult>({
    data: [],
    errors: [],
    unknownHeaders: [],
    missingHeaders: [],
  })
  const currentSearchParams = ref<Record<string, any>>({})
  const lifecycleListExtensions = useLifecycleListExtensions({
    objectCode,
    router,
    tableRef,
    t,
    te,
  })

  const batchActions = computed<BatchAction[]>(() => {
    const actions: BatchAction[] = []

    if (objectCode.value === 'FinanceVoucher') {
      actions.push({
        label: t('finance.actions.batchPush'),
        type: 'primary',
        action: async (selectedRows: any[]) => {
          const ids = selectedRows
            .map((row: any) => resolveDynamicListRowId(row))
            .filter(Boolean)
          if (!ids.length) return

          try {
            const result = await financeApi.batchPushVouchers(ids)
            const succeeded = Number(result?.success || 0)
            const failed = Number(result?.failed || 0)

            if (succeeded > 0 && failed > 0) {
              ElMessage.warning(`${t('common.messages.operationSuccess')} (${succeeded}/${ids.length})`)
            } else if (failed > 0) {
              ElMessage.error(t('common.messages.operationFailed'))
            } else {
              ElMessage.success(t('common.messages.operationSuccess'))
            }

            tableRef.value?.refresh()
          } catch (error: any) {
            ElMessage.error(error?.message || t('common.messages.operationFailed'))
          }
        },
      })
    }

    if (canDelete.value) {
      actions.push({
        label: t('common.actions.batchDelete'),
        type: 'danger',
        action: async (selectedRows: any[]) => {
          const ids = selectedRows
            .map((row: any) => resolveDynamicListRowId(row))
            .filter(Boolean)
          if (!ids.length) return

          await executeDynamicListDeleteOperation({
            runDelete: async () => {
              await ElMessageBox.confirm(
                t('common.messages.confirmDelete'),
                t('common.dialog.confirmTitle'),
                { type: 'warning' },
              )
              await apiClient.value.batchDelete(ids)
            },
            refresh: () => tableRef.value?.refresh(),
            notifySuccess: (message) => ElMessage.success(message),
            notifyError: (message) => ElMessage.error(message),
            successMessage: t('common.messages.deleteSuccess'),
            fallbackErrorMessage: t('common.messages.deleteFailed'),
          })
        },
      })
    }

    return actions
  })

  const slotFields = computed(() => {
    if (!orderedVisibleFieldsSource.value.length) return []

    return filterSystemFields(orderedVisibleFieldsSource.value)
      .filter((field: any) => {
        const fieldType = String(field.fieldType || field.type || '').trim()
        if (isReferenceLikeFieldType(fieldType)) return false
        if (field.referenceObject || field.relatedObject) return false
        return field.requiresSlot
      })
      .map((field: any) => ({
        fieldCode: field.code,
        dataKey: field.dataKey || field.code,
        slotName: field.code,
        fieldType: field.fieldType,
        options: field.options,
        referenceObject: field.referenceObject || field.targetObjectCode || field.relatedObject,
        targetObjectCode: field.targetObjectCode || field.referenceObject,
        referenceDisplayField: field.referenceDisplayField || field.displayField,
        referenceSecondaryField: field.referenceSecondaryField,
      }))
  })

  const hasStatusField = computed(() => {
    return orderedVisibleFieldsSource.value?.some((field: any) => field.code === 'status')
  })

  const fetchData = async (params: any) => {
    const nextParams = buildDynamicListRequestParams({
      params,
      routeFilters: routeFilters.value,
      unifiedSearchFieldOptions: unifiedSearchFieldOptions.value,
    })

    currentSearchParams.value = { ...nextParams }
    return lifecycleListExtensions.fetchData(nextParams, (resolvedParams) => apiClient.value.list(resolvedParams))
  }

  const buildAssetProjectRowActions = (row: Record<string, any>): RowActionDefinition[] => {
    if (objectCode.value !== 'AssetProject') return []

    const assetCount = Number(row.assetCount || row.asset_count || row.activeAssets || row.active_assets || 0)
    const memberCount = Number(row.memberCount || row.member_count || 0)

    return [
      {
        key: 'viewAssets',
        label: t('projects.actions.viewAssets', { count: assetCount }),
      },
      {
        key: 'viewMembers',
        label: t('projects.actions.viewMembers', { count: memberCount }),
      },
    ]
  }

  const handleAssetProjectRowAction = (actionKey: string, row: Record<string, any>) => {
    if (objectCode.value !== 'AssetProject') return false

    const recordId = resolveDynamicListRowId(row)
    if (!recordId) return true

    if (actionKey === 'viewAssets') {
      router.push({
        path: '/objects/ProjectAsset',
        query: { project: recordId },
      })
      return true
    }

    if (actionKey === 'viewMembers') {
      router.push({
        path: '/objects/ProjectMember',
        query: { project: recordId },
      })
      return true
    }

    return false
  }

  const handleView = (row: any) => {
    pushDynamicListView({
      router,
      objectCode: objectCode.value,
      row,
    })
  }

  const handleRowClick = (row: any) => {
    handleView(row)
  }

  const handleCreate = () => {
    pushDynamicListCreate({
      router,
      objectCode: objectCode.value,
    })
  }

  const handleLayoutSettings = () => {
    pushDynamicListLayoutSettings({
      router,
      objectCode: objectCode.value,
      objectName: objectDisplayName.value || objectCode.value,
    })
  }

  const handleEdit = (row: any) => {
    const recordId = resolveDynamicListRowId(row)
    if (!recordId) {
      ElMessage.error(t('common.messages.operationFailed'))
      return
    }

    pushDynamicListEdit({
      router,
      objectCode: objectCode.value,
      row,
    })
  }

  const handleDelete = async (row: any) => {
    const recordId = resolveDynamicListRowId(row)
    if (!recordId) {
      ElMessage.error(t('common.messages.operationFailed'))
      return
    }

    await executeDynamicListDeleteOperation({
      runDelete: async () => {
        await ElMessageBox.confirm(
          t('common.messages.confirmDeleteMessage'),
          t('common.dialog.confirmTitle'),
          { type: 'warning' },
        )
        await apiClient.value.delete(recordId)
      },
      refresh: () => tableRef.value?.refresh(),
      notifySuccess: (message) => ElMessage.success(message),
      notifyError: (message) => ElMessage.error(message),
      successMessage: t('common.messages.deleteSuccess'),
      fallbackErrorMessage: t('common.messages.deleteFailed'),
    })
  }

  const handleDrawerSuccess = () => {
    tableRef.value?.refresh()
  }

  const handleCustomExport = async (columns: ExportColumn[]) => {
    try {
      const selectedCodes = columns.map((column) => column.prop)
      const smartColumns = buildExportColumns(selectedCodes)
      await exportAllPages(
        objectDisplayName.value || objectCode.value,
        smartColumns,
        (params: any) => apiClient.value.list({ ...params, ...currentSearchParams.value })
      )
      ElMessage.success(t('reports.export.successMessage'))
    } catch (error: any) {
      ElMessage.error(error?.message || t('reports.export.errorMessage'))
    }
  }

  const handleImport = (result: ImportResult) => {
    importParseResult.value = result
    showImportConfig.value = true
  }

  const handleImportComplete = (result: { created: number; updated: number; skipped: number; failed: number }) => {
    const { created, updated, skipped, failed } = result
    if (failed > 0) {
      ElMessage.warning(
        t('reports.import.partialSuccess', { success: created + updated, fail: failed })
      )
    } else {
      const total = created + updated + skipped
      ElMessage.success(
        t('reports.import.readyMessage', { count: total })
      )
    }
    tableRef.value?.refresh()
  }

  const getDefaultStatusType = (status: string) => {
    const typeMap: Record<string, any> = {
      active: 'success',
      enabled: 'success',
      draft: 'info',
      pending: 'warning',
      disabled: 'danger',
      deleted: 'danger',
    }
    return typeMap[status] || 'info'
  }

  const getDefaultStatusLabel = (status: string) => {
    const normalized = String(status || '').trim().toLowerCase()
    if (!normalized) return ''
    const statusKey = `common.status.${normalized}`
    return te(statusKey) ? t(statusKey) : normalized
  }

  const getStatusType = (status: string) => {
    return lifecycleListExtensions.getStatusType(status, getDefaultStatusType)
  }

  const getStatusLabel = (status: string) => {
    return lifecycleListExtensions.getStatusLabel(status, getDefaultStatusLabel)
  }

  const getFieldDefinition = (slotField: any) => {
    const originalField = visibleFieldsSource.value?.find((field: any) => field.code === slotField.fieldCode)

    return {
      code: slotField.fieldCode,
      name: slotField.fieldCode,
      dataKey: originalField?.dataKey || slotField.dataKey || slotField.fieldCode,
      fieldType: originalField?.fieldType || slotField.fieldType || 'text',
      placeholder: '',
      isRequired: false,
      isReadonly: true,
      options: slotField.options,
      referenceObject: originalField?.referenceObject || originalField?.targetObjectCode || originalField?.relatedObject || slotField.referenceObject || slotField.targetObjectCode,
      targetObjectCode: originalField?.targetObjectCode || originalField?.referenceObject || slotField.targetObjectCode || slotField.referenceObject,
      referenceDisplayField: originalField?.referenceDisplayField || originalField?.displayField || slotField.referenceDisplayField,
      referenceSecondaryField: originalField?.referenceSecondaryField || slotField.referenceSecondaryField,
      description: undefined,
    }
  }

  const getSlotFieldValue = (row: any, slotField: any) => {
    return resolveListFieldValue(row, {
      fieldCode: slotField.fieldCode,
      prop: slotField.fieldCode,
      dataKey: slotField.dataKey || slotField.fieldCode,
      fieldType: slotField.fieldType || 'text',
      referenceObject: slotField.referenceObject || slotField.targetObjectCode || slotField.relatedObject,
      referenceDisplayField: slotField.referenceDisplayField,
    })
  }

  return {
    activeRecordId,
    batchActions,
    currentSearchParams,
    drawerVisible,
    fetchData,
    getFieldDefinition,
    getRowActions: (row: Record<string, any>) => [
      ...buildAssetProjectRowActions(row),
      ...lifecycleListExtensions.getRowActions(row),
    ],
    getSlotFieldValue,
    getStatusLabel,
    getStatusType,
    handleCreate,
    handleCustomExport,
    handleDelete,
    handleDrawerSuccess,
    handleEdit,
    handleImport,
    handleImportComplete,
    handleLayoutSettings,
    handleRowAction: async (actionKey: string, row: Record<string, any>) => {
      if (handleAssetProjectRowAction(actionKey, row)) return
      await lifecycleListExtensions.handleRowAction(actionKey, row)
    },
    handleRowClick,
    handleView,
    hasStatusField,
    importParseResult,
    quickFilters: lifecycleListExtensions.quickFilters,
    setQuickFilter: lifecycleListExtensions.setQuickFilter,
    showFieldSelector,
    showImportConfig,
    slotFields,
  }
}
