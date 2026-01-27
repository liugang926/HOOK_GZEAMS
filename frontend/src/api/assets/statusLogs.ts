import request from '@/utils/request'

export const getStatusLogList = (params: any) => {
    return request({
        url: '/assets/status-logs/',
        method: 'get',
        params
    })
}

export const getAssetStatusLogs = (assetId: string, params?: any) => {
    return request({
        url: `/assets/status-logs/`,
        method: 'get',
        params: { ...params, asset: assetId }
    })
}

export const getStatusLogDetail = (id: string) => {
    return request({
        url: `/assets/status-logs/${id}/`,
        method: 'get'
    })
}
