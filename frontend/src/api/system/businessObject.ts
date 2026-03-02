import request from '@/utils/request'

// =============================================================================
// Business Object API
// =============================================================================

/**
 * Business object metadata
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface BusinessObject {
    id: string
    code: string
    name: string
    nameEn?: string
    description?: string
    enableWorkflow: boolean
    enableVersion: boolean
    enableSoftDelete: boolean
    isHardcoded: boolean
    djangoModelPath?: string
    tableName?: string
    fieldCount?: number
    layoutCount?: number
}

export const businessObjectApi = {
    list(params?: any) {
        return request({
            url: '/system/business-objects/',
            method: 'get',
            params
        })
    },

    // Get business object by code (uses by-code endpoint)
    detail(code: string) {
        return request({
            url: `/system/business-objects/by-code/${code}/`,
            method: 'get'
        })
    },

    create(data: Partial<BusinessObject>) {
        return request({
            url: '/system/business-objects/',
            method: 'post',
            data
        })
    },

    // Update by ID (use primary key for update operations)
    update(id: string, data: Partial<BusinessObject>) {
        return request({
            url: `/system/business-objects/${id}/`,
            method: 'put',
            data
        })
    },

    // Partial update by ID (use primary key)
    partialUpdate(id: string, data: Partial<BusinessObject>) {
        return request({
            url: `/system/business-objects/${id}/`,
            method: 'patch',
            data
        })
    },

    // Delete by ID (use primary key)
    delete(id: string) {
        return request({
            url: `/system/business-objects/${id}/`,
            method: 'delete'
        })
    },

    // Update by code (uses by-code endpoint)
    updateByCode(code: string, data: Partial<BusinessObject>) {
        return request({
            url: `/system/business-objects/by-code/${code}/`,
            method: 'patch',
            data
        })
    },

    // Get field definitions for a business object
    // GET /api/system/business-objects/fields/?object_code=Asset
    getFields(code: string, params?: { context?: 'form' | 'detail' | 'list'; include_relations?: boolean }) {
        return request({
            url: '/system/business-objects/fields/',
            method: 'get',
            params: {
                object_code: code,
                ...params
            }
        })
    },

    // Get field definitions with context filtering via object router
    // GET /api/objects/{code}/fields/?context={context}&include_relations={true|false}
    getFieldsWithContext(code: string, context: 'form' | 'detail' | 'list' = 'form', options?: { includeRelations?: boolean }) {
        return request({
            url: `/system/objects/${code}/fields/`,
            method: 'get',
            params: {
                context,
                ...(options?.includeRelations !== undefined ? { include_relations: options.includeRelations } : {})
            }
        })
    },

    // Sync model fields for hardcoded objects
    syncFields(code: string) {
        return request({
            url: `/system/business-objects/by-code/${code}/sync_fields/`,
            method: 'post'
        })
    },

    // Get all available field types with their configurations
    // GET /api/system/business-objects/field-types/
    //
    // Returns grouped field types with component mappings for dynamic form rendering.
    // Frontend uses this to ensure field type selector matches backend capabilities.
    getFieldTypes() {
        return request<{
            success: boolean
            data: {
                field_type_groups: Array<{
                    label: string
                    icon: string
                    types: Array<{
                        value: string
                        label: string
                        icon?: string
                        description?: string
                        requires_reference?: boolean
                        supports_options?: boolean
                        component?: string
                        default_props?: Record<string, any>
                    }>
                }>
            }
        }>({
            url: '/system/business-objects/field-types/',
            method: 'get'
        })
    }
}

/**
 * Field type group for categorization in UI
 */
export interface FieldTypeGroup {
    label: string
    icon: string
    types: FieldTypeOption[]
}

/**
 * Single field type option for dropdown
 */
export interface FieldTypeOption {
    value: string
    label: string
}

/**
 * Field type configuration for component mapping
 */
export interface FieldTypeConfig {
    component: string
    defaultProps: Record<string, any>
}
