import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

export const returnApi = {
    list(params?: any): Promise<PaginatedResponse<any>> {
        return request.get('/assets/returns/', { params })
    },

    detail(id: string): Promise<any> {
        return request.get(`/assets/returns/${id}/`)
    },

    create(data: {
        assetId: string
        reason?: string
        returnDate: string
    }): Promise<any> {
        return request.post('/assets/returns/', data)
    },

    update(id: string, data: any): Promise<any> {
        return request.put(`/assets/returns/${id}/`, data)
    },

    submit(id: string): Promise<void> {
        return request.post(`/assets/returns/${id}/submit/`)
    },

    cancel(id: string): Promise<void> {
        return request.post(`/assets/returns/${id}/cancel/`)
    },

    approve(id: string): Promise<void> {
        return request.post(`/assets/returns/${id}/approve/`)
    },

    reject(id: string, reason: string): Promise<void> {
        return request.post(`/assets/returns/${id}/reject/`, { reason })
    },

    complete(id: string, data: any): Promise<void> {
        return request.post(`/assets/returns/${id}/complete/`, data)
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
