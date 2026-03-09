/**
 * Lifecycle Management API Client
 *
 * Handles asset lifecycle operations: purchase requests, receipts, maintenance, and disposal.
 * All custom action endpoints use /api/lifecycle/ prefix (NOT /system/objects/).
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

// ─── Purchase Requests ────────────────────────────────────────────────────────

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
  async delete(id: string): Promise<void> {
    await dynamicPurchaseRequestApi.delete(id)
  },
  /** Submit for approval */
  submit(id: string): Promise<any> {
    return request.post(`/lifecycle/purchase-requests/${id}/submit/`)
  },
  /** Approve or reject */
  approve(id: string, decision: 'approved' | 'rejected', comment?: string): Promise<any> {
    return request.post(`/lifecycle/purchase-requests/${id}/approve/`, { decision, comment })
  },
  /** Cancel request */
  cancel(id: string, reason?: string): Promise<any> {
    return request.post(`/lifecycle/purchase-requests/${id}/cancel/`, { reason })
  },
  /** Mark as completed */
  complete(id: string): Promise<any> {
    return request.post(`/lifecycle/purchase-requests/${id}/complete/`)
  },
  /** Get line items */
  items(id: string): Promise<any[]> {
    return request.get(`/lifecycle/purchase-requests/${id}/items/`)
  },
  /** Get all pending-approval requests */
  pendingApproval(): Promise<any[]> {
    return request.get('/lifecycle/purchase-requests/pending_approval/')
  }
}

// ─── Asset Receipts ───────────────────────────────────────────────────────────

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
  /** Submit for inspection */
  submitInspection(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-receipts/${id}/submit_inspection/`)
  },
  /** Record inspection result */
  inspect(id: string, result: string, passed: boolean): Promise<any> {
    return request.post(`/lifecycle/asset-receipts/${id}/inspect/`, { result, passed })
  },
  /** Generate asset cards from passed items */
  generateAssets(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-receipts/${id}/generate_assets/`)
  },
  /** Cancel receipt */
  cancel(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-receipts/${id}/cancel/`)
  },
  /** Get receipt items */
  items(id: string): Promise<any[]> {
    return request.get(`/lifecycle/asset-receipts/${id}/items/`)
  }
}

// ─── Maintenance ──────────────────────────────────────────────────────────────

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
  /** Assign technician */
  assign(id: string, technicianId: string): Promise<any> {
    return request.post(`/lifecycle/maintenance/${id}/assign/`, { technician_id: technicianId })
  },
  /** Start work */
  startWork(id: string): Promise<any> {
    return request.post(`/lifecycle/maintenance/${id}/start_work/`)
  },
  /** Complete work */
  completeWork(id: string, data: any): Promise<any> {
    return request.post(`/lifecycle/maintenance/${id}/complete_work/`, data)
  },
  /** Verify completed work */
  verify(id: string, result: string): Promise<any> {
    return request.post(`/lifecycle/maintenance/${id}/verify/`, { result })
  },
  /** Cancel maintenance */
  cancel(id: string, reason?: string): Promise<any> {
    return request.post(`/lifecycle/maintenance/${id}/cancel/`, { reason })
  },
  /** Get statistics */
  statistics(): Promise<any> {
    return request.get('/lifecycle/maintenance/statistics/')
  },
  /** Get urgent records */
  urgent(): Promise<any[]> {
    return request.get('/lifecycle/maintenance/urgent/')
  }
}

// ─── Maintenance Plans ────────────────────────────────────────────────────────

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
  /** Activate plan */
  activate(id: string): Promise<any> {
    return request.post(`/lifecycle/maintenance-plans/${id}/activate/`)
  },
  /** Pause plan */
  pause(id: string): Promise<any> {
    return request.post(`/lifecycle/maintenance-plans/${id}/pause/`)
  },
  /** Archive plan */
  archive(id: string): Promise<any> {
    return request.post(`/lifecycle/maintenance-plans/${id}/archive/`)
  },
  /** Generate tasks from plan */
  generateTasks(id: string): Promise<{ generated_count: number }> {
    return request.post(`/lifecycle/maintenance-plans/${id}/generate_tasks/`)
  }
}

// ─── Disposal Requests ────────────────────────────────────────────────────────

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
  async delete(id: string): Promise<void> {
    await dynamicDisposalRequestApi.delete(id)
  },
  /** Submit for approval */
  submit(id: string): Promise<any> {
    return request.post(`/lifecycle/disposal-requests/${id}/submit/`)
  },
  /** Start technical appraisal */
  startAppraisal(id: string): Promise<any> {
    return request.post(`/lifecycle/disposal-requests/${id}/start_appraisal/`)
  },
  /** Approve or reject */
  approve(id: string, decision: 'approved' | 'rejected', comment?: string): Promise<any> {
    return request.post(`/lifecycle/disposal-requests/${id}/approve/`, { decision, comment })
  },
  /** Cancel request */
  cancel(id: string, reason?: string): Promise<any> {
    return request.post(`/lifecycle/disposal-requests/${id}/cancel/`, { reason })
  },
  /** Get disposal items */
  items(id: string): Promise<any[]> {
    return request.get(`/lifecycle/disposal-requests/${id}/items/`)
  }
}

// ─── Maintenance Tasks ────────────────────────────────────────────────────────

export const maintenanceTaskApi = {
  async list(params?: any): Promise<PaginatedResponse<any>> {
    const res = await request.get('/lifecycle/maintenance-tasks/', { params }) as any
    return {
      results: res?.data?.results ?? res?.results ?? [],
      count: res?.data?.count ?? res?.count ?? 0,
      next: null,
      previous: null
    }
  },
  async detail(id: string): Promise<any> {
    const res = await request.get(`/lifecycle/maintenance-tasks/${id}/`) as any
    return res?.data ?? res
  },
  /** Execute maintenance task */
  execute(id: string, data: { execution_result: string; actual_hours: number }): Promise<any> {
    return request.post(`/lifecycle/maintenance-tasks/${id}/execute/`, data)
  },
  /** Verify completed task */
  verify(id: string, verifyResult: string): Promise<any> {
    return request.post(`/lifecycle/maintenance-tasks/${id}/verify/`, { verify_result: verifyResult })
  },
  /** Skip task with reason */
  skip(id: string, reason: string): Promise<any> {
    return request.post(`/lifecycle/maintenance-tasks/${id}/skip/`, { reason })
  },
  /** Get overdue tasks */
  overdue(): Promise<any[]> {
    return request.get('/lifecycle/maintenance-tasks/overdue/')
  },
  /** Get today's tasks */
  today(): Promise<any[]> {
    return request.get('/lifecycle/maintenance-tasks/today/')
  }
}

// ─── Legacy function exports (backward compat) ────────────────────────────────

export const getPurchaseRequestList = (p?: any) => purchaseRequestApi.list(p)
export const getPurchaseRequestDetail = (id: string) => purchaseRequestApi.detail(id)
export const createPurchaseRequest = (d: any) => purchaseRequestApi.create(d)
export const updatePurchaseRequest = (id: string, d: any) => purchaseRequestApi.update(id, d)
export const submitPurchaseRequest = (id: string) => purchaseRequestApi.submit(id)
export const approvePurchaseRequest = (id: string, d: any) => purchaseRequestApi.approve(id, d.decision, d.comment)
export const rejectPurchaseRequest = (id: string, d: any) => purchaseRequestApi.approve(id, 'rejected', d.comment)

export const getAssetReceiptList = (p?: any) => assetReceiptApi.list(p)
export const getAssetReceiptDetail = (id: string) => assetReceiptApi.detail(id)
export const createAssetReceipt = (d: any) => assetReceiptApi.create(d)
export const confirmReceipt = (id: string, d: any) => assetReceiptApi.inspect(id, d.result, d.passed)

export const getMaintenanceList = (p?: any) => maintenanceApi.list(p)
export const getMaintenanceDetail = (id: string) => maintenanceApi.detail(id)
export const createMaintenance = (d: any) => maintenanceApi.create(d)
export const updateMaintenance = (id: string, d: any) => maintenanceApi.update(id, d)
export const completeMaintenance = (id: string, d: any) => maintenanceApi.completeWork(id, d)

export const getMaintenancePlanList = (p?: any) => maintenancePlanApi.list(p)
export const getMaintenancePlanDetail = (id: string) => maintenancePlanApi.detail(id)
export const createMaintenancePlan = (d: any) => maintenancePlanApi.create(d)
export const updateMaintenancePlan = (id: string, d: any) => maintenancePlanApi.update(id, d)
export const activateMaintenancePlan = (id: string) => maintenancePlanApi.activate(id)

export const getDisposalRequestList = (p?: any) => disposalRequestApi.list(p)
export const getDisposalRequestDetail = (id: string) => disposalRequestApi.detail(id)
export const createDisposalRequest = (d: any) => disposalRequestApi.create(d)
export const updateDisposalRequest = (id: string, d: any) => disposalRequestApi.update(id, d)
export const submitDisposalRequest = (id: string) => disposalRequestApi.submit(id)
export const approveDisposalRequest = (id: string, d: any) => disposalRequestApi.approve(id, d.decision, d.comment)
export const confirmDisposal = (id: string, d: any) => disposalRequestApi.approve(id, 'approved', d.comment)

// ─── Asset Warranties ─────────────────────────────────────────────────────────

export const assetWarrantyApi = {
  async list(params?: any): Promise<PaginatedResponse<any>> {
    const res = await request.get('/lifecycle/asset-warranties/', { params }) as any
    return {
      results: res?.data?.results ?? res?.results ?? [],
      count: res?.data?.count ?? res?.count ?? 0,
      next: null,
      previous: null
    }
  },
  async detail(id: string): Promise<any> {
    const res = await request.get(`/lifecycle/asset-warranties/${id}/`) as any
    return res?.data ?? res
  },
  create(data: any): Promise<any> {
    return request.post('/lifecycle/asset-warranties/', data)
  },
  update(id: string, data: any): Promise<any> {
    return request.put(`/lifecycle/asset-warranties/${id}/`, data)
  },
  /** Activate warranty */
  activate(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-warranties/${id}/activate/`)
  },
  /** Mark as expired */
  expire(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-warranties/${id}/expire/`)
  },
  /** Renew warranty */
  renew(id: string, data: { end_date: string; warranty_cost?: number }): Promise<any> {
    return request.post(`/lifecycle/asset-warranties/${id}/renew/`, data)
  },
  /** Record a claim */
  recordClaim(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-warranties/${id}/record_claim/`)
  },
  /** Cancel warranty */
  cancel(id: string): Promise<any> {
    return request.post(`/lifecycle/asset-warranties/${id}/cancel/`)
  },
  /** Get expiring soon */
  expiringSoon(): Promise<any[]> {
    return request.get('/lifecycle/asset-warranties/expiring_soon/')
  },
  /** Get statistics */
  statistics(): Promise<any> {
    return request.get('/lifecycle/asset-warranties/statistics/')
  }
}

// ─── Legacy function exports (asset warranty) ──────────────────────────────────

export const getAssetWarrantyList = (p?: any) => assetWarrantyApi.list(p)
export const getAssetWarrantyDetail = (id: string) => assetWarrantyApi.detail(id)
export const createAssetWarranty = (d: any) => assetWarrantyApi.create(d)
export const updateAssetWarranty = (id: string, d: any) => assetWarrantyApi.update(id, d)
export const activateAssetWarranty = (id: string) => assetWarrantyApi.activate(id)
