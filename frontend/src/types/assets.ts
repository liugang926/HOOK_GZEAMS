/**
 * Asset Module Type Definitions
 *
 * Types for asset management including assets, categories, and lifecycle.
 * Reference: docs/plans/phase1_4_asset_crud/frontend_v2.md
 */

import type { BaseModel, User } from './common'

/**
 * Asset Status Enum
 */
export enum AssetStatus {
  DRAFT = 'draft',
  IN_USE = 'in_use',
  IDLE = 'idle',
  MAINTENANCE = 'maintenance',
  SCRAPPED = 'scrapped'
}

/**
 * Depreciation Method Enum
 */
export enum DepreciationMethod {
  STRAIGHT_LINE = 'straight_line',
  DOUBLE_DECLINING = 'double_declining',
  SUM_OF_YEARS = 'sum_of_years'
}

/**
 * Asset Category Interface
 */
export interface AssetCategory {
  id: string
  code: string
  name: string
  parentId?: string
  level: number
  path?: string
  depreciationMethod?: DepreciationMethod
  usefulLifeMonths?: number
  residualRate?: number
  isActive?: boolean
  children?: AssetCategory[]
}

/**
 * Location Interface
 */
export interface AssetLocation {
  id: string
  name: string
  code: string
  parentId?: string
  level: number
}

/**
 * Supplier Interface
 */
export interface AssetSupplier {
  id: string
  name: string
  code: string
  contact?: string
  phone?: string
  email?: string
}

/**
 * Main Asset Interface
 */
export interface Asset extends BaseModel {
  code: string
  name: string
  categoryId?: string
  category?: AssetCategory
  status: AssetStatus
  purchasePrice: number
  purchaseDate: string
  supplierId?: string
  supplier?: AssetSupplier
  locationId?: string
  location?: AssetLocation
  custodianId?: string
  custodian?: User
  description?: string
  images?: string[]
  qrCode?: string
  specifications?: Record<string, any>
}

/**
 * Asset Operation Log Interface
 */
export interface AssetOperationLog {
  id: string
  assetId: string
  asset?: Asset
  operationType: OperationType
  operationContent: string
  operatorId: string
  operator?: User
  createdAt: string
  ip?: string
}

/**
 * Asset Operation Type Enum
 */
export enum OperationType {
  CREATE = 'create',
  UPDATE = 'update',
  DELETE = 'delete',
  TRANSFER = 'transfer',
  BORROW = 'borrow',
  RETURN = 'return',
  MAINTAIN = 'maintain',
  SCRAPPED = 'scrapped'
}

/**
 * Asset Transfer Interface
 */
export interface AssetTransfer {
  id: string
  assetId: string
  asset?: Asset
  fromLocationId?: string
  fromLocation?: AssetLocation
  toLocationId?: string
  toLocation?: AssetLocation
  fromUserId?: string
  fromUser?: User
  toUserId?: string
  toUser?: User
  transferDate: string
  reason?: string
  status: TransferStatus
  approvedBy?: string
  approvedAt?: string
}

/**
 * Transfer Status Enum
 */
export enum TransferStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  COMPLETED = 'completed'
}
