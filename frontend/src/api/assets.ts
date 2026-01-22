/**
 * Asset API Service
 *
 * API methods for asset management.
 * Reference: docs/plans/2025-01-22-frontend-implementation.md
 */

import request from '@/utils/request'
import type { PaginatedResponse, BatchResponse } from '@/types/api'
import type { Asset, AssetCategory } from '@/types/assets'

/**
 * Asset API service object
 */
export const assetApi = {
  /**
   * List assets with pagination and filters
   */
  list(params?: {
    page?: number
    pageSize?: number
    categoryId?: string
    status?: string
    locationId?: string
    custodianId?: string
    search?: string
  }): Promise<PaginatedResponse<Asset>> {
    return request.get('/assets/', { params })
  },

  /**
   * Get single asset by ID
   */
  get(id: string): Promise<Asset> {
    return request.get(`/assets/${id}/`)
  },

  /**
   * Create new asset
   */
  create(data: Partial<Asset>): Promise<Asset> {
    return request.post('/assets/', data)
  },

  /**
   * Update asset
   */
  update(id: string, data: Partial<Asset>): Promise<Asset> {
    return request.put(`/assets/${id}/`, data)
  },

  /**
   * Delete asset (soft delete)
   */
  delete(id: string): Promise<void> {
    return request.delete(`/assets/${id}/`)
  },

  /**
   * Batch delete assets
   */
  batchDelete(ids: string[]): Promise<BatchResponse> {
    return request.post('/assets/batch-delete/', { ids })
  },

  /**
   * Export assets to Excel
   */
  export(params?: any): Promise<Blob> {
    return request.get('/assets/export/', {
      params,
      responseType: 'blob'
    })
  },

  /**
   * Get asset by QR code
   */
  getByQrCode(qrCode: string): Promise<Asset> {
    return request.get('/assets/by-qr-code/', { params: { qr_code: qrCode } })
  },

  /**
   * Restore deleted asset
   */
  restore(id: string): Promise<Asset> {
    return request.post(`/assets/${id}/restore/`)
  }
}

/**
 * Asset Category API service object
 */
export const categoryApi = {
  /**
   * List all categories (flat)
   */
  list(): Promise<AssetCategory[]> {
    return request.get('/assets/categories/')
  },

  /**
   * Get category tree structure
   */
  tree(): Promise<AssetCategory[]> {
    return request.get('/assets/categories/tree/')
  },

  /**
   * Get single category by ID
   */
  get(id: string): Promise<AssetCategory> {
    return request.get(`/assets/categories/${id}/`)
  },

  /**
   * Create new category
   */
  create(data: Partial<AssetCategory>): Promise<AssetCategory> {
    return request.post('/assets/categories/', data)
  },

  /**
   * Update category
   */
  update(id: string, data: Partial<AssetCategory>): Promise<AssetCategory> {
    return request.put(`/assets/categories/${id}/`, data)
  },

  /**
   * Delete category
   */
  delete(id: string): Promise<void> {
    return request.delete(`/assets/categories/${id}/`)
  }
}

/**
 * Asset Location API service object
 */
export const locationApi = {
  /**
   * List all locations (flat)
   */
  list(): Promise<any[]> {
    return request.get('/assets/locations/')
  },

  /**
   * Get location tree structure
   */
  tree(): Promise<any[]> {
    return request.get('/assets/locations/tree/')
  }
}

/**
 * Asset Transfer API service object
 */
export const transferApi = {
  /**
   * List transfers
   */
  list(params?: {
    page?: number
    pageSize?: number
    assetId?: string
    status?: string
  }): Promise<PaginatedResponse<any>> {
    return request.get('/assets/transfers/', { params })
  },

  /**
   * Create transfer request
   */
  create(data: {
    assetId: string
    toLocationId?: string
    toUserId?: string
    reason?: string
  }): Promise<any> {
    return request.post('/assets/transfers/', data)
  },

  /**
   * Approve transfer
   */
  approve(id: string): Promise<void> {
    return request.post(`/assets/transfers/${id}/approve/`)
  },

  /**
   * Reject transfer
   */
  reject(id: string, reason: string): Promise<void> {
    return request.post(`/assets/transfers/${id}/reject/`, { reason })
  }
}
