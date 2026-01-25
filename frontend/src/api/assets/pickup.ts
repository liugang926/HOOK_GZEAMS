import request from '@/utils/request'

export const getPickupList = (params: any) => {
    return request({
        url: '/assets/pickups/',
        method: 'get',
        params
    })
}

export const getPickupDetail = (id: string) => {
    return request({
        url: `/assets/pickups/${id}/`,
        method: 'get'
    })
}

export const createPickup = (data: any) => {
    return request({
        url: '/assets/pickups/',
        method: 'post',
        data
    })
}

export const updatePickup = (id: string, data: any) => {
    return request({
        url: `/assets/pickups/${id}/`,
        method: 'put',
        data
    })
}

export const submitPickup = (id: string) => {
    return request({
        url: `/assets/pickups/${id}/submit/`,
        method: 'post'
    })
}

export const cancelPickup = (id: string) => {
    return request({
        url: `/assets/pickups/${id}/cancel/`,
        method: 'post'
    })
}

export const completePickup = (id: string) => {
    return request({
        url: `/assets/pickups/${id}/complete/`,
        method: 'post'
    })
}

/**
 * Handle workflow callback for pickup order
 * Called by workflow engine when workflow is completed
 */
export const handleWorkflowCallback = (id: string, workflowInstanceId: string) => {
    return request({
        url: `/assets/pickups/${id}/workflow-callback/`,
        method: 'post',
        data: {
            workflow_instance_id: workflowInstanceId
        }
    })
}
