/**
 * User API Service
 *
 * API methods for user management.
 */

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { User } from '@/types/common'

/**
 * User API service
 */
export const userApi = {
  /**
   * List users with pagination and filters
   */
  list(params?: {
    page?: number
    pageSize?: number
    search?: string
    departmentId?: string
    isActive?: boolean
  }): Promise<PaginatedResponse<User>> {
    const query: any = { ...(params || {}) }
    if (query.pageSize !== undefined) {
      query.page_size = query.pageSize
      delete query.pageSize
    }
    if (query.departmentId !== undefined) {
      query.department_id = query.departmentId
      delete query.departmentId
    }
    if (query.isActive !== undefined) {
      query.is_active = query.isActive
      delete query.isActive
    }
    return request.get('/system/objects/User/', { params: query, silent: true })
  },

  /**
   * Get single user by ID
   */
  get(id: string): Promise<User> {
    return request.get(`/system/objects/User/${id}/`, { silent: true })
  },

  /**
   * Get current logged in user
   */
  getMe(): Promise<User> {
    return request.get('/system/objects/User/me/', { silent: true })
  },

  /**
   * Create new user
   */
  create(data: Partial<User>): Promise<User> {
    return request.post('/system/objects/User/', data)
  },

  /**
   * Update user
   */
  update(id: string, data: Partial<User>): Promise<User> {
    return request.put(`/system/objects/User/${id}/`, data)
  },

  /**
   * Delete user
   */
  delete(id: string): Promise<void> {
    return request.delete(`/system/objects/User/${id}/`)
  },

  /**
   * Update current user profile
   */
  updateProfile(data: {
    firstName?: string
    lastName?: string
    email?: string
    phone?: string
    avatar?: string
    preferredLanguage?: string
  }): Promise<User> {
    return request.put('/system/objects/User/me/profile/', data)
  },

  /**
   * Change password
   */
  changePassword(data: {
    oldPassword: string
    newPassword: string
  }): Promise<void> {
    return request.post('/system/objects/User/me/change-password/', data)
  }
}
