/**
 * Lifecycle Management API Client
 *
 * Now using unified Dynamic Object Routing for all lifecycle operations.
 * Handles asset lifecycle operations: purchase requests, receipts, maintenance, and disposal
 */

import request from '@/utils/request'
import { toData, toPaginated } from '@/api/contract'
import type { PaginatedResponse } from '@/types/api'
import {
  purchaseRequestApi as dynamicPurchaseRequestApi,
  assetReceiptApi as dynamicAssetReceiptApi,
  maintenanceApi as dynamicMaintenanceApi,
  maintenancePlanApi as dynamicMaintenancePlanApi,
  disposalRequestApi as dynamicDisposalRequestApi
} from '@/api/dynamic'

// Purchase Requests (using dynamic API)
export const purchaseRequestApi = {
  async list(params?: any): Promise<PaginatedResponse<any>> {
    return toPaginated<any>(await dynamicPurchaseRequestApi.list(params))
  },

  async detail(id: string): Promise<any> {
    return toData<any>(await dynamicPurchaseRequestApi.get(id))
  },

  async create(data: any): Promise<any> {
    return toData<any>(await dynamicPurchaseRequestApi.create(data))
  },

  async update(id: string, data: any): Promise<any> {
    return toData<any>(await dynamicPurchaseRequestApi.update(id, data))
  },

  /**
   * Submit for approval (custom action endpoint)
   */
  submit(id: string): Promise<void> {
    return request.post(`/system/objects/PurchaseRequest/${id}/submit/`)
  },

  /**
   * Approve request (custom action endpoint)
   */
  approve(id: string, data: any): Promise<void> {
    return request.post(`/system/objects/PurchaseRequest/${id}/approve/`, data)
  },

  /**
   * Reject request (custom action endpoint)
   */
  reject(id: string, data: any): Promise<void> {
    return request.post(`/system/objects/PurchaseRequest/${id}/reject/`, data)
  }
}

// Asset Receipts (using dynamic API)
export const assetReceiptApi = {
  async list(params?: any): Promise<PaginatedResponse<any>> {
    return toPaginated<any>(await dynamicAssetReceiptApi.list(params))
  },

  async detail(id: string): Promise<any> {
    return toData<any>(await dynamicAssetReceiptApi.get(id))
  },

  async create(data: any): Promise<any> {
    return toData<any>(await dynamicAssetReceiptApi.create(data))
  },

  /**
   * Confirm receipt (custom action endpoint)
   */
  confirm(id: string, data: any): Promise<void> {
    return request.post(`/system/objects/AssetReceipt/${id}/confirm/`, data)
  }
}

// Maintenance Records (using dynamic API)
export const maintenanceApi = {
  async list(params?: any): Promise<PaginatedResponse<any>> {
    return toPaginated<any>(await dynamicMaintenanceApi.list(params))
  },

  async detail(id: string): Promise<any> {
    return toData<any>(await dynamicMaintenanceApi.get(id))
  },

  async create(data: any): Promise<any> {
    return toData<any>(await dynamicMaintenanceApi.create(data))
  },

  async update(id: string, data: any): Promise<any> {
    return toData<any>(await dynamicMaintenanceApi.update(id, data))
  },

  /**
   * Complete maintenance (custom action endpoint)
   */
  complete(id: string, data: any): Promise<void> {
    return request.post(`/system/objects/Maintenance/${id}/complete/`, data)
  }
}

// Maintenance Plans (using dynamic API)
export const maintenancePlanApi = {
  async list(params?: any): Promise<PaginatedResponse<any>> {
    return toPaginated<any>(await dynamicMaintenancePlanApi.list(params))
  },

  async detail(id: string): Promise<any> {
    return toData<any>(await dynamicMaintenancePlanApi.get(id))
  },

  async create(data: any): Promise<any> {
    return toData<any>(await dynamicMaintenancePlanApi.create(data))
  },

  async update(id: string, data: any): Promise<any> {
    return toData<any>(await dynamicMaintenancePlanApi.update(id, data))
  },

  /**
   * Activate maintenance plan (custom action endpoint)
   */
  activate(id: string): Promise<void> {
    return request.post(`/system/objects/MaintenancePlan/${id}/activate/`)
  },

  /**
   * Deactivate maintenance plan (custom action endpoint)
   */
  deactivate(id: string): Promise<void> {
    return request.post(`/system/objects/MaintenancePlan/${id}/deactivate/`)
  }
}

// Disposal Requests (using dynamic API)
export const disposalRequestApi = {
  async list(params?: any): Promise<PaginatedResponse<any>> {
    return toPaginated<any>(await dynamicDisposalRequestApi.list(params))
  },

  async detail(id: string): Promise<any> {
    return toData<any>(await dynamicDisposalRequestApi.get(id))
  },

  async create(data: any): Promise<any> {
    return toData<any>(await dynamicDisposalRequestApi.create(data))
  },

  async update(id: string, data: any): Promise<any> {
    return toData<any>(await dynamicDisposalRequestApi.update(id, data))
  },

  /**
   * Submit for approval (custom action endpoint)
   */
  submit(id: string): Promise<void> {
    return request.post(`/system/objects/DisposalRequest/${id}/submit/`)
  },

  /**
   * Approve disposal (custom action endpoint)
   */
  approve(id: string, data: any): Promise<void> {
    return request.post(`/system/objects/DisposalRequest/${id}/approve/`, data)
  },

  /**
   * Confirm disposal (custom action endpoint)
   */
  confirm(id: string, data: any): Promise<void> {
    return request.post(`/system/objects/DisposalRequest/${id}/confirm/`, data)
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

export const getDisposalRequestList = disposalRequestApi.list
export const getDisposalRequestDetail = disposalRequestApi.detail
export const createDisposalRequest = disposalRequestApi.create
export const updateDisposalRequest = disposalRequestApi.update
export const submitDisposalRequest = disposalRequestApi.submit
export const approveDisposalRequest = disposalRequestApi.approve
export const confirmDisposal = disposalRequestApi.confirm
