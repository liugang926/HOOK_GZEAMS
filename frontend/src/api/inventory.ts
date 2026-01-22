/**
 * Inventory API Service
 *
 * API methods for inventory management.
 * Reference: docs/plans/phase4_1_inventory_qr/frontend_v2.md
 */

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { InventoryTask, InventorySnapshot } from '@/types/inventory'

/**
 * Inventory Task API service
 */
export const inventoryApi = {
  /**
   * List inventory tasks
   */
  listTasks(params?: {
    page?: number
    pageSize?: number
    status?: string
    taskType?: string
  }): Promise<PaginatedResponse<InventoryTask>> {
    return request.get('/inventory/tasks/', { params })
  },

  /**
   * Get single task by ID
   */
  getTask(id: string): Promise<InventoryTask> {
    return request.get(`/inventory/tasks/${id}/`)
  },

  /**
   * Create new inventory task
   */
  createTask(data: {
    taskName: string
    taskType: string
    plannedDate: string
    locationId?: string
    categoryId?: string
    assetIds?: string[]
    note?: string
  }): Promise<InventoryTask> {
    return request.post('/inventory/tasks/', data)
  },

  /**
   * Start inventory task
   */
  startTask(id: string): Promise<void> {
    return request.post(`/inventory/tasks/${id}/start/`)
  },

  /**
   * Complete inventory task
   */
  completeTask(id: string): Promise<void> {
    return request.post(`/inventory/tasks/${id}/complete/`)
  },

  /**
   * Cancel inventory task
   */
  cancelTask(id: string): Promise<void> {
    return request.post(`/inventory/tasks/${id}/cancel/`)
  },

  /**
   * Get task snapshots
   */
  getSnapshots(taskId: string, params?: {
    page?: number
    pageSize?: number
    filter?: 'all' | 'scanned' | 'unscanned' | 'abnormal'
  }): Promise<PaginatedResponse<InventorySnapshot>> {
    return request.get(`/inventory/tasks/${taskId}/snapshots/`, { params })
  },

  /**
   * Scan asset during inventory
   */
  scanAsset(taskId: string, data: {
    qrCode: string
    actualLocation?: string
    actualLocationId?: string
  }): Promise<InventorySnapshot> {
    return request.post(`/inventory/tasks/${taskId}/scan/`, data)
  },

  /**
   * Confirm/Update snapshot result
   */
  confirmSnapshot(taskId: string, snapshotId: string, data: {
    result: string
    remark?: string
    imageUrl?: string
  }): Promise<void> {
    return request.post(`/inventory/tasks/${taskId}/snapshots/${snapshotId}/confirm/`, data)
  },

  /**
   * Get recent scanned items (for real-time updates)
   */
  getRecentTags(taskId: string): Promise<{
    items: InventorySnapshot[]
    scannedCount: number
  }> {
    return request.get(`/inventory/tasks/${taskId}/recent-tags/`)
  },

  /**
   * Generate inventory report
   */
  generateReport(taskId: string): Promise<Blob> {
    return request.get(`/inventory/tasks/${taskId}/report/`, {
      responseType: 'blob'
    })
  }
}

/**
 * Inventory Reconciliation API service
 */
export const reconciliationApi = {
  /**
   * List reconciliations
   */
  list(params?: {
    page?: number
    pageSize?: number
    taskId?: string
    status?: string
  }): Promise<PaginatedResponse<any>> {
    return request.get('/inventory/reconciliations/', { params })
  },

  /**
   * Get reconciliation by ID
   */
  get(id: string): Promise<any> {
    return request.get(`/inventory/reconciliations/${id}/`)
  },

  /**
   * Submit reconciliation for approval
   */
  submit(id: string): Promise<void> {
    return request.post(`/inventory/reconciliations/${id}/submit/`)
  },

  /**
   * Approve reconciliation
   */
  approve(id: string, data?: {
    comment?: string
  }): Promise<void> {
    return request.post(`/inventory/reconciliations/${id}/approve/`, data)
  },

  /**
   * Reject reconciliation
   */
  reject(id: string, reason: string): Promise<void> {
    return request.post(`/inventory/reconciliations/${id}/reject/`, { reason })
  }
}

/**
 * QR Code Scan API service
 */
export const qrScanApi = {
  /**
   * Get asset info by QR code
   */
  getAssetByQrCode(qrCode: string): Promise<{
    id: string
    code: string
    name: string
    categoryName: string
    status: string
    location: string
    custodian: string
  }> {
    return request.get('/assets/by-qr-code/', { params: { qr_code: qrCode } })
  },

  /**
   * Verify QR code validity
   */
  verifyQrCode(qrCode: string): Promise<{
    valid: boolean
    assetId?: string
    error?: string
  }> {
    return request.post('/assets/verify-qr-code/', { qrCode })
  }
}
