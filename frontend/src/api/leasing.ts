import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

/**
 * Leasing Management API Client
 * Handles lease contracts, items, payments, returns, and extensions
 */

// Lease Contracts
export const leaseContractApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/leasing/lease-contracts/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/leasing/lease-contracts/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/leasing/lease-contracts/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/leasing/lease-contracts/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/leasing/lease-contracts/${id}/`)
  },

  activate(id: string): Promise<void> {
    return request.post(`/leasing/lease-contracts/${id}/activate/`)
  },

  terminate(id: string, data: any): Promise<void> {
    return request.post(`/leasing/lease-contracts/${id}/terminate/`, data)
  }
}

// Lease Items
export const leaseItemApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/leasing/lease-items/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/leasing/lease-items/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/leasing/lease-items/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/leasing/lease-items/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/leasing/lease-items/${id}/`)
  }
}

// Rent Payments
export const rentPaymentApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/leasing/rent-payments/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/leasing/rent-payments/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/leasing/rent-payments/', data)
  },

  confirm(id: string, data: any): Promise<void> {
    return request.post(`/leasing/rent-payments/${id}/confirm/`, data)
  }
}

// Lease Returns
export const leaseReturnApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/leasing/lease-returns/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/leasing/lease-returns/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/leasing/lease-returns/', data)
  },

  confirm(id: string, data: any): Promise<void> {
    return request.post(`/leasing/lease-returns/${id}/confirm/`, data)
  }
}

// Lease Extensions
export const leaseExtensionApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/leasing/lease-extensions/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/leasing/lease-extensions/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/leasing/lease-extensions/', data)
  },

  approve(id: string): Promise<void> {
    return request.post(`/leasing/lease-extensions/${id}/approve/`)
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
