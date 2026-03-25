/**
 * Asset Return API Service
 *
 * Now using unified Dynamic Object Routing via /api/objects/AssetReturn/
 * Custom actions (submit, cancel, approve, reject, complete) use dedicated endpoints
 */

import request from '@/utils/request'
import { assetReturnApi } from '@/api/dynamic'
import type { PaginatedResponse } from '@/types/api'

export const returnApi = {
    /**
     * List returns (delegates to dynamic API)
     */
    async list(params?: any): Promise<PaginatedResponse<any>> {
        const res = await assetReturnApi.list(params)
        return {
            items: res.data?.results || [],
            total: res.data?.count || 0,
            ...params
        }
    },

    /**
     * Get return detail (delegates to dynamic API)
     */
    async detail(id: string): Promise<any> {
        const res = await assetReturnApi.get(id)
        return res.data
    },

    /**
     * Create return (delegates to dynamic API)
     */
    async create(data: {
        assetId: string
        reason?: string
        returnDate: string
    }): Promise<any> {
        const res = await assetReturnApi.create(data)
        return res.data
    },

    /**
     * Update return (delegates to dynamic API)
     */
    async update(id: string, data: any): Promise<any> {
        const res = await assetReturnApi.update(id, data)
        return res.data
    },

    /**
     * Submit return for approval (custom action endpoint)
     */
    submit(id: string): Promise<void> {
        return request.post(`/system/objects/AssetReturn/${id}/submit/`)
    },

    /**
     * Cancel return (custom action endpoint)
     */
    cancel(id: string): Promise<void> {
        return request.post(`/system/objects/AssetReturn/${id}/cancel/`)
    },

    /**
     * Approve return (custom action endpoint)
     */
    approve(id: string): Promise<void> {
        return request.post(`/system/objects/AssetReturn/${id}/approve/`)
    },

    /**
     * Reject return (custom action endpoint)
     */
    reject(id: string, reason: string): Promise<void> {
        return request.post(`/system/objects/AssetReturn/${id}/reject/`, { reason })
    },

    /**
     * Complete return (custom action endpoint)
     */
    complete(id: string, data: any): Promise<void> {
        return request.post(`/system/objects/AssetReturn/${id}/complete/`, data)
    }
}

// Legacy function exports for backward compatibility
export const getReturnList = returnApi.list
export const getReturnDetail = returnApi.detail
export const createReturn = returnApi.create
export const updateReturn = returnApi.update
export const submitReturn = returnApi.submit
export const cancelReturn = returnApi.cancel
export const approveReturn = returnApi.approve
export const completeReturn = returnApi.complete
