import type {
  IntegrationConfigListParams,
  IntegrationConfigStatsParams,
  IntegrationFilterForm
} from '@/types/integration'
import type { IntegrationPageRequest } from '@/views/integration/composables/integrationConfig.shared'

export interface BuildIntegrationConfigQueryParamsResult {
  listParams: IntegrationConfigListParams
  statsParams: IntegrationConfigStatsParams
}

export const buildIntegrationConfigQueryParams = (
  filterForm: IntegrationFilterForm,
  pagination: IntegrationPageRequest
): BuildIntegrationConfigQueryParamsResult => {
  const listParams: IntegrationConfigListParams = {
    page: pagination.page,
    page_size: pagination.pageSize
  }
  const statsParams: IntegrationConfigStatsParams = {}

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

  return {
    listParams,
    statsParams
  }
}
