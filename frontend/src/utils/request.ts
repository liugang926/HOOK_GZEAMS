/**
 * Axios Instance with Interceptors
 *
 * Centralized HTTP client with automatic field transformation and error handling.
 *
 * Architecture Note:
 * - Backend uses djangorestframework-camel-case for automatic camelCase conversion
 * - Response data is already in camelCase format (no transformation needed)
 * - Request data is sent as camelCase (backend parser handles conversion to snake_case)
 *
 * Reference: docs/plans/common_base_features/00_core/frontend_api_standardization_design.md
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import type { ApiResponse } from '@/types/api'
import { handleApiError } from '@/utils/errorHandler'

type RequestInstance = AxiosInstance & {
  <T = any>(config: AxiosRequestConfig): Promise<T>
  <T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  request<T = any>(config: AxiosRequestConfig): Promise<T>
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  head<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  options<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
  patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>
}

/**
 * Create base axios instance
 */
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
}) as RequestInstance

/**
 * Request interceptor
 * - Add authorization token
 * - Add organization header
 * - Add Accept-Language header
 * - Data is sent as camelCase (backend parser handles conversion to snake_case)
 */
request.interceptors.request.use(
  (config) => {
    // Normalize legacy URLs that accidentally include the API prefix.
    // Since axios `baseURL` already includes `/api`, passing `/api/...` would become `/api/api/...` and 404.
    if (typeof config.url === 'string' && config.url.startsWith('/api/')) {
      config.url = config.url.slice('/api'.length)
    }

    // Let the browser/axios set multipart boundaries automatically.
    if (typeof FormData !== 'undefined' && config.data instanceof FormData && config.headers) {
      if (typeof (config.headers as any).set === 'function') {
        ;(config.headers as any).set('Content-Type', undefined)
        ;(config.headers as any).set('content-type', undefined)
      }
      delete (config.headers as any)['Content-Type']
      delete (config.headers as any)['content-type']
    }

    const noAuth = (config as any).noAuth === true

    // Add authorization header
    if (!noAuth) {
      const token = localStorage.getItem('access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }

      // Add organization header
      const orgId = localStorage.getItem('current_org_id')
      if (orgId) {
        config.headers['X-Organization-ID'] = orgId
      }

      // Add Accept-Language header for i18n
      const locale = localStorage.getItem('locale') || 'zh-CN'
      config.headers['Accept-Language'] = locale
    }

    // Note: Data and params are sent as camelCase
    // Backend's CamelCaseJSONParser handles conversion to snake_case

    return config
  },
  (error) => Promise.reject(error)
)

/**
 * Response interceptor
 * - Handle unified response format
 * - Handle errors consistently
 * - Note: Response data is already in camelCase from backend renderer
 */
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response
    const unwrap = (response.config as any)?.unwrap ?? 'auto'

    // Handle empty responses (204 No Content)
    if (!data) {
      return response
    }

    if (unwrap === 'none') {
      return data
    }

    // Data is already in camelCase from backend's CamelCaseJSONRenderer
    // Unwrap unified response format
    if (typeof data === 'object' && 'success' in data) {
      const apiResponse = data as ApiResponse

      // Handle error responses
      if (!apiResponse.success && apiResponse.error) {
        const err = new ApiErrorWrapper(apiResponse.error)
        ;(err as any).config = response.config
        return Promise.reject(err)
      }

      if (unwrap === 'data') {
        return apiResponse.data
      }

      // `auto`: Only unwrap when the response actually follows the `{ success, data }` contract.
      // Some endpoints return `{ success, message, summary, results }` (no `data` field).
      if ('data' in apiResponse || 'error' in apiResponse) return apiResponse.data
      return data
    }

    // Return data as-is for non-unified responses (legacy endpoints, blob, etc.)
    return data
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
