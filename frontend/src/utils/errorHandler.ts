/**
 * API Error Handler Utility
 *
 * Standardized error handling for all API calls.
 * Reference: docs/plans/common_base_features/00_core/frontend_api_standardization_design.md
 */

import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router'
import type { ErrorCode } from '@/types/error'
import { ErrorCodeMessages } from '@/types/error'

/**
 * Handle API errors with standardized behavior
 *
 * @param error - The error object from axios or API wrapper
 * @returns Promise that always rejects with the original error
 */
export function handleApiError(error: any): Promise<never> {
  const status = error.response?.status
  const data = error.response?.data

  // Extract error information
  let errorCode: ErrorCode = 'SERVER_ERROR'
  let message = '服务器错误，请稍后再试'
  let details: Record<string, string[]> | undefined

  if (data?.error) {
    errorCode = data.error.code
    message = data.error.message || ErrorCodeMessages[errorCode] || message
    details = data.error.details
  } else if (error.code) {
    errorCode = error.code
    message = error.message || ErrorCodeMessages[errorCode] || message
    details = error.details
  }

  // Handle specific status codes
  switch (status) {
    case 401:
      // Unauthorized - redirect to login
      ElMessageBox.confirm(
        '登录已过期，是否重新登录？',
        '提示',
        {
          confirmButtonText: '重新登录',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        localStorage.clear()
        router.push('/login')
      }).catch(() => {
        // User cancelled
      })
      return Promise.reject(error)

    case 403:
      // Permission denied
      ElMessage.error(message || '权限不足')
      return Promise.reject(error)

    case 404:
      // Not found
      ElMessage.error(message || '请求的资源不存在')
      return Promise.reject(error)

    case 410:
      // Soft deleted
      ElMessage.error(message || '资源已被删除')
      return Promise.reject(error)

    case 429:
      // Rate limit exceeded
      ElMessage.error(message || '请求过于频繁，请稍后再试')
      return Promise.reject(error)

    default:
      // Show error message
      if (details) {
        // Show validation errors - use first error message
        const firstError = Object.values(details)[0]?.[0]
        ElMessage.error(firstError || message)
      } else {
        ElMessage.error(message)
      }
  }
  // Mark error as handled so downstream catch blocks don't show it again
  if (typeof error === 'object' && error !== null) {
    error.isHandled = true
  }
  return Promise.reject(error)
}

/**
 * Extract error message from error object
 *
 * @param error - The error object
 * @returns The error message string
 */
export function getErrorMessage(error: any): string {
  if (error?.response?.data?.error?.message) {
    return error.response.data.error.message
  }
  if (error?.response?.data?.message) {
    return error.response.data.message
  }
  if (error?.message) {
    return error.message
  }
  return '操作失败，请稍后重试'
}

/**
 * Show success message
 *
 * @param message - The success message
 */
export function showSuccess(message: string): void {
  ElMessage.success(message)
}

/**
 * Show error message directly
 *
 * @param message - The error message
 */
export function showError(message: string): void {
  ElMessage.error(message)
}

/**
 * Show warning message
 *
 * @param message - The warning message
 */
export function showWarning(message: string): void {
  ElMessage.warning(message)
}

/**
 * Show info message
 *
 * @param message - The info message
 */
export function showInfo(message: string): void {
  ElMessage.info(message)
}
