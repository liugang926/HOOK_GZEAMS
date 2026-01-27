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
    return request.get('/organizations/organizations/')
  },

  /**
   * Get organization tree structure
   */
  tree(): Promise<Organization[]> {
    return request.get('/organizations/organizations/tree/')
  },

  /**
   * Get single organization by ID
   */
  get(id: string): Promise<Organization> {
    return request.get(`/organizations/organizations/${id}/`)
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
    return request.post('/organizations/organizations/', data)
  },

  /**
   * Update organization
   */
  update(id: string, data: Partial<Organization>): Promise<Organization> {
    return request.put(`/organizations/organizations/${id}/`, data)
  },

  /**
   * Delete organization
   */
  delete(id: string): Promise<void> {
    return request.delete(`/organizations/organizations/${id}/`)
  },

  /**
   * Get organization members
   */
  getMembers(id: string): Promise<any[]> {
    return request.get(`/organizations/organizations/${id}/members/`)
  },

  /**
   * Add member to organization
   */
  addMember(id: string, userId: string): Promise<void> {
    return request.post(`/organizations/organizations/${id}/members/`, { userId })
  },

  /**
   * Remove member from organization
   */
  removeMember(id: string, userId: string): Promise<void> {
    return request.delete(`/organizations/organizations/${id}/members/${userId}/`)
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
    return request.get('/organizations/departments/')
  },

  /**
   * Get department tree
   */
  tree(): Promise<any[]> {
    return request.get('/organizations/departments/tree/')
  },

  /**
   * Get single department by ID
   */
  get(id: string): Promise<any> {
    return request.get(`/organizations/departments/${id}/`)
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
    return request.post('/organizations/departments/', data)
  },

  /**
   * Update department
   */
  update(id: string, data: Partial<any>): Promise<any> {
    return request.put(`/organizations/departments/${id}/`, data)
  },

  /**
   * Delete department
   */
  delete(id: string): Promise<void> {
    return request.delete(`/organizations/departments/${id}/`)
  },

  /**
   * Get department members
   */
  getMembers(id: string): Promise<any[]> {
    return request.get(`/organizations/departments/${id}/members/`)
  }
}
