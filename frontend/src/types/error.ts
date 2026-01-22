/**
 * Error Code Type Definitions
 *
 * Standard error codes matching backend definition.
 * Reference: docs/plans/common_base_features/00_core/frontend_api_standardization_design.md
 */

/**
 * Standard error codes matching backend definition
 */
export enum ErrorCode {
  // Client errors (4xx)
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  UNAUTHORIZED = 'UNAUTHORIZED',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  NOT_FOUND = 'NOT_FOUND',
  METHOD_NOT_ALLOWED = 'METHOD_NOT_ALLOWED',
  CONFLICT = 'CONFLICT',
  ORGANIZATION_MISMATCH = 'ORGANIZATION_MISMATCH',
  SOFT_DELETED = 'SOFT_DELETED',

  // Server errors (5xx)
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  SERVER_ERROR = 'SERVER_ERROR'
}

/**
 * Error code to HTTP status mapping
 */
export const ErrorCodeStatusMap: Record<ErrorCode, number> = {
  [ErrorCode.VALIDATION_ERROR]: 400,
  [ErrorCode.UNAUTHORIZED]: 401,
  [ErrorCode.PERMISSION_DENIED]: 403,
  [ErrorCode.NOT_FOUND]: 404,
  [ErrorCode.METHOD_NOT_ALLOWED]: 405,
  [ErrorCode.CONFLICT]: 409,
  [ErrorCode.ORGANIZATION_MISMATCH]: 403,
  [ErrorCode.SOFT_DELETED]: 410,
  [ErrorCode.RATE_LIMIT_EXCEEDED]: 429,
  [ErrorCode.SERVER_ERROR]: 500
}

/**
 * Error code to user message mapping (i18n support)
 */
export const ErrorCodeMessages: Record<ErrorCode, string> = {
  [ErrorCode.VALIDATION_ERROR]: '请求数据验证失败',
  [ErrorCode.UNAUTHORIZED]: '未授权访问，请重新登录',
  [ErrorCode.PERMISSION_DENIED]: '权限不足',
  [ErrorCode.NOT_FOUND]: '请求的资源不存在',
  [ErrorCode.METHOD_NOT_ALLOWED]: '请求方法不允许',
  [ErrorCode.CONFLICT]: '数据冲突，请刷新后重试',
  [ErrorCode.ORGANIZATION_MISMATCH]: '组织不匹配',
  [ErrorCode.SOFT_DELETED]: '资源已被删除',
  [ErrorCode.RATE_LIMIT_EXCEEDED]: '请求过于频繁，请稍后再试',
  [ErrorCode.SERVER_ERROR]: '服务器错误，请稍后再试'
}
