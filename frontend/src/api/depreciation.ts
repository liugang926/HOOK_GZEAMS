/**
 * Depreciation API Service
 *
 * API methods for asset depreciation calculation and tracking.
 * Reference: docs/plans/phase5_3_depreciation/frontend_v2.md
 */

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { DepreciationRecord, DepreciationReport } from '@/types/depreciation'
import { normalizeQueryParams, toData, toPaginated } from '@/api/contract'

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
    const mappedParams = {
      ...params,
      // Backend filter key is `asset` (mapped to asset__asset_code), not `asset_id`.
      asset: params?.assetId || (params as any)?.asset
    } as any
    delete mappedParams.assetId

    return request
      .get('/system/objects/DepreciationRecord/', { params: normalizeQueryParams(mappedParams) })
      .then((res) => toPaginated<DepreciationRecord>(res))
  },

  /**
   * Get single record by ID
   */
  getRecord(id: string): Promise<DepreciationRecord> {
    return request.get(`/system/objects/DepreciationRecord/${id}/`)
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
    return request.post('/system/objects/DepreciationRun/calculate/', normalizeQueryParams(params)).then((res) => {
      const payload = toData<any>(res, {})
      const runId = payload?.id || payload?.taskId
      return { taskId: runId }
    })
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
    return request.get(`/system/objects/DepreciationRun/${taskId}/`).then((res) => {
      const payload = toData<any>(res, {})
      const backendStatus = payload?.status
      const mappedStatus =
        backendStatus === 'completed'
          ? 'completed'
          : backendStatus === 'failed'
            ? 'failed'
            : backendStatus === 'in_progress'
              ? 'processing'
              : 'pending'
      const total = Number(payload?.totalAssets || 0)
      const processed = mappedStatus === 'completed' ? total : 0
      return {
        status: mappedStatus,
        progress: mappedStatus === 'completed' ? 100 : 0,
        total,
        processed,
        error: payload?.errorMessage
      }
    })
  },

  /**
   * Post depreciation record to accounting
   */
  postRecord(id: string): Promise<void> {
    return request.post(`/system/objects/DepreciationRecord/${id}/post/`)
  },

  /**
   * Batch post depreciation records
   */
  batchPost(ids: string[]): Promise<void> {
    return request.post('/system/objects/DepreciationRecord/batch_post/', { ids })
  },

  /**
   * Submit record for approval
   */
  submitRecord(id: string): Promise<void> {
    return request.post(`/system/objects/DepreciationRecord/${id}/submit/`)
  },

  /**
   * Approve or reject record
   */
  approveRecord(id: string, data: {
    action: 'approve' | 'reject'
    comment?: string
  }): Promise<void> {
    return request.post(`/system/objects/DepreciationRecord/${id}/approve/`, data)
  },

  /**
   * Get depreciation report
   */
  getReport(params: {
    period: string
    categoryIds?: string[]
  }): Promise<DepreciationReport> {
    return request.get('/system/objects/DepreciationRecord/report/', { params: normalizeQueryParams(params) })
  },

  /**
   * Export depreciation report
   */
  exportReport(params: {
    period: string
    categoryIds?: string[]
    format?: 'xlsx' | 'pdf' | 'csv'
    fileFormat?: 'xlsx' | 'pdf' | 'csv'
  }): Promise<Blob> {
    const mappedParams = {
      ...params,
      fileFormat: params.fileFormat || params.format
    } as any
    delete mappedParams.format

    return request.get('/system/objects/DepreciationRecord/report/export/', {
      params: normalizeQueryParams(mappedParams),
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
    return request.get(`/system/objects/DepreciationRecord/assets/${assetId}/detail/`)
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
    return request.get(`/system/objects/DepreciationConfig/categories/${categoryId}/`)
  },

  /**
   * Update category depreciation configuration
   */
  updateCategoryConfig(categoryId: string, config: {
    depreciationMethod: string
    usefulLife: number
    residualRate: number
  }): Promise<void> {
    return request.put(`/system/objects/DepreciationConfig/categories/${categoryId}/`, config)
  },

  /**
   * Get global depreciation configuration
   */
  getGlobalConfig(): Promise<any> {
    return request.get('/system/objects/DepreciationConfig/global/')
  },

  /**
   * Update global depreciation configuration
   */
  updateGlobalConfig(config: {
    defaultMethod: string
    defaultUsefulLife: number
    defaultResidualRate: number
  }): Promise<void> {
    return request.put('/system/objects/DepreciationConfig/global/', config)
  }
}
