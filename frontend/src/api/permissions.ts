import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

/**
 * Permissions Management API Client
 * Handles field permissions, data permissions, and audit logs
 */

export interface FieldPermissionRecord {
  id: string
  user: string
  userDisplay?: string
  contentType: number
  contentTypeDisplay?: string
  fieldName: string
  permissionType: 'read' | 'write' | 'hidden' | 'masked'
  permissionTypeDisplay?: string
  maskRule?: string | null
  customMaskPattern?: string
  condition?: Record<string, unknown> | null
  priority?: number
  description?: string
}

export interface FieldPermissionUpdatePayload {
  permissionType: 'read' | 'write' | 'hidden' | 'masked'
  maskRule?: string | null
  customMaskPattern?: string
  condition?: Record<string, unknown> | null
  priority?: number
  description?: string
}

export interface DataPermissionRecord {
  id: string
  user: string
  userDisplay?: string
  contentType: number
  contentTypeDisplay?: string
  scopeType: 'all' | 'self' | 'self_dept' | 'self_and_sub' | 'specified' | 'custom'
  scopeTypeDisplay?: string
  scopeValue: Record<string, unknown>
  departmentField?: string
  userField?: string
  description?: string
}

export interface DataPermissionCreatePayload {
  userUsername: string
  contentTypeAppLabel: string
  contentTypeModel: string
  scopeType: 'all' | 'self' | 'self_dept' | 'self_and_sub' | 'specified' | 'custom'
  scopeValue: Record<string, unknown>
  departmentField?: string
  userField?: string
  description?: string
}

export interface DataPermissionUpdatePayload {
  scopeType: 'all' | 'self' | 'self_dept' | 'self_and_sub' | 'specified' | 'custom'
  scopeValue: Record<string, unknown>
  departmentField?: string
  userField?: string
  description?: string
}

export interface PermissionAuditLogRecord {
  id: string
  createdAt: string
  actor?: string | null
  actorDisplay?: string | null
  targetUser?: string | null
  targetUserDisplay?: string | null
  operationType: 'check' | 'grant' | 'revoke' | 'modify' | 'deny'
  operationTypeDisplay?: string
  targetType: 'field_permission' | 'data_permission' | 'user_permission'
  targetTypeDisplay?: string
  permissionDetails?: unknown
  contentType?: number | null
  objectId?: string | null
  result?: 'success' | 'failure' | 'partial'
  resultDisplay?: string
  errorMessage?: string
  ipAddress?: string | null
  userAgent?: string
}

export interface PermissionAuditStatistics {
  periodDays: number
  totalCount: number
  byOperation: Array<{
    operationType: string
    count: number
  }>
  byResult: Array<{
    result: string
    count: number
  }>
  byTargetType: Array<{
    targetType: string
    count: number
  }>
}

export interface PermissionListParams {
  page?: number
  page_size?: number
  user_username?: string
  content_type_model?: string
  operation_type?: string
  created_at_from?: string
  created_at_to?: string
}

// Field Permissions
export const fieldPermissionApi = {
  list(params?: PermissionListParams): Promise<PaginatedResponse<FieldPermissionRecord>> {
    return request.get('/permissions/field-permissions/', { params })
  },

  detail(id: string): Promise<FieldPermissionRecord> {
    return request.get(`/permissions/field-permissions/${id}/`)
  },

  create(data: Record<string, unknown>): Promise<FieldPermissionRecord> {
    return request.post('/permissions/field-permissions/', data)
  },

  update(id: string, data: FieldPermissionUpdatePayload): Promise<FieldPermissionRecord> {
    return request.put(`/permissions/field-permissions/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/permissions/field-permissions/${id}/`)
  },

  grant(data: Record<string, unknown>): Promise<void> {
    return request.post('/permissions/field-permissions/grant/', data)
  },

  revoke(data: Record<string, unknown>): Promise<void> {
    return request.post('/permissions/field-permissions/revoke/', data)
  }
}

// Data Permissions
export const dataPermissionApi = {
  list(params?: PermissionListParams): Promise<PaginatedResponse<DataPermissionRecord>> {
    return request.get('/permissions/data-permissions/', { params })
  },

  detail(id: string): Promise<DataPermissionRecord> {
    return request.get(`/permissions/data-permissions/${id}/`)
  },

  create(data: DataPermissionCreatePayload): Promise<DataPermissionRecord> {
    return request.post('/permissions/data-permissions/', data)
  },

  update(id: string, data: DataPermissionUpdatePayload): Promise<DataPermissionRecord> {
    return request.put(`/permissions/data-permissions/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/permissions/data-permissions/${id}/`)
  },

  grant(data: Record<string, unknown>): Promise<void> {
    return request.post('/permissions/data-permissions/grant/', data)
  },

  revoke(data: Record<string, unknown>): Promise<void> {
    return request.post('/permissions/data-permissions/revoke/', data)
  }
}

// Data Permission Expansions
export const dataPermissionExpandApi = {
  list(params?: PermissionListParams): Promise<PaginatedResponse<Record<string, unknown>>> {
    return request.get('/permissions/data-permission-expands/', { params })
  },

  detail(id: string): Promise<Record<string, unknown>> {
    return request.get(`/permissions/data-permission-expands/${id}/`)
  },

  activate(id: string): Promise<void> {
    return request.post(`/permissions/data-permission-expands/${id}/activate/`)
  },

  deactivate(id: string): Promise<void> {
    return request.post(`/permissions/data-permission-expands/${id}/deactivate/`)
  }
}

// Audit Logs
export const permissionAuditLogApi = {
  list(params?: PermissionListParams): Promise<PaginatedResponse<PermissionAuditLogRecord>> {
    return request.get('/permissions/audit-logs/', { params })
  },

  detail(id: string): Promise<PermissionAuditLogRecord> {
    return request.get(`/permissions/audit-logs/${id}/`)
  },

  statistics(params?: { user_id?: string; days?: number }): Promise<PermissionAuditStatistics> {
    return request.get('/permissions/audit-logs/statistics/', { params })
  }
}

// Legacy function exports for backward compatibility
export const getFieldPermissionList = fieldPermissionApi.list
export const getFieldPermissionDetail = fieldPermissionApi.detail
export const createFieldPermission = fieldPermissionApi.create
export const updateFieldPermission = fieldPermissionApi.update
export const deleteFieldPermission = fieldPermissionApi.delete
export const grantFieldPermission = fieldPermissionApi.grant
export const revokeFieldPermission = fieldPermissionApi.revoke

export const getDataPermissionList = dataPermissionApi.list
export const getDataPermissionDetail = dataPermissionApi.detail
export const createDataPermission = dataPermissionApi.create
export const updateDataPermission = dataPermissionApi.update
export const deleteDataPermission = dataPermissionApi.delete
export const grantDataPermission = dataPermissionApi.grant
export const revokeDataPermission = dataPermissionApi.revoke

export const getDataPermissionExpandList = dataPermissionExpandApi.list
export const getDataPermissionExpandDetail = dataPermissionExpandApi.detail
export const activateDataPermissionExpand = dataPermissionExpandApi.activate
export const deactivateDataPermissionExpand = dataPermissionExpandApi.deactivate

export const getPermissionAuditLogList = permissionAuditLogApi.list
export const getPermissionAuditLogDetail = permissionAuditLogApi.detail
export const getPermissionAuditLogStatistics = permissionAuditLogApi.statistics
