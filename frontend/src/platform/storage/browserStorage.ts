export type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>

const normalize = (value: unknown): string => String(value || '').trim()

export const resolveLocalStorage = (): StorageLike | null => {
  if (typeof globalThis === 'undefined') return null
  const storage = (globalThis as { localStorage?: Storage }).localStorage
  if (!storage) return null
  try {
    storage.getItem('__probe__')
    return storage
  } catch {
    return null
  }
}

export const readStorageString = (key: unknown, fallback = ''): string => {
  const storage = resolveLocalStorage()
  if (!storage) return fallback
  return normalize(storage.getItem(normalize(key))) || fallback
}

export const writeStorageString = (key: unknown, value: unknown): void => {
  const storage = resolveLocalStorage()
  if (!storage) return
  const normalizedKey = normalize(key)
  const normalizedValue = normalize(value)
  if (!normalizedKey || !normalizedValue) return
  storage.setItem(normalizedKey, normalizedValue)
}

export const removeStorageKey = (key: unknown): void => {
  const storage = resolveLocalStorage()
  if (!storage) return
  const normalizedKey = normalize(key)
  if (!normalizedKey) return
  storage.removeItem(normalizedKey)
}

export const readStorageJson = <T>(key: unknown, fallback: T): T => {
  const raw = readStorageString(key)
  if (!raw) return fallback
  try {
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

export const writeStorageJson = (key: unknown, value: unknown): void => {
  const storage = resolveLocalStorage()
  if (!storage) return
  const normalizedKey = normalize(key)
  if (!normalizedKey) return
  try {
    storage.setItem(normalizedKey, JSON.stringify(value))
  } catch {
    // Ignore write failures for optional client-side preferences.
  }
}
