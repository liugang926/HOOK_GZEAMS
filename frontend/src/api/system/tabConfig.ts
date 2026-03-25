import request from '@/utils/request'

// =============================================================================
// Tab Configuration API
// =============================================================================

export interface TabItem {
    id: string
    title: string
    icon?: string
    closable?: boolean
    disabled?: boolean
    badge?: string | number
    permission?: string
    visible?: boolean
    lazy?: boolean
    content?: any
    component?: any
    props?: Record<string, any>
    slots?: Record<string, any>
}

/**
 * Tab configuration
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface TabConfig {
    id?: string
    businessObject?: string
    businessObjectCode?: string
    businessObjectName?: string
    name: string
    position?: 'top' | 'left' | 'right' | 'bottom'
    positionDisplay?: string
    typeStyle?: '' | 'card' | 'border-card'
    typeStyleDisplay?: string
    stretch?: boolean
    lazy?: boolean
    animated?: boolean
    addable?: boolean
    draggable?: boolean
    tabsConfig: TabItem[]
    isActive?: boolean
}

export const tabConfigApi = {
    /**
     * Get tab configuration for business object
     * GET /api/system/tab-configs/by-object/{businessObject}/
     */
    getByObject: (businessObject: string) => {
        return request({
            url: `/system/tab-configs/by-object/${businessObject}/`,
            method: 'get'
        })
    },

    /**
     * Get single tab configuration
     * GET /api/system/tab-configs/{id}/
     */
    get: (id: string) => {
        return request({
            url: `/system/tab-configs/${id}/`,
            method: 'get'
        })
    },

    /**
     * List tab configurations
     * GET /api/system/tab-configs/
     */
    list: (params?: any) => {
        return request({
            url: '/system/tab-configs/',
            method: 'get',
            params
        })
    },

    /**
     * Create tab configuration
     * POST /api/system/tab-configs/
     */
    create: (config: Partial<TabConfig>) => {
        return request({
            url: '/system/tab-configs/',
            method: 'post',
            data: config
        })
    },

    /**
     * Update tab configuration
     * PUT /api/system/tab-configs/{id}/
     */
    update: (id: string, config: Partial<TabConfig>) => {
        return request({
            url: `/system/tab-configs/${id}/`,
            method: 'put',
            data: config
        })
    },

    /**
     * Partial update tab configuration
     * PATCH /api/system/tab-configs/{id}/
     */
    partialUpdate: (id: string, config: Partial<TabConfig>) => {
        return request({
            url: `/system/tab-configs/${id}/`,
            method: 'patch',
            data: config
        })
    },

    /**
     * Delete tab configuration
     * DELETE /api/system/tab-configs/{id}/
     */
    delete: (id: string) => {
        return request({
            url: `/system/tab-configs/${id}/`,
            method: 'delete'
        })
    }
}
