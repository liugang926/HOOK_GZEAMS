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
    return request.get('/auth/users/', { params })
  },

  /**
   * Get single user by ID
   */
  get(id: string): Promise<User> {
    return request.get(`/auth/users/${id}/`)
  },

  /**
   * Get current logged in user
   */
  getMe(): Promise<User> {
    return request.get('/auth/users/me/')
  },

  /**
   * Create new user
   */
  create(data: Partial<User>): Promise<User> {
    return request.post('/auth/users/', data)
  },

  /**
   * Update user
   */
  update(id: string, data: Partial<User>): Promise<User> {
    return request.put(`/auth/users/${id}/`, data)
  },

  /**
   * Delete user
   */
  delete(id: string): Promise<void> {
    return request.delete(`/auth/users/${id}/`)
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
  }): Promise<User> {
    return request.put('/auth/users/me/profile/', data)
  },

  /**
   * Change password
   */
  changePassword(data: {
    oldPassword: string
    newPassword: string
  }): Promise<void> {
    return request.post('/auth/users/me/change-password/', data)
  }
}
