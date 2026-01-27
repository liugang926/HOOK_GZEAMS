/**
 * Asset API Service
 *
 * API methods for asset management.
 * Reference: docs/plans/2025-01-22-frontend-implementation.md
 */

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { Asset, AssetCategory, AssetLocation, AssetTransfer } from '@/types/assets'
import { BaseApiService } from '@/api/base'

/**
 * Asset API service object
 */
/**
 * Asset API service object
 */
class AssetApiService extends BaseApiService<Asset> {
  constructor() {
    super('assets')
  }

  /**
   * Get asset by QR code
   */
  getByQrCode(qrCode: string): Promise<Asset> {
    return request.get('/assets/by-qr-code/', { params: { qr_code: qrCode } })
  }

  /**
   * Restore deleted asset
   */
  restore(id: string): Promise<Asset> {
    return request.post(`/assets/${id}/restore/`)
  }

  /**
   * Get asset statistics
   */
  statistics(): Promise<{
    total: number
    by_status: Record<string, number>
    total_value: number
    total_net_value: number
    by_category: Record<string, number>
  }> {
    return request.get(`/${this.resource}/statistics/`)
  }
}

export const assetApi = new AssetApiService()

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
  list(): Promise<AssetLocation[]> {
    return request.get('/assets/locations/')
  },

  /**
   * Get location tree structure
   */
  tree(): Promise<AssetLocation[]> {
    return request.get('/assets/locations/tree/')
  }
}

/**
 * Convenience function for getting assets (used by other components)
 */
export const getAssets = (params?: any): Promise<any> => {
  return request.get('/api/assets/', { params })
}

/**
 * Convenience function for getting categories (used by other components)
 */
export const getCategories = (): Promise<any> => {
  return request.get('/api/assets/categories/')
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
  }): Promise<PaginatedResponse<AssetTransfer>> {
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
  }): Promise<AssetTransfer> {
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
