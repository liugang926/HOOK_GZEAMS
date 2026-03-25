import request from '@/utils/request'
import type { LayoutMode } from '@/types/layout'
import type { PageLayout } from './fieldDefinition'

export type PageLayoutLookupMode = LayoutMode | 'form' | 'detail' | 'list'
export type PageLayoutMutationPayload = Partial<Omit<PageLayout, 'layoutConfig'>> & {
    layoutConfig?: unknown
    layout_config?: unknown
    [key: string]: unknown
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

    // Get layout by object code and mode (with custom layout priority)
    byObjectAndMode(objectCode: string, mode: PageLayoutLookupMode) {
        return request({
            url: `/system/page-layouts/by-object/${objectCode}/${mode}/`,
            method: 'get'
        })
    },

    // Get default layout or template
    getDefault(objectCode: string, mode: PageLayoutLookupMode) {
        return request({
            url: `/system/page-layouts/default/${objectCode}/${mode}/`,
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

    create(data: PageLayoutMutationPayload) {
        return request({
            url: '/system/page-layouts/',
            method: 'post',
            data
        })
    },

    update(id: string, data: PageLayoutMutationPayload) {
        return request({
            url: `/system/page-layouts/${id}/`,
            method: 'put',
            data
        })
    },

    partialUpdate(id: string, data: PageLayoutMutationPayload) {
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
    },

    // Save differential configuration (user/role/org level changes only)
    saveDiffConfig(data: {
        businessObject: string
        mode: LayoutMode
        priority: 'user' | 'role' | 'org'
        diffConfig: {
            fieldOrder?: string[]
            sections?: Array<{
                id: string
                fields?: Array<{
                    fieldCode?: string
                    code?: string
                    span?: number
                    readonly?: boolean
                    visible?: boolean
                    required?: boolean
                }>
            }>
        }
    }) {
        return request({
            url: '/system/page-layouts/save-diff-config/',
            method: 'post',
            data
        })
    },

    // Get merged layout (default + differential config applied)
    getMergedLayout(params: {
        businessObject: string
        mode: LayoutMode
        priority?: 'user' | 'role' | 'org'
    }) {
        return request<{
            success: boolean
            data: PageLayout
        }>({
            url: '/system/page-layouts/get-merged-layout/',
            method: 'post',
            data: params
        })
    }
}
