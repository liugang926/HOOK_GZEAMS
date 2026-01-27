import request from '@/utils/request'

export const getLocationList = (params: any) => {
    return request({
        url: '/assets/locations/',
        method: 'get',
        params
    })
}

export const getLocationTree = () => {
    return request({
        url: '/assets/locations/tree/',
        method: 'get'
    })
}

export const getLocationDetail = (id: string) => {
    return request({
        url: `/assets/locations/${id}/`,
        method: 'get'
    })
}

export const createLocation = (data: any) => {
    return request({
        url: '/assets/locations/',
        method: 'post',
        data
    })
}

export const updateLocation = (id: string, data: any) => {
    return request({
        url: `/assets/locations/${id}/`,
        method: 'put',
        data
    })
}

export const partialUpdateLocation = (id: string, data: any) => {
    return request({
        url: `/assets/locations/${id}/`,
        method: 'patch',
        data
    })
}

export const deleteLocation = (id: string) => {
    return request({
        url: `/assets/locations/${id}/`,
        method: 'delete'
    })
}
