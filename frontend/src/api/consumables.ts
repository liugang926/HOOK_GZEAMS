/**
 * Consumables API Service
 *
 * API methods for consumable management using BaseApiService.
 * Reference: docs/reports/FRONTEND_OPTIMIZATION_ANALYSIS.md
 */

import request from '@/utils/request'
import { BaseApiService } from '@/api/base'
import type { PaginatedResponse } from '@/types/api'

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
 * Consumable API service using BaseApiService
 */
class ConsumableApiService extends BaseApiService<Consumable> {
    constructor() {
        super('consumables/consumables')
    }

    /**
     * Stock in operation
     */
    stockIn(data: StockOperation): Promise<void> {
        return request.post(`/${this.resource}/stock_in/`, data)
    }

    /**
     * Stock out operation
     */
    stockOut(data: StockOperation): Promise<void> {
        return request.post(`/${this.resource}/stock_out/`, data)
    }

    /**
     * Get stock history for a consumable
     */
    getStockHistory(consumableId: string, params?: any): Promise<PaginatedResponse<any>> {
        return request.get(`/${this.resource}/${consumableId}/history/`, { params })
    }
}

export const consumableApi = new ConsumableApiService()

// Legacy function exports for backward compatibility
export const getConsumables = consumableApi.list.bind(consumableApi)
export const getConsumable = consumableApi.get.bind(consumableApi)
export const createConsumable = consumableApi.create.bind(consumableApi)
export const updateConsumable = consumableApi.update.bind(consumableApi)
export const deleteConsumable = consumableApi.delete.bind(consumableApi)
export const stockIn = consumableApi.stockIn.bind(consumableApi)
export const stockOut = consumableApi.stockOut.bind(consumableApi)
export const getStockHistory = consumableApi.getStockHistory.bind(consumableApi)

