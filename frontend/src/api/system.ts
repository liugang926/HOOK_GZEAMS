import request from '@/utils/request'

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

// =============================================================================
// Business Object API
// =============================================================================

export const businessObjectApi = {
    list(params?: any) {
        return request({
            url: '/system/business-objects/',
            method: 'get',
            params
        })
    },

    detail(code: string) {
        return request({
            url: `/system/business-objects/${code}/`,
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

    update(code: string, data: Partial<BusinessObject>) {
        return request({
            url: `/system/business-objects/${code}/`,
            method: 'put',
            data
        })
    },

    partialUpdate(code: string, data: Partial<BusinessObject>) {
        return request({
            url: `/system/business-objects/${code}/`,
            method: 'patch',
            data
        })
    },

    delete(code: string) {
        return request({
            url: `/system/business-objects/${code}/`,
            method: 'delete'
        })
    },

    // Get field definitions for a business object
    getFields(code: string) {
        return request({
            url: `/system/business-objects/${code}/fields/`,
            method: 'get'
        })
    },

    // Sync model fields for hardcoded objects
    syncFields(code: string) {
        return request({
            url: `/system/business-objects/${code}/sync-fields/`,
            method: 'post'
        })
    }
}

export interface FieldDefinition {
    id: string
    code: string
    name: string
    field_type: string
    is_required: boolean
    is_readonly: boolean
    is_system: boolean
    default_value?: any
    options?: any[]
    reference_object?: string
    placeholder?: string
    component_props?: Record<string, any>
}

export interface PageLayout {
    id: string
    layoutCode: string
    layoutName: string
    layoutType: 'form' | 'list' | 'detail' | 'search'
    layoutTypeDisplay?: string
    description?: string
    layoutConfig: {
        sections?: Array<{
            id: string
            type?: string
            title?: string
            fields?: Array<{
                id: string
                fieldCode: string
                label: string
                span: number
                readonly?: boolean
                visible?: boolean
                required?: boolean
            }>
            columns?: number
            collapsible?: boolean
            collapsed?: boolean
        }>
        columns?: Array<{
            fieldCode: string
            label: string
            width?: number
            fixed?: string
            sortable?: boolean
        }>
        actions?: Array<{
            code: string
            label: string
            type: string
            position: string
        }>
    }
    status: 'draft' | 'published' | 'archived'
    statusDisplay?: string
    version: string
    parentVersion?: string
    isDefault: boolean
    isActive: boolean
    isSystem?: boolean
    publishedAt?: string
    publishedBy?: string
    publishedByInfo?: {
        id: string
        username: string
    }
    business_object?: string
    business_object_name?: string
    history_count?: number
}

export interface LayoutHistory {
    id: string
    layout: string
    version: string
    config_snapshot: any
    action: 'publish' | 'update' | 'rollback'
    action_display?: string
    change_summary?: string
    published_by?: string
    published_by_info?: {
        id: string
        username: string
    }
    created_at: string
}

// 获取业务对象详情
export function getBusinessObject(code: string) {
    return request({
        url: `/system/business-objects/${code}/`,
        method: 'get'
    })
}

// 获取字段定义列表
export function getFieldDefinitions(objectCode: string) {
    return request({
        url: '/system/field-definitions/',
        method: 'get',
        params: {
            business_object__code: objectCode,
            ordering: 'sort_order'
        }
    })
}

// 获取页面布局
export function getPageLayout(objectCode: string, layoutType: string = 'form') {
    return request({
        url: '/system/page-layouts/get_active_layout/',
        method: 'get',
        params: {
            object_code: objectCode,
            layout_type: layoutType
        }
    })
}

// 获取动态数据详情
export function getDynamicData(objectCode: string, id: string) {
    return request({
        url: `/dynamic/${objectCode.toLowerCase()}/${id}/`,
        method: 'get'
    })
}

// 创建动态数据
export function createDynamicData(objectCode: string, data: any) {
    return request({
        url: `/dynamic/${objectCode.toLowerCase()}/`,
        method: 'post',
        data
    })
}

// 更新动态数据
export function updateDynamicData(objectCode: string, id: string, data: any) {
    return request({
        url: `/dynamic/${objectCode.toLowerCase()}/${id}/`,
        method: 'put',
        data
    })
}

// 获取关联引用数据
export function searchReferenceData(params: { reference_object: string; search?: string; page?: number; page_size?: number }) {
    return request({
        url: '/system/references/search/',
        method: 'get',
        params
    })
}
// 获取部门列表
export function getDepartments(params?: any) {
    return request({
        url: '/system/departments/',
        method: 'get',
        params
    })
}

// Department CRUD operations
export const getDepartmentTree = () => {
    return request({
        url: '/organizations/departments/tree/',
        method: 'get'
    })
}

export const getDepartmentDetail = (id: string) => {
    return request({
        url: `/organizations/departments/${id}/`,
        method: 'get'
    })
}

export const createDepartment = (data: any) => {
    return request({
        url: '/organizations/departments/',
        method: 'post',
        data
    })
}

export const updateDepartment = (id: string, data: any) => {
    return request({
        url: `/organizations/departments/${id}/`,
        method: 'put',
        data
    })
}

export const partialUpdateDepartment = (id: string, data: any) => {
    return request({
        url: `/organizations/departments/${id}/`,
        method: 'patch',
        data
    })
}

export const deleteDepartment = (id: string) => {
    return request({
        url: `/organizations/departments/${id}/`,
        method: 'delete'
    })
}

// 获取用户列表
export function getUsers(params?: any) {
    return request({
        url: '/system/users/',
        method: 'get',
        params
    })
}

// =============================================================================
// Data Dictionary API
// =============================================================================

export interface DictionaryType {
    id: string
    code: string
    name: string
    name_en?: string
    description?: string
    is_system: boolean
    is_active: boolean
    sort_order: number
    item_count?: number
}

export interface DictionaryItem {
    id: string
    dictionary_type: string
    code: string
    name: string
    name_en?: string
    description?: string
    color?: string
    icon?: string
    extra_data?: Record<string, any>
    is_default: boolean
    is_active: boolean
    sort_order: number
}

// Dictionary Type API
export const dictionaryTypeApi = {
    list(params?: any) {
        return request({
            url: '/system/dictionary-types/',
            method: 'get',
            params
        })
    },

    detail(id: string) {
        return request({
            url: `/system/dictionary-types/${id}/`,
            method: 'get'
        })
    },

    create(data: Partial<DictionaryType>) {
        return request({
            url: '/system/dictionary-types/',
            method: 'post',
            data
        })
    },

    update(id: string, data: Partial<DictionaryType>) {
        return request({
            url: `/system/dictionary-types/${id}/`,
            method: 'put',
            data
        })
    },

    partialUpdate(id: string, data: Partial<DictionaryType>) {
        return request({
            url: `/system/dictionary-types/${id}/`,
            method: 'patch',
            data
        })
    },

    delete(id: string) {
        return request({
            url: `/system/dictionary-types/${id}/`,
            method: 'delete'
        })
    }
}

// Dictionary Item API
export const dictionaryItemApi = {
    list(params?: any) {
        return request({
            url: '/system/dictionary-items/',
            method: 'get',
            params
        })
    },

    detail(id: string) {
        return request({
            url: `/system/dictionary-items/${id}/`,
            method: 'get'
        })
    },

    create(data: Partial<DictionaryItem>) {
        return request({
            url: '/system/dictionary-items/',
            method: 'post',
            data
        })
    },

    update(id: string, data: Partial<DictionaryItem>) {
        return request({
            url: `/system/dictionary-items/${id}/`,
            method: 'put',
            data
        })
    },

    partialUpdate(id: string, data: Partial<DictionaryItem>) {
        return request({
            url: `/system/dictionary-items/${id}/`,
            method: 'patch',
            data
        })
    },

    delete(id: string) {
        return request({
            url: `/system/dictionary-items/${id}/`,
            method: 'delete'
        })
    },

    getByType(typeCode: string, params?: any) {
        return request({
            url: '/system/dictionary-items/',
            method: 'get',
            params: {
                dictionary_type__code: typeCode,
                is_active: true,
                ordering: 'sort_order',
                ...params
            }
        })
    }
}

// =============================================================================
// Sequence Rule API
// =============================================================================

export interface SequenceRule {
    id: string
    code: string
    name: string
    prefix?: string
    pattern: string
    seq_length: number
    current_value: number
    reset_period: 'never' | 'yearly' | 'monthly' | 'daily'
    last_reset_date?: string
    description?: string
    is_active: boolean
}

export const sequenceRuleApi = {
    list(params?: any) {
        return request({
            url: '/system/sequence-rules/',
            method: 'get',
            params
        })
    },

    detail(id: string) {
        return request({
            url: `/system/sequence-rules/${id}/`,
            method: 'get'
        })
    },

    create(data: Partial<SequenceRule>) {
        return request({
            url: '/system/sequence-rules/',
            method: 'post',
            data
        })
    },

    update(id: string, data: Partial<SequenceRule>) {
        return request({
            url: `/system/sequence-rules/${id}/`,
            method: 'put',
            data
        })
    },

    delete(id: string) {
        return request({
            url: `/system/sequence-rules/${id}/`,
            method: 'delete'
        })
    },

    preview(code: string) {
        return request({
            url: `/system/sequence-rules/${code}/preview/`,
            method: 'get'
        })
    },

    reset(code: string) {
        return request({
            url: `/system/sequence-rules/${code}/reset/`,
            method: 'post'
        })
    }
}

// =============================================================================
// System Configuration API
// =============================================================================

export interface SystemConfig {
    id: string
    config_key: string
    config_value: string
    value_type: 'string' | 'integer' | 'float' | 'boolean' | 'json'
    name: string
    description?: string
    category?: string
    is_system: boolean
    is_encrypted: boolean
}

export const systemConfigApi = {
    list(params?: any) {
        return request({
            url: '/system/configs/',
            method: 'get',
            params
        })
    },

    detail(id: string) {
        return request({
            url: `/system/configs/${id}/`,
            method: 'get'
        })
    },

    create(data: Partial<SystemConfig>) {
        return request({
            url: '/system/configs/',
            method: 'post',
            data
        })
    },

    update(id: string, data: Partial<SystemConfig>) {
        return request({
            url: `/system/configs/${id}/`,
            method: 'put',
            data
        })
    },

    partialUpdate(id: string, data: Partial<SystemConfig>) {
        return request({
            url: `/system/configs/${id}/`,
            method: 'patch',
            data
        })
    },

    delete(id: string) {
        return request({
            url: `/system/configs/${id}/`,
            method: 'delete'
        })
    },

    getByCategory(category: string, params?: any) {
        return request({
            url: '/system/configs/',
            method: 'get',
            params: {
                category,
                ...params
            }
        })
    },

    updateAll(data: Record<string, any>) {
        return request({
            url: '/system/configs/batch/',
            method: 'post',
            data
        })
    }
}

// =============================================================================
// Page Layout API
// =============================================================================

export const pageLayoutApi = {
    // List layouts for a business object
    byObject(objectCode: string) {
        return request({
            url: `/system/page-layouts/by-object/${objectCode}/`,
            method: 'get'
        })
    },

    // Get layout by object code and type (with custom layout priority)
    byObjectAndType(objectCode: string, layoutType: 'form' | 'list' | 'detail' | 'search') {
        return request({
            url: `/system/page-layouts/by-object/${objectCode}/${layoutType}/`,
            method: 'get'
        })
    },

    // Get default layout or template
    getDefault(objectCode: string, layoutType: 'form' | 'list' | 'detail' | 'search') {
        return request({
            url: `/system/page-layouts/default/${objectCode}/${layoutType}/`,
            method: 'get'
        })
    },

    // CRUD operations
    list(params?: any) {
        return request({
            url: '/system/page-layouts/',
            method: 'get',
            params
        })
    },

    detail(id: string) {
        return request({
            url: `/system/page-layouts/${id}/`,
            method: 'get'
        })
    },

    create(data: Partial<PageLayout>) {
        return request({
            url: '/system/page-layouts/',
            method: 'post',
            data
        })
    },

    update(id: string, data: Partial<PageLayout>) {
        return request({
            url: `/system/page-layouts/${id}/`,
            method: 'put',
            data
        })
    },

    partialUpdate(id: string, data: Partial<PageLayout>) {
        return request({
            url: `/system/page-layouts/${id}/`,
            method: 'patch',
            data
        })
    },

    delete(id: string) {
        return request({
            url: `/system/page-layouts/${id}/`,
            method: 'delete'
        })
    },

    // Publish layout (creates version and history)
    publish(id: string, data?: { set_as_default?: boolean; change_summary?: string }) {
        return request({
            url: `/system/page-layouts/${id}/publish/`,
            method: 'post',
            data: data || {}
        })
    },

    // Get version history
    history(id: string) {
        return request({
            url: `/system/page-layouts/${id}/history/`,
            method: 'get'
        })
    },

    // Rollback to a specific version
    rollback(id: string, version: string) {
        return request({
            url: `/system/page-layouts/${id}/rollback/${version}/`,
            method: 'post'
        })
    },

    // Set as default layout
    setDefault(id: string) {
        return request({
            url: `/system/page-layouts/${id}/set-default/`,
            method: 'post'
        })
    },

    // Duplicate layout
    duplicate(id: string) {
        return request({
            url: `/system/page-layouts/${id}/duplicate/`,
            method: 'post'
        })
    }
}
