/**
 * Base API Service
 * 
 * Generic class for standard REST API operations.
 * Reference: docs/reports/FRONTEND_OPTIMIZATION_ANALYSIS.md
 */

import request from '@/utils/request'
import type { PaginatedResponse, BatchResponse } from '@/types/api'

export class BaseApiService<T> {
    protected resource: string

    constructor(resource: string) {
        this.resource = resource
    }

    /**
     * List resources with pagination and filters
     */
    list(params?: any): Promise<PaginatedResponse<T>> {
        return request.get(`/${this.resource}/`, { params })
    }

    /**
     * Get single resource by ID
     */
    get(id: string): Promise<T> {
        return request.get(`/${this.resource}/${id}/`)
    }

    /**
     * Create new resource
     */
    create(data: Partial<T>): Promise<T> {
        return request.post(`/${this.resource}/`, data)
    }

    /**
     * Update resource
     */
    update(id: string, data: Partial<T>): Promise<T> {
        return request.put(`/${this.resource}/${id}/`, data)
    }

    /**
     * Delete resource (soft delete)
     */
    delete(id: string): Promise<void> {
        return request.delete(`/${this.resource}/${id}/`)
    }

    /**
     * Batch delete resources
     */
    batchDelete(ids: string[]): Promise<BatchResponse> {
        return request.post(`/${this.resource}/batch-delete/`, { ids })
    }

    /**
     * Export resources to Excel
     */
    export(params?: any): Promise<Blob> {
        return request.get(`/${this.resource}/export/`, {
            params,
            responseType: 'blob'
        })
    }
}
