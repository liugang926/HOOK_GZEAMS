import request from '@/utils/request'

export const getLocationList = (params: any) => {
    return request({
        url: '/system/objects/Location/',
        method: 'get',
        params
    })
}

export const getLocationTree = () => {
    return request({
        url: '/system/objects/Location/tree/',
        method: 'get'
    })
}

export const getLocationDetail = (id: string) => {
    return request({
        url: `/system/objects/Location/${id}/`,
        method: 'get'
    })
}

export const createLocation = (data: any) => {
    return request({
        url: '/system/objects/Location/',
        method: 'post',
        data
    })
}

export const updateLocation = (id: string, data: any) => {
    return request({
        url: `/system/objects/Location/${id}/`,
        method: 'put',
        data
    })
}

export const partialUpdateLocation = (id: string, data: any) => {
    return request({
        url: `/system/objects/Location/${id}/`,
        method: 'patch',
        data
    })
}

export const deleteLocation = (id: string) => {
    return request({
        url: `/system/objects/Location/${id}/`,
        method: 'delete'
    })
}
