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
    groupTranslationKey?: string
    translationKey?: string
    badge?: any
}

export interface MenuTranslationTarget {
    contentType: string
    contentTypeModel: string
    objectId: string
    fieldName: string
}

export interface MenuGroup {
    id?: string
    code?: string
    name: string
    translationKey?: string
    localeNames?: Record<string, string>
    translationTarget?: MenuTranslationTarget
    order: number
    icon: string
    items: MenuItem[]
}

export interface MenuResponse {
    groups: MenuGroup[]
    items: MenuItem[]
}

export interface MenuManagementCategory {
    id?: string
    code: string
    name: string
    translationKey?: string
    localeNames?: Record<string, string>
    translationTarget?: MenuTranslationTarget
    icon: string
    order: number
    isVisible: boolean
    isLocked: boolean
    isDefault: boolean
    entryCount: number
    supportsDelete: boolean
}

export interface MenuManagementItem {
    code: string
    name: string
    nameEn?: string
    translationKey?: string
    sourceType: 'business_object' | 'static'
    sourceCode: string
    path: string
    icon: string
    groupCode: string
    groupTranslationKey?: string
    order: number
    isVisible: boolean
    isLocked: boolean
    isDefault: boolean
    supportsDelete: boolean
    supportsVisibility: boolean
    supportsReorder: boolean
    supportsGroupChange: boolean
}

export interface MenuManagementResponse {
    categories: MenuManagementCategory[]
    items: MenuManagementItem[]
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
    },

    management: () => {
        return request<MenuManagementResponse>({
            url: '/system/menu/management/',
            method: 'get'
        })
    },

    updateManagement: (data: MenuManagementResponse) => {
        return request<MenuManagementResponse>({
            url: '/system/menu/management/',
            method: 'put',
            data
        })
    }
}
