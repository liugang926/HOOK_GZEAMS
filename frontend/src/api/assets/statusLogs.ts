import request from '@/utils/request'

export const getStatusLogList = (params: any) => {
    return request({
        url: '/system/objects/AssetStatusLog/',
        method: 'get',
        params
    })
}

export const getAssetStatusLogs = (assetId: string, params?: any) => {
    return request({
        url: '/system/objects/AssetStatusLog/',
        method: 'get',
        params: { ...params, asset: assetId }
    })
}

export const getStatusLogDetail = (id: string) => {
    return request({
        url: `/system/objects/AssetStatusLog/${id}/`,
        method: 'get'
    })
}
