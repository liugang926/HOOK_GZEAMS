/**
 * Depreciation Module Type Definitions
 *
 * Types for asset depreciation calculation and tracking.
 * Reference: docs/plans/phase5_3_depreciation/frontend_v2.md
 */

import type { BaseModel } from './common'
import type { Asset, AssetCategory } from './assets'

/**
 * Depreciation Method Enum
 */
export enum DepreciationMethod {
  STRAIGHT_LINE = 'straight_line',
  DOUBLE_DECLINING = 'double_declining',
  SUM_OF_YEARS = 'sum_of_years',
  UNITS_OF_PRODUCTION = 'units_of_production'
}

/**
 * Depreciation Status Enum
 */
export enum DepreciationStatus {
  CALCULATED = 'calculated',
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  APPROVED = 'approved',
  POSTED = 'posted',
  REJECTED = 'rejected'
}

/**
 * Depreciation Record Interface
 */
export interface DepreciationRecord extends BaseModel {
  assetId?: string
  asset?: Asset
  assetCode?: string
  assetName?: string
  period?: string
  periodIndex?: number
  depreciationMethod?: DepreciationMethod | string
  purchasePrice?: number
  residualValue?: number
  usefulLife?: number
  usedMonths?: number
  depreciationAmount?: number
  accumulatedAmount?: number
  accumulatedDepreciation?: number
  netValue?: number
  status?: DepreciationStatus | string
  statusDisplay?: string
  postDate?: string | null
  voucherId?: string
  voucherNo?: string
}

/**
 * Depreciation Calculation Interface
 */
export interface DepreciationCalculation {
  assetId: string
  period: string
  method: DepreciationMethod
  purchasePrice: number
  residualValue: number
  usefulLife: number
  usedMonths: number
  monthlyDepreciation: number
  currentPeriodDepreciation: number
  accumulatedDepreciation: number
  netValue: number
}

/**
 * Depreciation Summary Interface
 */
export interface DepreciationSummary {
  assetCount: number
  originalValue: number
  currentAmount: number
  accumulatedAmount: number
  netValue: number
  postedCount?: number
  calculatedCount?: number
  rejectedCount?: number
}

/**
 * Depreciation Report Interface
 */
export interface DepreciationReport {
  period: string
  summary: DepreciationSummary
  byCategory: CategoryDepreciation[]
  byAsset: AssetDepreciation[]
}

/**
 * Category Depreciation Interface
 */
export interface CategoryDepreciation {
  categoryId: string
  categoryName: string
  assetCount: number
  originalValue: number
  currentDepreciation: number
  accumulatedDepreciation: number
  netValue: number
  depreciationRate: number
}

/**
 * Asset Depreciation Interface
 */
export interface AssetDepreciation {
  assetId: string
  assetCode: string
  assetName: string
  categoryName: string
  purchasePrice: number
  currentDepreciation: number
  accumulatedDepreciation: number
  netValue: number
  depreciationRate: number
}

/**
 * Depreciation Configuration Interface
 */
export interface DepreciationConfig {
  id?: string
  categoryId?: string
  category?: AssetCategory | string
  categoryCode?: string
  categoryName?: string
  categoryParentName?: string | null
  depreciationMethod: DepreciationMethod | string
  depreciationMethodDisplay?: string
  usefulLife: number
  residualRate: number
  salvageValueRate?: number
  monthlyRate?: number
  isActive?: boolean
  notes?: string
}

export interface GlobalDepreciationConfig {
  defaultMethod: DepreciationMethod | string
  defaultUsefulLife: number
  defaultResidualRate: number
  totalConfigs?: number
}

export interface DepreciationAssetDetail {
  assetInfo: {
    id: string
    assetCode: string
    assetName: string
    purchasePrice: number
    currentValue: number
    accumulatedDepreciation: number
    usefulLife: number
    residualRate: number
  }
  stat: {
    usedMonths: number
    accumulated: number
    netValue: number
    progress: number
  }
  records: DepreciationRecord[]
}

export interface DepreciationBatchPostResult {
  success: number
  failed: number
  results: Array<{
    id: string
    success: boolean
    error?: string
  }>
}

/**
 * Depreciation Calculation Task Status
 */
export interface CalculationTaskStatus {
  taskId: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  total: number
  processed: number
  error?: string
}
