/**
 * Finance Module Type Definitions
 *
 * Types for financial voucher management and ERP integration.
 * Reference: docs/plans/phase5_2_finance_integration/frontend_v2.md
 */

import type { BaseModel } from './common'

/**
 * Business Type Enum
 */
export enum BusinessType {
  PURCHASE = 'purchase',
  DEPRECIATION = 'depreciation',
  DISPOSAL = 'disposal',
  INVENTORY = 'inventory',
  OTHER = 'other'
}

/**
 * Voucher Status Enum
 */
export enum VoucherStatus {
  DRAFT = 'draft',
  SUBMITTED = 'submitted',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  POSTED = 'posted'
}

/**
 * Integration System Enum
 */
export enum IntegrationSystem {
  M18 = 'm18',
  SAP = 'sap',
  KINGDEE = 'kingdee',
  YONYOU = 'yonyou'
}

/**
 * Integration Status Enum
 */
export enum IntegrationStatus {
  PENDING = 'pending',
  SUCCESS = 'success',
  FAILED = 'failed'
}

/**
 * Voucher Entry Interface
 */
export interface VoucherEntry {
  id: string
  lineNo: number
  accountCode: string
  accountName: string
  debit: number
  credit: number
  description: string
}

/**
 * Finance Voucher Interface
 */
export interface FinanceVoucher extends BaseModel {
  voucherNo: string
  voucherDate: string
  businessType: BusinessType
  businessId?: string
  sourceObjectCode?: string
  sourceObjectLabel?: string
  sourceId?: string
  sourceRecordNo?: string
  sourceAssetCount?: number
  sourceSummary?: {
    objectCode?: string
    objectLabel?: string
    sourceId?: string
    recordNo?: string
    assetCount?: number
    assetIds?: string[]
    assetCodes?: string[]
    purchaseRequestId?: string
    purchaseRequestNo?: string
    receiptId?: string
    receiptNo?: string
    requestedBusinessId?: string
  }
  voucherType: string
  description: string
  totalDebit: number
  totalCredit: number
  status: VoucherStatus
  entries: VoucherEntry[]
  externalVoucherNo?: string
  externalSystem?: IntegrationSystem
  integrationStatus?: IntegrationStatus
  integrationError?: string
  approvedBy?: string
  approvedAt?: string
  approveComment?: string
}

/**
 * Voucher Template Entry Interface
 */
export interface VoucherTemplateEntry {
  accountCode: string
  accountName: string
  debitAmount: number
  creditAmount: number
  description: string
}

/**
 * Voucher Template Configuration
 */
export interface VoucherTemplateConfig {
  businessType?: BusinessType | string
  entries: VoucherTemplateEntry[]
  [key: string]: unknown
}

/**
 * Voucher Template Interface
 */
export interface VoucherTemplate extends BaseModel {
  name: string
  code: string
  businessType: BusinessType | string
  templateConfig: VoucherTemplateConfig
  isActive: boolean
  description: string
}

/**
 * Voucher Create Data Interface
 */
export interface VoucherCreate {
  voucherDate: string
  businessType: BusinessType
  businessId?: string
  description: string
  entries: Array<{
    accountCode: string
    debit: number
    credit: number
    description: string
  }>
}

/**
 * Voucher Approval Action Interface
 */
export interface VoucherApprovalAction {
  action: 'approve' | 'reject'
  comment?: string
}

/**
 * Voucher Template Apply Payload
 */
export interface VoucherTemplateApplyPayload {
  voucherDate: string
  summary?: string
  totalAmount?: number
  notes?: string
}

/**
 * Integration Log Interface
 */
export interface IntegrationLog {
  id: string
  voucherId: string
  system: IntegrationSystem
  endpoint: string
  requestData: Record<string, any>
  responseData?: Record<string, any>
  status: IntegrationStatus
  statusCode?: number
  error?: string
  executedAt: string
  duration: number
}
