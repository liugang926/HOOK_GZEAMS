import { computed, ref, type ComputedRef, type Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Router } from 'vue-router'
import { exportAllPages, type ExportColumn } from '@/utils/exportService'
import type { ImportResult } from '@/utils/importService'
import type { SearchField } from '@/types/common'
import { filterSystemFields } from '@/utils/transform'
import { resolveListFieldValue } from '@/utils/listFieldValue'
import { isReferenceLikeFieldType } from '@/platform/reference/referenceFieldMeta'

interface BatchAction {
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  icon?: any
  action: (selectedRows: any[]) => void | Promise<void>
  confirm?: boolean
  confirmMessage?: string
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

  const batchActions = computed<BatchAction[]>(() => {
    if (!canDelete.value) return []
    return [
      {
        label: t('common.actions.batchDelete'),
        type: 'danger',
        action: async (selectedRows: any[]) => {
          try {
            await ElMessageBox.confirm(
              t('common.messages.confirmDelete'),
              t('common.dialog.confirmTitle'),
              { type: 'warning' }
            )
            const ids = selectedRows.map((row: any) => row.id)
            await apiClient.value.batchDelete(ids)
            ElMessage.success(t('common.messages.deleteSuccess'))
            tableRef.value?.refresh()
          } catch (error: any) {
            if (error !== 'cancel') {
              ElMessage.error(error.message || t('common.messages.deleteFailed'))
            }
          }
        },
      },
    ]
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
    const nextParams = { ...(params || {}) }
    const keyword = String(nextParams.__unifiedKeyword || '').trim()
    const selectedField = String(nextParams.__unifiedField || '__all').trim()
    const visibleFieldCodeSet = new Set(
      (Array.isArray(nextParams.__visibleFieldCodes) ? nextParams.__visibleFieldCodes : [])
        .map((item: any) => String(item || '').trim())
        .filter(Boolean)
    )
    const constrainedFieldCodes = unifiedSearchFieldOptions.value
      .map((item) => String(item?.value || '').trim())
      .filter((value) => !visibleFieldCodeSet.size || visibleFieldCodeSet.has(value))

    delete nextParams.__unifiedKeyword
    delete nextParams.__unifiedField
    delete nextParams.__unifiedSearch
    delete nextParams.__visibleFieldCodes
    delete nextParams.searchFields
    delete nextParams.search_fields

    if (keyword) {
      if (selectedField && selectedField !== '__all') {
        nextParams[selectedField] = keyword
      } else if (constrainedFieldCodes.length) {
        nextParams.search = keyword
        nextParams.searchFields = constrainedFieldCodes.join(',')
      } else {
        nextParams.search = keyword
      }
    }

    currentSearchParams.value = { ...nextParams }
    return apiClient.value.list(nextParams)
  }

  const handleView = (row: any) => {
    router.push(`/objects/${objectCode.value}/${row.id || row.id}`)
  }

  const handleRowClick = (row: any) => {
    handleView(row)
  }

  const handleCreate = () => {
    router.push(`/objects/${encodeURIComponent(objectCode.value)}/create`)
  }

  const handleLayoutSettings = () => {
    router.push({
      path: '/system/page-layouts',
      query: {
        objectCode: objectCode.value,
        objectName: objectDisplayName.value || objectCode.value,
      },
    })
  }

  const handleEdit = (row: any) => {
    const recordId = row?.id || row?._id
    if (!recordId) {
      ElMessage.error(t('common.messages.operationFailed'))
      return
    }

    router.push(`/objects/${encodeURIComponent(objectCode.value)}/${encodeURIComponent(String(recordId))}/edit`)
  }

  const handleDelete = async (row: any) => {
    try {
      await ElMessageBox.confirm(
        t('common.messages.confirmDeleteMessage'),
        t('common.dialog.confirmTitle'),
        { type: 'warning' }
      )
      await apiClient.value.delete(row.id)
      ElMessage.success(t('common.messages.deleteSuccess'))
      tableRef.value?.refresh()
    } catch (error: any) {
      if (error !== 'cancel') {
        ElMessage.error(error.message || t('common.messages.deleteFailed'))
      }
    }
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

  const getStatusType = (status: string) => {
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

  const getStatusLabel = (status: string) => {
    const normalized = String(status || '').trim().toLowerCase()
    if (!normalized) return ''
    const statusKey = `common.status.${normalized}`
    return te(statusKey) ? t(statusKey) : normalized
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
    handleRowClick,
    handleView,
    hasStatusField,
    importParseResult,
    showFieldSelector,
    showImportConfig,
    slotFields,
  }
}
