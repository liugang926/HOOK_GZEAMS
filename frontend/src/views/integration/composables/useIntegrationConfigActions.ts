import { ref, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { integrationConfigApi } from '@/api/integration'
import type { IntegrationConfig, IntegrationFormData } from '@/types/integration'
import { createDefaultIntegrationFormData } from '@/views/integration/integrationConfig.constants'
import type { IntegrationTranslate } from '@/views/integration/composables/integrationConfig.shared'
import {
  buildIntegrationFormDataFromConfig,
  runFlagIntegrationAction,
  runIntegrationAction,
  runRowIntegrationAction
} from '@/views/integration/composables/integrationConfigActions.helpers'

interface UseIntegrationConfigActionsOptions {
  t: IntegrationTranslate
  refresh: () => Promise<void>
}

export interface UseIntegrationConfigActionsReturn {
  editingConfig: Ref<IntegrationConfig | null>
  dialogVisible: Ref<boolean>
  submitting: Ref<boolean>
  testing: Ref<Record<string, boolean>>
  syncing: Ref<Record<string, boolean>>
  isEdit: Ref<boolean>
  formData: Ref<IntegrationFormData>
  handleCreate: () => void
  handleEdit: (row: IntegrationConfig) => void
  handleSubmit: (payload: IntegrationFormData) => Promise<void>
  handleDelete: (row: IntegrationConfig) => Promise<void>
  handleTest: (row: IntegrationConfig) => Promise<void>
  handleSync: (row: IntegrationConfig) => Promise<void>
}

export const useIntegrationConfigActions = (
  { t, refresh }: UseIntegrationConfigActionsOptions
): UseIntegrationConfigActionsReturn => {
  const editingConfig = ref<IntegrationConfig | null>(null)
  const dialogVisible = ref(false)
  const submitting = ref(false)
  const testing = ref<Record<string, boolean>>({})
  const syncing = ref<Record<string, boolean>>({})
  const isEdit = ref(false)
  const formData = ref<IntegrationFormData>(createDefaultIntegrationFormData())

  const refreshList = () => {
    void refresh()
  }
  const notifier = {
    success: (message: string) => ElMessage.success(message),
    warning: (message: string) => ElMessage.warning(message),
    error: (message: string) => ElMessage.error(message)
  }

  const handleCreate = () => {
    isEdit.value = false
    editingConfig.value = null
    formData.value = createDefaultIntegrationFormData()
    dialogVisible.value = true
  }

  const handleEdit = (row: IntegrationConfig) => {
    isEdit.value = true
    formData.value = buildIntegrationFormDataFromConfig(row)
    editingConfig.value = row
    dialogVisible.value = true
  }

  const handleSubmit = async (payload: IntegrationFormData) => {
    await runFlagIntegrationAction({
      loadingFlag: submitting,
      notifier,
      messages: {
        successFallback: isEdit.value
          ? t('integration.messages.updatedSuccessfully')
          : t('integration.messages.createdSuccessfully'),
        failureFallback: t('integration.messages.operationFailed'),
        errorFallback: t('integration.messages.operationFailed')
      },
      invoke: () => (
        isEdit.value && editingConfig.value
          ? integrationConfigApi.update(editingConfig.value.id, payload)
          : integrationConfigApi.create(payload)
      ),
      onSuccess: () => {
        if (isEdit.value && editingConfig.value) {
          editingConfig.value = null
        }
        dialogVisible.value = false
        refreshList()
      }
    })
  }

  const handleDelete = async (row: IntegrationConfig) => {
    await runIntegrationAction({
      notifier,
      messages: {
        successFallback: t('integration.messages.deletedSuccessfully'),
        failureFallback: t('integration.messages.deleteFailed'),
        errorFallback: t('integration.messages.deleteFailed')
      },
      invoke: () => integrationConfigApi.delete(row.id),
      onSuccess: () => {
        refreshList()
      }
    })
  }

  const handleTest = async (row: IntegrationConfig) => {
    await runRowIntegrationAction({
      loadingMap: testing,
      rowId: row.id,
      notifier,
      messages: {
        successFallback: t('integration.messages.connectionTestSuccess'),
        failureFallback: t('integration.messages.connectionTestFailed'),
        errorFallback: t('integration.messages.connectionTestFailed')
      },
      invoke: () => integrationConfigApi.test(row.id),
      onSuccess: () => {
        refreshList()
      },
      onFailure: () => {
        refreshList()
      }
    })
  }

  const handleSync = async (row: IntegrationConfig) => {
    await runRowIntegrationAction({
      loadingMap: syncing,
      rowId: row.id,
      notifier,
      messages: {
        successFallback: t('integration.messages.syncTaskCreated'),
        failureFallback: t('integration.messages.syncFailed'),
        errorFallback: t('integration.messages.syncFailed')
      },
      invoke: () => integrationConfigApi.sync(row.id),
      onSuccess: () => {
        refreshList()
      },
      onFailure: () => {
        refreshList()
      }
    })
  }

  return {
    editingConfig,
    dialogVisible,
    submitting,
    testing,
    syncing,
    isEdit,
    formData,
    handleCreate,
    handleEdit,
    handleSubmit,
    handleDelete,
    handleTest,
    handleSync
  }
}
