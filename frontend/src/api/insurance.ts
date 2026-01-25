import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

/**
 * Insurance Management API Client
 * Handles insurance companies, policies, claims, and renewals
 */

// Insurance Companies
export const insuranceCompanyApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/insurance/companies/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/insurance/companies/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/insurance/companies/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/insurance/companies/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/insurance/companies/${id}/`)
  }
}

// Insurance Policies
export const insurancePolicyApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/insurance/policies/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/insurance/policies/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/insurance/policies/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/insurance/policies/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/insurance/policies/${id}/`)
  }
}

// Insured Assets
export const insuredAssetApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/insurance/insured-assets/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/insurance/insured-assets/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/insurance/insured-assets/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/insurance/insured-assets/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/insurance/insured-assets/${id}/`)
  }
}

// Premium Payments
export const premiumPaymentApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/insurance/payments/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/insurance/payments/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/insurance/payments/', data)
  },

  confirm(id: string, data: any): Promise<void> {
    return request.post(`/insurance/payments/${id}/confirm/`, data)
  }
}

// Claim Records
export const claimRecordApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/insurance/claims/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/insurance/claims/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/insurance/claims/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/insurance/claims/${id}/`, data)
  },

  submit(id: string): Promise<void> {
    return request.post(`/insurance/claims/${id}/submit/`)
  },

  approve(id: string, data: any): Promise<void> {
    return request.post(`/insurance/claims/${id}/approve/`, data)
  }
}

// Policy Renewals
export const policyRenewalApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/insurance/renewals/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/insurance/renewals/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/insurance/renewals/', data)
  },

  process(id: string, data: any): Promise<void> {
    return request.post(`/insurance/renewals/${id}/process/`, data)
  }
}

// Legacy function exports for backward compatibility
export const getInsuranceCompanyList = insuranceCompanyApi.list
export const getInsuranceCompanyDetail = insuranceCompanyApi.detail
export const createInsuranceCompany = insuranceCompanyApi.create
export const updateInsuranceCompany = insuranceCompanyApi.update
export const deleteInsuranceCompany = insuranceCompanyApi.delete

export const getInsurancePolicyList = insurancePolicyApi.list
export const getInsurancePolicyDetail = insurancePolicyApi.detail
export const createInsurancePolicy = insurancePolicyApi.create
export const updateInsurancePolicy = insurancePolicyApi.update
export const deleteInsurancePolicy = insurancePolicyApi.delete

export const getInsuredAssetList = insuredAssetApi.list
export const getInsuredAssetDetail = insuredAssetApi.detail
export const createInsuredAsset = insuredAssetApi.create
export const updateInsuredAsset = insuredAssetApi.update
export const deleteInsuredAsset = insuredAssetApi.delete

export const getPremiumPaymentList = premiumPaymentApi.list
export const getPremiumPaymentDetail = premiumPaymentApi.detail
export const createPremiumPayment = premiumPaymentApi.create
export const confirmPremiumPayment = premiumPaymentApi.confirm

export const getClaimRecordList = claimRecordApi.list
export const getClaimRecordDetail = claimRecordApi.detail
export const createClaimRecord = claimRecordApi.create
export const updateClaimRecord = claimRecordApi.update
export const submitClaimRecord = claimRecordApi.submit
export const approveClaimRecord = claimRecordApi.approve

export const getPolicyRenewalList = policyRenewalApi.list
export const getPolicyRenewalDetail = policyRenewalApi.detail
export const createPolicyRenewal = policyRenewalApi.create
export const processPolicyRenewal = policyRenewalApi.process
