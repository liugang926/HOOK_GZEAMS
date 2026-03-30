/**
 * Depreciation API Service
 *
 * API methods for asset depreciation calculation and tracking.
 * Reference: docs/plans/phase5_3_depreciation/frontend_v2.md
 */

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  DepreciationAssetDetail,
  DepreciationBatchPostResult,
  DepreciationConfig,
  DepreciationRecord,
  DepreciationReport,
  GlobalDepreciationConfig,
} from '@/types/depreciation'
import { normalizeQueryParams, toCamelDeep, toData, toPaginated } from '@/api/contract'

const toNumber = (value: unknown): number => {
  const parsed = Number(value ?? 0)
  return Number.isFinite(parsed) ? parsed : 0
}

const normalizeRecord = (record: Record<string, any>): DepreciationRecord => {
  const normalized = toCamelDeep<Record<string, any>>(record)
  return {
    ...normalized,
    assetId: normalized.assetId || normalized.asset,
    assetCode: normalized.assetCode || normalized.asset?.assetCode || normalized.asset?.code,
    assetName: normalized.assetName || normalized.asset?.assetName || normalized.asset?.name,
    depreciationMethod: normalized.depreciationMethod || normalized.asset?.depreciationMethod,
    purchasePrice: toNumber(normalized.purchasePrice),
    depreciationAmount: toNumber(normalized.depreciationAmount),
    accumulatedAmount: toNumber(normalized.accumulatedAmount),
    accumulatedDepreciation: toNumber(normalized.accumulatedDepreciation ?? normalized.accumulatedAmount),
    netValue: toNumber(normalized.netValue),
  } as DepreciationRecord
}

const normalizeCategoryReportItem = (item: Record<string, any>) => {
  const normalized = toCamelDeep<Record<string, any>>(item)
  const accumulatedDepreciation = toNumber(normalized.totalAccumulated ?? normalized.accumulatedDepreciation)
  const netValue = toNumber(normalized.totalNet ?? normalized.netValue)
  return {
    categoryId: String(normalized.categoryId || normalized.categoryCode || ''),
    categoryName: String(normalized.categoryName || normalized.assetAssetCategoryName || '-'),
    assetCount: toNumber(normalized.assetCount ?? normalized.recordCount),
    originalValue: accumulatedDepreciation + netValue,
    currentDepreciation: toNumber(normalized.currentDepreciation ?? normalized.totalDepreciation),
    accumulatedDepreciation,
    netValue,
    depreciationRate: toNumber(normalized.depreciationRate),
  }
}

const normalizeAssetReportItem = (item: Record<string, any>) => {
  const normalized = toCamelDeep<Record<string, any>>(item)
  return {
    assetId: String(normalized.assetId || normalized.id || ''),
    assetCode: String(normalized.assetCode || ''),
    assetName: String(normalized.assetName || ''),
    categoryName: String(normalized.categoryName || normalized.assetAssetCategoryName || '-'),
    purchasePrice: toNumber(normalized.purchasePrice),
    currentDepreciation: toNumber(normalized.currentDepreciation ?? normalized.depreciationAmount),
    accumulatedDepreciation: toNumber(
      normalized.accumulatedDepreciation ?? normalized.accumulatedAmount
    ),
    netValue: toNumber(normalized.netValue),
    depreciationRate: toNumber(normalized.depreciationRate),
  }
}

const normalizeConfig = (config: Record<string, any>): DepreciationConfig => {
  const normalized = toCamelDeep<Record<string, any>>(config)
  const residualRate = toNumber(normalized.residualRate ?? normalized.salvageValueRate)

  return {
    ...normalized,
    categoryId: normalized.categoryId || normalized.category,
    depreciationMethod: normalized.depreciationMethod,
    usefulLife: toNumber(normalized.usefulLife),
    residualRate,
    salvageValueRate: toNumber(normalized.salvageValueRate ?? residualRate),
    monthlyRate: toNumber(normalized.monthlyRate),
  } as DepreciationConfig
}

const normalizeGlobalConfig = (config: Record<string, any>): GlobalDepreciationConfig => {
  const normalized = toCamelDeep<Record<string, any>>(config)
  return {
    defaultMethod: normalized.defaultMethod,
    defaultUsefulLife: toNumber(normalized.defaultUsefulLife),
    defaultResidualRate: toNumber(normalized.defaultResidualRate),
    totalConfigs: toNumber(normalized.totalConfigs),
  }
}

const normalizeAssetDetail = (payload: Record<string, any>): DepreciationAssetDetail => {
  const normalized = toCamelDeep<Record<string, any>>(payload)
  const assetInfo = normalized.assetInfo || {}
  const stat = normalized.stat || {}

  return {
    assetInfo: {
      id: String(assetInfo.id || ''),
      assetCode: String(assetInfo.assetCode || ''),
      assetName: String(assetInfo.assetName || ''),
      purchasePrice: toNumber(assetInfo.purchasePrice),
      currentValue: toNumber(assetInfo.currentValue),
      accumulatedDepreciation: toNumber(assetInfo.accumulatedDepreciation),
      usefulLife: toNumber(assetInfo.usefulLife),
      residualRate: toNumber(assetInfo.residualRate),
    },
    stat: {
      usedMonths: toNumber(stat.usedMonths),
      accumulated: toNumber(stat.accumulated),
      netValue: toNumber(stat.netValue),
      progress: toNumber(stat.progress),
    },
    records: Array.isArray(normalized.records)
      ? normalized.records.map((record) => normalizeRecord(record))
      : [],
  }
}

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
    assetKeyword?: string
    assetId?: string
    period?: string
    status?: string
  }): Promise<PaginatedResponse<DepreciationRecord>> {
    const mappedParams = {
      ...params,
      // Backend `asset` filter accepts asset code/name keyword matching.
      asset: params?.assetKeyword || params?.assetId || (params as any)?.asset
    } as any
    delete mappedParams.assetKeyword
    delete mappedParams.assetId

    return request
      .get('/system/objects/DepreciationRecord/', { params: normalizeQueryParams(mappedParams) })
      .then((res) => {
        const paginated = toPaginated<Record<string, any>>(res)
        return {
          ...paginated,
          results: paginated.results.map((record) => normalizeRecord(record)),
        }
      })
  },

  /**
   * Get single record by ID
   */
  getRecord(id: string): Promise<DepreciationRecord> {
    return request
      .get(`/system/objects/DepreciationRecord/${id}/`)
      .then((res) => normalizeRecord(toData<Record<string, any>>(res, {})))
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
  batchPost(ids: string[]): Promise<DepreciationBatchPostResult> {
    return request.post('/system/objects/DepreciationRecord/batch_post/', { ids }).then((res: any) => {
      const summary = res?.summary || {}
      return {
        success: Number(summary.succeeded || 0),
        failed: Number(summary.failed || 0),
        results: Array.isArray(res?.results) ? res.results : [],
      }
    })
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
    return request
      .get('/system/objects/DepreciationRecord/report/', { params: normalizeQueryParams(params) })
      .then((res) => {
        const payload = toCamelDeep<Record<string, any>>(toData<Record<string, any>>(res, {}))
        const summary = payload.summary || {}
        const accumulatedAmount = toNumber(summary.totalAccumulatedAmount)
        const netValue = toNumber(summary.totalNetValue)

        return {
          period: params.period,
          summary: {
            assetCount: toNumber(summary.totalRecords),
            originalValue: accumulatedAmount + netValue,
            currentAmount: toNumber(summary.totalDepreciationAmount),
            accumulatedAmount,
            netValue,
            postedCount: toNumber(summary.postedCount),
            calculatedCount: toNumber(summary.calculatedCount),
            rejectedCount: toNumber(summary.rejectedCount),
          },
          byCategory: Array.isArray(payload.categoryBreakdown)
            ? payload.categoryBreakdown.map((item) => normalizeCategoryReportItem(item))
            : [],
          byAsset: Array.isArray(payload.byAsset)
            ? payload.byAsset.map((item) => normalizeAssetReportItem(item))
            : [],
        }
      })
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
  getAssetDetail(assetId: string): Promise<DepreciationAssetDetail> {
    return request
      .get(`/system/objects/DepreciationRecord/assets/${assetId}/detail/`)
      .then((res) => normalizeAssetDetail(toData<Record<string, any>>(res, {})))
  }
}

/**
 * Depreciation Configuration API service
 */
export const depreciationConfigApi = {
  /**
   * Get category depreciation configuration
   */
  getCategoryConfig(categoryId: string): Promise<DepreciationConfig> {
    return request
      .get(`/system/objects/DepreciationConfig/categories/${categoryId}/`)
      .then((res) => normalizeConfig(toData<Record<string, any>>(res, {})))
  },

  /**
   * Update category depreciation configuration
   */
  updateCategoryConfig(categoryId: string, config: {
    depreciationMethod: string
    usefulLife: number
    residualRate: number
  }): Promise<DepreciationConfig> {
    return request
      .put(`/system/objects/DepreciationConfig/categories/${categoryId}/`, config)
      .then((res) => normalizeConfig(toData<Record<string, any>>(res, {})))
  },

  /**
   * Get global depreciation configuration
   */
  getGlobalConfig(): Promise<GlobalDepreciationConfig> {
    return request
      .get('/system/objects/DepreciationConfig/global/')
      .then((res) => normalizeGlobalConfig(toData<Record<string, any>>(res, {})))
  },

  /**
   * Update global depreciation configuration
   */
  updateGlobalConfig(config: {
    defaultMethod: string
    defaultUsefulLife: number
    defaultResidualRate: number
  }): Promise<GlobalDepreciationConfig> {
    return request
      .put('/system/objects/DepreciationConfig/global/', config)
      .then((res) => normalizeGlobalConfig(toData<Record<string, any>>(res, {})))
  }
}
