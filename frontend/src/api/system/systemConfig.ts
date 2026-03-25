import request from '@/utils/request'

// =============================================================================
// System Configuration API
// =============================================================================

/**
 * System configuration
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface SystemConfig {
    id: string
    configKey: string
    configValue: string
    valueType: 'string' | 'integer' | 'float' | 'boolean' | 'json'
    name: string
    description?: string
    category?: string
    isSystem: boolean
    isEncrypted: boolean
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
