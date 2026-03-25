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
  id: string | null
  code: string
  name: string
  parentId?: string
  parent_id?: string
  level: number
  path?: string
  depreciationMethod?: DepreciationMethod
  depreciation_method?: DepreciationMethod | string
  usefulLifeMonths?: number
  useful_life?: number
  residualRate?: number
  salvage_rate?: number
  isActive?: boolean
  is_active?: boolean
  children?: AssetCategory[]
  [key: string]: any
}

/**
 * Location Interface
 */
export interface AssetLocation {
  id: string | null
  name: string
  code: string
  parentId?: string
  parent_id?: string
  level: number
  [key: string]: any
}

/**
 * Supplier Interface
 */
export interface AssetSupplier {
  id: string | null
  name: string
  code: string
  contact?: string
  contactPerson?: string
  contact_person?: string
  phone?: string
  contactPhone?: string
  contact_phone?: string
  email?: string
  address?: string
  remark?: string
  isActive?: boolean
  is_active?: boolean
  [key: string]: any
}

/**
 * Main Asset Interface
 */
export interface Asset extends BaseModel {
  code: string
  name: string
  categoryId?: string
  category?: AssetCategory
  categoryName?: string
  status: AssetStatus
  purchasePrice: number
  purchaseDate: string
  supplierId?: string
  supplier?: AssetSupplier | string
  supplierName?: string
  locationId?: string
  location?: AssetLocation
  locationName?: string
  custodianId?: string
  custodian?: User
  custodianName?: string
  departmentName?: string
  user?: User
  description?: string
  images?: string[]
  qrCode?: string
  specifications?: Record<string, any>
  specification?: string
  [key: string]: any
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
