import request from '@/utils/request'
import type { LayoutMode } from '@/types/layout'

// =============================================================================
// Legacy Helper Functions
// =============================================================================

// 获取业务对象详情 - uses by-code endpoint
export function getBusinessObject(code: string) {
    return request({
        url: `/system/business-objects/by-code/${code}/`,
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

// Get page layout by object code and mode
export function getPageLayout(objectCode: string, mode: LayoutMode = 'edit') {
    return request({
        url: '/system/page-layouts/get_active_layout/',
        method: 'get',
        params: {
            object_code: objectCode,
            mode
        }
    })
}

// 获取动态数据详情
export function getDynamicData(objectCode: string, id: string) {
    return request({
        url: `/system/objects/${objectCode}/${id}/`,
        method: 'get'
    })
}

// 创建动态数据
export function createDynamicData(objectCode: string, data: any) {
    return request({
        url: `/system/objects/${objectCode}/`,
        method: 'post',
        data
    })
}

// 更新动态数据
export function updateDynamicData(objectCode: string, id: string, data: any) {
    return request({
        url: `/system/objects/${objectCode}/${id}/`,
        method: 'put',
        data
    })
}

// 获取关联引用数据
export function searchReferenceData(params: { reference_object: string; search?: string; page?: number; page_size?: number }) {
    // Backend does not expose a generic /system/references/search/ endpoint.
    // Resolve reference_object to an object code and query the unified dynamic object route.
    const ref = (params.reference_object || '').trim()
    const noQuery = ref.split('?')[0].replace(/\/+$/, '')
    const lastDot = noQuery.split('.').pop() || noQuery
    const objectCode = (lastDot.split('/').filter(Boolean).pop() || lastDot).trim()

    // Unified object router only (engine should not depend on legacy /auth/users).
    const doList = (url: string) =>
        request({
            url,
            method: 'get',
            params: {
                search: params.search || '',
                page: params.page,
                page_size: params.page_size || 50,
            }
        })

    return doList(`/system/objects/${objectCode}/`)
}

// 获取部门列表
export function getDepartments(params?: any) {
    return request({
        url: '/system/objects/Department/',
        method: 'get',
        params
    })
}

// Department CRUD operations
export const getDepartmentTree = () => {
    return request({
        url: '/system/objects/Department/tree/',
        method: 'get'
    })
}

export const getDepartmentDetail = (id: string) => {
    return request({
        url: `/system/objects/Department/${id}/`,
        method: 'get'
    })
}

export const createDepartment = (data: any) => {
    return request({
        url: '/system/objects/Department/',
        method: 'post',
        data
    })
}

export const updateDepartment = (id: string, data: any) => {
    return request({
        url: `/system/objects/Department/${id}/`,
        method: 'put',
        data
    })
}

export const partialUpdateDepartment = (id: string, data: any) => {
    return request({
        url: `/system/objects/Department/${id}/`,
        method: 'patch',
        data
    })
}

export const deleteDepartment = (id: string) => {
    return request({
        url: `/system/objects/Department/${id}/`,
        method: 'delete'
    })
}

// Get user list
export function getUsers(params?: any) {
    // Unified object router only (engine should not depend on legacy /auth/users).
    return request({
        url: '/system/objects/User/',
        method: 'get',
        params,
        silent: true
    })
}
