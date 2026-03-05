const PREF_PREFIX = 'gzeams:lookup:columns:'
const LAST_PROFILE_PREFIX = 'gzeams:lookup:last-profile:'

type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>
export type LookupColumnsProfile = 'standard' | 'compact' | 'custom'

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

const makeKey = (objectCode: unknown, preferenceKey?: unknown, userScope?: unknown): string => {
  const object = normalize(objectCode)
  const scope = normalize(preferenceKey) || '_default'
  const user = normalize(userScope) || 'anonymous'
  return `${PREF_PREFIX}${object}:${scope}:${user}`
}

const makeLastProfileKey = (objectCode: unknown, userScope?: unknown): string => {
  const object = normalize(objectCode)
  const user = normalize(userScope) || 'anonymous'
  return `${LAST_PROFILE_PREFIX}${object}:${user}`
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
  options?: { preferenceKey?: unknown; userScope?: unknown; storage?: StorageLike | null }
): LookupColumnsPreference => {
  const object = normalize(objectCode)
  if (!object) return { hidden: new Set<string>(), order: [], widths: {}, profile: 'standard' }
  const storage = resolveStorage(options?.storage)
  if (!storage) return { hidden: new Set<string>(), order: [], widths: {}, profile: 'standard' }
  const key = makeKey(object, options?.preferenceKey, options?.userScope)
  const raw = storage.getItem(key)
  return {
    hidden: new Set(safeParseHidden(raw)),
    order: safeParseOrder(raw),
    widths: safeParseWidths(raw),
    profile: safeParseProfile(raw)
  }
}

export const hasLookupColumnsPreference = (
  objectCode: unknown,
  options?: { preferenceKey?: unknown; userScope?: unknown; storage?: StorageLike | null }
): boolean => {
  const object = normalize(objectCode)
  if (!object) return false
  const storage = resolveStorage(options?.storage)
  if (!storage) return false
  return storage.getItem(makeKey(object, options?.preferenceKey, options?.userScope)) !== null
}

export const saveLookupColumnsPreference = (
  objectCode: unknown,
  preference: { hidden?: unknown[]; order?: unknown[]; widths?: unknown; profile?: unknown },
  options?: { preferenceKey?: unknown; userScope?: unknown; storage?: StorageLike | null }
): void => {
  const object = normalize(objectCode)
  if (!object) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return

  const hidden = Array.from(new Set((preference.hidden || []).map((item) => normalize(item)).filter(Boolean)))
  const order = Array.from(new Set((preference.order || []).map((item) => normalize(item)).filter(Boolean)))
  const widths = normalizeWidths(preference.widths)
  const profile = normalizeProfile(preference.profile)
  const key = makeKey(object, options?.preferenceKey, options?.userScope)

  if (hidden.length === 0 && order.length === 0 && Object.keys(widths).length === 0 && profile === 'standard') {
    storage.removeItem(key)
    return
  }
  storage.setItem(key, JSON.stringify({ hidden, order, widths, profile }))
}

export const loadLastLookupProfile = (
  objectCode: unknown,
  options?: { userScope?: unknown; storage?: StorageLike | null }
): LookupColumnsProfile => {
  const object = normalize(objectCode)
  if (!object) return 'standard'
  const storage = resolveStorage(options?.storage)
  if (!storage) return 'standard'
  const raw = storage.getItem(makeLastProfileKey(object, options?.userScope))
  return normalizeProfile(raw)
}

export const saveLastLookupProfile = (
  objectCode: unknown,
  profile: unknown,
  options?: { userScope?: unknown; storage?: StorageLike | null }
): void => {
  const object = normalize(objectCode)
  if (!object) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return
  const normalizedProfile = normalizeProfile(profile)
  storage.setItem(makeLastProfileKey(object, options?.userScope), normalizedProfile)
}

export const clearLookupColumnsPreference = (
  objectCode: unknown,
  options?: { preferenceKey?: unknown; userScope?: unknown; storage?: StorageLike | null }
): void => {
  const object = normalize(objectCode)
  if (!object) return
  const storage = resolveStorage(options?.storage)
  if (!storage) return
  storage.removeItem(makeKey(object, options?.preferenceKey, options?.userScope))
}

export const loadLookupHiddenColumns = (
  objectCode: unknown,
  options?: { preferenceKey?: unknown; userScope?: unknown; storage?: StorageLike | null }
): Set<string> => {
  return loadLookupColumnsPreference(objectCode, options).hidden
}

export const saveLookupHiddenColumns = (
  objectCode: unknown,
  hiddenColumns: unknown[],
  options?: { preferenceKey?: unknown; userScope?: unknown; storage?: StorageLike | null }
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
