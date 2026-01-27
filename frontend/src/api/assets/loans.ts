import request from '@/utils/request'

export const getLoanList = (params: any) => {
    return request({
        url: '/assets/loans/',
        method: 'get',
        params
    })
}

export const getLoanDetail = (id: string) => {
    return request({
        url: `/assets/loans/${id}/`,
        method: 'get'
    })
}

export const createLoan = (data: any) => {
    return request({
        url: '/assets/loans/',
        method: 'post',
        data
    })
}

export const updateLoan = (id: string, data: any) => {
    return request({
        url: `/assets/loans/${id}/`,
        method: 'put',
        data
    })
}

export const submitLoan = (id: string) => {
    return request({
        url: `/assets/loans/${id}/submit/`,
        method: 'post'
    })
}

export const cancelLoan = (id: string) => {
    return request({
        url: `/assets/loans/${id}/cancel/`,
        method: 'post'
    })
}

export const approveLoan = (id: string) => {
    return request({
        url: `/assets/loans/${id}/approve/`,
        method: 'post'
    })
}

export const rejectLoan = (id: string, reason: string) => {
    return request({
        url: `/assets/loans/${id}/reject/`,
        method: 'post',
        data: { reason }
    })
}

export const returnLoan = (id: string, data: any) => {
    return request({
        url: `/assets/loans/${id}/return/`,
        method: 'post',
        data
    })
}
