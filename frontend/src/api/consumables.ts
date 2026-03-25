/**
 * Consumables API Service
 *
 * Now using unified Dynamic Object Routing for all consumable-related operations.
 * Reference: docs/reports/FRONTEND_OPTIMIZATION_ANALYSIS.md
 */

import request from '@/utils/request'
import { toData, toPaginated } from '@/api/contract'
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
    consumableId?: string | number
    consumable_id?: string | number
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
        return toPaginated<Consumable>(await consumableApi.list(params))
    }

    /**
     * Get single consumable (delegates to dynamic API)
     */
    async get(id: string | number, params?: any): Promise<Consumable> {
        return toData<Consumable>(await consumableApi.get(String(id), params))
    }

    /**
     * Create consumable (delegates to dynamic API)
     */
    async create(data: Partial<Consumable>): Promise<Consumable> {
        return toData<Consumable>(await consumableApi.create(data))
    }

    /**
     * Update consumable (delegates to dynamic API)
     */
    async update(id: string | number, data: Partial<Consumable>): Promise<Consumable> {
        return toData<Consumable>(await consumableApi.update(String(id), data))
    }

    /**
     * Delete consumable (delegates to dynamic API)
     */
    async delete(id: string | number): Promise<void> {
        await consumableApi.delete(String(id))
    }

    /**
     * Stock in operation (custom action endpoint)
     */
    stockIn(data: StockOperation): Promise<void> {
        const payload = {
            ...data,
            consumable_id: data.consumable_id ?? data.consumableId
        }
        return request.post(`/system/objects/Consumable/stock-in/`, payload)
    }

    /**
     * Stock out operation (custom action endpoint)
     */
    stockOut(data: StockOperation): Promise<void> {
        const payload = {
            ...data,
            consumable_id: data.consumable_id ?? data.consumableId
        }
        return request.post(`/system/objects/Consumable/stock-out/`, payload)
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
        return toPaginated<any>(await consumableCategoryApi.list(params)).results
    },

    async get(id: string): Promise<any> {
        return toData<any>(await consumableCategoryApi.get(id))
    },

    async create(data: any): Promise<any> {
        return toData<any>(await consumableCategoryApi.create(data))
    },

    async update(id: string, data: any): Promise<any> {
        return toData<any>(await consumableCategoryApi.update(id, data))
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
        return toPaginated<any>(await consumableStockApi.list(params))
    },

    async get(id: string): Promise<any> {
        return toData<any>(await consumableStockApi.get(id))
    }
}

/**
 * Consumable Purchase API (delegates to dynamic API)
 */
export const consumablePurchaseApiService = {
    async list(params?: any): Promise<PaginatedResponse<any>> {
        return toPaginated<any>(await consumablePurchaseApi.list(params))
    },

    async get(id: string): Promise<any> {
        return toData<any>(await consumablePurchaseApi.get(id))
    },

    async create(data: any): Promise<any> {
        return toData<any>(await consumablePurchaseApi.create(data))
    }
}

/**
 * Consumable Issue API (delegates to dynamic API)
 */
export const consumableIssueApiService = {
    async list(params?: any): Promise<PaginatedResponse<any>> {
        return toPaginated<any>(await consumableIssueApi.list(params))
    },

    async get(id: string): Promise<any> {
        return toData<any>(await consumableIssueApi.get(id))
    },

    async create(data: any): Promise<any> {
        return toData<any>(await consumableIssueApi.create(data))
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
