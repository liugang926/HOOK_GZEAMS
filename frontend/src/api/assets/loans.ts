/**
 * Asset Loan API Service
 *
 * Now using unified Dynamic Object Routing via /api/objects/AssetLoan/
 * Custom actions (submit, cancel, approve, reject, return) use dedicated endpoints
 */

import request from '@/utils/request'
import { assetLoanApi } from '@/api/dynamic'

/**
 * List loans (delegates to dynamic API)
 */
export const getLoanList = (params: any) => {
    return assetLoanApi.list(params)
}

/**
 * Get loan detail (delegates to dynamic API)
 */
export const getLoanDetail = (id: string) => {
    return assetLoanApi.get(id)
}

/**
 * Create loan (delegates to dynamic API)
 */
export const createLoan = (data: any) => {
    return assetLoanApi.create(data)
}

/**
 * Update loan (delegates to dynamic API)
 */
export const updateLoan = (id: string, data: any) => {
    return assetLoanApi.update(id, data)
}

/**
 * Submit loan for approval (custom action endpoint)
 */
export const submitLoan = (id: string) => {
    return request({
        url: `/system/objects/AssetLoan/${id}/submit/`,
        method: 'post'
    })
}

/**
 * Cancel loan (custom action endpoint)
 */
export const cancelLoan = (id: string) => {
    return request({
        url: `/system/objects/AssetLoan/${id}/cancel/`,
        method: 'post'
    })
}

/**
 * Approve loan (custom action endpoint)
 */
export const approveLoan = (id: string) => {
    return request({
        url: `/system/objects/AssetLoan/${id}/approve/`,
        method: 'post'
    })
}

/**
 * Reject loan (custom action endpoint)
 */
export const rejectLoan = (id: string, reason: string) => {
    return request({
        url: `/system/objects/AssetLoan/${id}/reject/`,
        method: 'post',
        data: { reason }
    })
}

/**
 * Return loaned asset (custom action endpoint)
 */
export const returnLoan = (id: string, data: any) => {
    return request({
        url: `/system/objects/AssetLoan/${id}/return/`,
        method: 'post',
        data
    })
}
