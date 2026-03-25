/**
 * Asset API Service
 *
 * API methods for asset management.
 * Now using unified Dynamic Object Routing for all business objects.
 * Reference: docs/plans/2025-01-22-frontend-implementation.md
 */

import request from '@/utils/request'
import { toData, toPaginated } from '@/api/contract'
import type { PaginatedResponse } from '@/types/api'
import type { Asset, AssetCategory, AssetLocation, AssetTransfer } from '@/types/assets'
import { BaseApiService } from '@/api/base'
import {
  assetApi as dynamicAssetApi,
  assetTransferApi,
} from '@/api/dynamic'

type LegacyPaginatedResponse<T> = PaginatedResponse<T> & {
  items: T[]
  total: number
}

/**
 * Asset API service object
 *
 * Extends BaseApiService but uses dynamic routing for core operations
 */
class AssetApiService extends BaseApiService<Asset> {
  constructor() {
    super('assets')
  }

  /**
   * Get asset by QR code (custom endpoint, not in dynamic routing)
   */
  getByQrCode(qrCode: string): Promise<Asset> {
    return request.get('/system/objects/Asset/lookup/', { params: { qr_code: qrCode } })
  }

  /**
   * Restore deleted asset (delegates to dynamic API)
   */
  async restore(id: string): Promise<void> {
    await dynamicAssetApi.restore(id)
  }

  /**
   * Get asset statistics (custom endpoint, not in dynamic routing)
   */
  statistics(): Promise<{
    total: number
    by_status: Record<string, number>
    total_value: number
    total_net_value: number
    by_category: Record<string, number>
  }> {
    return request.get('/system/objects/Asset/statistics/')
  }

  /**
   * List assets (delegates to dynamic API)
   */
  async list(params?: any): Promise<PaginatedResponse<Asset>> {
    return toPaginated<Asset>(await dynamicAssetApi.list(params))
  }

  /**
   * Get single asset (delegates to dynamic API)
   */
  async get(id: string, params?: any): Promise<Asset> {
    return toData<Asset>(await dynamicAssetApi.get(id, params))
  }

  /**
   * Create asset (delegates to dynamic API)
   */
  async create(data: Partial<Asset>): Promise<Asset> {
    return toData<Asset>(await dynamicAssetApi.create(data))
  }

  /**
   * Update asset (delegates to dynamic API)
   */
  async update(id: string, data: Partial<Asset>): Promise<Asset> {
    return toData<Asset>(await dynamicAssetApi.update(id, data))
  }

  /**
   * Delete asset (delegates to dynamic API)
   */
  async delete(id: string): Promise<void> {
    await dynamicAssetApi.delete(id)
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
    return request.get('/system/objects/AssetCategory/')
  },

  /**
   * Get category tree structure
   */
  tree(): Promise<AssetCategory[]> {
    return request.get('/system/objects/AssetCategory/tree/')
  },

  /**
   * Get single category by ID
   */
  get(id: string): Promise<AssetCategory> {
    return request.get(`/system/objects/AssetCategory/${id}/`)
  },

  /**
   * Create new category
   */
  create(data: Partial<AssetCategory>): Promise<AssetCategory> {
    return request.post('/system/objects/AssetCategory/', data)
  },

  /**
   * Update category
   */
  update(id: string, data: Partial<AssetCategory>): Promise<AssetCategory> {
    return request.put(`/system/objects/AssetCategory/${id}/`, data)
  },

  /**
   * Delete category
   */
  delete(id: string): Promise<void> {
    return request.delete(`/system/objects/AssetCategory/${id}/`)
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
    return request.get('/system/objects/Location/')
  },

  /**
   * Get location tree structure
   */
  tree(): Promise<AssetLocation[]> {
    return request.get('/system/objects/Location/tree/')
  }
}

/**
 * Convenience function for getting assets (used by other components)
 */
export const getAssets = (params?: any): Promise<any> => {
  return request.get('/system/objects/Asset/', { params })
}

/**
 * Convenience function for getting categories (used by other components)
 */
export const getCategories = (): Promise<any> => {
  return request.get('/system/objects/AssetCategory/')
}

/**
 * Asset Transfer API service object
 *
 * Now using unified Dynamic Object Routing via /api/objects/AssetTransfer/
 * Custom actions (approve/reject) still use dedicated endpoints
 */
export const transferApi = {
  /**
   * List transfers (delegates to dynamic API)
   */
  async list(params?: {
    page?: number
    pageSize?: number
    assetId?: string
    status?: string
  }): Promise<LegacyPaginatedResponse<AssetTransfer>> {
    const paginated = toPaginated<AssetTransfer>(await assetTransferApi.list(params))
    return {
      ...paginated,
      items: paginated.results,
      total: paginated.count
    }
  },

  /**
   * Create transfer request (delegates to dynamic API)
   */
  async create(data: {
    assetId: string
    toLocationId?: string
    toUserId?: string
    reason?: string
  }): Promise<AssetTransfer> {
    return toData<AssetTransfer>(await assetTransferApi.create(data))
  },

  /**
   * Get single transfer (delegates to dynamic API)
   */
  async get(id: string): Promise<AssetTransfer> {
    return toData<AssetTransfer>(await assetTransferApi.get(id))
  },

  /**
   * Update transfer (delegates to dynamic API)
   */
  async update(id: string, data: Partial<AssetTransfer>): Promise<AssetTransfer> {
    return toData<AssetTransfer>(await assetTransferApi.update(id, data))
  },

  /**
   * Delete transfer (delegates to dynamic API)
   */
  async delete(id: string): Promise<void> {
    await assetTransferApi.delete(id)
  },

  /**
   * Approve transfer (custom action endpoint)
   */
  approve(id: string): Promise<void> {
    return request.post(`/system/objects/AssetTransfer/${id}/approve/`)
  },

  /**
   * Reject transfer (custom action endpoint)
   */
  reject(id: string, reason: string): Promise<void> {
    return request.post(`/system/objects/AssetTransfer/${id}/reject/`, { reason })
  }
}
