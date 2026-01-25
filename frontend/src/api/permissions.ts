import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

/**
 * Permissions Management API Client
 * Handles field permissions, data permissions, and audit logs
 */

// Field Permissions
export const fieldPermissionApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/permissions/field-permissions/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/permissions/field-permissions/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/permissions/field-permissions/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/permissions/field-permissions/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/permissions/field-permissions/${id}/`)
  },

  grant(data: any): Promise<void> {
    return request.post('/permissions/field-permissions/grant/', data)
  },

  revoke(data: any): Promise<void> {
    return request.post('/permissions/field-permissions/revoke/', data)
  }
}

// Data Permissions
export const dataPermissionApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/permissions/data-permissions/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/permissions/data-permissions/${id}/`)
  },

  create(data: any): Promise<any> {
    return request.post('/permissions/data-permissions/', data)
  },

  update(id: string, data: any): Promise<any> {
    return request.put(`/permissions/data-permissions/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/permissions/data-permissions/${id}/`)
  },

  grant(data: any): Promise<void> {
    return request.post('/permissions/data-permissions/grant/', data)
  },

  revoke(data: any): Promise<void> {
    return request.post('/permissions/data-permissions/revoke/', data)
  }
}

// Data Permission Expansions
export const dataPermissionExpandApi = {
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/permissions/data-permission-expands/', { params })
  },

  detail(id: string): Promise<any> {
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
  list(params?: any): Promise<PaginatedResponse<any>> {
    return request.get('/permissions/audit-logs/', { params })
  },

  detail(id: string): Promise<any> {
    return request.get(`/permissions/audit-logs/${id}/`)
  },

  statistics(params?: any): Promise<any> {
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
