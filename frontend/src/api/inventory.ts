/**
 * Inventory API Service
 *
 * Now using unified Dynamic Object Routing for all inventory-related operations.
 * Reference: docs/plans/phase4_1_inventory_qr/frontend_v2.md
 */

import request from '@/utils/request'
import { BaseApiService } from '@/api/base'
import type { PaginatedResponse } from '@/types/api'
import type { InventoryTask, InventorySnapshot } from '@/types/inventory'
import {
  inventoryTaskApi,
  inventorySnapshotApi
} from '@/api/dynamic'

/**
 * Inventory Task API service using Dynamic Object Routing
 */
class InventoryTaskApiService extends BaseApiService<InventoryTask> {
  constructor() {
    super('inventory/tasks')
  }

  /**
   * List inventory tasks (delegates to dynamic API)
   */
  async list(params?: any): Promise<PaginatedResponse<InventoryTask>> {
    const res = await inventoryTaskApi.list(params)
    return {
      items: res.data?.results || [],
      total: res.data?.count || 0,
      ...params
    }
  }

  /**
   * Get single task (delegates to dynamic API)
   */
  async get(id: string, params?: any): Promise<InventoryTask> {
    const res = await inventoryTaskApi.get(id, params)
    return res.data as InventoryTask
  }

  /**
   * Create task (delegates to dynamic API)
   */
  async create(data: Partial<InventoryTask>): Promise<InventoryTask> {
    const res = await inventoryTaskApi.create(data)
    return res.data as InventoryTask
  }

  /**
   * Update task (delegates to dynamic API)
   */
  async update(id: string, data: Partial<InventoryTask>): Promise<InventoryTask> {
    const res = await inventoryTaskApi.update(id, data)
    return res.data as InventoryTask
  }

  /**
   * Delete task (delegates to dynamic API)
   */
  async delete(id: string): Promise<void> {
    await inventoryTaskApi.delete(id)
  }

  // ---------------------------------------------------------------------------
  // Low-code runtime compatibility helpers
  // ---------------------------------------------------------------------------
  // Some pages/components (e.g. BaseListPage-based views) expect the unified
  // object-router pagination shape: `{ count, next, previous, results }`.
  // These helpers bridge that expectation without forcing a full UI refactor.

  async listTasks(params?: any): Promise<any> {
    const next = { ...(params || {}) }
    if (next.pageSize !== undefined && next.page_size === undefined) {
      next.page_size = next.pageSize
      delete next.pageSize
    }
    return inventoryTaskApi.list(next)
  }

  async getTask(id: string, params?: any): Promise<any> {
    return inventoryTaskApi.get(id, params)
  }

  async createTask(data: Partial<InventoryTask>): Promise<any> {
    return inventoryTaskApi.create(data as any)
  }

  async updateTask(id: string, data: Partial<InventoryTask>): Promise<any> {
    return inventoryTaskApi.update(id, data as any)
  }

  async deleteTask(id: string): Promise<void> {
    await inventoryTaskApi.delete(id)
  }

  async batchDeleteTasks(ids: string[]): Promise<any> {
    return inventoryTaskApi.batchDelete(ids)
  }

  /**
   * Start inventory task (custom action endpoint)
   */
  start(id: string): Promise<void> {
    return request.post(`/system/objects/InventoryTask/${id}/start/`)
  }

  /**
   * Complete inventory task (custom action endpoint)
   */
  complete(id: string): Promise<void> {
    return request.post(`/system/objects/InventoryTask/${id}/complete/`)
  }

  /**
   * Cancel inventory task (custom action endpoint)
   */
  cancel(id: string): Promise<void> {
    return request.post(`/system/objects/InventoryTask/${id}/cancel/`)
  }

  /**
   * Get task snapshots (custom action endpoint)
   */
  getSnapshots(taskId: string, params?: {
    page?: number
    pageSize?: number
    filter?: 'all' | 'scanned' | 'unscanned' | 'abnormal'
  }): Promise<PaginatedResponse<InventorySnapshot>> {
    return request.get(`/system/objects/InventoryTask/${taskId}/snapshots/`, { params })
  }

  /**
   * Scan asset during inventory (custom action endpoint)
   */
  scanAsset(taskId: string, data: {
    qrCode: string
    actualLocation?: string
    actualLocationId?: string
  }): Promise<InventorySnapshot> {
    return request.post(`/system/objects/InventoryTask/${taskId}/scan/`, data)
  }

  /**
   * Confirm/Update snapshot result (custom action endpoint)
   */
  confirmSnapshot(taskId: string, snapshotId: string, data: {
    result: string
    remark?: string
    imageUrl?: string
    userId?: string
  }): Promise<void> {
    return request.post(`/system/objects/InventoryTask/${taskId}/snapshots/${snapshotId}/confirm/`, data)
  }

  /**
   * Get recent scanned items for real-time updates (custom endpoint)
   */
  getRecentTags(taskId: string): Promise<{
    items: InventorySnapshot[]
    scannedCount: number
  }> {
    return request.get(`/system/objects/InventoryTask/${taskId}/recent-tags/`)
  }

  /**
   * Generate inventory report (custom endpoint)
   */
  generateReport(taskId: string): Promise<Blob> {
    return request.get(`/system/objects/InventoryTask/${taskId}/report/`, {
      responseType: 'blob'
    })
  }
}

export const inventoryApi = new InventoryTaskApiService()

/**
 * Inventory Snapshot API service using Dynamic Object Routing
 */
export const snapshotApi = {
  /**
   * List snapshots (delegates to dynamic API)
   */
  async list(params?: any): Promise<PaginatedResponse<InventorySnapshot>> {
    const res = await inventorySnapshotApi.list(params)
    return {
      items: res.data?.results || [],
      total: res.data?.count || 0
    }
  },

  /**
   * Get single snapshot (delegates to dynamic API)
   */
  async get(id: string): Promise<InventorySnapshot> {
    const res = await inventorySnapshotApi.get(id)
    return res.data as InventorySnapshot
  }
}

/**
 * Inventory Reconciliation API service
 */
class ReconciliationApiService extends BaseApiService<any> {
  constructor() {
    super('inventory/reconciliations')
  }

  /**
   * Submit reconciliation for approval (custom endpoint)
   */
  submit(id: string): Promise<void> {
    return request.post(`/system/objects/InventoryReconciliation/${id}/submit/`)
  }

  /**
   * Approve reconciliation (custom endpoint)
   */
  approve(id: string, data?: { comment?: string }): Promise<void> {
    return request.post(`/system/objects/InventoryReconciliation/${id}/approve/`, data)
  }

  /**
   * Reject reconciliation (custom endpoint)
   */
  reject(id: string, reason: string): Promise<void> {
    return request.post(`/system/objects/InventoryReconciliation/${id}/reject/`, { reason })
  }
}

export const reconciliationApi = new ReconciliationApiService()

/**
 * QR Code Scan API service (custom endpoints)
 */
export const qrScanApi = {
  /**
   * Get asset info by QR code
   */
  async getAssetByQrCode(qrCode: string): Promise<{
    id: string
    code: string
    name: string
    categoryName: string
    status: string
    location: string
    custodian: string
  }> {
    const asset: any = await request.get('/system/objects/Asset/lookup/', { params: { qr_code: qrCode } })
    return {
      id: asset?.id || '',
      code: asset?.assetCode || asset?.asset_code || '',
      name: asset?.assetName || asset?.asset_name || '',
      categoryName: asset?.assetCategoryName || asset?.asset_category_name || '',
      status: asset?.assetStatus || asset?.asset_status || '',
      location: asset?.locationName || asset?.location_name || '',
      custodian: asset?.custodianName || asset?.custodian_name || ''
    }
  },

  /**
   * Verify QR code validity
   */
  async verifyQrCode(qrCode: string): Promise<{
    valid: boolean
    assetId?: string
    error?: string
  }> {
    try {
      const asset: any = await request.get('/system/objects/Asset/lookup/', { params: { qr_code: qrCode } })
      return {
        valid: true,
        assetId: asset?.id
      }
    } catch (error: any) {
      const message =
        error?.message ||
        error?.response?.data?.error?.message ||
        'Invalid QR code'
      return {
        valid: false,
        error: message
      }
    }
  }
}
