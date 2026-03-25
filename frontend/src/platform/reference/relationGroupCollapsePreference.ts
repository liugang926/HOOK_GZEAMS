import {
  buildStorageKey,
  normalizeStorageSegment,
  readWithLegacyMigration,
  removeLegacyKey,
  resolveStorage,
  type StorageLike
} from '@/platform/reference/scopedStorage'

const PREF_PREFIX = 'gzeams:detail:related-groups:'

type PreferencePayload = {
  expanded: string[]
}

const normalize = (value: unknown): string => normalizeStorageSegment(value)

const normalizeExpandedGroups = (groups: unknown): string[] => {
  if (!Array.isArray(groups)) return []
  return Array.from(new Set(groups.map((group) => normalize(group)).filter(Boolean)))
}

const makeScopedKey = (objectCode: unknown, scopeId: unknown): string => {
  const object = normalize(objectCode)
  const scope = normalize(scopeId) || '_record'
  return buildStorageKey(PREF_PREFIX, object, scope)
}

const makeLegacyRecordKey = (objectCode: unknown): string => buildStorageKey(PREF_PREFIX, normalize(objectCode), '_record')

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
  scopeId: unknown,
  options?: { storage?: StorageLike | null }
): string[] | null => {
  const object = normalize(objectCode)
  if (!object) return null
  const storage = resolveStorage(options?.storage)
  if (!storage) return null
  const scopedKey = makeScopedKey(object, scopeId)
  const scope = normalize(scopeId)
  const legacyKey = scope && scope !== '_record' ? makeLegacyRecordKey(object) : undefined
  const raw = readWithLegacyMigration(storage, scopedKey, legacyKey)
  if (raw === null) return null
  return safeParseExpandedGroups(raw)
}

export const saveRelationGroupExpandedPreference = (
  objectCode: unknown,
  scopeId: unknown,
  expandedGroups: unknown[],
  options?: { storage?: StorageLike | null }
): void => {
  const object = normalize(objectCode)
  if (!object) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return

  const expanded = normalizeExpandedGroups(expandedGroups)
  const scopedKey = makeScopedKey(object, scopeId)
  const scope = normalize(scopeId)
  const legacyKey = scope && scope !== '_record' ? makeLegacyRecordKey(object) : undefined
  storage.setItem(scopedKey, JSON.stringify({ expanded }))
  removeLegacyKey(storage, scopedKey, legacyKey)
}

export const clearRelationGroupExpandedPreference = (
  objectCode: unknown,
  scopeId: unknown,
  options?: { storage?: StorageLike | null }
): void => {
  const object = normalize(objectCode)
  if (!object) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return
  const scopedKey = makeScopedKey(object, scopeId)
  const scope = normalize(scopeId)
  const legacyKey = scope && scope !== '_record' ? makeLegacyRecordKey(object) : undefined
  storage.removeItem(scopedKey)
  removeLegacyKey(storage, scopedKey, legacyKey)
}
