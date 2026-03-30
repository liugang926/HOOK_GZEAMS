/**
 * Finance API Service
 *
 * API methods for financial voucher management and ERP integration.
 * Reference: docs/plans/phase5_2_finance_integration/frontend_v2.md
 */

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  FinanceVoucher,
  VoucherTemplate,
  VoucherCreate,
  VoucherApprovalAction,
  VoucherTemplateApplyPayload,
} from '@/types/finance'
import { normalizeQueryParams, toPaginated } from '@/api/contract'

/**
 * Finance Voucher API service
 */
export const financeApi = {
  /**
   * List vouchers with pagination and filters
   */
  listVouchers(params?: {
    page?: number
    pageSize?: number
    voucherNo?: string
    businessType?: string
    status?: string
    voucherDateFrom?: string
    voucherDateTo?: string
  }): Promise<PaginatedResponse<FinanceVoucher>> {
    return request
      .get('/system/objects/FinanceVoucher/', { params: normalizeQueryParams(params) })
      .then((res) => toPaginated<FinanceVoucher>(res))
  },

  /**
   * Get single voucher by ID
   */
  getVoucher(id: string): Promise<FinanceVoucher> {
    return request.get(`/system/objects/FinanceVoucher/${id}/`)
  },

  /**
   * Create new voucher
   */
  createVoucher(data: VoucherCreate): Promise<FinanceVoucher> {
    return request.post('/system/objects/FinanceVoucher/', data)
  },

  /**
   * Update voucher
   */
  updateVoucher(id: string, data: Partial<FinanceVoucher>): Promise<FinanceVoucher> {
    return request.put(`/system/objects/FinanceVoucher/${id}/`, data)
  },

  /**
   * Delete voucher
   */
  deleteVoucher(id: string): Promise<void> {
    return request.delete(`/system/objects/FinanceVoucher/${id}/`)
  },

  /**
   * Submit voucher for approval
   */
  submitVoucher(id: string): Promise<void> {
    return request.post(`/system/objects/FinanceVoucher/${id}/submit/`)
  },

  /**
   * Approve or reject voucher
   */
  approveVoucher(id: string, data: VoucherApprovalAction): Promise<void> {
    return request.post(`/system/objects/FinanceVoucher/${id}/approve/`, data)
  },

  /**
   * Post voucher to accounting
   */
  postVoucher(id: string): Promise<void> {
    return request.post(`/system/objects/FinanceVoucher/${id}/post/`)
  },

  /**
   * Push voucher to external ERP system
   */
  pushVoucher(id: string, system?: string): Promise<{
    success: boolean
    queued?: boolean
    taskId?: string
    syncTaskId?: string
    externalVoucherNo?: string
    error?: string
  }> {
    return request.post(`/system/objects/FinanceVoucher/${id}/push/`, { system })
  },

  /**
   * Batch push vouchers to ERP
   */
  batchPushVouchers(ids: string[]): Promise<{
    success: number
    failed: number
    results: Array<{
      id: string
      success: boolean
      error?: string
      queued?: boolean
      duplicate?: boolean
      taskId?: string
      syncTaskId?: string
    }>
  }> {
    return request.post('/system/objects/FinanceVoucher/batch_push/', { ids }).then((res: any) => {
      const summary = res?.summary || {}
      return {
        success: Number(summary.succeeded || 0),
        failed: Number(summary.failed || 0),
        results: Array.isArray(res?.results)
          ? res.results.map((item: any) => ({
            ...item,
            taskId: item?.taskId || item?.task_id,
            syncTaskId: item?.syncTaskId || item?.sync_task_id,
          }))
          : [],
      }
    })
  },

  /**
   * Get voucher entries for editing
   */
  getEntries(id: string): Promise<FinanceVoucher> {
    return request.get(`/system/objects/FinanceVoucher/${id}/entries/`)
  },

  /**
   * Update voucher entries
   */
  updateEntries(id: string, entries: Array<{
    accountCode: string
    debit: number
    credit: number
    description: string
  }>): Promise<FinanceVoucher> {
    return request.put(`/system/objects/FinanceVoucher/${id}/entries/`, { entries })
  }
}

/**
 * Voucher Template API service
 */
export const voucherTemplateApi = {
  /**
   * List voucher templates
   */
  listTemplates(params?: {
    businessType?: string
    isActive?: boolean
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<VoucherTemplate>> {
    return request
      .get('/system/objects/VoucherTemplate/', { params: normalizeQueryParams(params) })
      .then((res) => toPaginated<VoucherTemplate>(res))
  },

  /**
   * Get single template by ID
   */
  getTemplate(id: string): Promise<VoucherTemplate> {
    return request.get(`/system/objects/VoucherTemplate/${id}/`)
  },

  /**
   * Create new template
   */
  createTemplate(data: Partial<VoucherTemplate>): Promise<VoucherTemplate> {
    return request.post('/system/objects/VoucherTemplate/', data)
  },

  /**
   * Update template
   */
  updateTemplate(id: string, data: Partial<VoucherTemplate>): Promise<VoucherTemplate> {
    return request.put(`/system/objects/VoucherTemplate/${id}/`, data)
  },

  /**
   * Delete template
   */
  deleteTemplate(id: string): Promise<void> {
    return request.delete(`/system/objects/VoucherTemplate/${id}/`)
  },

  /**
   * Activate template
   */
  activateTemplate(id: string): Promise<void> {
    return request.patch(`/system/objects/VoucherTemplate/${id}/`, { isActive: true })
  },

  /**
   * Deactivate template
   */
  deactivateTemplate(id: string): Promise<void> {
    return request.patch(`/system/objects/VoucherTemplate/${id}/`, { isActive: false })
  },

  /**
   * Apply template and create a voucher draft
   */
  applyTemplate(id: string, data: VoucherTemplateApplyPayload): Promise<FinanceVoucher> {
    return request.post(`/system/objects/VoucherTemplate/${id}/apply/`, data)
  }
}

/**
 * Auto-generation API service
 */
export const voucherGenerationApi = {
  /**
   * Generate asset purchase voucher
   */
  generateAssetPurchaseVoucher(data: {
    businessId: string
    assetIds: string[]
  }): Promise<FinanceVoucher> {
    return request.post('/system/objects/FinanceVoucher/generate/asset-purchase/', data)
  },

  /**
   * Generate depreciation voucher
   */
  generateDepreciationVoucher(data: {
    period: string
    categoryIds?: string[]
  }): Promise<FinanceVoucher> {
    return request.post('/system/objects/FinanceVoucher/generate/depreciation/', data)
  },

  /**
   * Generate asset disposal voucher
   */
  generateDisposalVoucher(data: {
    businessId: string
    assetId: string
  }): Promise<FinanceVoucher> {
    return request.post('/system/objects/FinanceVoucher/generate/disposal/', data)
  }
}

/**
 * Integration Log API service
 */
export const integrationApi = {
  /**
   * Get integration logs for a voucher
   */
  getLogs(voucherId: string): Promise<any[]> {
    return request.get(`/system/objects/FinanceVoucher/${voucherId}/integration-logs/`)
  },

  /**
   * Retry failed integration
   */
  retry(voucherId: string): Promise<{
    success?: boolean
    queued?: boolean
    taskId?: string
    syncTaskId?: string
    externalVoucherNo?: string
  }> {
    return request.post(`/system/objects/FinanceVoucher/${voucherId}/retry/`)
  }
}
