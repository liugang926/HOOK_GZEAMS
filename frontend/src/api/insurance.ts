import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

/**
 * Insurance Management API Client
 * Handles insurance companies, policies, claims, and renewals
 */

// Insurance Companies
export const insuranceCompanyApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/system/objects/InsuranceCompany/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/system/objects/InsuranceCompany/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/system/objects/InsuranceCompany/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/system/objects/InsuranceCompany/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/system/objects/InsuranceCompany/${id}/`)
  }
}

// Insurance Policies
export const insurancePolicyApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/system/objects/InsurancePolicy/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/system/objects/InsurancePolicy/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/system/objects/InsurancePolicy/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/system/objects/InsurancePolicy/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/system/objects/InsurancePolicy/${id}/`)
  }
}

// Insured Assets
export const insuredAssetApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/system/objects/InsuredAsset/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/system/objects/InsuredAsset/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/system/objects/InsuredAsset/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/system/objects/InsuredAsset/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/system/objects/InsuredAsset/${id}/`)
  }
}

// Premium Payments
export const premiumPaymentApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/system/objects/PremiumPayment/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/system/objects/PremiumPayment/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/system/objects/PremiumPayment/', data)
  },

  confirm(id: string, data: any): Promise<void> {
    return request.post(`/system/objects/PremiumPayment/${id}/record_payment/`, data)
  }
}

// Claim Records
export const claimRecordApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/system/objects/ClaimRecord/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/system/objects/ClaimRecord/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/system/objects/ClaimRecord/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/system/objects/ClaimRecord/${id}/`, data)
  },

  submit(id: string): Promise<void> {
    return request.patch(`/system/objects/ClaimRecord/${id}/`, { status: 'reported' })
  },

  approve(id: string, data: any): Promise<void> {
    return request.post(`/system/objects/ClaimRecord/${id}/approve/`, data)
  }
}

// Policy Renewals
export const policyRenewalApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/system/objects/PolicyRenewal/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/system/objects/PolicyRenewal/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/system/objects/PolicyRenewal/', data)
  },

  process(id: string, data: any): Promise<void> {
    return request.patch(`/system/objects/PolicyRenewal/${id}/`, data)
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
