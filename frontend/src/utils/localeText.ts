import { getStoredLocale } from '@/platform/i18n/localePreference'

type LocaleType = 'zh-CN' | 'en-US'

const normalizeLocale = (locale?: string | null): LocaleType => {
  if (!locale) return 'zh-CN'
  if (locale === 'zh' || locale.toLowerCase().startsWith('zh')) return 'zh-CN'
  if (locale === 'en' || locale.toLowerCase().startsWith('en')) return 'en-US'
  if (locale === 'zh-CN' || locale === 'en-US') return locale
  return 'zh-CN'
}

type AnyRecord = Record<string, any>

const DEFAULT_TEXT_KEYS = [
  'label',
  'name',
  'title',
  'placeholder',
  'description',
  'helpText',
  'emptyText'
]

const toRecord = (value: any): AnyRecord => {
  return value && typeof value === 'object' ? value : {}
}

const ucfirst = (value: string): string => {
  if (!value) return value
  return `${value.charAt(0).toUpperCase()}${value.slice(1)}`
}

const localeAliases = (locale: LocaleType): string[] => {
  const normalized = normalizeLocale(locale)
  const common = normalized.toLowerCase().replace('-', '_')

  if (normalized === 'zh-CN') {
    return [common, 'zh_cn', 'zhcn', 'zh']
  }
  if (normalized === 'en-US') {
    return [common, 'en_us', 'enus', 'en']
  }
  return [common, common.replace('_', '')]
}

const candidateKeys = (baseKey: string, locale: LocaleType): string[] => {
  const aliases = localeAliases(locale)
  const keys: string[] = []

  for (const suffix of aliases) {
    keys.push(`${baseKey}_${suffix}`)
    keys.push(`${baseKey}${ucfirst(suffix.replace('_', ''))}`)
  }

  if (baseKey === 'label') {
    for (const suffix of aliases) {
      keys.push(`name_${suffix}`)
      keys.push(`name${ucfirst(suffix.replace('_', ''))}`)
    }
  }

  return [...new Set(keys)]
}

const hasOwn = (obj: AnyRecord, key: string): boolean => {
  return Object.prototype.hasOwnProperty.call(obj, key)
}

const getCurrentLocale = (): LocaleType => {
  if (typeof window === 'undefined') return 'zh-CN'
  return normalizeLocale(getStoredLocale())
}

export const resolveLocalizedValue = (
  source: AnyRecord,
  baseKey: string,
  locale: LocaleType = getCurrentLocale()
): string | undefined => {
  const value = source[baseKey]
  if (value && typeof value === 'object') {
    const localeMap = toRecord(value)
    const aliases = localeAliases(locale)
    for (const alias of aliases) {
      if (typeof localeMap[alias] === 'string' && localeMap[alias].trim()) {
        return localeMap[alias]
      }
    }
  }

  for (const key of candidateKeys(baseKey, locale)) {
    if (hasOwn(source, key) && typeof source[key] === 'string' && source[key].trim()) {
      return source[key]
    }
  }

  if (typeof value === 'string' && value.trim()) return value
  return undefined
}

export const localizeMultilingualObject = <T extends AnyRecord>(
  source: T,
  keys: string[] = DEFAULT_TEXT_KEYS,
  locale: LocaleType = getCurrentLocale()
): T => {
  const target: AnyRecord = { ...source }

  for (const key of keys) {
    const localized = resolveLocalizedValue(source, key, locale)
    if (localized !== undefined) {
      target[key] = localized
    }
  }

  return target as T
}

export const localizeMultilingualTree = <T>(
  input: T,
  keys: string[] = DEFAULT_TEXT_KEYS,
  locale: LocaleType = getCurrentLocale()
): T => {
  if (Array.isArray(input)) {
    return input.map((item) => localizeMultilingualTree(item, keys, locale)) as T
  }

  if (!input || typeof input !== 'object') {
    return input
  }

  const source = input as AnyRecord
  const localized = localizeMultilingualObject(source, keys, locale)

  for (const [key, value] of Object.entries(localized)) {
    if (value && typeof value === 'object') {
      localized[key] = localizeMultilingualTree(value, keys, locale)
    }
  }

  return localized as T
}

