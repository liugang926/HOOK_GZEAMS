import request from '@/utils/request'

// =============================================================================
// Menu API
// =============================================================================

/**
 * Menu item metadata
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface MenuItem {
    code: string
    name: string
    nameEn?: string
    url: string
    icon: string
    order: number
    group: string
    groupCode?: string
    badge?: any
}

export interface MenuGroup {
    code?: string
    name: string
    order: number
    icon: string
    items: MenuItem[]
}

export interface MenuResponse {
    groups: MenuGroup[]
    items: MenuItem[]
}

export const menuApi = {
    /**
     * Get full menu structure grouped by category
     * GET /api/system/menu/
     */
    get: () => {
        return request<MenuResponse>({
            url: '/system/menu/',
            method: 'get'
        })
    },

    /**
     * Get flat menu item list
     * GET /api/system/menu/flat/
     */
    flat: () => {
        return request<{ success: boolean; data: MenuItem[] }>({
            url: '/system/menu/flat/',
            method: 'get'
        })
    },

    /**
     * Get menu configuration schema
     * GET /api/system/menu/config/
     */
    config: () => {
        return request<{
            schema: Record<string, any>
            common_groups: Array<{ name: string; order: number; icon: string }>
            common_icons: string[]
        }>({
            url: '/system/menu/config/',
            method: 'get'
        })
    }
}
