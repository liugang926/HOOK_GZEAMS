import request from '@/utils/request'

export const getSupplierList = (params: any) => {
    return request({
        url: '/assets/suppliers/',
        method: 'get',
        params
    })
}

export const getSupplierDetail = (id: string) => {
    return request({
        url: `/assets/suppliers/${id}/`,
        method: 'get'
    })
}

export const createSupplier = (data: any) => {
    return request({
        url: '/assets/suppliers/',
        method: 'post',
        data
    })
}

export const updateSupplier = (id: string, data: any) => {
    return request({
        url: `/assets/suppliers/${id}/`,
        method: 'put',
        data
    })
}

export const partialUpdateSupplier = (id: string, data: any) => {
    return request({
        url: `/assets/suppliers/${id}/`,
        method: 'patch',
        data
    })
}

export const deleteSupplier = (id: string) => {
    return request({
        url: `/assets/suppliers/${id}/`,
        method: 'delete'
    })
}
