/**
 * API Error Handler Utility
 *
 * Standardized error handling for all API calls.
 * Reference: docs/plans/common_base_features/00_core/frontend_api_standardization_design.md
 */

import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router'
import i18n from '@/locales'
import { ErrorCode, ErrorCodeMessages } from '@/types/error'

const I18N_KEY_PATTERN = /^[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/

const resolveBackendMessage = (raw: unknown, fallback: string): string => {
  if (typeof raw !== 'string' || !raw.trim()) return fallback
  const candidate = raw.trim()
  const composer = i18n.global
  const te = (composer as any)?.te
  const t = (composer as any)?.t

  if (I18N_KEY_PATTERN.test(candidate) && typeof te === 'function' && te(candidate) && typeof t === 'function') {
    return t(candidate)
  }
  return candidate
}

/**
 * Handle API errors with standardized behavior
 *
 * @param error - The error object from axios or API wrapper
 * @returns Promise that always rejects with the original error
 */
export function handleApiError(error: any): Promise<never> {
  const status = error.response?.status
  const data = error.response?.data
  const silent = error?.config?.silent === true
  const t = i18n.global.t

  // Extract error information
  let errorCode: ErrorCode = ErrorCode.SERVER_ERROR
  let message = t('common.messages.serverError')
  let details: Record<string, string[]> | undefined

  if (data?.error) {
    if (Object.values(ErrorCode).includes(data.error.code as ErrorCode)) {
      errorCode = data.error.code as ErrorCode
    }
    message = resolveBackendMessage(data.error.message, t(ErrorCodeMessages[errorCode]) || message)
    details = data.error.details
  } else if (status) {
    const statusMessages: Record<number, string> = {
      400: t('common.messages.badRequest'),
      401: t('common.messages.sessionExpired'),
      403: t('common.messages.permissionDenied'),
      404: t('common.messages.resourceNotFound'),
      410: t('common.messages.resourceGone'),
      429: t('common.messages.tooManyRequests'),
      500: t('common.messages.serverError')
    }
    message = statusMessages[status] || message
  } else if (error.code) {
    if (Object.values(ErrorCode).includes(error.code as ErrorCode)) {
      errorCode = error.code as ErrorCode
    }
    message = error.message || t(ErrorCodeMessages[errorCode]) || message
    details = error.details
  }

  // Normalize downstream error.message consumers
  if (typeof error === 'object' && error !== null) {
    try {
      error.message = message
    } catch {
      // ignore read-only properties
    }
  }

  switch (status) {
    case 401:
      if (silent) return Promise.reject(error)
      ElMessageBox.confirm(
        t('common.messages.reloginPrompt'),
        t('common.messages.tips'),
        {
          confirmButtonText: t('common.actions.confirm'),
          cancelButtonText: t('common.actions.cancel'),
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
    case 404:
    case 410:
    case 429:
      if (silent) return Promise.reject(error)
      ElMessage.error(message)
      return Promise.reject(error)

    default:
      if (silent) return Promise.reject(error)
      if (details) {
        const firstError = Object.values(details)[0]?.[0]
        ElMessage.error(firstError || message)
      } else {
        ElMessage.error(message)
      }
  }

  if (typeof error === 'object' && error !== null) {
    error.isHandled = true
  }
  return Promise.reject(error)
}

/**
 * Extract error message from error object
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
  return i18n.global.t('common.messages.operationFailed')
}

export function showSuccess(message: string): void {
  ElMessage.success(message)
}

export function showError(message: string): void {
  ElMessage.error(message)
}

export function showWarning(message: string): void {
  ElMessage.warning(message)
}

export function showInfo(message: string): void {
  ElMessage.info(message)
}
