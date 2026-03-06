export type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>

export const normalizeStorageSegment = (value: unknown): string => String(value || '').trim()

export const resolveStorage = (storage?: StorageLike | null): StorageLike | null => {
  if (storage) return storage
  if (typeof window === 'undefined') return null
  try {
    return window.localStorage
  } catch {
    return null
  }
}

export const buildStorageKey = (prefix: string, ...segments: unknown[]): string => {
  const normalized = segments.map((segment) => normalizeStorageSegment(segment))
  return `${prefix}${normalized.join(':')}`
}

/**
 * Reads scoped value and performs one-time migration from legacy key when needed.
 */
export const readWithLegacyMigration = (
  storage: StorageLike,
  scopedKey: string,
  legacyKey?: string
): string | null => {
  const raw = storage.getItem(scopedKey)
  if (raw !== null) return raw

  if (!legacyKey || legacyKey === scopedKey) return null
  const legacyRaw = storage.getItem(legacyKey)
  if (legacyRaw === null) return null

  storage.setItem(scopedKey, legacyRaw)
  storage.removeItem(legacyKey)
  return legacyRaw
}

export const removeLegacyKey = (storage: StorageLike, scopedKey: string, legacyKey?: string): void => {
  if (!legacyKey || legacyKey === scopedKey) return
  storage.removeItem(legacyKey)
}
