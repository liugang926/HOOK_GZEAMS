/**
 * Software Licenses API Service
 *
 * API methods for software catalog, licenses, and allocations.
 */

import request from '@/utils/request'
import type { PaginatedResponse, BatchResponse } from '@/types/api'
import type { Software, SoftwareLicense, LicenseAllocation, ComplianceReport } from '@/types/softwareLicenses'

/**
 * Software Catalog API
 */
export const softwareApi = {
  /**
   * List software catalog with pagination and filters
   */
  list(params?: {
    page?: number
    pageSize?: number
    softwareType?: string
    vendor?: string
    isActive?: boolean
    search?: string
  }): Promise<PaginatedResponse<Software>> {
    return request.get('/system/objects/Software/', { params })
  },

  /**
   * Get single software by ID
   */
  get(id: string): Promise<Software> {
    return request.get(`/system/objects/Software/${id}/`)
  },

  /**
   * Create new software entry
   */
  create(data: Partial<Software>): Promise<Software> {
    return request.post('/system/objects/Software/', data)
  },

  /**
   * Update software
   */
  update(id: string, data: Partial<Software>): Promise<Software> {
    return request.put(`/system/objects/Software/${id}/`, data)
  },

  /**
   * Delete software (soft delete)
   */
  delete(id: string): Promise<void> {
    return request.delete(`/system/objects/Software/${id}/`)
  },

  /**
   * Batch delete software
   */
  batchDelete(ids: string[]): Promise<BatchResponse> {
    return request.post('/system/objects/Software/batch-delete/', { ids })
  }
}

/**
 * Software Licenses API
 */
export const softwareLicenseApi = {
  /**
   * List software licenses with pagination and filters
   */
  list(params?: {
    page?: number
    pageSize?: number
    software?: string
    status?: string
    expiringSoon?: boolean
    search?: string
  }): Promise<PaginatedResponse<SoftwareLicense>> {
    return request.get('/system/objects/SoftwareLicense/', { params })
  },

  /**
   * Get single license by ID
   */
  get(id: string): Promise<SoftwareLicense> {
    return request.get(`/system/objects/SoftwareLicense/${id}/`)
  },

  /**
   * Create new license
   */
  create(data: Partial<SoftwareLicense>): Promise<SoftwareLicense> {
    return request.post('/system/objects/SoftwareLicense/', data)
  },

  /**
   * Update license
   */
  update(id: string, data: Partial<SoftwareLicense>): Promise<SoftwareLicense> {
    return request.put(`/system/objects/SoftwareLicense/${id}/`, data)
  },

  /**
   * Delete license (soft delete)
   */
  delete(id: string): Promise<void> {
    return request.delete(`/system/objects/SoftwareLicense/${id}/`)
  },

  /**
   * Get licenses expiring within 30 days
   */
  expiring(params?: {
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<SoftwareLicense>> {
    return request.get('/system/objects/SoftwareLicense/expiring/', { params })
  },

  /**
   * Get compliance report
   */
  complianceReport(): Promise<{ data: ComplianceReport }> {
    return request.get('/system/objects/SoftwareLicense/compliance_report/')
  },

  /**
   * Batch delete licenses
   */
  batchDelete(ids: string[]): Promise<BatchResponse> {
    return request.post('/system/objects/SoftwareLicense/batch-delete/', { ids })
  }
}

/**
 * License Allocations API
 */
export const licenseAllocationApi = {
  /**
   * List allocations with pagination and filters
   */
  list(params?: {
    page?: number
    pageSize?: number
    license?: string
    asset?: string
    isActive?: boolean
    search?: string
  }): Promise<PaginatedResponse<LicenseAllocation>> {
    return request.get('/system/objects/LicenseAllocation/', { params })
  },

  /**
   * Get single allocation by ID
   */
  get(id: string): Promise<LicenseAllocation> {
    return request.get(`/system/objects/LicenseAllocation/${id}/`)
  },

  /**
   * Create allocation (assign license to asset)
   */
  create(data: {
    license: string
    asset: string
    allocationKey?: string
    notes?: string
  }): Promise<LicenseAllocation> {
    return request.post('/system/objects/LicenseAllocation/', data)
  },

  /**
   * Update allocation
   */
  update(id: string, data: Partial<LicenseAllocation>): Promise<LicenseAllocation> {
    return request.put(`/system/objects/LicenseAllocation/${id}/`, data)
  },

  /**
   * Delete allocation
   */
  delete(id: string): Promise<void> {
    return request.delete(`/system/objects/LicenseAllocation/${id}/`)
  },

  /**
   * Deallocate license from asset
   */
  deallocate(id: string, data?: { notes?: string }): Promise<{ data: LicenseAllocation }> {
    return request.post(`/system/objects/LicenseAllocation/${id}/deallocate/`, data)
  },

  /**
   * Batch delete allocations
   */
  batchDelete(ids: string[]): Promise<BatchResponse> {
    return request.post('/system/objects/LicenseAllocation/batch-delete/', { ids })
  }
}

// Re-export types
export type { Software, SoftwareLicense, LicenseAllocation, ComplianceReport }
