import {
  readStorageString,
  removeStorageKey,
  writeStorageString
} from '@/platform/storage/browserStorage'

export const LOCALE_STORAGE_KEY = 'locale'
export const LOCALE_SOURCE_STORAGE_KEY = 'locale_source'

export type LocaleSource = 'local' | 'profile'

export const getStoredLocale = (fallback = 'zh-CN'): string => {
  return readStorageString(LOCALE_STORAGE_KEY, fallback)
}

export const setStoredLocale = (locale: unknown): void => {
  writeStorageString(LOCALE_STORAGE_KEY, locale)
}

export const getStoredLocaleSource = (): LocaleSource | '' => {
  const source = readStorageString(LOCALE_SOURCE_STORAGE_KEY)
  return source === 'local' || source === 'profile' ? source : ''
}

export const setStoredLocaleSource = (source: LocaleSource): void => {
  writeStorageString(LOCALE_SOURCE_STORAGE_KEY, source)
}

export const clearStoredLocaleSource = (): void => {
  removeStorageKey(LOCALE_SOURCE_STORAGE_KEY)
}
