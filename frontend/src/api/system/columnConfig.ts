import request from '@/utils/request'

// =============================================================================
// Column Configuration API
// =============================================================================

/**
 * Column configuration item
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface ColumnItem {
    fieldCode: string
    prop?: string  // Legacy support
    label?: string
    labelOverride?: string
    width?: number | string
    defaultWidth?: number | string
    fixed?: 'left' | 'right' | '' | null
    sortable?: boolean
    visible?: boolean
    defaultVisible?: boolean
    requiredInList?: boolean
    fieldType?: string
}

/**
 * Column configuration
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface ColumnConfig {
    columns: ColumnItem[]
    columnOrder?: string[]
    source?: 'user' | 'default'
}

export const columnConfigApi = {
    /**
     * Get merged column configuration for object
     * GET /api/system/column-preferences/for-object/{objectCode}/
     */
    get: (objectCode: string) => {
        return request({
            url: `/system/column-preferences/for-object/${objectCode}/`,
            method: 'get'
        })
    },

    /**
     * Save user column configuration
     * POST /api/system/column-preferences/upsert/
     */
    save: (objectCode: string, config: ColumnConfig) => {
        return request({
            url: '/system/column-preferences/upsert/',
            method: 'post',
            data: {
                object_code: objectCode,
                column_config: config
            }
        })
    },

    /**
     * Reset column configuration to default
     * POST /api/system/column-preferences/reset/
     */
    reset: (objectCode: string) => {
        return request({
            url: '/system/column-preferences/reset/',
            method: 'post',
            data: {
                object_code: objectCode
            }
        })
    },

    /**
     * List user preferences
     * GET /api/system/column-preferences/
     */
    list: (params?: any) => {
        return request({
            url: '/system/column-preferences/',
            method: 'get',
            params
        })
    }
}
