/**
 * Organization API Service
 *
 * API methods for organization and department management.
 */

import request from '@/utils/request'
import type { Organization } from '@/types/common'

/**
 * Organization API service
 */
export const orgApi = {
  /**
   * List all organizations (flat)
   */
  list(): Promise<Organization[]> {
    return request.get('/system/objects/Organization/')
  },

  /**
   * Get organization tree structure
   */
  tree(): Promise<Organization[]> {
    return request.get('/system/objects/Organization/tree/')
  },

  /**
   * Get single organization by ID
   */
  get(id: string): Promise<Organization> {
    return request.get(`/system/objects/Organization/${id}/`)
  },

  /**
   * Create new organization
   */
  create(data: {
    name: string
    code: string
    parentId?: string
    description?: string
  }): Promise<Organization> {
    return request.post('/system/objects/Organization/', data)
  },

  /**
   * Update organization
   */
  update(id: string, data: Partial<Organization>): Promise<Organization> {
    return request.put(`/system/objects/Organization/${id}/`, data)
  },

  /**
   * Delete organization
   */
  delete(id: string): Promise<void> {
    return request.delete(`/system/objects/Organization/${id}/`)
  },

  /**
   * Get organization members
   */
  getMembers(id: string): Promise<any[]> {
    return request.get(`/system/objects/Organization/${id}/members/`)
  },

  /**
   * Add member to organization
   */
  addMember(id: string, userId: string): Promise<void> {
    return request.post(`/system/objects/Organization/${id}/members/`, { userId })
  },

  /**
   * Remove member from organization
   */
  removeMember(id: string, userId: string): Promise<void> {
    return request.delete(`/system/objects/Organization/${id}/members/`, {
      data: { userId }
    })
  }
}

/**
 * Department API service
 */
export const deptApi = {
  /**
   * List all departments
   */
  list(): Promise<any[]> {
    return request.get('/system/objects/Department/')
  },

  /**
   * Get department tree
   */
  tree(): Promise<any[]> {
    return request.get('/system/objects/Department/tree/')
  },

  /**
   * Get single department by ID
   */
  get(id: string): Promise<any> {
    return request.get(`/system/objects/Department/${id}/`)
  },

  /**
   * Create new department
   */
  create(data: {
    name: string
    code: string
    parentId?: string
    managerId?: string
  }): Promise<any> {
    return request.post('/system/objects/Department/', data)
  },

  /**
   * Update department
   */
  update(id: string, data: Partial<any>): Promise<any> {
    return request.put(`/system/objects/Department/${id}/`, data)
  },

  /**
   * Delete department
   */
  delete(id: string): Promise<void> {
    return request.delete(`/system/objects/Department/${id}/`)
  },

  /**
   * Get department members
   */
  getMembers(id: string): Promise<any[]> {
    return request.get(`/system/objects/Department/${id}/users/`)
  }
}
