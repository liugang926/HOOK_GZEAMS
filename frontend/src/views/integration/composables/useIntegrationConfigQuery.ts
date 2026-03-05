import { reactive, ref, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { integrationConfigApi } from '@/api/integration'
import type {
  IntegrationConfig,
  IntegrationFilterForm,
  IntegrationStats
} from '@/types/integration'
import { buildIntegrationConfigQueryParams } from '@/views/integration/composables/integrationConfigQuery.params'
import {
  buildIntegrationStatsFromRows,
  createEmptyIntegrationStats
} from '@/views/integration/composables/integrationConfigStats'
import {
  createLatestRequestGuard,
  createIntegrationPaginationState,
  type IntegrationPaginationState,
  type IntegrationTranslate
} from '@/views/integration/composables/integrationConfig.shared'

interface UseIntegrationConfigQueryOptions {
  t: IntegrationTranslate
}

export interface UseIntegrationConfigQueryReturn {
  loading: Ref<boolean>
  tableData: Ref<IntegrationConfig[]>
  filterForm: IntegrationFilterForm
  pagination: IntegrationPaginationState
  stats: Ref<IntegrationStats>
  fetchData: () => Promise<void>
  handleFilterReset: () => void
  handlePageChange: (page: number) => void
  handlePageSizeChange: (pageSize: number) => void
}

export const useIntegrationConfigQuery = ({ t }: UseIntegrationConfigQueryOptions): UseIntegrationConfigQueryReturn => {
  const loading = ref(false)
  const tableData = ref<IntegrationConfig[]>([])
  const latestRequest = createLatestRequestGuard()
  const filterForm = reactive<IntegrationFilterForm>({
    systemType: undefined,
    isEnabled: undefined,
    healthStatus: undefined
  })
  const pagination = reactive<IntegrationPaginationState>(createIntegrationPaginationState())
  const stats = ref(createEmptyIntegrationStats())

  const fetchData = async () => {
    const requestId = latestRequest.begin()
    loading.value = true
    try {
      const { listParams, statsParams } = buildIntegrationConfigQueryParams(filterForm, {
        page: pagination.page,
        pageSize: pagination.pageSize
      })

      const [listResult, statsResult] = await Promise.allSettled([
        integrationConfigApi.list(listParams),
        integrationConfigApi.stats(statsParams)
      ])

      if (listResult.status === 'rejected') {
        throw listResult.reason
      }

      const rows = listResult.value.results || []
      const total = listResult.value.count || 0

      if (!latestRequest.isActive(requestId)) {
        return
      }

      tableData.value = rows
      pagination.total = total
      stats.value = statsResult.status === 'fulfilled'
        ? statsResult.value
        : buildIntegrationStatsFromRows(rows, total)
    } catch {
      if (!latestRequest.isActive(requestId)) {
        return
      }
      ElMessage.error(t('integration.messages.loadConfigsFailed'))
    } finally {
      if (latestRequest.isActive(requestId)) {
        loading.value = false
      }
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

  return {
    loading,
    tableData,
    filterForm,
    pagination,
    stats,
    fetchData,
    handleFilterReset,
    handlePageChange,
    handlePageSizeChange
  }
}
