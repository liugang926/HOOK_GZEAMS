/**
 * Workflow API Service
 *
 * API methods for BPM workflow management.
 * Refactored to use BaseApiService.
 * Reference: docs/plans/phase3_1_logicflow/frontend_v2.md
 */

import request from '@/utils/request'
import { BaseApiService } from '@/api/base'
import type {
  ApprovalAction,
  MyTasksResponse,
  TaskDetailWithPermissions,
  WorkflowDefinition,
  WorkflowInstance,
  WorkflowInstanceStartPayload,
} from '@/types/workflow'

/**
 * Workflow Definition API service
 */
class WorkflowDefinitionApiService extends BaseApiService<WorkflowDefinition> {
  constructor() {
    super('workflows/definitions')
  }

  /**
   * Activate workflow definition
   */
  activate(id: string): Promise<void> {
    return request.post(`/${this.resource}/${id}/activate/`)
  }

  /**
   * Deactivate workflow definition
   */
  deactivate(id: string): Promise<void> {
    return request.post(`/${this.resource}/${id}/deactivate/`)
  }

  /**
   * Get workflow definition version history
   */
  getVersionHistory(id: string): Promise<any[]> {
    return request.get(`/${this.resource}/${id}/versions/`)
  }

  // Aliases for compatibility
  listDefinitions(params?: any) { return this.list(params) }
  getDefinition(id: string) { return this.get(id) }
  saveDefinition(data: any) {
    // Logic might need check if ID exists, or if 'save' means create/update smart handling
    return this.create(data)
  }
  updateDefinition(id: string, data: any) { return this.update(id, data) }
  deleteDefinition(id: string) { return this.delete(id) }
  activateDefinition(id: string) { return this.activate(id) }
  deactivateDefinition(id: string) { return this.deactivate(id) }
}
export const workflowApi = new WorkflowDefinitionApiService()


/**
 * Workflow Instance API service
 */
class WorkflowInstanceApiService extends BaseApiService<WorkflowInstance> {
  constructor() {
    super('workflows/instances')
  }

  /**
   * Start workflow instance
   */
  start(data: WorkflowInstanceStartPayload): Promise<WorkflowInstance> {
    return request.post(`/${this.resource}/start/`, data)
  }

  /**
   * Start workflow instance by process key (convenience method)
   */
  startProcess(data: {
    processKey: string
    businessKey: string
    variables?: Record<string, any>
  }): Promise<WorkflowInstance> {
    return request.post(`/${this.resource}/start/`, {
      processKey: data.processKey,
      businessKey: data.businessKey,
      variables: data.variables,
    })
  }

  /**
   * Cancel workflow instance
   * Backend uses `withdraw` as the user-facing cancel action.
   */
  cancel(id: string, reason?: string): Promise<void> {
    return request.post(`/${this.resource}/${id}/withdraw/`, reason ? { reason } : {})
  }

  /**
   * Force terminate workflow instance (admin action)
   */
  terminate(id: string, reason?: string): Promise<void> {
    return request.post(`/${this.resource}/${id}/terminate/`, reason ? { reason } : {})
  }

  /**
   * Get instance timeline/history
   */
  getTimeline(id: string): Promise<any[]> {
    return request.get(`/${this.resource}/${id}/timeline/`)
  }

  // Aliases
  listInstances(params?: any) { return this.list(params) }
  getInstance(id: string) { return this.get(id) }
  startInstance(data: any) { return this.start(data) }
  cancelInstance(id: string, reason?: string) { return this.cancel(id, reason) }
  terminateInstance(id: string, reason?: string) { return this.terminate(id, reason) }
}
export const workflowInstanceApi = new WorkflowInstanceApiService()

/**
 * Workflow Node API service
 */
export const workflowNodeApi = {
  /**
   * Get pending tasks for current user
   */
  getMyTasks(params?: {
    page?: number
    pageSize?: number
    status?: string
  }): Promise<MyTasksResponse> {
    return request.get('/workflows/tasks/my_tasks/', { params })
  },

  /**
   * Approve or reject workflow node
   * Compatibility adapter:
   * - legacy callers pass (instanceId, nodeId)
   * - backend action is task-centric: /workflows/tasks/{taskId}/approve|reject/
   */
  approveNode(instanceId: string, nodeId: string, data: ApprovalAction): Promise<void> {
    const taskId = nodeId || instanceId
    const action = data?.action || 'approve'
    const payload = data?.comment ? { comment: data.comment } : {}
    if (action === 'reject') {
      return request.post(`/workflows/tasks/${taskId}/reject/`, payload)
    }
    return request.post(`/workflows/tasks/${taskId}/approve/`, payload)
  },

  /**
   * Get node details
   * Compatibility adapter to task detail endpoint.
   */
  getNode(instanceId: string, nodeId: string): Promise<TaskDetailWithPermissions> {
    const taskId = nodeId || instanceId
    return request.get(`/workflows/tasks/${taskId}/`)
  },

  /**
   * Delegate node to another user
   * Compatibility adapter to task delegate endpoint.
   */
  delegateNode(instanceId: string, nodeId: string, userId: string): Promise<void> {
    const taskId = nodeId || instanceId
    return request.post(`/workflows/tasks/${taskId}/delegate/`, { toUserId: userId })
  }
}

/**
 * Workflow Task API service
 * For task approval and detail viewing
 */
export const taskApi = {
  /**
   * Get task detail by ID
   */
  getTaskDetail(id: string): Promise<TaskDetailWithPermissions> {
    return request.get(`/workflows/tasks/${id}/`)
  },

  /**
   * Get task form data
   * Backend currently has no dedicated `/form-data/` endpoint.
   * Fallback to task detail and extract instance variables if present.
   */
  async getTaskFormData(taskId: string): Promise<any> {
    const detail = await request.get(`/workflows/tasks/${taskId}/`)
    const payload = detail?.data || detail
    const instance = payload?.instance || payload?.task?.instance
    return instance?.variables || payload?.variables || payload
  },

  /**
   * Approve task
   */
  approveTask(id: string, data: { comment: string }): Promise<any> {
    return request.post(`/workflows/tasks/${id}/approve/`, data)
  },

  /**
   * Reject task
   */
  rejectTask(id: string, data: { comment: string }): Promise<any> {
    return request.post(`/workflows/tasks/${id}/reject/`, data)
  },

  /**
   * Return task to previous step
   */
  returnTask(id: string, data: { comment: string }): Promise<any> {
    return request.post(`/workflows/tasks/${id}/return_task/`, data)
  }
}

/**
 * Legacy function exports for backward compatibility
 */
export const getTaskDetail = taskApi.getTaskDetail
export const getTaskFormData = taskApi.getTaskFormData
export const approveTask = taskApi.approveTask
export const rejectTask = taskApi.rejectTask
export const returnTask = taskApi.returnTask

/**
 * Additional API functions required by Vue components
 */
export const getWorkflowDefinitions = (params?: any) => workflowApi.list(params)
export const publishWorkflow = (id: string) => request.post(`/workflows/definitions/${id}/publish/`)
export const unpublishWorkflow = (id: string) => request.post(`/workflows/definitions/${id}/unpublish/`)
export const deleteWorkflowDefinitions = (ids: string[]) => {
  return Promise.all(ids.map(id => workflowApi.delete(id)))
}

export const getWorkflowInstances = (params?: any) => workflowInstanceApi.list(params)
export const cancelWorkflowInstance = (id: string, reason?: string) => workflowInstanceApi.cancel(id, reason)
export const getWorkflowInstanceStats = () => request.get('/workflows/statistics/')

export const getUserTasks = (params?: any) => request.get('/workflows/tasks/', { params })
export const getPotentialAssignees = (params: { task_id: string; exclude_current?: boolean }) => 
  request.get('/workflows/tasks/potential-assignees/', { params })
export const transferTask = (taskId: string, data: { to_user_id: string; comment?: string }) => 
  request.post(`/workflows/tasks/${taskId}/transfer/`, data)
export const getTaskStatistics = () => request.get('/workflows/tasks/statistics/')
