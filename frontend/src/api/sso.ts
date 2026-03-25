import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

/**
 * SSO Management API Client
 * Handles single sign-on configs, user mappings, and sync operations
 */

// SSO Configs (WeWork, DingTalk, Feishu)
export const ssoConfigApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/sso/configs/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/sso/configs/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/sso/configs/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/sso/configs/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/sso/configs/${id}/`)
  },

  test(id: string): Promise<any> {
    return request.post(`/sso/configs/${id}/test/`)
  }
}

// User Mappings
export const userMappingApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/sso/mappings/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/sso/mappings/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/sso/mappings/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/sso/mappings/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/sso/mappings/${id}/`)
  },

  sync(id: string): Promise<void> {
    return request.post(`/sso/mappings/${id}/sync/`)
  }
}

// Sync Tasks
export const ssoSyncApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/sso/sync/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/sso/sync/${id}/`)
  },

  execute(platform: string): Promise<void> {
    return request.post(`/sso/sync/${platform}/execute/`)
  },

  getLogs(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/sso/sync/logs/', { params })
  }
}

// Legacy function exports for backward compatibility
export const getWeWorkConfigList = ssoConfigApi.list
export const getWeWorkConfigDetail = ssoConfigApi.detail
export const createWeWorkConfig = ssoConfigApi.create
export const updateWeWorkConfig = ssoConfigApi.update
export const deleteWeWorkConfig = ssoConfigApi.delete
export const testWeWorkConnection = ssoConfigApi.test

export const getUserMappingList = userMappingApi.list
export const getUserMappingDetail = userMappingApi.detail
export const createUserMapping = userMappingApi.create
export const updateUserMapping = userMappingApi.update
export const deleteUserMapping = userMappingApi.delete
export const syncUserMapping = userMappingApi.sync

export const getSyncTaskList = ssoSyncApi.list
export const getSyncTaskDetail = ssoSyncApi.detail
export const executeSyncTask = ssoSyncApi.execute
export const getSyncLogList = ssoSyncApi.getLogs
