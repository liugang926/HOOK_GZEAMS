import request from '@/utils/request'

export const getSupplierList = (params: any) => {
    return request({
        url: '/system/objects/Supplier/',
        method: 'get',
        params
    })
}

export const getSupplierDetail = (id: string) => {
    return request({
        url: `/system/objects/Supplier/${id}/`,
        method: 'get'
    })
}

export const createSupplier = (data: any) => {
    return request({
        url: '/system/objects/Supplier/',
        method: 'post',
        data
    })
}

export const updateSupplier = (id: string, data: any) => {
    return request({
        url: `/system/objects/Supplier/${id}/`,
        method: 'put',
        data
    })
}

export const partialUpdateSupplier = (id: string, data: any) => {
    return request({
        url: `/system/objects/Supplier/${id}/`,
        method: 'patch',
        data
    })
}

export const deleteSupplier = (id: string) => {
    return request({
        url: `/system/objects/Supplier/${id}/`,
        method: 'delete'
    })
}
