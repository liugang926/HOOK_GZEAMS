import {
  buildStorageKey,
  normalizeStorageSegment,
  readWithLegacyMigration,
  removeLegacyKey,
  resolveStorage,
  type StorageLike
} from '@/platform/reference/scopedStorage'

const RECENT_PREFIX = 'gzeams:lookup:recent:'
const DEFAULT_LIMIT = 6
const MAX_LIMIT = 20

const normalizeObjectCode = (raw: unknown): string => {
  return normalizeStorageSegment(raw)
}

const normalizeId = (raw: unknown): string => {
  return normalizeStorageSegment(raw)
}

const normalizeScope = (raw: unknown): string => {
  return normalizeStorageSegment(raw)
}

const makeKey = (objectCode: string, scope?: unknown): string => {
  const normalizedScope = normalizeScope(scope)
  if (!normalizedScope) return buildStorageKey(RECENT_PREFIX, objectCode)
  return buildStorageKey(RECENT_PREFIX, objectCode, normalizedScope)
}

const makeLegacyKey = (objectCode: string): string => buildStorageKey(RECENT_PREFIX, objectCode)

const safeParse = (raw: string | null): string[] => {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed
      .map((id) => normalizeId(id))
      .filter(Boolean)
  } catch {
    return []
  }
}

const clampLimit = (limit: number | undefined): number => {
  const normalized = Number(limit || DEFAULT_LIMIT)
  if (!Number.isFinite(normalized) || normalized <= 0) return DEFAULT_LIMIT
  return Math.min(Math.max(Math.round(normalized), 1), MAX_LIMIT)
}

export const loadRecentReferenceIds = (
  objectCode: unknown,
  options?: { limit?: number; scope?: unknown; storage?: StorageLike | null }
): string[] => {
  const code = normalizeObjectCode(objectCode)
  if (!code) return []
  const storage = resolveStorage(options?.storage)
  if (!storage) return []

  const scopedKey = makeKey(code, options?.scope)
  const scoped = normalizeScope(options?.scope)
  const legacyKey = scoped ? makeLegacyKey(code) : undefined
  const raw = readWithLegacyMigration(storage, scopedKey, legacyKey)
  const ids = safeParse(raw)
  const limit = clampLimit(options?.limit)
  return ids.slice(0, limit)
}

export const saveRecentReferenceIds = (
  objectCode: unknown,
  ids: unknown[],
  options?: { limit?: number; scope?: unknown; storage?: StorageLike | null }
): void => {
  const code = normalizeObjectCode(objectCode)
  if (!code) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return

  const incoming = (ids || [])
    .map((id) => normalizeId(id))
    .filter(Boolean)
  if (incoming.length === 0) return

  const scopedKey = makeKey(code, options?.scope)
  const scoped = normalizeScope(options?.scope)
  const legacyKey = scoped ? makeLegacyKey(code) : undefined
  const current = safeParse(readWithLegacyMigration(storage, scopedKey, legacyKey))
  const merged = Array.from(new Set([...incoming, ...current]))
  const limit = clampLimit(options?.limit)
  storage.setItem(scopedKey, JSON.stringify(merged.slice(0, limit)))
  removeLegacyKey(storage, scopedKey, legacyKey)
}

export const clearRecentReferenceIds = (
  objectCode: unknown,
  options?: { scope?: unknown; storage?: StorageLike | null }
): void => {
  const code = normalizeObjectCode(objectCode)
  if (!code) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return
  const scopedKey = makeKey(code, options?.scope)
  const legacyKey = normalizeScope(options?.scope) ? makeLegacyKey(code) : undefined
  storage.removeItem(scopedKey)
  removeLegacyKey(storage, scopedKey, legacyKey)
}
