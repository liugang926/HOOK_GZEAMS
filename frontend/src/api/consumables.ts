/**
 * Consumables API Service
 *
 * Now using unified Dynamic Object Routing for all consumable-related operations.
 * Reference: docs/reports/FRONTEND_OPTIMIZATION_ANALYSIS.md
 */

import request from '@/utils/request'
import { BaseApiService } from '@/api/base'
import type { PaginatedResponse } from '@/types/api'
import {
  consumableApi,
  consumableCategoryApi,
  consumableStockApi,
  consumablePurchaseApi,
  consumableIssueApi
} from '@/api/dynamic'

export interface Consumable {
    id?: string
    name: string
    code: string
    category: string
    unit: string
    spec?: string
    stockQuantity?: number
    warningQuantity?: number
    description?: string
}

export interface StockOperation {
    consumableId: string
    quantity: number
    type: 'in' | 'out'
    remark?: string
}

/**
 * Consumable API service using Dynamic Object Routing
 */
class ConsumableApiService extends BaseApiService<Consumable> {
    constructor() {
        super('consumables/consumables')
    }

    /**
     * List consumables (delegates to dynamic API)
     */
    async list(params?: any): Promise<PaginatedResponse<Consumable>> {
        const res = await consumableApi.list(params)
        return {
            items: res.data?.results || [],
            total: res.data?.count || 0,
            ...params
        }
    }

    /**
     * Get single consumable (delegates to dynamic API)
     */
    async get(id: string, params?: any): Promise<Consumable> {
        const res = await consumableApi.get(id, params)
        return res.data as Consumable
    }

    /**
     * Create consumable (delegates to dynamic API)
     */
    async create(data: Partial<Consumable>): Promise<Consumable> {
        const res = await consumableApi.create(data)
        return res.data as Consumable
    }

    /**
     * Update consumable (delegates to dynamic API)
     */
    async update(id: string, data: Partial<Consumable>): Promise<Consumable> {
        const res = await consumableApi.update(id, data)
        return res.data as Consumable
    }

    /**
     * Delete consumable (delegates to dynamic API)
     */
    async delete(id: string): Promise<void> {
        await consumableApi.delete(id)
    }

    /**
     * Stock in operation (custom action endpoint)
     */
    stockIn(data: StockOperation): Promise<void> {
        return request.post(`/system/objects/Consumable/stock-in/`, data)
    }

    /**
     * Stock out operation (custom action endpoint)
     */
    stockOut(data: StockOperation): Promise<void> {
        return request.post(`/system/objects/Consumable/stock-out/`, data)
    }

    /**
     * Get stock history for a consumable (custom action endpoint)
     */
    getStockHistory(consumableId: string, params?: any): Promise<PaginatedResponse<any>> {
        return request.get(`/system/objects/Consumable/${consumableId}/history/`, { params })
    }
}

export const consumableApiService = new ConsumableApiService()

/**
 * Consumable Category API (delegates to dynamic API)
 */
export const consumableCategoryApiService = {
    async list(params?: any): Promise<any[]> {
        const res = await consumableCategoryApi.list(params)
        return res.data?.results || []
    },

    async get(id: string): Promise<any> {
        const res = await consumableCategoryApi.get(id)
        return res.data
    },

    async create(data: any): Promise<any> {
        const res = await consumableCategoryApi.create(data)
        return res.data
    },

    async update(id: string, data: any): Promise<any> {
        const res = await consumableCategoryApi.update(id, data)
        return res.data
    },

    async delete(id: string): Promise<void> {
        await consumableCategoryApi.delete(id)
    }
}

/**
 * Consumable Stock API (delegates to dynamic API)
 */
export const consumableStockApiService = {
    async list(params?: any): Promise<PaginatedResponse<any>> {
        const res = await consumableStockApi.list(params)
        return {
            items: res.data?.results || [],
            total: res.data?.count || 0
        }
    },

    async get(id: string): Promise<any> {
        const res = await consumableStockApi.get(id)
        return res.data
    }
}

/**
 * Consumable Purchase API (delegates to dynamic API)
 */
export const consumablePurchaseApiService = {
    async list(params?: any): Promise<PaginatedResponse<any>> {
        const res = await consumablePurchaseApi.list(params)
        return {
            items: res.data?.results || [],
            total: res.data?.count || 0
        }
    },

    async get(id: string): Promise<any> {
        const res = await consumablePurchaseApi.get(id)
        return res.data
    },

    async create(data: any): Promise<any> {
        const res = await consumablePurchaseApi.create(data)
        return res.data
    }
}

/**
 * Consumable Issue API (delegates to dynamic API)
 */
export const consumableIssueApiService = {
    async list(params?: any): Promise<PaginatedResponse<any>> {
        const res = await consumableIssueApi.list(params)
        return {
            items: res.data?.results || [],
            total: res.data?.count || 0
        }
    },

    async get(id: string): Promise<any> {
        const res = await consumableIssueApi.get(id)
        return res.data
    },

    async create(data: any): Promise<any> {
        const res = await consumableIssueApi.create(data)
        return res.data
    }
}

// Legacy function exports for backward compatibility
export const getConsumables = consumableApiService.list.bind(consumableApiService)
export const getConsumable = consumableApiService.get.bind(consumableApiService)
export const createConsumable = consumableApiService.create.bind(consumableApiService)
export const updateConsumable = consumableApiService.update.bind(consumableApiService)
export const deleteConsumable = consumableApiService.delete.bind(consumableApiService)
export const stockIn = consumableApiService.stockIn.bind(consumableApiService)
export const stockOut = consumableApiService.stockOut.bind(consumableApiService)
export const getStockHistory = consumableApiService.getStockHistory.bind(consumableApiService)
