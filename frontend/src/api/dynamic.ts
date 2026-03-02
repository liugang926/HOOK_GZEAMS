/**
 * Dynamic Object API Client
 *
 * Unified API client for all business objects accessed via /api/objects/{code}/
 *
 * Usage:
 *   import { createObjectClient, dynamicApi } from '@/api/dynamic'
 *
 *   // Create client for specific object
 *   const assetApi = createObjectClient('Asset')
 *   const list = await assetApi.list({ page: 1, page_size: 20 })
 *
 *   // Or use dynamicApi directly
 *   const data = await dynamicApi.list('Asset', { page: 1 })
 */

import request from '@/utils/request'
import type { ObjectMetadata } from '@/types'
import { checkRuntimeContract, type RuntimeMode } from '@/contracts/runtimeContract'

/**
 * Paginated list response
 */
export interface ListResponse<T = any> {
    success: boolean
    data: {
        count: number
        next: string | null
        previous: string | null
        results: T[]
    }
}

/**
 * Standard API response
 */
export interface ApiResponse<T = any> {
    success: boolean
    message?: string
    data?: T
    error?: {
        code: string
        message: string
        details?: any
    }
}

/**
 * Batch operation result
 */
export interface BatchOperationResult {
    id: string
    success: boolean
    error?: string
}

/**
 * Batch operation summary
 */
export interface BatchOperationSummary {
    total: number
    succeeded: number
    failed: number
}

/**
 * Dynamic API class - handles all CRUD operations for business objects
 *
 * Note: Uses '/system/objects' path because request baseURL already includes '/api'
 * Final URL will be: /api/system/objects/{code}/
 */
class DynamicAPI {
    private baseUrl = '/system/objects'

    /**
     * List objects with pagination, filtering, and search
     * GET /api/system/objects/{code}/
     */
    list<T = any>(code: string, params?: Record<string, any>): Promise<ListResponse<T>> {
        return request({
            url: `${this.baseUrl}/${code}/`,
            method: 'get',
            params
        })
    }

    /**
     * Get single object by ID
     * GET /api/system/objects/{code}/{id}/
     */
    get<T = any>(code: string, id: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
        return request({
            url: `${this.baseUrl}/${code}/${id}/`,
            method: 'get',
            params
        })
    }

    /**
     * Create new object
     * POST /api/system/objects/{code}/
     */
    create<T = any>(code: string, data: Record<string, any>): Promise<ApiResponse<T>> {
        return request({
            url: `${this.baseUrl}/${code}/`,
            method: 'post',
            data
        })
    }

    /**
     * Full update of an object
     * PUT /api/system/objects/{code}/{id}/
     */
    update<T = any>(code: string, id: string, data: Record<string, any>): Promise<ApiResponse<T>> {
        return request({
            url: `${this.baseUrl}/${code}/${id}/`,
            method: 'put',
            data
        })
    }

    /**
     * Partial update of an object
     * PATCH /api/system/objects/{code}/{id}/
     */
    partialUpdate<T = any>(code: string, id: string, data: Record<string, any>): Promise<ApiResponse<T>> {
        return request({
            url: `${this.baseUrl}/${code}/${id}/`,
            method: 'patch',
            data
        })
    }

    /**
     * Delete (soft delete) an object
     * DELETE /api/system/objects/{code}/{id}/
     */
    delete(code: string, id: string): Promise<ApiResponse<void>> {
        return request({
            url: `${this.baseUrl}/${code}/${id}/`,
            method: 'delete'
        })
    }

    /**
     * Batch delete objects
     * POST /api/system/objects/{code}/batch-delete/
     */
    batchDelete(
        code: string,
        ids: string[]
    ): Promise<ApiResponse<{
        summary: BatchOperationSummary
        results: BatchOperationResult[]
    }>> {
        return request({
            url: `${this.baseUrl}/${code}/batch-delete/`,
            method: 'post',
            data: { ids }
        })
    }

    /**
     * Batch restore soft-deleted objects
     * POST /api/system/objects/{code}/batch-restore/
     */
    batchRestore(
        code: string,
        ids: string[]
    ): Promise<ApiResponse<{
        summary: BatchOperationSummary
        results: BatchOperationResult[]
    }>> {
        return request({
            url: `${this.baseUrl}/${code}/batch-restore/`,
            method: 'post',
            data: { ids }
        })
    }

    /**
     * Batch update objects
     * POST /api/system/objects/{code}/batch-update/
     */
    batchUpdate(
        code: string,
        data: Record<string, any>
    ): Promise<ApiResponse<{
        summary: BatchOperationSummary
        results: BatchOperationResult[]
    }>> {
        return request({
            url: `${this.baseUrl}/${code}/batch-update/`,
            method: 'post',
            data
        })
    }

    /**
     * List deleted objects
     * GET /api/system/objects/{code}/deleted/
     */
    listDeleted<T = any>(code: string, params?: Record<string, any>): Promise<ListResponse<T>> {
        return request({
            url: `${this.baseUrl}/${code}/deleted/`,
            method: 'get',
            params
        })
    }

    /**
     * Restore a deleted object
     * POST /api/system/objects/{code}/{id}/restore/
     */
    restore(code: string, id: string): Promise<ApiResponse<void>> {
        return request({
            url: `${this.baseUrl}/${code}/${id}/restore/`,
            method: 'post'
        })
    }

    /**
     * Get object metadata for dynamic rendering
     * GET /api/system/objects/{code}/metadata/
     */
    getMetadata(code: string): Promise<ApiResponse<ObjectMetadata>> {
        return request({
            url: `${this.baseUrl}/${code}/metadata/`,
            method: 'get'
        })
    }

    /**
     * Get JSON Schema for form validation
     * GET /api/system/objects/{code}/schema/
     */
    getSchema(code: string): Promise<ApiResponse<any>> {
        return request({
            url: `${this.baseUrl}/${code}/schema/`,
            method: 'get'
        })
    }

    /**
     * Get runtime metadata (fields + active layout) for frontend rendering.
     * GET /api/system/objects/{code}/runtime/?mode=...
     */
    async getRuntime(code: string, mode: RuntimeMode = 'edit', params?: Record<string, any>): Promise<any> {
        const payload = await request({
            url: `${this.baseUrl}/${code}/runtime/`,
            method: 'get',
            params: {
                mode,
                include_relations: true,
                ...(params || {})
            },
            silent: true
        } as any)

        const check = checkRuntimeContract(payload)
        if (!check.ok) {
            const err = new Error(`[dynamicApi.getRuntime] Invalid runtime contract for ${code}(${mode}): ${check.errors.join('; ')}`)
            ;(err as any).details = check.errors
            throw err
        }

        return payload
    }
}

/**
 * Global dynamic API instance
 */
export const dynamicApi = new DynamicAPI()

/**
 * Object client interface - type-safe client for a specific business object
 */
export interface ObjectClient {
    list<T = any>(params?: Record<string, any>): Promise<ListResponse<T>>
    get<T = any>(id: string, params?: Record<string, any>): Promise<ApiResponse<T>>
    create<T = any>(data: Record<string, any>): Promise<ApiResponse<T>>
    update<T = any>(id: string, data: Record<string, any>): Promise<ApiResponse<T>>
    partialUpdate<T = any>(id: string, data: Record<string, any>): Promise<ApiResponse<T>>
    delete(id: string): Promise<ApiResponse<void>>
    batchDelete(ids: string[]): Promise<ApiResponse<any>>
    batchRestore(ids: string[]): Promise<ApiResponse<any>>
    batchUpdate(data: Record<string, any>): Promise<ApiResponse<any>>
    listDeleted<T = any>(params?: Record<string, any>): Promise<ListResponse<T>>
    restore(id: string): Promise<ApiResponse<void>>
    getMetadata(): Promise<ApiResponse<ObjectMetadata>>
    getSchema(): Promise<ApiResponse<any>>
    getRuntime(mode?: 'edit' | 'readonly' | 'list' | 'search', params?: Record<string, any>): Promise<any>
}

/**
 * Create a typed API client for a specific business object
 *
 * @param code - Business object code (e.g., 'Asset', 'AssetPickup')
 * @returns Object client with all CRUD methods
 *
 * @example
 * const assetApi = createObjectClient('Asset')
 * const assets = await assetApi.list({ page: 1, page_size: 20 })
 * const asset = await assetApi.get('uuid')
 * const created = await assetApi.create({ name: 'New Asset' })
 */
export function createObjectClient(code: string): ObjectClient {
    return {
        list: (params?: Record<string, any>) => dynamicApi.list(code, params),
        get: (id: string, params?: Record<string, any>) => dynamicApi.get(code, id, params),
        create: (data: Record<string, any>) => dynamicApi.create(code, data),
        update: (id: string, data: Record<string, any>) => dynamicApi.update(code, id, data),
        partialUpdate: (id: string, data: Record<string, any>) => dynamicApi.partialUpdate(code, id, data),
        delete: (id: string) => dynamicApi.delete(code, id),
        batchDelete: (ids: string[]) => dynamicApi.batchDelete(code, ids),
        batchRestore: (ids: string[]) => dynamicApi.batchRestore(code, ids),
        batchUpdate: (data: Record<string, any>) => dynamicApi.batchUpdate(code, data),
        listDeleted: (params?: Record<string, any>) => dynamicApi.listDeleted(code, params),
        restore: (id: string) => dynamicApi.restore(code, id),
        getMetadata: () => dynamicApi.getMetadata(code),
        getSchema: () => dynamicApi.getSchema(code),
        getRuntime: (mode: 'edit' | 'readonly' | 'list' | 'search' = 'edit', params?: Record<string, any>) =>
            dynamicApi.getRuntime(code, mode, params)
    }
}

// ============================================
// Predefined API clients for standard objects
// These provide backward compatibility with existing code
// ============================================

/**
 * Asset module API clients
 */
export const assetApi = createObjectClient('Asset')
export const assetCategoryApi = createObjectClient('AssetCategory')
export const assetPickupApi = createObjectClient('AssetPickup')
export const assetTransferApi = createObjectClient('AssetTransfer')
export const assetReturnApi = createObjectClient('AssetReturn')
export const assetLoanApi = createObjectClient('AssetLoan')
export const supplierApi = createObjectClient('Supplier')
export const locationApi = createObjectClient('Location')

/**
 * Consumables module API clients
 */
export const consumableApi = createObjectClient('Consumable')
export const consumableCategoryApi = createObjectClient('ConsumableCategory')
export const consumableStockApi = createObjectClient('ConsumableStock')
export const consumablePurchaseApi = createObjectClient('ConsumablePurchase')
export const consumableIssueApi = createObjectClient('ConsumableIssue')

/**
 * Lifecycle module API clients
 */
export const purchaseRequestApi = createObjectClient('PurchaseRequest')
export const assetReceiptApi = createObjectClient('AssetReceipt')
export const maintenanceApi = createObjectClient('Maintenance')
export const maintenancePlanApi = createObjectClient('MaintenancePlan')
export const maintenanceTaskApi = createObjectClient('MaintenanceTask')
export const disposalRequestApi = createObjectClient('DisposalRequest')

/**
 * Inventory module API clients
 */
export const inventoryTaskApi = createObjectClient('InventoryTask')
export const inventorySnapshotApi = createObjectClient('InventorySnapshot')
export const inventoryItemApi = createObjectClient('InventoryItem')

/**
 * IT Assets module API clients
 */
export const itAssetApi = createObjectClient('ITAsset')

/**
 * Software Licenses module API clients
 */
export const softwareLicenseApi = createObjectClient('SoftwareLicense')

/**
 * Leasing module API clients
 */
export const leasingContractApi = createObjectClient('LeasingContract')
export const leaseItemApi = createObjectClient('LeaseItem')
export const rentPaymentApi = createObjectClient('RentPayment')
export const leaseReturnApi = createObjectClient('LeaseReturn')
export const leaseExtensionApi = createObjectClient('LeaseExtension')

/**
 * Insurance module API clients
 */
export const insuranceCompanyApi = createObjectClient('InsuranceCompany')
export const insurancePolicyApi = createObjectClient('InsurancePolicy')
export const insuredAssetApi = createObjectClient('InsuredAsset')
export const premiumPaymentApi = createObjectClient('PremiumPayment')
export const claimRecordApi = createObjectClient('ClaimRecord')
export const policyRenewalApi = createObjectClient('PolicyRenewal')

/**
 * Finance module API clients
 */
export const depreciationRecordApi = createObjectClient('DepreciationRecord')
export const financeVoucherApi = createObjectClient('FinanceVoucher')

/**
 * Organization module API clients
 */
export const organizationApi = createObjectClient('Organization')
export const departmentApi = createObjectClient('Department')

// Export all API clients as a grouped object for convenience
export const api = {
    // Asset module
    asset: assetApi,
    assetCategory: assetCategoryApi,
    assetPickup: assetPickupApi,
    assetTransfer: assetTransferApi,
    assetReturn: assetReturnApi,
    assetLoan: assetLoanApi,
    supplier: supplierApi,
    location: locationApi,

    // Consumables
    consumable: consumableApi,
    consumableCategory: consumableCategoryApi,
    consumableStock: consumableStockApi,
    consumablePurchase: consumablePurchaseApi,
    consumableIssue: consumableIssueApi,

    // Lifecycle
    purchaseRequest: purchaseRequestApi,
    assetReceipt: assetReceiptApi,
    maintenance: maintenanceApi,
    maintenancePlan: maintenancePlanApi,
    maintenanceTask: maintenanceTaskApi,
    disposalRequest: disposalRequestApi,

    // Inventory
    inventoryTask: inventoryTaskApi,
    inventorySnapshot: inventorySnapshotApi,
    inventoryItem: inventoryItemApi,

    // Others
    itAsset: itAssetApi,
    softwareLicense: softwareLicenseApi,
    leasingContract: leasingContractApi,
    leaseItem: leaseItemApi,
    rentPayment: rentPaymentApi,
    leaseReturn: leaseReturnApi,
    leaseExtension: leaseExtensionApi,
    insuranceCompany: insuranceCompanyApi,
    insurancePolicy: insurancePolicyApi,
    insuredAsset: insuredAssetApi,
    premiumPayment: premiumPaymentApi,
    claimRecord: claimRecordApi,
    policyRenewal: policyRenewalApi,
    depreciationRecord: depreciationRecordApi,
    financeVoucher: financeVoucherApi,
    organization: organizationApi,
    department: departmentApi,
}

export default dynamicApi
