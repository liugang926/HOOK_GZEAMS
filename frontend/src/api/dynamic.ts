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
export type { ObjectMetadata } from '@/types'
import { checkRuntimeContract, type RuntimeMode } from '@/contracts/runtimeContract'
import type {
    AggregateDocumentPageMode,
    AggregateDocumentResponse,
    RuntimeAggregate,
    RuntimeWorkbench,
} from '@/types/runtime'

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

export interface ObjectRelationDefinition {
    relationCode: string
    relationName: string
    relationNameEn?: string
    relationNameI18n?: Record<string, string>
    relationTranslationKey?: string
    parentObjectCode?: string
    targetObjectCode: string
    targetObjectName?: string
    targetObjectNameEn?: string
    targetObjectLocaleNames?: Record<string, string>
    targetObjectRole?: 'root' | 'detail' | 'reference' | 'log' | string
    targetAllowStandaloneQuery?: boolean
    targetAllowStandaloneRoute?: boolean
    targetInheritPermissions?: boolean
    targetInheritWorkflow?: boolean
    targetInheritStatus?: boolean
    targetInheritLifecycle?: boolean
    relationKind: 'direct_fk' | 'through_line_item' | 'derived_query' | string
    relationType?: 'lookup' | 'master_detail' | 'derived' | string
    displayMode: 'inline_editable' | 'inline_readonly' | 'tab_readonly' | 'hidden' | string
    detailEditMode?: 'inline_table' | 'nested_form' | 'readonly_table' | string
    sortOrder: number
    targetFkField?: string
    throughObjectCode?: string
    throughParentFkField?: string
    throughTargetFkField?: string
    derivedParentKeyField?: string
    derivedTargetKeyField?: string
    cascadeSoftDelete?: boolean
    detailToolbarConfig?: Record<string, any>
    detailSummaryRules?: Array<Record<string, any>>
    detailValidationRules?: Array<Record<string, any>>
    extraConfig?: Record<string, any>
    groupKey?: string
    groupName?: string
    groupOrder?: number
    defaultExpanded?: boolean
    displayTier?: 'L1' | 'L2' | 'L3'
    actionLabel?: string
}

export interface ObjectRelationsResponse {
    objectCode: string
    locale: string
    relations: ObjectRelationDefinition[]
}

export interface RelatedRecordsResponse<T = any> {
    count: number
    next: string | null
    previous: string | null
    results: T[]
    relation: {
        relationCode: string
        relationKind: string
        targetObjectCode: string
        displayMode: string
        sortOrder: number
    }
    parentObjectCode: string
    parentId: string
    targetObjectCode: string
}

export interface CompactDetailField {
    fieldCode: string
    label: string
    value: any
    fieldType: string
}

export interface GlobalSearchMatch {
    record_id: string
    display_name: string
    match_field: string
    match_value: string
}

export interface GlobalSearchResult {
    object_code: string
    object_name: string
    matches: GlobalSearchMatch[]
}

export interface ObjectActionDefinition {
    actionCode: string
    label: string
    buttonType?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default' | string
    enabled: boolean
    disabledReason?: string
    confirmMessage?: string
    targetObjectCode?: string
}

export interface ObjectActionsResponse {
    objectCode: string
    recordId: string
    actions: ObjectActionDefinition[]
}

export interface ObjectActionExecutionResult {
    actionCode: string
    message?: string
    targetObjectCode?: string
    targetId?: string
    targetUrl?: string
    targetRecordNo?: string
    navigateAfterSuccess?: boolean
    refreshCurrent?: boolean
    summary?: Record<string, any>
}

export interface ObjectRuntimeResponse {
    runtimeVersion?: number
    objectCode?: string
    mode?: RuntimeMode
    context?: string
    locale?: string
    permissions?: Record<string, boolean>
    fields?: Record<string, any>
    aggregate?: RuntimeAggregate | null
    workbench?: RuntimeWorkbench | null
    layout?: Record<string, any>
    isDefault?: boolean | null
}

export interface AggregateDocumentPayload {
    master: Record<string, any>
    details?: Record<string, { rows: Array<Record<string, any>> }>
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
    getMetadata(code: string): Promise<ObjectMetadata> {
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
    async getRuntime(code: string, mode: RuntimeMode = 'edit', params?: Record<string, any>): Promise<ObjectRuntimeResponse> {
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

        return payload as ObjectRuntimeResponse
    }

    /**
     * Get unified aggregate document payload for a record.
     * GET /api/system/objects/{code}/{id}/document/?mode=...
     */
    getDocument(
        code: string,
        id: string,
        mode: AggregateDocumentPageMode = 'readonly'
    ): Promise<AggregateDocumentResponse> {
        return request({
            url: `${this.baseUrl}/${code}/${id}/document/`,
            method: 'get',
            params: { mode }
        })
    }

    /**
     * Create a record through the aggregate document contract.
     * POST /api/system/objects/{code}/document/
     */
    createDocument(
        code: string,
        payload: AggregateDocumentPayload,
        mode: AggregateDocumentPageMode = 'edit'
    ): Promise<AggregateDocumentResponse> {
        return request({
            url: `${this.baseUrl}/${code}/document/`,
            method: 'post',
            params: { mode },
            data: payload
        })
    }

    /**
     * Update a record through the aggregate document contract.
     * PUT /api/system/objects/{code}/{id}/document/
     */
    updateDocument(
        code: string,
        id: string,
        payload: AggregateDocumentPayload,
        mode: AggregateDocumentPageMode = 'edit'
    ): Promise<AggregateDocumentResponse> {
        return request({
            url: `${this.baseUrl}/${code}/${id}/document/`,
            method: 'put',
            params: { mode },
            data: payload
        })
    }

    /**
     * Partial update through the aggregate document contract.
     * PATCH /api/system/objects/{code}/{id}/document/
     */
    partialUpdateDocument(
        code: string,
        id: string,
        payload: AggregateDocumentPayload,
        mode: AggregateDocumentPageMode = 'edit'
    ): Promise<AggregateDocumentResponse> {
        return request({
            url: `${this.baseUrl}/${code}/${id}/document/`,
            method: 'patch',
            params: { mode },
            data: payload
        })
    }

    /**
     * Get relation definitions for an object.
     * GET /api/system/objects/{code}/relations/
     */
    getRelations(code: string): Promise<ObjectRelationsResponse> {
        return request({
            url: `${this.baseUrl}/${code}/relations/`,
            method: 'get'
        })
    }

    /**
     * Get related records for a parent record by relation code.
     * GET /api/system/objects/{code}/{id}/related/{relationCode}/
     */
    getRelated<T = any>(
        code: string,
        id: string,
        relationCode: string,
        params?: Record<string, any>
    ): Promise<RelatedRecordsResponse<T>> {
        return request({
            url: `${this.baseUrl}/${code}/${id}/related/${relationCode}/`,
            method: 'get',
            params
        })
    }

    /**
     * Get relation counts for a parent record.
     * GET /api/system/objects/{code}/{id}/relation-counts/
     */
    getRelationCounts(
        code: string,
        id: string
    ): Promise<ApiResponse<{ counts: Record<string, number> }>> {
        return request({
            url: `${this.baseUrl}/${code}/${id}/relation-counts/`,
            method: 'get'
        })
    }

    /**
     * Get compact detail fields for a record (used by hover cards).
     * GET /api/system/objects/{code}/{id}/compact/
     */
    getCompactDetail(
        code: string,
        id: string
    ): Promise<ApiResponse<{ fields: CompactDetailField[] }>> {
        return request({
            url: `${this.baseUrl}/${code}/${id}/compact/`,
            method: 'get'
        })
    }

    /**
     * Get unified cross-object actions for a record.
     * GET /api/system/objects/{code}/{id}/actions/
     */
    getActions(
        code: string,
        id: string
    ): Promise<ObjectActionsResponse> {
        return request({
            url: `${this.baseUrl}/${code}/${id}/actions/`,
            method: 'get'
        })
    }

    /**
     * Execute a unified cross-object action for a record.
     * POST /api/system/objects/{code}/{id}/actions/{actionCode}/execute/
     */
    executeAction(
        code: string,
        id: string,
        actionCode: string,
        payload?: Record<string, any>
    ): Promise<ObjectActionExecutionResult> {
        return request({
            url: `${this.baseUrl}/${code}/${id}/actions/${actionCode}/execute/`,
            method: 'post',
            data: payload || {}
        })
    }

    /**
     * Global search across all business objects.
     * GET /api/system/global-search/?q=<keyword>&limit=5&object_codes=code1,code2
     */
    globalSearch(
        keyword: string,
        options?: { limit?: number; objectCodes?: string[] }
    ): Promise<ApiResponse<GlobalSearchResult[]>> {
        const params: Record<string, string> = { q: keyword }
        if (options?.limit) params.limit = String(options.limit)
        if (options?.objectCodes?.length) params.object_codes = options.objectCodes.join(',')
        return request({
            url: '/api/system/global-search/',
            method: 'get',
            params
        })
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
    getMetadata(): Promise<ObjectMetadata>
    getSchema(): Promise<ApiResponse<any>>
    getRuntime(mode?: 'edit' | 'readonly' | 'list' | 'search', params?: Record<string, any>): Promise<ObjectRuntimeResponse>
    getDocument(id: string, mode?: AggregateDocumentPageMode): Promise<AggregateDocumentResponse>
    createDocument(payload: AggregateDocumentPayload, mode?: AggregateDocumentPageMode): Promise<AggregateDocumentResponse>
    updateDocument(id: string, payload: AggregateDocumentPayload, mode?: AggregateDocumentPageMode): Promise<AggregateDocumentResponse>
    partialUpdateDocument(id: string, payload: AggregateDocumentPayload, mode?: AggregateDocumentPageMode): Promise<AggregateDocumentResponse>
    getRelations(): Promise<ObjectRelationsResponse>
    getRelated<T = any>(id: string, relationCode: string, params?: Record<string, any>): Promise<RelatedRecordsResponse<T>>
    getRelationCounts(id: string): Promise<ApiResponse<{ counts: Record<string, number> }>>
    getCompactDetail(id: string): Promise<ApiResponse<{ fields: CompactDetailField[] }>>
    getActions(id: string): Promise<ObjectActionsResponse>
    executeAction(id: string, actionCode: string, payload?: Record<string, any>): Promise<ObjectActionExecutionResult>
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
            dynamicApi.getRuntime(code, mode, params),
        getDocument: (id: string, mode: AggregateDocumentPageMode = 'readonly') =>
            dynamicApi.getDocument(code, id, mode),
        createDocument: (payload: AggregateDocumentPayload, mode: AggregateDocumentPageMode = 'edit') =>
            dynamicApi.createDocument(code, payload, mode),
        updateDocument: (id: string, payload: AggregateDocumentPayload, mode: AggregateDocumentPageMode = 'edit') =>
            dynamicApi.updateDocument(code, id, payload, mode),
        partialUpdateDocument: (id: string, payload: AggregateDocumentPayload, mode: AggregateDocumentPageMode = 'edit') =>
            dynamicApi.partialUpdateDocument(code, id, payload, mode),
        getRelations: () => dynamicApi.getRelations(code),
        getRelated: <T = any>(id: string, relationCode: string, params?: Record<string, any>) =>
            dynamicApi.getRelated<T>(code, id, relationCode, params),
        getRelationCounts: (id: string) =>
            dynamicApi.getRelationCounts(code, id),
        getCompactDetail: (id: string) =>
            dynamicApi.getCompactDetail(code, id),
        getActions: (id: string) =>
            dynamicApi.getActions(code, id),
        executeAction: (id: string, actionCode: string, payload?: Record<string, any>) =>
            dynamicApi.executeAction(code, id, actionCode, payload)
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
export const assetWarrantyApi = createObjectClient('AssetWarranty')

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
    assetWarranty: assetWarrantyApi,

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
