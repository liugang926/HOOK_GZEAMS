import request from '@/utils/request'

// =============================================================================
// Data Dictionary API
// =============================================================================

/**
 * Data dictionary type
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface DictionaryType {
    id: string
    code: string
    name: string
    nameEn?: string
    name_en?: string
    description?: string
    isSystem: boolean
    isActive: boolean
    is_active?: boolean
    sortOrder: number
    sort_order?: number
    itemCount?: number
}

/**
 * Data dictionary item
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface DictionaryItem {
    id: string
    dictionaryType: string
    dictionary_type?: string
    code: string
    name: string
    nameEn?: string
    name_en?: string
    description?: string
    color?: string
    icon?: string
    extraData?: Record<string, any>
    isDefault: boolean
    is_default?: boolean
    isActive: boolean
    is_active?: boolean
    sortOrder: number
    sort_order?: number
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
