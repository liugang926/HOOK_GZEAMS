const PREF_PREFIX = 'gzeams:detail:related-groups:'

type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>

type PreferencePayload = {
  expanded: string[]
}

const normalize = (value: unknown): string => String(value || '').trim()

const resolveStorage = (storage?: StorageLike | null): StorageLike | null => {
  if (storage) return storage
  if (typeof window === 'undefined') return null
  try {
    return window.localStorage
  } catch {
    return null
  }
}

const normalizeExpandedGroups = (groups: unknown): string[] => {
  if (!Array.isArray(groups)) return []
  return Array.from(new Set(groups.map((group) => normalize(group)).filter(Boolean)))
}

const makeKey = (objectCode: unknown, recordId: unknown): string => {
  const object = normalize(objectCode)
  const record = normalize(recordId) || '_record'
  return `${PREF_PREFIX}${object}:${record}`
}

const safeParseExpandedGroups = (raw: string | null): string[] => {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return []
    return normalizeExpandedGroups((parsed as PreferencePayload).expanded)
  } catch {
    return []
  }
}

export const loadRelationGroupExpandedPreference = (
  objectCode: unknown,
  recordId: unknown,
  options?: { storage?: StorageLike | null }
): string[] | null => {
  const object = normalize(objectCode)
  if (!object) return null
  const storage = resolveStorage(options?.storage)
  if (!storage) return null
  const raw = storage.getItem(makeKey(object, recordId))
  if (raw === null) return null
  return safeParseExpandedGroups(raw)
}

export const saveRelationGroupExpandedPreference = (
  objectCode: unknown,
  recordId: unknown,
  expandedGroups: unknown[],
  options?: { storage?: StorageLike | null }
): void => {
  const object = normalize(objectCode)
  if (!object) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return

  const expanded = normalizeExpandedGroups(expandedGroups)
  storage.setItem(makeKey(object, recordId), JSON.stringify({ expanded }))
}

export const clearRelationGroupExpandedPreference = (
  objectCode: unknown,
  recordId: unknown,
  options?: { storage?: StorageLike | null }
): void => {
  const object = normalize(objectCode)
  if (!object) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return
  storage.removeItem(makeKey(object, recordId))
}

