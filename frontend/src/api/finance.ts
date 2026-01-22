/**
 * Finance API Service
 *
 * API methods for financial voucher management and ERP integration.
 * Reference: docs/plans/phase5_2_finance_integration/frontend_v2.md
 */

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { FinanceVoucher, VoucherTemplate, VoucherCreate, VoucherApprovalAction } from '@/types/finance'

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
    return request.get('/finance/vouchers/', { params })
  },

  /**
   * Get single voucher by ID
   */
  getVoucher(id: string): Promise<FinanceVoucher> {
    return request.get(`/finance/vouchers/${id}/`)
  },

  /**
   * Create new voucher
   */
  createVoucher(data: VoucherCreate): Promise<FinanceVoucher> {
    return request.post('/finance/vouchers/', data)
  },

  /**
   * Update voucher
   */
  updateVoucher(id: string, data: Partial<FinanceVoucher>): Promise<FinanceVoucher> {
    return request.put(`/finance/vouchers/${id}/`, data)
  },

  /**
   * Delete voucher
   */
  deleteVoucher(id: string): Promise<void> {
    return request.delete(`/finance/vouchers/${id}/`)
  },

  /**
   * Submit voucher for approval
   */
  submitVoucher(id: string): Promise<void> {
    return request.post(`/finance/vouchers/${id}/submit/`)
  },

  /**
   * Approve or reject voucher
   */
  approveVoucher(id: string, data: VoucherApprovalAction): Promise<void> {
    return request.post(`/finance/vouchers/${id}/approve/`, data)
  },

  /**
   * Post voucher to accounting
   */
  postVoucher(id: string): Promise<void> {
    return request.post(`/finance/vouchers/${id}/post/`)
  },

  /**
   * Push voucher to external ERP system
   */
  pushVoucher(id: string, system?: string): Promise<{
    success: boolean
    externalVoucherNo?: string
    error?: string
  }> {
    return request.post(`/finance/vouchers/${id}/push/`, { system })
  },

  /**
   * Batch push vouchers to ERP
   */
  batchPushVouchers(ids: string[]): Promise<{
    success: number
    failed: number
    results: Array<{ id: string; success: boolean; error?: string }>
  }> {
    return request.post('/finance/vouchers/batch-push/', { ids })
  },

  /**
   * Get voucher entries for editing
   */
  getEntries(id: string): Promise<FinanceVoucher> {
    return request.get(`/finance/vouchers/${id}/entries/`)
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
    return request.put(`/finance/vouchers/${id}/entries/`, { entries })
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
  }): Promise<VoucherTemplate[]> {
    return request.get('/finance/voucher-templates/', { params })
  },

  /**
   * Get single template by ID
   */
  getTemplate(id: string): Promise<VoucherTemplate> {
    return request.get(`/finance/voucher-templates/${id}/`)
  },

  /**
   * Create new template
   */
  createTemplate(data: Partial<VoucherTemplate>): Promise<VoucherTemplate> {
    return request.post('/finance/voucher-templates/', data)
  },

  /**
   * Update template
   */
  updateTemplate(id: string, data: Partial<VoucherTemplate>): Promise<VoucherTemplate> {
    return request.put(`/finance/voucher-templates/${id}/`, data)
  },

  /**
   * Delete template
   */
  deleteTemplate(id: string): Promise<void> {
    return request.delete(`/finance/voucher-templates/${id}/`)
  },

  /**
   * Activate template
   */
  activateTemplate(id: string): Promise<void> {
    return request.post(`/finance/voucher-templates/${id}/activate/`)
  },

  /**
   * Deactivate template
   */
  deactivateTemplate(id: string): Promise<void> {
    return request.post(`/finance/voucher-templates/${id}/deactivate/`)
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
    return request.post('/finance/vouchers/generate/asset-purchase/', data)
  },

  /**
   * Generate depreciation voucher
   */
  generateDepreciationVoucher(data: {
    period: string
    categoryIds?: string[]
  }): Promise<FinanceVoucher> {
    return request.post('/finance/vouchers/generate/depreciation/', data)
  },

  /**
   * Generate asset disposal voucher
   */
  generateDisposalVoucher(data: {
    businessId: string
    assetId: string
  }): Promise<FinanceVoucher> {
    return request.post('/finance/vouchers/generate/disposal/', data)
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
    return request.get(`/finance/vouchers/${voucherId}/integration-logs/`)
  },

  /**
   * Retry failed integration
   */
  retry(voucherId: string): Promise<void> {
    return request.post(`/finance/vouchers/${voucherId}/retry/`)
  }
}
