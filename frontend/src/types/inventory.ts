/**
 * Inventory Module Type Definitions
 *
 * Types for inventory management including tasks, snapshots, and reconciliation.
 * Reference: docs/plans/phase4_1_inventory_qr/frontend_v2.md
 */

import type { BaseModel, User } from './common'
import type { Asset } from './assets'

/**
 * Task Type Enum
 */
export enum TaskType {
  FULL = 'full',
  PARTIAL = 'partial',
  LOCATION = 'location',
  CATEGORY = 'category'
}

/**
 * Task Status Enum
 */
export enum TaskStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

/**
 * Scan Result Enum
 */
export enum ScanResult {
  NORMAL = 'normal',
  LOCATION_CHANGED = 'location_changed',
  DAMAGED = 'damaged',
  MISSING = 'missing',
  EXTRA = 'extra'
}

/**
 * Inventory Task Interface
 */
export interface InventoryTask extends BaseModel {
  taskNo: string
  taskName: string
  taskType: TaskType
  status: TaskStatus
  plannedDate: string
  locationId?: string
  locationName?: string
  categoryId?: string
  categoryName?: string
  assetCount: number
  scannedCount: number
  abnormalCount: number
  completedAt?: string
  completedBy?: string
  note?: string
}

/**
 * Inventory Snapshot Interface
 */
export interface InventorySnapshot {
  id: string
  taskId: string
  assetId: string
  asset?: Asset
  expectedLocation: string
  expectedLocationId?: string
  scanned: boolean
  scanResult?: ScanResult
  actualLocation?: string
  actualLocationId?: string
  scannedAt?: string
  scannedBy?: User
  remark?: string
  imageUrl?: string
}

/**
 * Inventory Reconciliation Interface
 */
export interface InventoryReconciliation {
  id: string
  taskId: string
  task?: InventoryTask
  reconciledAt: string
  reconciledBy: string
  normalCount: number
  abnormalCount: number
  adjustments: ReconciliationAdjustment[]
  status: ReconciliationStatus
  note?: string
}

/**
 * Reconciliation Status Enum
 */
export enum ReconciliationStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  APPROVED = 'approved',
  REJECTED = 'rejected'
}

/**
 * Reconciliation Adjustment Interface
 */
export interface ReconciliationAdjustment {
  id: string
  reconciliationId: string
  assetId: string
  asset?: Asset
  adjustmentType: AdjustmentType
  oldValue?: any
  newValue?: any
  reason: string
}

/**
 * Adjustment Type Enum
 */
export enum AdjustmentType {
  LOCATION_CHANGE = 'location_change',
  CUSTODIAN_CHANGE = 'custodian_change',
  STATUS_CHANGE = 'status_change',
  DAMAGED = 'damaged',
  LOST = 'lost',
  EXTRA_FOUND = 'extra_found'
}

/**
 * Scan Record Interface
 */
export interface ScanRecord {
  id: string
  taskId: string
  snapshotId: string
  assetId: string
  qrCode: string
  scannedAt: string
  scannedBy: User
  location?: string
  result: ScanResult
  remark?: string
}

/**
 * Inventory Statistics Interface
 */
export interface InventoryStatistics {
  totalTasks: number
  pendingTasks: number
  inProgressTasks: number
  completedTasks: number
  thisMonthTasks: number
  recentTasks: InventoryTask[]
}
