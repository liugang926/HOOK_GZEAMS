/**
 * Location API Service
 *
 * API methods for location management.
 */

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

/**
 * Location API service object
 */
export const locationApi = {
  /**
   * List all locations (flat)
   */
  list(params?: {
    page?: number
    pageSize?: number
    search?: string
  }): Promise<PaginatedResponse<any>> {
    return request.get('/assets/locations/', { params })
  },

  /**
   * Get location tree structure
   */
  tree(): Promise<any[]> {
    return request.get('/assets/locations/tree/')
  },

  /**
   * Get single location by ID
   */
  get(id: string): Promise<any> {
    return request.get(`/assets/locations/${id}/`)
  },

  /**
   * Create new location
   */
  create(data: Partial<any>): Promise<any> {
    return request.post('/assets/locations/', data)
  },

  /**
   * Update location
   */
  update(id: string, data: Partial<any>): Promise<any> {
    return request.put(`/assets/locations/${id}/`, data)
  },

  /**
   * Delete location
   */
  delete(id: string): Promise<void> {
    return request.delete(`/assets/locations/${id}/`)
  }
}

/**
 * Convenience function for getting locations (used by other components)
 */
export const getLocations = (params?: any): Promise<any> => {
  return request.get('/api/assets/locations/', { params })
}
