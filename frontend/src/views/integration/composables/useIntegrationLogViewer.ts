import { reactive, ref, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { integrationLogApi } from '@/api/integration'
import type {
  IntegrationConfig,
  IntegrationLog,
  IntegrationLogListParams,
  IntegrationSystemType
} from '@/types/integration'
import {
  createLatestRequestGuard,
  createIntegrationPaginationState,
  type IntegrationPaginationState,
  type IntegrationTranslate
} from '@/views/integration/composables/integrationConfig.shared'

interface UseIntegrationLogViewerOptions {
  t: IntegrationTranslate
}

export interface UseIntegrationLogViewerReturn {
  logsDrawerVisible: Ref<boolean>
  logDetailVisible: Ref<boolean>
  logsLoading: Ref<boolean>
  currentConfig: Ref<IntegrationConfig | null>
  currentLog: Ref<IntegrationLog | null>
  logs: Ref<IntegrationLog[]>
  logsPagination: IntegrationPaginationState
  fetchLogs: () => Promise<void>
  handleViewLogs: (row: IntegrationConfig) => void
  handleLogsPageChange: (page: number) => void
  handleLogsPageSizeChange: (pageSize: number) => void
  handleViewLogDetail: (log: IntegrationLog) => void
}

export const useIntegrationLogViewer = ({ t }: UseIntegrationLogViewerOptions): UseIntegrationLogViewerReturn => {
  const logsDrawerVisible = ref(false)
  const logDetailVisible = ref(false)
  const logsLoading = ref(false)
  const latestRequest = createLatestRequestGuard()
  const currentConfig = ref<IntegrationConfig | null>(null)
  const currentLog = ref<IntegrationLog | null>(null)
  const logs = ref<IntegrationLog[]>([])
  const logsPagination = reactive<IntegrationPaginationState>(createIntegrationPaginationState())

  const fetchLogs = async () => {
    if (!currentConfig.value) return

    const requestId = latestRequest.begin()
    logsLoading.value = true
    try {
      const params: IntegrationLogListParams = {
        page: logsPagination.page,
        page_size: logsPagination.pageSize,
        systemType: currentConfig.value.systemType as IntegrationSystemType
      }
      const res = await integrationLogApi.list(params)
      if (!latestRequest.isActive(requestId)) {
        return
      }
      logs.value = res.results || []
      logsPagination.total = res.count || 0
    } catch {
      if (!latestRequest.isActive(requestId)) {
        return
      }
      ElMessage.error(t('integration.messages.loadLogsFailed'))
    } finally {
      if (latestRequest.isActive(requestId)) {
        logsLoading.value = false
      }
    }
  }

  const handleViewLogs = (row: IntegrationConfig) => {
    currentConfig.value = row
    logsDrawerVisible.value = true
    logsPagination.page = 1
    void fetchLogs()
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
    logsDrawerVisible,
    logDetailVisible,
    logsLoading,
    currentConfig,
    currentLog,
    logs,
    logsPagination,
    fetchLogs,
    handleViewLogs,
    handleLogsPageChange,
    handleLogsPageSizeChange,
    handleViewLogDetail
  }
}
