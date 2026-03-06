import {
  buildStorageKey,
  normalizeStorageSegment,
  readWithLegacyMigration,
  removeLegacyKey,
  resolveStorage,
  type StorageLike
} from '@/platform/reference/scopedStorage'

const PREF_PREFIX = 'gzeams:lookup:columns:'
const LAST_PROFILE_PREFIX = 'gzeams:lookup:last-profile:'

export type LookupColumnsProfile = 'standard' | 'compact' | 'custom'
type LookupPreferenceOptions = {
  preferenceKey?: unknown
  userScope?: unknown
  scope?: unknown
  storage?: StorageLike | null
}

const normalize = (value: unknown): string => normalizeStorageSegment(value)

const makeKey = (
  objectCode: unknown,
  preferenceKey?: unknown,
  userScope?: unknown,
  contextScope?: unknown
): string => {
  const object = normalize(objectCode)
  const preference = normalize(preferenceKey) || '_default'
  const user = normalize(userScope) || 'anonymous'
  const pageScope = normalize(contextScope)
  if (!pageScope) return buildStorageKey(PREF_PREFIX, object, preference, user)
  return buildStorageKey(PREF_PREFIX, object, pageScope, preference, user)
}

const makeLegacyKey = (
  objectCode: unknown,
  preferenceKey?: unknown,
  userScope?: unknown
): string => {
  const object = normalize(objectCode)
  const preference = normalize(preferenceKey) || '_default'
  const user = normalize(userScope) || 'anonymous'
  return buildStorageKey(PREF_PREFIX, object, preference, user)
}

const makeLastProfileKey = (objectCode: unknown, userScope?: unknown, scope?: unknown): string => {
  const object = normalize(objectCode)
  const user = normalize(userScope) || 'anonymous'
  const pageScope = normalize(scope)
  if (!pageScope) return buildStorageKey(LAST_PROFILE_PREFIX, object, user)
  return buildStorageKey(LAST_PROFILE_PREFIX, object, pageScope, user)
}

const makeLegacyLastProfileKey = (objectCode: unknown, userScope?: unknown): string => {
  const object = normalize(objectCode)
  const user = normalize(userScope) || 'anonymous'
  return buildStorageKey(LAST_PROFILE_PREFIX, object, user)
}

const safeParseHidden = (raw: string | null): string[] => {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return []
    const hidden = (parsed as { hidden?: unknown }).hidden
    if (!Array.isArray(hidden)) return []
    return hidden.map((item) => normalize(item)).filter(Boolean)
  } catch {
    return []
  }
}

const safeParseOrder = (raw: string | null): string[] => {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return []
    const order = (parsed as { order?: unknown }).order
    if (!Array.isArray(order)) return []
    return order.map((item) => normalize(item)).filter(Boolean)
  } catch {
    return []
  }
}

const safeParseWidths = (raw: string | null): Record<string, number> => {
  if (!raw) return {}
  try {
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return {}
    const widths = (parsed as { widths?: unknown }).widths
    if (!widths || typeof widths !== 'object' || Array.isArray(widths)) return {}
    const out: Record<string, number> = {}
    for (const [key, value] of Object.entries(widths as Record<string, unknown>)) {
      const normalizedKey = normalize(key)
      const width = Number(value)
      if (!normalizedKey) continue
      if (!Number.isFinite(width) || width <= 0) continue
      out[normalizedKey] = Math.round(width)
    }
    return out
  } catch {
    return {}
  }
}

const safeParseProfile = (raw: string | null): LookupColumnsProfile => {
  if (!raw) return 'standard'
  try {
    const parsed = JSON.parse(raw)
    if (!parsed || typeof parsed !== 'object') return 'standard'
    const profile = normalize((parsed as { profile?: unknown }).profile).toLowerCase()
    if (profile === 'standard' || profile === 'compact' || profile === 'custom') {
      return profile
    }
    return 'standard'
  } catch {
    return 'standard'
  }
}

const normalizeProfile = (profile: unknown): LookupColumnsProfile => {
  const value = normalize(profile).toLowerCase()
  if (value === 'standard' || value === 'compact' || value === 'custom') {
    return value
  }
  return 'standard'
}

const normalizeWidths = (widths: unknown): Record<string, number> => {
  if (!widths || typeof widths !== 'object' || Array.isArray(widths)) return {}
  const out: Record<string, number> = {}
  for (const [key, value] of Object.entries(widths as Record<string, unknown>)) {
    const normalizedKey = normalize(key)
    const width = Number(value)
    if (!normalizedKey) continue
    if (!Number.isFinite(width) || width <= 0) continue
    out[normalizedKey] = Math.round(width)
  }
  return out
}

export type LookupColumnsPreference = {
  hidden: Set<string>
  order: string[]
  widths: Record<string, number>
  profile: LookupColumnsProfile
}

export const loadLookupColumnsPreference = (
  objectCode: unknown,
  options?: LookupPreferenceOptions
): LookupColumnsPreference => {
  const object = normalize(objectCode)
  if (!object) return { hidden: new Set<string>(), order: [], widths: {}, profile: 'standard' }
  const storage = resolveStorage(options?.storage)
  if (!storage) return { hidden: new Set<string>(), order: [], widths: {}, profile: 'standard' }
  const key = makeKey(object, options?.preferenceKey, options?.userScope, options?.scope)
  const scoped = normalize(options?.scope)
  const legacyKey = scoped ? makeLegacyKey(object, options?.preferenceKey, options?.userScope) : undefined
  const raw = readWithLegacyMigration(storage, key, legacyKey)
  return {
    hidden: new Set(safeParseHidden(raw)),
    order: safeParseOrder(raw),
    widths: safeParseWidths(raw),
    profile: safeParseProfile(raw)
  }
}

export const hasLookupColumnsPreference = (
  objectCode: unknown,
  options?: LookupPreferenceOptions
): boolean => {
  const object = normalize(objectCode)
  if (!object) return false
  const storage = resolveStorage(options?.storage)
  if (!storage) return false
  const scopedKey = makeKey(object, options?.preferenceKey, options?.userScope, options?.scope)
  if (storage.getItem(scopedKey) !== null) return true
  if (!normalize(options?.scope)) return false
  const legacyKey = makeLegacyKey(object, options?.preferenceKey, options?.userScope)
  return storage.getItem(legacyKey) !== null
}

export const saveLookupColumnsPreference = (
  objectCode: unknown,
  preference: { hidden?: unknown[]; order?: unknown[]; widths?: unknown; profile?: unknown },
  options?: LookupPreferenceOptions
): void => {
  const object = normalize(objectCode)
  if (!object) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return

  const hidden = Array.from(new Set((preference.hidden || []).map((item) => normalize(item)).filter(Boolean)))
  const order = Array.from(new Set((preference.order || []).map((item) => normalize(item)).filter(Boolean)))
  const widths = normalizeWidths(preference.widths)
  const profile = normalizeProfile(preference.profile)
  const key = makeKey(object, options?.preferenceKey, options?.userScope, options?.scope)
  const scoped = normalize(options?.scope)
  const legacyKey = scoped ? makeLegacyKey(object, options?.preferenceKey, options?.userScope) : undefined

  if (hidden.length === 0 && order.length === 0 && Object.keys(widths).length === 0 && profile === 'standard') {
    storage.removeItem(key)
    removeLegacyKey(storage, key, legacyKey)
    return
  }
  storage.setItem(key, JSON.stringify({ hidden, order, widths, profile }))
  removeLegacyKey(storage, key, legacyKey)
}

export const loadLastLookupProfile = (
  objectCode: unknown,
  options?: { userScope?: unknown; scope?: unknown; storage?: StorageLike | null }
): LookupColumnsProfile => {
  const object = normalize(objectCode)
  if (!object) return 'standard'
  const storage = resolveStorage(options?.storage)
  if (!storage) return 'standard'
  const key = makeLastProfileKey(object, options?.userScope, options?.scope)
  const scoped = normalize(options?.scope)
  const legacyKey = scoped ? makeLegacyLastProfileKey(object, options?.userScope) : undefined
  const raw = readWithLegacyMigration(storage, key, legacyKey)
  return normalizeProfile(raw)
}

export const saveLastLookupProfile = (
  objectCode: unknown,
  profile: unknown,
  options?: { userScope?: unknown; scope?: unknown; storage?: StorageLike | null }
): void => {
  const object = normalize(objectCode)
  if (!object) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return
  const normalizedProfile = normalizeProfile(profile)
  const scopedKey = makeLastProfileKey(object, options?.userScope, options?.scope)
  storage.setItem(scopedKey, normalizedProfile)
  const legacyKey = normalize(options?.scope) ? makeLegacyLastProfileKey(object, options?.userScope) : undefined
  removeLegacyKey(storage, scopedKey, legacyKey)
}

export const clearLookupColumnsPreference = (
  objectCode: unknown,
  options?: LookupPreferenceOptions
): void => {
  const object = normalize(objectCode)
  if (!object) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return
  const key = makeKey(object, options?.preferenceKey, options?.userScope, options?.scope)
  const legacyKey = normalize(options?.scope) ? makeLegacyKey(object, options?.preferenceKey, options?.userScope) : undefined
  storage.removeItem(key)
  removeLegacyKey(storage, key, legacyKey)
}

export const loadLookupHiddenColumns = (
  objectCode: unknown,
  options?: LookupPreferenceOptions
): Set<string> => {
  return loadLookupColumnsPreference(objectCode, options).hidden
}

export const saveLookupHiddenColumns = (
  objectCode: unknown,
  hiddenColumns: unknown[],
  options?: LookupPreferenceOptions
): void => {
  const current = loadLookupColumnsPreference(objectCode, options)
  saveLookupColumnsPreference(
    objectCode,
    {
      hidden: hiddenColumns,
      order: current.order,
      widths: current.widths,
      profile: current.profile
    },
    options
  )
}
