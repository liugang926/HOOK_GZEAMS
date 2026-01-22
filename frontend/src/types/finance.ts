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
  ASSET_PURCHASE = 'asset_purchase',
  ASSET_DEPRECIATION = 'asset_depreciation',
  ASSET_DISPOSAL = 'asset_disposal',
  ASSET_TRANSFER = 'asset_transfer',
  CONSUMABLE_PURCHASE = 'consumable_purchase'
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
 * Voucher Template Interface
 */
export interface VoucherTemplate {
  id: string
  templateName: string
  code: string
  businessType: BusinessType
  voucherType: string
  defaultDescription: string
  entriesConfig: TemplateEntryConfig[]
  isActive: boolean
  organizationId: string
}

/**
 * Template Entry Configuration
 */
export interface TemplateEntryConfig {
  lineNo: number
  accountCode: string
  accountName: string
  debitOrCredit: 'debit' | 'credit'
  amountFormula?: string
  description?: string
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
