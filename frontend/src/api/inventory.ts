/**
 * Inventory API Service
 *
 * API methods for inventory management using BaseApiService.
 * Reference: docs/plans/phase4_1_inventory_qr/frontend_v2.md
 */

import request from '@/utils/request'
import { BaseApiService } from '@/api/base'
import type { PaginatedResponse } from '@/types/api'
import type { InventoryTask, InventorySnapshot } from '@/types/inventory'

/**
 * Inventory Task API service
 */
class InventoryTaskApiService extends BaseApiService<InventoryTask> {
  constructor() {
    super('inventory/tasks')
  }

  /**
   * Start inventory task
   */
  start(id: string): Promise<void> {
    return request.post(`/${this.resource}/${id}/start/`)
  }

  /**
   * Complete inventory task
   */
  complete(id: string): Promise<void> {
    return request.post(`/${this.resource}/${id}/complete/`)
  }

  /**
   * Cancel inventory task
   */
  cancel(id: string): Promise<void> {
    return request.post(`/${this.resource}/${id}/cancel/`)
  }

  /**
   * Get task snapshots
   */
  getSnapshots(taskId: string, params?: {
    page?: number
    pageSize?: number
    filter?: 'all' | 'scanned' | 'unscanned' | 'abnormal'
  }): Promise<PaginatedResponse<InventorySnapshot>> {
    return request.get(`/${this.resource}/${taskId}/snapshots/`, { params })
  }

  /**
   * Scan asset during inventory
   */
  scanAsset(taskId: string, data: {
    qrCode: string
    actualLocation?: string
    actualLocationId?: string
  }): Promise<InventorySnapshot> {
    return request.post(`/${this.resource}/${taskId}/scan/`, data)
  }

  /**
   * Confirm/Update snapshot result
   */
  confirmSnapshot(taskId: string, snapshotId: string, data: {
    result: string
    remark?: string
    imageUrl?: string
    userId?: string
  }): Promise<void> {
    return request.post(`/${this.resource}/${taskId}/snapshots/${snapshotId}/confirm/`, data)
  }

  /**
   * Get recent scanned items (for real-time updates)
   */
  getRecentTags(taskId: string): Promise<{
    items: InventorySnapshot[]
    scannedCount: number
  }> {
    return request.get(`/${this.resource}/${taskId}/recent-tags/`)
  }

  /**
   * Generate inventory report
   */
  generateReport(taskId: string): Promise<Blob> {
    return request.get(`/${this.resource}/${taskId}/report/`, {
      responseType: 'blob'
    })
  }
}

export const inventoryApi = new InventoryTaskApiService()

/**
 * Inventory Reconciliation API service
 */
class ReconciliationApiService extends BaseApiService<any> {
  constructor() {
    super('inventory/reconciliations')
  }

  /**
   * Submit reconciliation for approval
   */
  submit(id: string): Promise<void> {
    return request.post(`/${this.resource}/${id}/submit/`)
  }

  /**
   * Approve reconciliation
   */
  approve(id: string, data?: { comment?: string }): Promise<void> {
    return request.post(`/${this.resource}/${id}/approve/`, data)
  }

  /**
   * Reject reconciliation
   */
  reject(id: string, reason: string): Promise<void> {
    return request.post(`/${this.resource}/${id}/reject/`, { reason })
  }
}

export const reconciliationApi = new ReconciliationApiService()

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



