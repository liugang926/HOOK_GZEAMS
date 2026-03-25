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
 * Error code to i18n key mapping
 */
export const ErrorCodeMessages: Record<ErrorCode, string> = {
  [ErrorCode.VALIDATION_ERROR]: 'common.messages.badRequest',
  [ErrorCode.UNAUTHORIZED]: 'common.messages.sessionExpired',
  [ErrorCode.PERMISSION_DENIED]: 'common.messages.permissionDenied',
  [ErrorCode.NOT_FOUND]: 'common.messages.resourceNotFound',
  [ErrorCode.METHOD_NOT_ALLOWED]: 'common.messages.operationFailed',
  [ErrorCode.CONFLICT]: 'common.messages.operationFailed',
  [ErrorCode.ORGANIZATION_MISMATCH]: 'common.messages.operationFailed',
  [ErrorCode.SOFT_DELETED]: 'common.messages.resourceGone',
  [ErrorCode.RATE_LIMIT_EXCEEDED]: 'common.messages.tooManyRequests',
  [ErrorCode.SERVER_ERROR]: 'common.messages.serverError'
}
