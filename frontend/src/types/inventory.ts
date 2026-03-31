/**
 * Inventory Module Type Definitions
 *
 * Types for inventory management including tasks, snapshots, differences,
 * reconciliation, and scan workflows.
 * Reference: docs/plans/phase4_3_inventory_snapshot/frontend_v2.md
 */

import type { User } from "./common";
import type { Asset } from "./assets";
import type { BaseModel } from "./common";

/**
 * Task Type Enum
 */
export enum TaskType {
  FULL = "full",
  PARTIAL = "partial",
  LOCATION = "location",
  DEPARTMENT = "department",
  CATEGORY = "category",
}

/**
 * Task Status Enum
 */
export enum TaskStatus {
  DRAFT = "draft",
  PENDING_APPROVAL = "pending_approval",
  PENDING = "pending",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
  CANCELLED = "cancelled",
}

/**
 * Scan Result Enum
 */
export enum ScanResult {
  NORMAL = "normal",
  LOCATION_CHANGED = "location_changed",
  DAMAGED = "damaged",
  MISSING = "missing",
  EXTRA = "extra",
  SURPLUS = "surplus",
}

/**
 * Inventory difference type.
 */
export type InventoryDifferenceType =
  | "normal"
  | "missing"
  | "extra"
  | "surplus"
  | "damaged"
  | "location_mismatch"
  | "custodian_mismatch";

/**
 * Inventory difference status.
 */
export type InventoryDifferenceStatus =
  | "pending"
  | "confirmed"
  | "in_review"
  | "approved"
  | "executing"
  | "resolved"
  | "ignored"
  | "closed";

/**
 * Batch resolution action.
 */
export type DifferenceResolutionAction = "confirm" | "adjust";

/**
 * Snapshot asset payload stored in task snapshots.
 */
export interface SnapshotAsset {
  assetId: string;
  assetCode: string;
  assetName: string;
  categoryId?: string;
  categoryName?: string;
  locationId?: string | null;
  locationName?: string;
  custodianId?: string | null;
  custodianName?: string;
  departmentId?: string | null;
  departmentName?: string;
  status?: string;
  qrCode?: string;
}

/**
 * Inventory Task Interface
 */
export interface InventoryTask extends BaseModel {
  taskNo: string;
  taskCode?: string;
  name?: string;
  taskName: string;
  taskType: TaskType;
  inventoryType?: TaskType | string;
  status: TaskStatus | string;
  approvalStatus?: string;
  workflowInstanceId?: string | null;
  submittedAt?: string | null;
  approvedAt?: string | null;
  startDate?: string;
  endDate?: string;
  plannedDate: string;
  startedAt?: string;
  locationId?: string;
  locationName?: string;
  categoryId?: string;
  categoryName?: string;
  departmentId?: string;
  departmentName?: string;
  assetCount: number;
  totalAssets?: number;
  totalCount?: number;
  scannedCount: number;
  abnormalCount?: number;
  normalCount?: number;
  missingCount?: number;
  extraCount?: number;
  surplusCount?: number;
  damagedCount?: number;
  locationChangedCount?: number;
  completedAt?: string;
  completedBy?: string;
  progressPercentage?: number;
  note?: string;
  notes?: string;
}

/**
 * Inventory task assignment status.
 */
export type InventoryAssignmentStatus = "pending" | "in_progress" | "completed";

/**
 * Inventory task assignment payload.
 */
export interface InventoryTaskAssignment {
  id: string;
  taskId: string;
  task?: InventoryTask | string;
  taskName?: string;
  assigneeId: string;
  assignee?: User | string | null;
  assigneeName?: string;
  assignedBy: string;
  assignedByUser?: User | string | null;
  assignedByName?: string;
  assignedAt: string;
  status: InventoryAssignmentStatus;
  completedAt?: string;
  scanCount: number;
  assetCount: number;
  region?: string;
  locationIds?: string[];
  locationNames?: string[];
}

/**
 * Assignment creation request payload.
 */
export interface TaskAssignment {
  taskId: string;
  assigneeIds: string[];
  region?: string;
  locationIds?: string[];
}

/**
 * Assignment progress payload.
 */
export interface AssignmentProgress {
  assignmentId: string;
  assigneeId: string;
  assigneeName: string;
  totalAssets: number;
  scannedCount: number;
  normalCount: number;
  abnormalCount: number;
  progress: number;
  status?: InventoryAssignmentStatus;
}

/**
 * Assignment reassignment request payload.
 */
export interface ReassignmentRequest {
  fromAssigneeId: string;
  toAssigneeId: string;
  taskIds: string[];
  reason?: string;
}

/**
 * Inventory Snapshot Interface
 *
 * This interface supports both the Phase 4.3 task-level snapshot shape and the
 * existing per-asset runtime snapshot payloads used by scan execution pages.
 */
export interface InventorySnapshot {
  id: string;
  taskId: string;
  task?: InventoryTask | string;
  snapshotAt?: string;
  totalAssets?: number;
  snapshotData?: SnapshotAsset[];
  organizationId?: string;
  createdAt?: string;
  createdBy?: string | User;
  assetId?: string;
  asset?: Asset | string | null;
  assetCode?: string;
  assetName?: string;
  categoryId?: string;
  categoryName?: string;
  departmentId?: string | null;
  departmentName?: string;
  locationId?: string | null;
  locationName?: string;
  custodianId?: string | null;
  custodianName?: string;
  status?: string;
  assetStatus?: string;
  qrCode?: string;
  expectedLocation?: string;
  expectedLocationId?: string;
  scanned?: boolean;
  scanResult?: ScanResult | string;
  actualLocation?: string;
  actualLocationId?: string;
  actualCustodian?: string;
  actualCustodianId?: string;
  scannedAt?: string;
  scannedBy?: User | string;
  remark?: string;
  imageUrl?: string;
  scanCount?: number;
}

/**
 * Inventory difference payload.
 */
export interface InventoryDifference {
  id: string;
  taskId: string;
  task?: InventoryTask | string;
  taskCode?: string;
  assetId?: string;
  asset?: SnapshotAsset | Asset | string | null;
  assetCode?: string;
  assetName?: string;
  differenceType: InventoryDifferenceType;
  differenceTypeLabel?: string;
  expectedData?: SnapshotAsset;
  actualData?: SnapshotAsset;
  description?: string;
  expectedQuantity?: number;
  actualQuantity?: number;
  quantityDifference?: number;
  expectedLocation?: string;
  actualLocation?: string;
  expectedCustodian?: string;
  actualCustodian?: string;
  status: InventoryDifferenceStatus;
  statusLabel?: string;
  remark?: string;
  resolution?: string;
  owner?: User | string | null;
  reviewedBy?: User | string | null;
  approvedBy?: User | string | null;
  resolvedBy?: User | string | null;
  resolvedAt?: string;
  reviewedAt?: string;
  approvedAt?: string;
  createdAt: string;
  updatedAt?: string;
  closureType?: string;
  closureTypeLabel?: string;
  closureNotes?: string;
  closureCompletedAt?: string;
  evidenceRefs?: string[];
  linkedActionCode?: string;
  closureSummary?: Record<string, unknown>;
  customFields?: Record<string, unknown>;
}

/**
 * Batch difference resolution payload.
 */
export interface DifferenceResolution {
  differenceIds: string[];
  action: DifferenceResolutionAction;
  remark?: string;
}

/**
 * Difference adjustment payload.
 */
export interface DifferenceAdjustment {
  resolution?: string;
  remark?: string;
  syncAsset?: boolean;
  linkedActionCode?: string;
}

/**
 * Lightweight task reference payload used by reconciliation and report APIs.
 */
export interface InventoryTaskReference {
  id: string;
  taskNo?: string;
  taskName?: string;
  name?: string;
  startDate?: string;
  endDate?: string;
}

/**
 * Lightweight asset reference payload used by adjustment APIs.
 */
export interface InventoryAssetReference {
  id: string;
  assetNo?: string;
  assetCode?: string;
  assetName?: string;
  name?: string;
  category?: string;
  department?: string;
}

/**
 * Inventory Reconciliation Interface
 */
export interface InventoryReconciliation extends BaseModel {
  reconciliationNo?: string;
  taskId: string;
  task?: InventoryTaskReference | InventoryTask | string | null;
  taskNo?: string;
  taskName?: string;
  reconciledAt?: string;
  reconciledBy?: User | string | null;
  reconciledByName?: string;
  normalCount: number;
  abnormalCount: number;
  differenceCount?: number;
  adjustmentCount?: number;
  adjustments?: ReconciliationAdjustment[];
  status: ReconciliationStatus | string;
  statusDisplay?: string;
  currentApprover?: User | string | null;
  currentApproverName?: string;
  note?: string;
  submittedAt?: string;
  approvedAt?: string;
  rejectedAt?: string;
}

/**
 * Reconciliation Status Enum
 */
export enum ReconciliationStatus {
  DRAFT = "draft",
  SUBMITTED = "submitted",
  APPROVED = "approved",
  REJECTED = "rejected",
}

/**
 * Reconciliation Adjustment Interface
 */
export interface ReconciliationAdjustment extends BaseModel {
  reconciliationId?: string;
  resolutionId?: string;
  resolution?: {
    id: string;
    resolutionNo?: string;
  } | null;
  adjustmentNo?: string;
  assetId?: string;
  asset?: Asset | InventoryAssetReference | string | null;
  assetNo?: string;
  assetCode?: string;
  assetName?: string;
  adjustmentType: AdjustmentType | string;
  adjustmentTypeDisplay?: string;
  status?: string;
  statusDisplay?: string;
  beforeValue?: Record<string, unknown>;
  afterValue?: Record<string, unknown>;
  oldValue?: unknown;
  newValue?: unknown;
  reason?: string;
  changeDescription?: string;
  executedBy?: User | string | null;
  executedAt?: string;
  rolledBack?: boolean;
  rolledBackAt?: string;
  rolledBackBy?: User | string | null;
  rollbackReason?: string;
}

/**
 * Adjustment Type Enum
 */
export enum AdjustmentType {
  LOCATION = "location",
  STATUS = "status",
  VALUE = "value",
  INFO = "info",
  NEW = "new",
  REMOVE = "remove",
}

/**
 * Inventory report lifecycle status.
 */
export enum ReportStatus {
  DRAFT = "draft",
  PENDING_APPROVAL = "pending_approval",
  APPROVED = "approved",
  REJECTED = "rejected",
}

/**
 * Inventory report summary block.
 */
export interface InventoryReportSummary {
  taskNo?: string;
  taskName?: string;
  periodStart?: string;
  periodEnd?: string;
  totalAssets: number;
  scannedAssets: number;
  unscannedAssets?: number;
  scanRate?: string;
  differenceCount: number;
  differenceRate?: string;
}

/**
 * Department-level report statistics.
 */
export interface InventoryReportDepartmentSummary {
  department: string;
  total: number;
  scanned: number;
  differences: number;
}

/**
 * Detailed difference row inside a report.
 */
export interface InventoryReportDifferenceDetail {
  type: string;
  asset: string;
  assetNo?: string;
  value?: string;
  description?: string;
  status?: string;
}

/**
 * Structured report content returned by report detail APIs.
 */
export interface InventoryReportData {
  summary?: InventoryReportSummary;
  differencesByType?: Record<string, number>;
  differencesByDepartment?: InventoryReportDepartmentSummary[];
  differencesDetail?: InventoryReportDifferenceDetail[];
  recommendations?: string[];
}

/**
 * Approval trace item for inventory reports.
 */
export interface InventoryReportApproval {
  level: number;
  approver?: User | string | null;
  action: string;
  opinion?: string;
  approvedAt?: string;
}

/**
 * Inventory report payload.
 */
export interface InventoryReport extends BaseModel {
  reportNo?: string;
  taskId?: string;
  task?: InventoryTaskReference | InventoryTask | string | null;
  status: ReportStatus | string;
  statusDisplay?: string;
  summary?: InventoryReportSummary;
  template?: {
    id: string;
    templateName?: string;
    templateCode?: string;
  } | null;
  reportData?: InventoryReportData;
  generatedBy?: User | string | null;
  generatedAt?: string;
  currentApprover?: User | string | null;
  currentApproverName?: string;
  approvals?: InventoryReportApproval[];
}

/**
 * Reconciliation creation payload.
 */
export interface CreateInventoryReconciliationPayload {
  taskId: string;
  note?: string;
}

/**
 * Report generation payload.
 */
export interface GenerateInventoryReportPayload {
  taskId: string;
  templateId?: string;
}

/**
 * Scan Record Interface
 */
export interface ScanRecord {
  id: string;
  taskId: string;
  snapshotId: string;
  assetId: string;
  qrCode: string;
  scannedAt: string;
  scannedBy: User;
  location?: string;
  result: ScanResult | string;
  remark?: string;
}

/**
 * Inventory Statistics Interface
 */
export interface InventoryStatistics {
  totalTasks: number;
  pendingTasks: number;
  inProgressTasks: number;
  completedTasks: number;
  thisMonthTasks: number;
  recentTasks: InventoryTask[];
}
