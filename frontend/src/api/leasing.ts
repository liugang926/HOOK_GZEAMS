import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

/**
 * Leasing Management API Client
 * Handles lease contracts, items, payments, returns, and extensions
 */

// Lease Contracts
export const leaseContractApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/system/objects/LeasingContract/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/system/objects/LeasingContract/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/system/objects/LeasingContract/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/system/objects/LeasingContract/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/system/objects/LeasingContract/${id}/`)
  },

  activate(id: string): Promise<void> {
    return request.post(`/system/objects/LeasingContract/${id}/activate/`)
  },

  terminate(id: string, data: any): Promise<void> {
    return request.post(`/system/objects/LeasingContract/${id}/terminate/`, data)
  }
}

// Lease Items
export const leaseItemApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/system/objects/LeaseItem/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/system/objects/LeaseItem/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/system/objects/LeaseItem/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/system/objects/LeaseItem/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/system/objects/LeaseItem/${id}/`)
  }
}

// Rent Payments
export const rentPaymentApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/system/objects/RentPayment/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/system/objects/RentPayment/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/system/objects/RentPayment/', data)
  },

  confirm(id: string, data: any): Promise<void> {
    return request.post(`/system/objects/RentPayment/${id}/record_payment/`, data)
  }
}

// Lease Returns
export const leaseReturnApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/system/objects/LeaseReturn/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/system/objects/LeaseReturn/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/system/objects/LeaseReturn/', data)
  },

  confirm(id: string, data: any): Promise<void> {
    return request.patch(`/system/objects/LeaseReturn/${id}/`, data)
  }
}

// Lease Extensions
export const leaseExtensionApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/system/objects/LeaseExtension/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/system/objects/LeaseExtension/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/system/objects/LeaseExtension/', data)
  },

  approve(id: string): Promise<void> {
    return request.post(`/system/objects/LeaseExtension/${id}/approve/`)
  }
}

// Legacy function exports for backward compatibility
export const getLeaseContractList = leaseContractApi.list
export const getLeaseContractDetail = leaseContractApi.detail
export const createLeaseContract = leaseContractApi.create
export const updateLeaseContract = leaseContractApi.update
export const deleteLeaseContract = leaseContractApi.delete
export const activateLeaseContract = leaseContractApi.activate
export const terminateLeaseContract = leaseContractApi.terminate

export const getLeaseItemList = leaseItemApi.list
export const getLeaseItemDetail = leaseItemApi.detail
export const createLeaseItem = leaseItemApi.create
export const updateLeaseItem = leaseItemApi.update
export const deleteLeaseItem = leaseItemApi.delete

export const getRentPaymentList = rentPaymentApi.list
export const getRentPaymentDetail = rentPaymentApi.detail
export const createRentPayment = rentPaymentApi.create
export const confirmRentPayment = rentPaymentApi.confirm

export const getLeaseReturnList = leaseReturnApi.list
export const getLeaseReturnDetail = leaseReturnApi.detail
export const createLeaseReturn = leaseReturnApi.create
export const confirmLeaseReturn = leaseReturnApi.confirm

export const getLeaseExtensionList = leaseExtensionApi.list
export const getLeaseExtensionDetail = leaseExtensionApi.detail
export const createLeaseExtension = leaseExtensionApi.create
export const approveLeaseExtension = leaseExtensionApi.approve
