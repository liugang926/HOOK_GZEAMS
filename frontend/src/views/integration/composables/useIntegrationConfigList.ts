import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { integrationConfigApi, integrationLogApi } from '@/api/integration'
import type {
  IntegrationConfig,
  IntegrationConfigListParams,
  IntegrationFilterForm,
  IntegrationFormData,
  IntegrationLog,
  IntegrationLogListParams,
  IntegrationStats
} from '@/types/integration'
import { createDefaultIntegrationFormData } from '@/views/integration/integrationConfig.constants'

interface PaginationState {
  page: number
  pageSize: number
  total: number
}

const buildStats = (rows: IntegrationConfig[], total: number): IntegrationStats => ({
  total,
  healthy: rows.filter((row) => row.healthStatus === 'healthy').length,
  degraded: rows.filter((row) => row.healthStatus === 'degraded').length,
  unhealthy: rows.filter((row) => row.healthStatus === 'unhealthy').length
})

const createPagination = (): PaginationState => ({
  page: 1,
  pageSize: 20,
  total: 0
})

export const useIntegrationConfigList = () => {
  const { t } = useI18n()

  const loading = ref(false)
  const tableData = ref<IntegrationConfig[]>([])
  const dialogVisible = ref(false)
  const logsDrawerVisible = ref(false)
  const logDetailVisible = ref(false)
  const submitting = ref(false)
  const testing = ref<Record<string, boolean>>({})
  const syncing = ref<Record<string, boolean>>({})
  const logsLoading = ref(false)

  const currentConfig = ref<IntegrationConfig | null>(null)
  const currentLog = ref<IntegrationLog | null>(null)
  const logs = ref<IntegrationLog[]>([])

  const filterForm = reactive<IntegrationFilterForm>({
    systemType: undefined,
    isEnabled: undefined,
    healthStatus: undefined
  })

  const pagination = reactive<PaginationState>(createPagination())
  const logsPagination = reactive<PaginationState>(createPagination())

  const stats = ref<IntegrationStats>({
    total: 0,
    healthy: 0,
    degraded: 0,
    unhealthy: 0
  })

  const isEdit = ref(false)

  const formData = ref<IntegrationFormData>(createDefaultIntegrationFormData())

  const fetchData = async () => {
    loading.value = true
    try {
      const listParams: IntegrationConfigListParams = {
        page: pagination.page,
        page_size: pagination.pageSize
      }
      const statsParams: Omit<IntegrationConfigListParams, 'page' | 'page_size'> = {}

      if (filterForm.systemType) {
        listParams.systemType = filterForm.systemType
        statsParams.systemType = filterForm.systemType
      }
      if (filterForm.isEnabled !== undefined) {
        listParams.isEnabled = filterForm.isEnabled
        statsParams.isEnabled = filterForm.isEnabled
      }
      if (filterForm.healthStatus) {
        listParams.healthStatus = filterForm.healthStatus
        statsParams.healthStatus = filterForm.healthStatus
      }

      const [listResult, statsResult] = await Promise.allSettled([
        integrationConfigApi.list(listParams),
        integrationConfigApi.stats(statsParams)
      ])

      if (listResult.status === 'rejected') {
        throw listResult.reason
      }

      const rows = listResult.value.results || []
      const total = listResult.value.count || 0

      tableData.value = rows
      pagination.total = total
      stats.value = statsResult.status === 'fulfilled'
        ? statsResult.value
        : buildStats(rows, total)
    } catch {
      ElMessage.error(t('integration.messages.loadConfigsFailed'))
    } finally {
      loading.value = false
    }
  }

  const handleFilterReset = () => {
    filterForm.systemType = undefined
    filterForm.isEnabled = undefined
    filterForm.healthStatus = undefined
    pagination.page = 1
    void fetchData()
  }

  const handlePageChange = (page: number) => {
    pagination.page = page
    void fetchData()
  }

  const handlePageSizeChange = (pageSize: number) => {
    pagination.page = 1
    pagination.pageSize = pageSize
    void fetchData()
  }

  const handleCreate = () => {
    isEdit.value = false
    currentConfig.value = null
    formData.value = createDefaultIntegrationFormData()
    dialogVisible.value = true
  }

  const handleEdit = (row: IntegrationConfig) => {
    isEdit.value = true
    formData.value = {
      systemType: row.systemType,
      systemName: row.systemName,
      isEnabled: row.isEnabled,
      enabledModules: row.enabledModules || [],
      connectionConfig: {
        apiUrl: '',
        apiKey: '',
        apiSecret: '',
        timeout: 30,
        ...(row.connectionConfig || {})
      },
      syncConfig: {
        autoSync: false,
        interval: 60,
        ...(row.syncConfig || {})
      }
    }
    currentConfig.value = row
    dialogVisible.value = true
  }

  const handleSubmit = async (payload: IntegrationFormData) => {
    submitting.value = true
    try {
      if (isEdit.value && currentConfig.value) {
        await integrationConfigApi.update(currentConfig.value.id, payload)
        ElMessage.success(t('integration.messages.updatedSuccessfully'))
      } else {
        await integrationConfigApi.create(payload)
        ElMessage.success(t('integration.messages.createdSuccessfully'))
      }
      dialogVisible.value = false
      void fetchData()
    } catch {
      ElMessage.error(t('integration.messages.operationFailed'))
    } finally {
      submitting.value = false
    }
  }

  const handleDelete = async (row: IntegrationConfig) => {
    try {
      await integrationConfigApi.delete(row.id)
      ElMessage.success(t('integration.messages.deletedSuccessfully'))
      void fetchData()
    } catch {
      ElMessage.error(t('integration.messages.deleteFailed'))
    }
  }

  const handleTest = async (row: IntegrationConfig) => {
    testing.value[row.id] = true
    try {
      const res = await integrationConfigApi.test(row.id)
      if (res.success) {
        ElMessage.success(res.message || t('integration.messages.connectionTestSuccess'))
      } else {
        ElMessage.warning(res.message || t('integration.messages.connectionTestFailed'))
      }
      void fetchData()
    } catch {
      ElMessage.error(t('integration.messages.connectionTestFailed'))
    } finally {
      testing.value[row.id] = false
    }
  }

  const handleSync = async (row: IntegrationConfig) => {
    syncing.value[row.id] = true
    try {
      const res = await integrationConfigApi.sync(row.id)
      if (res.success) {
        ElMessage.success(res.message || t('integration.messages.syncTaskCreated'))
      } else {
        ElMessage.warning(res.message || t('integration.messages.syncFailed'))
      }
      void fetchData()
    } catch {
      ElMessage.error(t('integration.messages.syncFailed'))
    } finally {
      syncing.value[row.id] = false
    }
  }

  const handleViewLogs = (row: IntegrationConfig) => {
    currentConfig.value = row
    logsDrawerVisible.value = true
    logsPagination.page = 1
    void fetchLogs()
  }

  const fetchLogs = async () => {
    if (!currentConfig.value) return

    logsLoading.value = true
    try {
      const params: IntegrationLogListParams = {
        page: logsPagination.page,
        page_size: logsPagination.pageSize,
        systemType: currentConfig.value.systemType
      }
      const res = await integrationLogApi.list(params)
      logs.value = res.results || []
      logsPagination.total = res.count || 0
    } catch {
      ElMessage.error(t('integration.messages.loadLogsFailed'))
    } finally {
      logsLoading.value = false
    }
  }

  const handleLogsPageChange = (page: number) => {
    logsPagination.page = page
    void fetchLogs()
  }

  const handleLogsPageSizeChange = (pageSize: number) => {
    logsPagination.page = 1
    logsPagination.pageSize = pageSize
    void fetchLogs()
  }

  const handleViewLogDetail = (log: IntegrationLog) => {
    currentLog.value = log
    logDetailVisible.value = true
  }

  return {
    loading,
    tableData,
    dialogVisible,
    logsDrawerVisible,
    logDetailVisible,
    submitting,
    testing,
    syncing,
    logsLoading,
    currentConfig,
    currentLog,
    logs,
    filterForm,
    pagination,
    logsPagination,
    stats,
    isEdit,
    formData,
    fetchData,
    handleFilterReset,
    handlePageChange,
    handlePageSizeChange,
    handleCreate,
    handleEdit,
    handleSubmit,
    handleDelete,
    handleTest,
    handleSync,
    handleViewLogs,
    fetchLogs,
    handleLogsPageChange,
    handleLogsPageSizeChange,
    handleViewLogDetail
  }
}
