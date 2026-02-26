/**
 * Asset Pickup API Service
 *
 * Now using unified Dynamic Object Routing via /api/system/objects/AssetPickup/
 * Custom actions (submit, cancel, complete, workflow-callback) use dedicated endpoints
 */

import request from '@/utils/request'
import { assetPickupApi } from '@/api/dynamic'

/**
 * List pickups (delegates to dynamic API)
 */
export const getPickupList = (params: any) => {
    return assetPickupApi.list(params)
}

/**
 * Get pickup detail (delegates to dynamic API)
 */
export const getPickupDetail = (id: string) => {
    return assetPickupApi.get(id)
}

/**
 * Create pickup (delegates to dynamic API)
 */
export const createPickup = (data: any) => {
    return assetPickupApi.create(data)
}

/**
 * Update pickup (delegates to dynamic API)
 */
export const updatePickup = (id: string, data: any) => {
    return assetPickupApi.update(id, data)
}

/**
 * Submit pickup for approval (custom action endpoint)
 */
export const submitPickup = (id: string) => {
    return request({
        url: `/system/objects/AssetPickup/${id}/submit/`,
        method: 'post'
    })
}

/**
 * Cancel pickup (custom action endpoint)
 */
export const cancelPickup = (id: string) => {
    return request({
        url: `/system/objects/AssetPickup/${id}/cancel/`,
        method: 'post'
    })
}

/**
 * Complete pickup (custom action endpoint)
 */
export const completePickup = (id: string) => {
    return request({
        url: `/system/objects/AssetPickup/${id}/complete/`,
        method: 'post'
    })
}

/**
 * Handle workflow callback for pickup order
 * Called by workflow engine when workflow is completed
 */
export const handleWorkflowCallback = (id: string, workflowInstanceId: string) => {
    return request({
        url: `/system/objects/AssetPickup/${id}/workflow-callback/`,
        method: 'post',
        data: {
            workflow_instance_id: workflowInstanceId
        }
    })
}
