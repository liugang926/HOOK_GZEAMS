import type { PaginatedResponse } from '@/types/api'

export type UnknownRecord = Record<string, unknown>

export interface NormalizedListPayload<T> extends PaginatedResponse<T> {
  statistics?: UnknownRecord
  unreadCount?: number
}

export const isRecord = (value: unknown): value is UnknownRecord => (
  value !== null && typeof value === 'object' && !Array.isArray(value)
)

const getCandidateValue = (
  record: UnknownRecord | undefined,
  keys: readonly string[]
): unknown => {
  if (!record) {
    return undefined
  }

  for (const key of keys) {
    const value = record[key]
    if (value !== undefined) {
      return value
    }
  }

  return undefined
}

export const readString = (
  record: UnknownRecord | undefined,
  keys: readonly string[]
): string | undefined => {
  const value = getCandidateValue(record, keys)
  if (typeof value === 'string') {
    return value
  }
  if (typeof value === 'number') {
    return String(value)
  }
  return undefined
}

export const readNullableString = (
  record: UnknownRecord | undefined,
  keys: readonly string[]
): string | null | undefined => {
  const value = getCandidateValue(record, keys)
  if (value === null) {
    return null
  }
  return readString(record, keys)
}

export const readNumber = (
  record: UnknownRecord | undefined,
  keys: readonly string[]
): number | undefined => {
  const value = getCandidateValue(record, keys)
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  if (typeof value === 'string') {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : undefined
  }
  return undefined
}

export const readRecord = (
  record: UnknownRecord | undefined,
  keys: readonly string[]
): UnknownRecord | undefined => {
  const value = getCandidateValue(record, keys)
  return isRecord(value) ? value : undefined
}

export const readArray = <T = unknown>(
  record: UnknownRecord | undefined,
  keys: readonly string[]
): T[] => {
  const value = getCandidateValue(record, keys)
  return Array.isArray(value) ? (value as T[]) : []
}

interface NormalizeListPayloadOptions {
  countKeys?: readonly string[]
  resultKeys?: readonly string[]
  statisticsKeys?: readonly string[]
  unreadCountKeys?: readonly string[]
}

export const normalizeListPayload = <T>(
  payload: unknown,
  mapper: (item: UnknownRecord) => T,
  options: NormalizeListPayloadOptions = {}
): NormalizedListPayload<T> => {
  const root = isRecord(payload) ? payload : {}
  const data = readRecord(root, ['data'])
  const resultKeys = options.resultKeys ?? ['results', 'items']
  const rawResults = readArray(root, resultKeys)
  const nestedResults = readArray(data, resultKeys)
  const sourceResults = rawResults.length > 0 ? rawResults : nestedResults
  const results = sourceResults.flatMap((item) => (isRecord(item) ? [mapper(item)] : []))
  const countKeys = options.countKeys ?? ['count', 'total']
  const count = readNumber(root, countKeys) ?? readNumber(data, countKeys) ?? results.length
  const next = readNullableString(root, ['next']) ?? readNullableString(data, ['next']) ?? null
  const previous = readNullableString(root, ['previous']) ?? readNullableString(data, ['previous']) ?? null
  const statisticsKeys = options.statisticsKeys ?? ['statistics']
  const statistics = readRecord(root, statisticsKeys) ?? readRecord(data, statisticsKeys)
  const unreadCountKeys = options.unreadCountKeys ?? ['unreadCount', 'unread_count']
  const unreadCount = readNumber(root, unreadCountKeys) ?? readNumber(data, unreadCountKeys)

  return {
    count,
    next,
    previous,
    results,
    ...(statistics ? { statistics } : {}),
    ...(unreadCount !== undefined ? { unreadCount } : {})
  }
}
