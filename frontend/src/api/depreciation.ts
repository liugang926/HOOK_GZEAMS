/**
 * Depreciation API Service
 *
 * API methods for asset depreciation calculation and tracking.
 * Reference: docs/plans/phase5_3_depreciation/frontend_v2.md
 */

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { DepreciationRecord, DepreciationReport } from '@/types/depreciation'

/**
 * Depreciation API service
 */
export const depreciationApi = {
  /**
   * List depreciation records
   */
  listRecords(params?: {
    page?: number
    pageSize?: number
    assetId?: string
    period?: string
    status?: string
  }): Promise<PaginatedResponse<DepreciationRecord>> {
    return request.get('/depreciation/records/', { params })
  },

  /**
   * Get single record by ID
   */
  getRecord(id: string): Promise<DepreciationRecord> {
    return request.get(`/depreciation/records/${id}/`)
  },

  /**
   * Calculate depreciation for a period
   * Returns a task ID for async processing
   */
  calculate(params?: {
    period?: string
    assetIds?: string[]
    categoryIds?: string[]
  }): Promise<{ taskId: string }> {
    return request.post('/depreciation/calculate/', params)
  },

  /**
   * Get calculation task status
   * Poll this endpoint to track async calculation progress
   */
  getCalculationStatus(taskId: string): Promise<{
    status: 'pending' | 'processing' | 'completed' | 'failed'
    progress: number
    total: number
    processed: number
    error?: string
  }> {
    return request.get(`/depreciation/calculate/${taskId}/status/`)
  },

  /**
   * Post depreciation record to accounting
   */
  postRecord(id: string): Promise<void> {
    return request.post(`/depreciation/records/${id}/post/`)
  },

  /**
   * Batch post depreciation records
   */
  batchPost(ids: string[]): Promise<void> {
    return request.post('/depreciation/records/batch-post/', { ids })
  },

  /**
   * Submit record for approval
   */
  submitRecord(id: string): Promise<void> {
    return request.post(`/depreciation/records/${id}/submit/`)
  },

  /**
   * Approve or reject record
   */
  approveRecord(id: string, data: {
    action: 'approve' | 'reject'
    comment?: string
  }): Promise<void> {
    return request.post(`/depreciation/records/${id}/approve/`, data)
  },

  /**
   * Get depreciation report
   */
  getReport(params: {
    period: string
    categoryIds?: string[]
  }): Promise<DepreciationReport> {
    return request.get('/depreciation/report/', { params })
  },

  /**
   * Export depreciation report
   */
  exportReport(params: {
    period: string
    categoryIds?: string[]
    format?: 'xlsx' | 'pdf'
  }): Promise<Blob> {
    return request.get('/depreciation/report/export/', {
      params,
      responseType: 'blob'
    })
  },

  /**
   * Get asset depreciation detail
   */
  getAssetDetail(assetId: string): Promise<{
    assetInfo: any
    stat: {
      usedMonths: number
      accumulated: number
      netValue: number
      progress: number
    }
    records: DepreciationRecord[]
  }> {
    return request.get(`/depreciation/assets/${assetId}/detail/`)
  }
}

/**
 * Depreciation Configuration API service
 */
export const depreciationConfigApi = {
  /**
   * Get category depreciation configuration
   */
  getCategoryConfig(categoryId: string): Promise<any> {
    return request.get(`/depreciation/config/categories/${categoryId}/`)
  },

  /**
   * Update category depreciation configuration
   */
  updateCategoryConfig(categoryId: string, config: {
    depreciationMethod: string
    usefulLife: number
    residualRate: number
  }): Promise<void> {
    return request.put(`/depreciation/config/categories/${categoryId}/`, config)
  },

  /**
   * Get global depreciation configuration
   */
  getGlobalConfig(): Promise<any> {
    return request.get('/depreciation/config/global/')
  },

  /**
   * Update global depreciation configuration
   */
  updateGlobalConfig(config: {
    defaultMethod: string
    defaultUsefulLife: number
    defaultResidualRate: number
  }): Promise<void> {
    return request.put('/depreciation/config/global/', config)
  }
}
