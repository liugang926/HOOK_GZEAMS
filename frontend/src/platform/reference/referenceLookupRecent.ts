const RECENT_PREFIX = 'gzeams:lookup:recent:'
const DEFAULT_LIMIT = 6
const MAX_LIMIT = 20

type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>

const normalizeObjectCode = (raw: unknown): string => {
  return String(raw || '').trim()
}

const normalizeId = (raw: unknown): string => {
  return String(raw || '').trim()
}

const resolveStorage = (storage?: StorageLike | null): StorageLike | null => {
  if (storage) return storage
  if (typeof window === 'undefined') return null
  try {
    return window.localStorage
  } catch {
    return null
  }
}

const makeKey = (objectCode: string): string => `${RECENT_PREFIX}${objectCode}`

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
  options?: { limit?: number; storage?: StorageLike | null }
): string[] => {
  const code = normalizeObjectCode(objectCode)
  if (!code) return []
  const storage = resolveStorage(options?.storage)
  if (!storage) return []

  const ids = safeParse(storage.getItem(makeKey(code)))
  const limit = clampLimit(options?.limit)
  return ids.slice(0, limit)
}

export const saveRecentReferenceIds = (
  objectCode: unknown,
  ids: unknown[],
  options?: { limit?: number; storage?: StorageLike | null }
): void => {
  const code = normalizeObjectCode(objectCode)
  if (!code) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return

  const incoming = (ids || [])
    .map((id) => normalizeId(id))
    .filter(Boolean)
  if (incoming.length === 0) return

  const current = safeParse(storage.getItem(makeKey(code)))
  const merged = Array.from(new Set([...incoming, ...current]))
  const limit = clampLimit(options?.limit)
  storage.setItem(makeKey(code), JSON.stringify(merged.slice(0, limit)))
}

export const clearRecentReferenceIds = (
  objectCode: unknown,
  options?: { storage?: StorageLike | null }
): void => {
  const code = normalizeObjectCode(objectCode)
  if (!code) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return
  storage.removeItem(makeKey(code))
}

