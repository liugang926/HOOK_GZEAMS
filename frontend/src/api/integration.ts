import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  IntegrationConfig,
  IntegrationConfigListParams,
  IntegrationFormData,
  IntegrationLog,
  IntegrationLogListParams,
  IntegrationStats,
} from '@/types/integration'
import {
  normalizeQueryParams,
  toActionResult,
  toCamelDeep,
  toData,
  toPaginated,
  type ApiActionResult,
} from '@/api/contract'

/**
 * Integration Management API Client
 * Handles third-party integrations, sync tasks, logs, and data mappings
 */

type IntegrationLooseRecord = Record<string, unknown>
type IntegrationLooseParams = Record<string, unknown>
type SyncTaskDetail = IntegrationLooseRecord & {
  status?: string
  statusDisplay?: string
  status_display?: string
}

// Integration Configs
export const integrationConfigApi = {
  list(params?: IntegrationConfigListParams): Promise<PaginatedResponse<IntegrationConfig>> {
    return request
      .get('/integration/configs/', {
        params: normalizeQueryParams(params, { preserveKeys: ['page', 'page_size'] }),
      })
      .then((res) => {
        const page = toPaginated(res)
        return {
          ...page,
          results: toCamelDeep(page.results) as IntegrationConfig[],
        }
      })
  },

  stats(params?: Omit<IntegrationConfigListParams, 'page' | 'page_size'>): Promise<IntegrationStats> {
    return request
      .get('/integration/configs/stats/', {
        params: normalizeQueryParams(params),
      })
      .then((res) => toCamelDeep(toData(res)) as IntegrationStats)
  },

  detail(id: string): Promise<IntegrationConfig> {
    return request.get(`/integration/configs/${id}/`).then((res) => toCamelDeep(toData(res)) as IntegrationConfig)
  },

  create(data: IntegrationFormData): Promise<ApiActionResult<IntegrationConfig>> {
    return request
      .post('/integration/configs/', data, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data) as IntegrationConfig | undefined,
        }
      })
  },

  update(id: string, data: IntegrationFormData): Promise<ApiActionResult<IntegrationConfig>> {
    return request
      .put(`/integration/configs/${id}/`, data, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data) as IntegrationConfig | undefined,
        }
      })
  },

  delete(id: string): Promise<ApiActionResult<void>> {
    return request.delete(`/integration/configs/${id}/`, { unwrap: 'none' }).then((res) => toActionResult(res))
  },

  test(id: string): Promise<ApiActionResult<Record<string, unknown>>> {
    return request
      .post(`/integration/configs/${id}/test/`, undefined, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data) as Record<string, unknown> | undefined,
        }
      })
  },

  sync(id: string): Promise<ApiActionResult<Record<string, unknown>>> {
    return request
      .post(`/integration/configs/${id}/sync/`, undefined, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data) as Record<string, unknown> | undefined,
        }
      })
  }
}

// Sync Tasks
export const syncTaskApi = {
  list(params?: IntegrationLooseParams): Promise<PaginatedResponse<IntegrationLooseRecord>> {
    return request
      .get('/integration/sync-tasks/', {
        params: normalizeQueryParams(params, { preserveKeys: ['page', 'page_size'] }),
      })
      .then((res) => {
        const page = toPaginated(res)
        return {
          ...page,
          results: toCamelDeep(page.results) as IntegrationLooseRecord[],
        }
      })
  },

  detail(id: string): Promise<SyncTaskDetail> {
    return request
      .get(`/integration/sync-tasks/${id}/`)
      .then((res) => toCamelDeep(toData(res)) as SyncTaskDetail)
  },

  execute(id: string): Promise<ApiActionResult<IntegrationLooseRecord>> {
    return request
      .post(`/integration/sync-tasks/${id}/execute/`, undefined, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data) as IntegrationLooseRecord | undefined,
        }
      })
  },

  cancel(id: string): Promise<ApiActionResult<IntegrationLooseRecord>> {
    return request
      .post(`/integration/sync-tasks/${id}/cancel/`, undefined, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data) as IntegrationLooseRecord | undefined,
        }
      })
  }
}

// Integration Logs
export const integrationLogApi = {
  list(params?: IntegrationLogListParams): Promise<PaginatedResponse<IntegrationLog>> {
    return request
      .get('/integration/logs/', {
        params: normalizeQueryParams(params, { preserveKeys: ['page', 'page_size'] }),
      })
      .then((res) => {
        const page = toPaginated(res)
        return {
          ...page,
          results: toCamelDeep(page.results) as IntegrationLog[],
        }
      })
  },

  detail(id: string): Promise<IntegrationLog> {
    return request.get(`/integration/logs/${id}/`).then((res) => toCamelDeep(toData(res)) as IntegrationLog)
  },

  retry(id: string): Promise<ApiActionResult<Record<string, unknown>>> {
    return request
      .post(`/integration/logs/${id}/retry/`, undefined, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data) as Record<string, unknown> | undefined,
        }
      })
  }
}

// Data Mapping Templates
export const dataMappingApi = {
  list(params?: IntegrationLooseParams): Promise<PaginatedResponse<IntegrationLooseRecord>> {
    return request
      .get('/integration/mappings/', {
        params: normalizeQueryParams(params, { preserveKeys: ['page', 'page_size'] }),
      })
      .then((res) => {
        const page = toPaginated(res)
        return {
          ...page,
          results: toCamelDeep(page.results) as IntegrationLooseRecord[],
        }
      })
  },

  detail(id: string): Promise<IntegrationLooseRecord> {
    return request.get(`/integration/mappings/${id}/`).then((res) => toCamelDeep(toData(res)) as IntegrationLooseRecord)
  },

  create(data: IntegrationLooseRecord): Promise<ApiActionResult<IntegrationLooseRecord>> {
    return request
      .post('/integration/mappings/', data, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data) as IntegrationLooseRecord | undefined,
        }
      })
  },

  update(id: string, data: IntegrationLooseRecord): Promise<ApiActionResult<IntegrationLooseRecord>> {
    return request
      .put(`/integration/mappings/${id}/`, data, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data) as IntegrationLooseRecord | undefined,
        }
      })
  },

  delete(id: string): Promise<ApiActionResult<void>> {
    return request.delete(`/integration/mappings/${id}/`, { unwrap: 'none' }).then((res) => toActionResult(res))
  },

  test(id: string, data: IntegrationLooseRecord): Promise<ApiActionResult<IntegrationLooseRecord>> {
    return request
      .post(`/integration/mappings/${id}/test/`, data, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data) as IntegrationLooseRecord | undefined,
        }
      })
  }
}

// Legacy function exports for backward compatibility
export const getIntegrationConfigList = integrationConfigApi.list
export const getIntegrationConfigStats = integrationConfigApi.stats
export const getIntegrationConfigDetail = integrationConfigApi.detail
export const createIntegrationConfig = integrationConfigApi.create
export const updateIntegrationConfig = integrationConfigApi.update
export const deleteIntegrationConfig = integrationConfigApi.delete
export const testIntegrationConnection = integrationConfigApi.test
export const syncIntegrationData = integrationConfigApi.sync

export const getSyncTaskList = syncTaskApi.list
export const getSyncTaskDetail = syncTaskApi.detail
export const executeSyncTask = syncTaskApi.execute
export const cancelSyncTask = syncTaskApi.cancel

export const getIntegrationLogList = integrationLogApi.list
export const getIntegrationLogDetail = integrationLogApi.detail
export const retryIntegrationLog = integrationLogApi.retry

export const getDataMappingTemplateList = dataMappingApi.list
export const getDataMappingTemplateDetail = dataMappingApi.detail
export const createDataMappingTemplate = dataMappingApi.create
export const updateDataMappingTemplate = dataMappingApi.update
export const deleteDataMappingTemplate = dataMappingApi.delete
export const testDataMapping = dataMappingApi.test
