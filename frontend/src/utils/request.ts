/**
 * Axios Instance with Interceptors
 *
 * Centralized HTTP client with automatic field transformation and error handling.
 * Reference: docs/plans/common_base_features/00_core/frontend_api_standardization_design.md
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse } from '@/types/api'
import { toCamelCase, toSnakeCase } from '@/utils/transform'
import { handleApiError } from '@/utils/errorHandler'

/**
 * Create base axios instance
 */
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * Request interceptor
 * - Add authorization token
 * - Add organization header
 * - Transform request data from camelCase to snake_case
 */
request.interceptors.request.use(
  (config) => {
    // Add authorization header
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add organization header
    const orgId = localStorage.getItem('current_org_id')
    if (orgId) {
      config.headers['X-Organization-ID'] = orgId
    }

    // Transform request data to snake_case
    if (config.data && typeof config.data === 'object' && !(config.data instanceof FormData)) {
      config.data = toSnakeCase(config.data)
    }

    // Transform request params to snake_case
    if (config.params && typeof config.params === 'object') {
      config.params = toSnakeCase(config.params)
    }

    return config
  },
  (error) => Promise.reject(error)
)

/**
 * Response interceptor
 * - Transform response data from snake_case to camelCase
 * - Handle unified response format
 * - Handle errors consistently
 */
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response

    // Handle empty responses (204 No Content)
    if (!data) {
      return response
    }

    // Transform snake_case to camelCase
    const camelData = toCamelCase(data)

    // Unwrap unified response format
    if (typeof camelData === 'object' && 'success' in camelData) {
      const apiResponse = camelData as ApiResponse

      // Handle error responses
      if (!apiResponse.success && apiResponse.error) {
        return Promise.reject(new ApiErrorWrapper(apiResponse.error))
      }

      // Return data directly for success responses
      return apiResponse.data
    }

    // Return data as-is for non-unified responses (legacy endpoints, blob, etc.)
    return camelData
  },
  (error) => handleApiError(error)
)

/**
 * Custom error class for API errors
 */
class ApiErrorWrapper extends Error {
  code: string
  details?: Record<string, string[]>

  constructor(apiError: any) {
    super(apiError.message)
    this.code = apiError.code
    this.details = apiError.details
    this.name = 'ApiError'
  }
}

/**
 * Export the configured axios instance
 */
export default request

/**
 * Export the request type for use in other modules
 */
export type { AxiosInstance, AxiosRequestConfig, AxiosResponse }
