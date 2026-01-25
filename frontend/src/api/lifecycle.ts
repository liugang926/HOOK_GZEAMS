import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

/**
 * Lifecycle Management API Client
 * Handles asset lifecycle operations: purchase requests, receipts, maintenance, and disposal
 */

// Purchase Requests
export const purchaseRequestApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/lifecycle/purchase-requests/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/lifecycle/purchase-requests/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/lifecycle/purchase-requests/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/lifecycle/purchase-requests/${id}/`, data)
  },

  submit(id: string): Promise<void> {
    return request.post(`/lifecycle/purchase-requests/${id}/submit/`)
  },

  approve(id: string, data: any): Promise<void> {
    return request.post(`/lifecycle/purchase-requests/${id}/approve/`, data)
  },

  reject(id: string, data: any): Promise<void> {
    return request.post(`/lifecycle/purchase-requests/${id}/reject/`, data)
  }
}

// Asset Receipts
export const assetReceiptApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/lifecycle/asset-receipts/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/lifecycle/asset-receipts/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/lifecycle/asset-receipts/', data)
  },

  confirm(id: string, data: any): Promise<void> {
    return request.post(`/lifecycle/asset-receipts/${id}/confirm/`, data)
  }
}

// Maintenance Records
export const maintenanceApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/lifecycle/maintenance/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/lifecycle/maintenance/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/lifecycle/maintenance/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/lifecycle/maintenance/${id}/`, data)
  },

  complete(id: string, data: any): Promise<void> {
    return request.post(`/lifecycle/maintenance/${id}/complete/`, data)
  }
}

// Maintenance Plans
export const maintenancePlanApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/lifecycle/maintenance-plans/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/lifecycle/maintenance-plans/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/lifecycle/maintenance-plans/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/lifecycle/maintenance-plans/${id}/`, data)
  },

  activate(id: string): Promise<void> {
    return request.post(`/lifecycle/maintenance-plans/${id}/activate/`)
  },

  deactivate(id: string): Promise<void> {
    return request.post(`/lifecycle/maintenance-plans/${id}/deactivate/`)
  }
}

// Maintenance Tasks
export const maintenanceTaskApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/lifecycle/maintenance-tasks/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/lifecycle/maintenance-tasks/${id}/`)
  },

  complete(id: string, data: any): Promise<void> {
    return request.post(`/lifecycle/maintenance-tasks/${id}/complete/`, data)
  }
}

// Disposal Requests
export const disposalRequestApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/lifecycle/disposal-requests/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/lifecycle/disposal-requests/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/lifecycle/disposal-requests/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/lifecycle/disposal-requests/${id}/`, data)
  },

  submit(id: string): Promise<void> {
    return request.post(`/lifecycle/disposal-requests/${id}/submit/`)
  },

  approve(id: string, data: any): Promise<void> {
    return request.post(`/lifecycle/disposal-requests/${id}/approve/`, data)
  },

  confirm(id: string, data: any): Promise<void> {
    return request.post(`/lifecycle/disposal-requests/${id}/confirm/`, data)
  }
}

// Legacy function exports for backward compatibility
export const getPurchaseRequestList = purchaseRequestApi.list
export const getPurchaseRequestDetail = purchaseRequestApi.detail
export const createPurchaseRequest = purchaseRequestApi.create
export const updatePurchaseRequest = purchaseRequestApi.update
export const submitPurchaseRequest = purchaseRequestApi.submit
export const approvePurchaseRequest = purchaseRequestApi.approve
export const rejectPurchaseRequest = purchaseRequestApi.reject

export const getAssetReceiptList = assetReceiptApi.list
export const getAssetReceiptDetail = assetReceiptApi.detail
export const createAssetReceipt = assetReceiptApi.create
export const confirmReceipt = assetReceiptApi.confirm

export const getMaintenanceList = maintenanceApi.list
export const getMaintenanceDetail = maintenanceApi.detail
export const createMaintenance = maintenanceApi.create
export const updateMaintenance = maintenanceApi.update
export const completeMaintenance = maintenanceApi.complete

export const getMaintenancePlanList = maintenancePlanApi.list
export const getMaintenancePlanDetail = maintenancePlanApi.detail
export const createMaintenancePlan = maintenancePlanApi.create
export const updateMaintenancePlan = maintenancePlanApi.update
export const activateMaintenancePlan = maintenancePlanApi.activate

export const getMaintenanceTaskList = maintenanceTaskApi.list
export const getMaintenanceTaskDetail = maintenanceTaskApi.detail
export const completeMaintenanceTask = maintenanceTaskApi.complete

export const getDisposalRequestList = disposalRequestApi.list
export const getDisposalRequestDetail = disposalRequestApi.detail
export const createDisposalRequest = disposalRequestApi.create
export const updateDisposalRequest = disposalRequestApi.update
export const submitDisposalRequest = disposalRequestApi.submit
export const approveDisposalRequest = disposalRequestApi.approve
export const confirmDisposal = disposalRequestApi.confirm
