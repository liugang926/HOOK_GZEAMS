/**
 * Workflow API Service
 *
 * API methods for BPM workflow management.
 * Reference: docs/plans/phase3_1_logicflow/frontend_v2.md
 */

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { WorkflowDefinition, WorkflowInstance } from '@/types/workflow'
import type { ApprovalAction } from '@/types/workflow'

/**
 * Workflow Definition API service
 */
export const workflowApi = {
  /**
   * List workflow definitions
   */
  listDefinitions(params?: {
    businessObject?: string
    isActive?: boolean
  }): Promise<WorkflowDefinition[]> {
    return request.get('/workflows/definitions/', { params })
  },

  /**
   * Get single definition by ID
   */
  getDefinition(id: string): Promise<WorkflowDefinition> {
    return request.get(`/workflows/definitions/${id}/`)
  },

  /**
   * Save workflow definition (create or update)
   */
  saveDefinition(data: {
    name: string
    code: string
    businessObject: string
    graphData: any
    description?: string
  }): Promise<WorkflowDefinition> {
    return request.post('/workflows/definitions/', data)
  },

  /**
   * Update workflow definition
   */
  updateDefinition(id: string, data: Partial<WorkflowDefinition>): Promise<WorkflowDefinition> {
    return request.put(`/workflows/definitions/${id}/`, data)
  },

  /**
   * Activate workflow definition
   */
  activateDefinition(id: string): Promise<void> {
    return request.post(`/workflows/definitions/${id}/activate/`)
  },

  /**
   * Deactivate workflow definition
   */
  deactivateDefinition(id: string): Promise<void> {
    return request.post(`/workflows/definitions/${id}/deactivate/`)
  },

  /**
   * Delete workflow definition
   */
  deleteDefinition(id: string): Promise<void> {
    return request.delete(`/workflows/definitions/${id}/`)
  },

  /**
   * Get workflow definition version history
   */
  getVersionHistory(id: string): Promise<any[]> {
    return request.get(`/workflows/definitions/${id}/versions/`)
  }
}

/**
 * Workflow Instance API service
 */
export const workflowInstanceApi = {
  /**
   * List workflow instances
   */
  listInstances(params?: {
    businessDataType?: string
    businessDataId?: string
    status?: string
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<WorkflowInstance>> {
    return request.get('/workflows/instances/', { params })
  },

  /**
   * Get single instance by ID
   */
  getInstance(id: string): Promise<WorkflowInstance> {
    return request.get(`/workflows/instances/${id}/`)
  },

  /**
   * Start workflow instance
   */
  startInstance(data: {
    definitionId: string
    businessDataType: string
    businessDataId: string
    variables?: Record<string, any>
  }): Promise<WorkflowInstance> {
    return request.post('/workflows/instances/start/', data)
  },

  /**
   * Cancel workflow instance
   */
  cancelInstance(id: string, reason?: string): Promise<void> {
    return request.post(`/workflows/instances/${id}/cancel/`, { reason })
  },

  /**
   * Get instance timeline/history
   */
  getTimeline(id: string): Promise<any[]> {
    return request.get(`/workflows/instances/${id}/timeline/`)
  }
}

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
  }): Promise<PaginatedResponse<any>> {
    return request.get('/workflows/nodes/my-tasks/', { params })
  },

  /**
   * Approve or reject workflow node
   */
  approveNode(instanceId: string, nodeId: string, data: ApprovalAction): Promise<void> {
    return request.post(`/workflows/instances/${instanceId}/nodes/${nodeId}/approve/`, data)
  },

  /**
   * Get node details
   */
  getNode(instanceId: string, nodeId: string): Promise<any> {
    return request.get(`/workflows/instances/${instanceId}/nodes/${nodeId}/`)
  },

  /**
   * Delegate node to another user
   */
  delegateNode(instanceId: string, nodeId: string, userId: string): Promise<void> {
    return request.post(`/workflows/instances/${instanceId}/nodes/${nodeId}/delegate/`, { userId })
  }
}
