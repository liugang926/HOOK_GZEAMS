import request from '@/utils/request'

// =============================================================================
// Sequence Rule API
// =============================================================================

/**
 * Sequence rule for auto-generated codes
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface SequenceRule {
    id: string
    code: string
    name: string
    prefix?: string
    pattern: string
    seqLength: number
    currentValue: number
    resetPeriod: 'never' | 'yearly' | 'monthly' | 'daily'
    lastResetDate?: string
    description?: string
    isActive: boolean
}

export const sequenceRuleApi = {
    list(params?: any) {
        return request({
            url: '/system/sequence-rules/',
            method: 'get',
            params
        })
    },

    detail(id: string) {
        return request({
            url: `/system/sequence-rules/${id}/`,
            method: 'get'
        })
    },

    create(data: Partial<SequenceRule>) {
        return request({
            url: '/system/sequence-rules/',
            method: 'post',
            data
        })
    },

    update(id: string, data: Partial<SequenceRule>) {
        return request({
            url: `/system/sequence-rules/${id}/`,
            method: 'put',
            data
        })
    },

    delete(id: string) {
        return request({
            url: `/system/sequence-rules/${id}/`,
            method: 'delete'
        })
    },

    preview(code: string) {
        return request({
            url: `/system/sequence-rules/${code}/preview/`,
            method: 'get'
        })
    },

    reset(code: string) {
        return request({
            url: `/system/sequence-rules/${code}/reset/`,
            method: 'post'
        })
    }
}
