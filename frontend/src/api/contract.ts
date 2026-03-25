import type { ApiResponse, PaginatedResponse } from '@/types/api'
import { camelToSnake, snakeToCamel } from '@/utils/case'

export interface ApiActionResult<T = any> {
  success: boolean
  message?: string
  data?: T
  error?: unknown
}

export interface UnsupportedApiError extends Error {
  code: 'UNSUPPORTED_API'
  endpoint: string
  feature: string
}

interface NormalizeParamsOptions {
  aliases?: Record<string, string>
  preserveKeys?: string[]
}

const isPlainObject = (value: unknown): value is Record<string, any> => {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}

const isAxiosLikeResponse = (value: unknown): value is { data: any } => {
  if (!isPlainObject(value)) return false
  return 'data' in value && ('status' in value || 'headers' in value || 'config' in value)
}

const isApiEnvelope = (value: unknown): value is ApiResponse<any> => {
  return isPlainObject(value) && typeof value.success === 'boolean'
}

const extractPayload = (raw: unknown): unknown => {
  if (isAxiosLikeResponse(raw)) return raw.data
  return raw
}

export const normalizeQueryParams = (
  params?: Record<string, any>,
  options?: NormalizeParamsOptions
): Record<string, any> => {
  if (!params) return {}

  const aliases = options?.aliases || {}
  const preserved = new Set(options?.preserveKeys || [])
  const normalized: Record<string, any> = {}

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return
    const aliasedKey = aliases[key]
    const targetKey = aliasedKey || (preserved.has(key) ? key : camelToSnake(key))
    normalized[targetKey] = value
  })

  return normalized
}

export const toActionResult = <T = any>(raw: unknown): ApiActionResult<T> => {
  const payload = extractPayload(raw)
  if (isApiEnvelope(payload)) {
    return {
      success: payload.success,
      message: payload.message,
      data: payload.data as T,
      error: payload.error,
    }
  }

  return {
    success: true,
    data: payload as T,
  }
}

export const toData = <T = any>(raw: unknown, fallback?: T): T => {
  const payload = extractPayload(raw)

  if (isApiEnvelope(payload)) {
    if (payload.data === undefined && fallback !== undefined) return fallback
    return payload.data as T
  }

  if (payload === undefined && fallback !== undefined) return fallback
  return payload as T
}

export const toPaginated = <T = any>(raw: unknown): PaginatedResponse<T> => {
  const payload = toData<any>(raw, {})

  if (Array.isArray(payload)) {
    return {
      count: payload.length,
      next: null,
      previous: null,
      results: payload,
    }
  }

  if (isPlainObject(payload) && Array.isArray(payload.results)) {
    return {
      count: Number(payload.count ?? payload.results.length ?? 0),
      next: payload.next ?? null,
      previous: payload.previous ?? null,
      results: payload.results,
    }
  }

  if (isPlainObject(payload) && Array.isArray(payload.items)) {
    return {
      count: Number(payload.total ?? payload.count ?? payload.items.length ?? 0),
      next: payload.next ?? null,
      previous: payload.previous ?? null,
      results: payload.items,
    }
  }

  return {
    count: 0,
    next: null,
    previous: null,
    results: [],
  }
}

export const toCamelDeep = <T = any>(value: T): T => {
  if (Array.isArray(value)) {
    return value.map((item) => toCamelDeep(item)) as T
  }

  if (isPlainObject(value)) {
    const output: Record<string, any> = {}
    Object.entries(value).forEach(([key, val]) => {
      output[snakeToCamel(key)] = toCamelDeep(val)
    })
    return output as T
  }

  return value
}

export const rejectUnsupportedApi = <T = never>(
  feature: string,
  endpoint: string
): Promise<T> => {
  const error = new Error(
    `Feature "${feature}" is not available because backend endpoint "${endpoint}" is not implemented yet.`
  ) as UnsupportedApiError
  error.code = 'UNSUPPORTED_API'
  error.feature = feature
  error.endpoint = endpoint
  return Promise.reject(error)
}
