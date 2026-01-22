/**
 * API Type Definitions
 *
 * Unified API response interface for all endpoints following v2.0 standards.
 * Reference: docs/plans/common_base_features/00_core/frontend_api_standardization_design.md
 */

/**
 * Unified API response interface for all endpoints
 */
export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  error?: ApiError
}

/**
 * Standard error structure
 */
export interface ApiError {
  code: ErrorCode
  message: string
  details?: Record<string, string[]>
}

/**
 * Paginated response data
 */
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/**
 * Batch operation response
 */
export interface BatchResponse {
  summary: {
    total: number
    succeeded: number
    failed: number
  }
  results: BatchResultItem[]
}

/**
 * Individual batch operation result
 */
export interface BatchResultItem {
  id: string
  success: boolean
  error?: string
}

/**
 * Import error code type
 */
import type { ErrorCode } from './error'
