import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

/**
 * Mobile Enhancement API Client
 * Handles mobile devices, sync, approvals, and delegates
 */

// Mobile Devices
export const mobileDeviceApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/mobile/devices/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/mobile/devices/${id}/`)
  },

  register(data: any): Promise<any> {
    return request.post('/mobile/devices/register/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/mobile/devices/${id}/`, data)
  },

  unbind(id: string): Promise<void> {
    return request.post(`/mobile/devices/${id}/unbind/`)
  },

  getMyDevices(): Promise<any> {
    return request.get('/mobile/devices/my_devices/')
  }
}

// Security Logs
export const securityLogApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/mobile/security-logs/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/mobile/security-logs/${id}/`)
  }
}

// Data Sync
export const mobileSyncApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/mobile/sync/', { params })
  },

  uploadOfflineData(data: any): Promise<any> {
    return request.post('/mobile/sync/upload/', data)
  },

  downloadServerChanges(params: any): Promise<any> {
    return request.post('/mobile/sync/download/', params)
  },

  resolveConflict(id: string, data: any): Promise<void> {
    return request.post('/mobile/sync/resolve_conflict/', { conflict_id: id, ...data })
  },

  getPendingCount(): Promise<{ count: number }> {
    return request.get('/mobile/sync/pending_count/')
  },

  syncAll(): Promise<void> {
    return request.post('/mobile/sync/sync_all/')
  }
}

// Sync Conflicts
export const syncConflictApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/mobile/conflicts/', { params })
  },

  getPending(): Promise<any> {
    return request.get('/mobile/conflicts/pending/')
  },

  resolve(id: string, data: any): Promise<void> {
    return request.post(`/mobile/conflicts/${id}/resolve/`, data)
  }
}

// Sync Logs
export const syncLogApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/mobile/sync-logs/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/mobile/sync-logs/${id}/`)
  }
}

// Mobile Approvals
export const mobileApprovalApi = {
  getPending(): Promise<any> {
    return request.get('/mobile/approvals/pending/')
  },

  execute(data: any): Promise<void> {
    return request.post('/mobile/approvals/approve/', data)
  },

  batchApprove(data: any): Promise<void> {
    return request.post('/mobile/approvals/batch_approve/', data)
  },

  getMyDelegations(): Promise<any> {
    return request.get('/mobile/approvals/my_delegations/')
  }
}

// Approval Delegates
export const delegateApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/mobile/delegates/', { params })
  },

  getActive(): Promise<any> {
    return request.get('/mobile/delegates/active/')
  },

  activate(id: string): Promise<void> {
    return request.post(`/mobile/delegates/${id}/activate/`)
  },

  deactivate(id: string): Promise<void> {
    return request.post(`/mobile/delegates/${id}/deactivate/`)
  }
}

// Legacy function exports for backward compatibility
export const getMobileDeviceList = mobileDeviceApi.list
export const getMobileDeviceDetail = mobileDeviceApi.detail
export const registerMobileDevice = mobileDeviceApi.register
export const updateMobileDevice = mobileDeviceApi.update
export const unbindMobileDevice = mobileDeviceApi.unbind
export const getMyDevices = mobileDeviceApi.getMyDevices

export const getSecurityLogList = securityLogApi.list
export const getSecurityLogDetail = securityLogApi.detail

export const getSyncDataList = mobileSyncApi.list
export const uploadOfflineData = mobileSyncApi.uploadOfflineData
export const downloadServerChanges = mobileSyncApi.downloadServerChanges
export const resolveSyncConflict = mobileSyncApi.resolveConflict
export const getPendingSyncCount = mobileSyncApi.getPendingCount
export const syncAll = mobileSyncApi.syncAll

export const getConflictList = syncConflictApi.list
export const getPendingConflicts = syncConflictApi.getPending
export const resolveConflict = syncConflictApi.resolve

export const getSyncLogList = syncLogApi.list
export const getSyncLogDetail = syncLogApi.detail

export const getPendingApprovals = mobileApprovalApi.getPending
export const executeMobileApproval = mobileApprovalApi.execute
export const batchApprove = mobileApprovalApi.batchApprove
export const getMyDelegations = mobileApprovalApi.getMyDelegations

export const getDelegateList = delegateApi.list
export const getActiveDelegates = delegateApi.getActive
export const activateDelegate = delegateApi.activate
export const deactivateDelegate = delegateApi.deactivate
