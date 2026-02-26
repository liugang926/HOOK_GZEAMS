import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
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

// Integration Configs
export const integrationConfigApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request
      .get('/integration/configs/', {
        params: normalizeQueryParams(params, { preserveKeys: ['page', 'page_size'] }),
      })
      .then((res) => {
        const page = toPaginated(res)
        return {
          ...page,
          results: toCamelDeep(page.results),
        }
      })
  },

  detail(id: string): Promise<any> {
    return request.get(`/integration/configs/${id}/`).then((res) => toCamelDeep(toData(res)))
  },

  create(data: any): Promise<ApiActionResult<any>> {
    return request
      .post('/integration/configs/', data, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data),
        }
      })
  },

  update(id: string, data: any): Promise<ApiActionResult<any>> {
    return request
      .put(`/integration/configs/${id}/`, data, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data),
        }
      })
  },

  delete(id: string): Promise<ApiActionResult<void>> {
    return request.delete(`/integration/configs/${id}/`, { unwrap: 'none' }).then((res) => toActionResult(res))
  },

  test(id: string): Promise<ApiActionResult<any>> {
    return request
      .post(`/integration/configs/${id}/test/`, undefined, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data),
        }
      })
  },

  sync(id: string): Promise<ApiActionResult<any>> {
    return request
      .post(`/integration/configs/${id}/sync/`, undefined, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data),
        }
      })
  }
}

// Sync Tasks
export const syncTaskApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request
      .get('/integration/sync-tasks/', {
        params: normalizeQueryParams(params, { preserveKeys: ['page', 'page_size'] }),
      })
      .then((res) => {
        const page = toPaginated(res)
        return {
          ...page,
          results: toCamelDeep(page.results),
        }
      })
  },

  detail(id: string): Promise<any> {
    return request.get(`/integration/sync-tasks/${id}/`).then((res) => toCamelDeep(toData(res)))
  },

  execute(id: string): Promise<ApiActionResult<any>> {
    return request
      .post(`/integration/sync-tasks/${id}/execute/`, undefined, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data),
        }
      })
  },

  cancel(id: string): Promise<ApiActionResult<any>> {
    return request
      .post(`/integration/sync-tasks/${id}/cancel/`, undefined, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data),
        }
      })
  }
}

// Integration Logs
export const integrationLogApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request
      .get('/integration/logs/', {
        params: normalizeQueryParams(params, { preserveKeys: ['page', 'page_size'] }),
      })
      .then((res) => {
        const page = toPaginated(res)
        return {
          ...page,
          results: toCamelDeep(page.results),
        }
      })
  },

  detail(id: string): Promise<any> {
    return request.get(`/integration/logs/${id}/`).then((res) => toCamelDeep(toData(res)))
  },

  retry(id: string): Promise<ApiActionResult<any>> {
    return request
      .post(`/integration/logs/${id}/retry/`, undefined, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data),
        }
      })
  }
}

// Data Mapping Templates
export const dataMappingApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request
      .get('/integration/mappings/', {
        params: normalizeQueryParams(params, { preserveKeys: ['page', 'page_size'] }),
      })
      .then((res) => {
        const page = toPaginated(res)
        return {
          ...page,
          results: toCamelDeep(page.results),
        }
      })
  },

  detail(id: string): Promise<any> {
    return request.get(`/integration/mappings/${id}/`).then((res) => toCamelDeep(toData(res)))
  },

  create(data: any): Promise<ApiActionResult<any>> {
    return request
      .post('/integration/mappings/', data, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data),
        }
      })
  },

  update(id: string, data: any): Promise<ApiActionResult<any>> {
    return request
      .put(`/integration/mappings/${id}/`, data, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data),
        }
      })
  },

  delete(id: string): Promise<ApiActionResult<void>> {
    return request.delete(`/integration/mappings/${id}/`, { unwrap: 'none' }).then((res) => toActionResult(res))
  },

  test(id: string, data: any): Promise<ApiActionResult<any>> {
    return request
      .post(`/integration/mappings/${id}/test/`, data, { unwrap: 'none' })
      .then((res) => {
        const result = toActionResult(res)
        return {
          ...result,
          data: toCamelDeep(result.data),
        }
      })
  }
}

// Legacy function exports for backward compatibility
export const getIntegrationConfigList = integrationConfigApi.list
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
