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
  SUM_OF_YEARS = 'sum_of_years'
}

/**
 * Depreciation Status Enum
 */
export enum DepreciationStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  APPROVED = 'approved',
  POSTED = 'posted'
}

/**
 * Depreciation Record Interface
 */
export interface DepreciationRecord extends BaseModel {
  assetId: string
  asset?: Asset
  period: string
  periodIndex: number
  depreciationMethod: DepreciationMethod
  purchasePrice: number
  residualValue: number
  usefulLife: number
  usedMonths: number
  depreciationAmount: number
  accumulatedDepreciation: number
  netValue: number
  status: DepreciationStatus
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
  categoryId?: string
  category?: AssetCategory
  depreciationMethod: DepreciationMethod
  usefulLife: number
  residualRate: number
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
