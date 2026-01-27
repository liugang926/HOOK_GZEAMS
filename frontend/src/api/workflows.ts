import request from '@/utils/request'

export interface WorkflowDefinition {
    id?: number
    code: string
    name: string
    business_object: string
    graph_data: any
    description?: string
    version?: number
    is_enabled?: boolean
    is_default?: boolean
}

/**
 * 获取工作流列表
 */
export const getWorkflows = (params?: { business_object?: string }) => {
    return request.get('/workflows/definitions/', { params })
}

/**
 * 获取工作流详情
 */
export const getWorkflow = (id: number) => {
    return request.get(`/workflows/definitions/${id}/`)
}

/**
 * 创建工作流
 */
export const createWorkflow = (data: WorkflowDefinition) => {
    return request.post('/workflows/definitions/', data)
}

/**
 * 更新工作流
 */
export const updateWorkflow = (id: number, data: Partial<WorkflowDefinition>) => {
    return request.patch(`/workflows/definitions/${id}/`, data)
}

/**
 * 删除工作流
 */
export const deleteWorkflow = (id: number) => {
    return request.delete(`/workflows/definitions/${id}/`)
}

/**
 * 激活工作流
 */
export const activateWorkflow = (id: number) => {
    return request.post(`/workflows/definitions/${id}/activate/`)
}

/**
 * 克隆工作流
 */
export const cloneWorkflow = (id: number) => {
    return request.post(`/workflows/definitions/${id}/clone/`)
}
