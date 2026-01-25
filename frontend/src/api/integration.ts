import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

/**
 * Integration Management API Client
 * Handles third-party integrations, sync tasks, logs, and data mappings
 */

// Integration Configs
export const integrationConfigApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/integration/configs/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/integration/configs/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/integration/configs/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/integration/configs/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/integration/configs/${id}/`)
  },

  test(id: string): Promise<any> {
    return request.post(`/integration/configs/${id}/test/`)
  },

  sync(id: string): Promise<any> {
    return request.post(`/integration/configs/${id}/sync/`)
  }
}

// Sync Tasks
export const syncTaskApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/integration/sync-tasks/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/integration/sync-tasks/${id}/`)
  },

  execute(id: string): Promise<void> {
    return request.post(`/integration/sync-tasks/${id}/execute/`)
  },

  cancel(id: string): Promise<void> {
    return request.post(`/integration/sync-tasks/${id}/cancel/`)
  }
}

// Integration Logs
export const integrationLogApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/integration/logs/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/integration/logs/${id}/`)
  },

  retry(id: string): Promise<void> {
    return request.post(`/integration/logs/${id}/retry/`)
  }
}

// Data Mapping Templates
export const dataMappingApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/integration/mappings/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/integration/mappings/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/integration/mappings/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/integration/mappings/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/integration/mappings/${id}/`)
  },

  test(id: string, data: any): Promise<any> {
    return request.post(`/integration/mappings/${id}/test/`, data)
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
