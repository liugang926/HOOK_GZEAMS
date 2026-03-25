import type { MenuManagementCategory, MenuManagementItem } from '@/api/system'
import { normalizeIconList, resolveIcon } from './icons'
import { MANAGEMENT_COPY } from './copy'

export type LocaleKey = 'zh-CN' | 'en-US'
export type LocaleNames = Record<string, string>

export type EditableCategory = MenuManagementCategory & {
  originalCode: string
  localeNames: LocaleNames
}

export const CATEGORY_EDIT_LOCALES: LocaleKey[] = ['zh-CN', 'en-US']

export const BUILTIN_CATEGORY_LABELS: Record<LocaleKey, Record<string, string>> = {
  'zh-CN': {
    asset_master: '资产主数据',
    asset_operation: '资产业务',
    lifecycle: '资产生命周期',
    consumable: '耗材管理',
    inventory: '盘点管理',
    finance: '财务管理',
    organization: '组织管理',
    workflow: '工作流',
    system: '系统管理',
    reports: '报表中心',
    other: '其他',
  },
  'en-US': {
    asset_master: 'Asset Master',
    asset_operation: 'Asset Operation',
    lifecycle: 'Lifecycle',
    consumable: 'Consumables',
    inventory: 'Inventory',
    finance: 'Finance',
    organization: 'Organization',
    workflow: 'Workflow',
    system: 'System',
    reports: 'Reports',
    other: 'Other',
  },
}


export const sortByOrder = <T extends { order: number; code: string }>(collection: T[]) =>
  [...collection].sort((a, b) => a.order - b.order || a.code.localeCompare(b.code))

export const normalizeOrder = <T extends { order: number }>(collection: T[]) => {
  collection.forEach((item, index) => {
    item.order = (index + 1) * 10
  })
}

export const humanizeCode = (code: string) =>
  String(code || '').replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase()).trim()

export const normalizeLocaleNames = (value: unknown): LocaleNames => {
  if (!value || typeof value !== 'object') return {}
  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>)
      .map(([locale, text]) => [String(locale), String(text || '').trim()])
      .filter(([, text]) => Boolean(text)),
  )
}

export const getCategoryLocaleName = (
  category: Pick<EditableCategory, 'localeNames' | 'isDefault' | 'code' | 'name'>,
  locale: LocaleKey,
) => {
  const directName = String(category.localeNames?.[locale] || '').trim()
  if (directName) return directName

  if (category.isDefault) {
    const builtinName = BUILTIN_CATEGORY_LABELS[locale][category.code]
    if (builtinName) return builtinName
  }

  return ''
}

export const getCategoryFallbackName = (
  category: Pick<EditableCategory, 'localeNames' | 'isDefault' | 'code' | 'name'>,
) =>
  getCategoryLocaleName(category, 'en-US') ||
  getCategoryLocaleName(category, 'zh-CN') ||
  String(category.name || '').trim() ||
  category.code

export const syncCategoryFallbackName = (category: EditableCategory) => {
  category.name = getCategoryFallbackName(category)
  return category
}

export const normalizeCategoryLocaleNames = (
  category: MenuManagementCategory,
  currentLocale: LocaleKey,
): LocaleNames => {
  const localeNames = normalizeLocaleNames(category.localeNames)

  if (category.isDefault) {
    localeNames['zh-CN'] ||= BUILTIN_CATEGORY_LABELS['zh-CN'][category.code] || ''
    localeNames['en-US'] ||= BUILTIN_CATEGORY_LABELS['en-US'][category.code] || humanizeCode(category.code)
  }

  if (!localeNames[currentLocale] && category.name) {
    localeNames[currentLocale] = String(category.name).trim()
  }

  localeNames['en-US'] ||= humanizeCode(category.code)
  return localeNames
}

export const hydrateCategory = (
  category: MenuManagementCategory,
  currentLocale: LocaleKey,
): EditableCategory => ({
  ...category,
  originalCode: category.code,
  localeNames: normalizeCategoryLocaleNames(category, currentLocale),
  isLocked: category.isLocked ?? false,
  supportsDelete: category.supportsDelete ?? true,
  name: category.name,
})

export const normalizeLanguageCodes = (payload: unknown) => {
  const source = Array.isArray(payload)
    ? payload
    : Array.isArray((payload as { data?: unknown[] } | undefined)?.data)
      ? ((payload as { data: unknown[] }).data)
      : []

  return Array.from(
    new Set(
      source
        .map((language) => String((language as { code?: string })?.code || '').trim())
        .filter(Boolean),
    ),
  )
}

export const getItemIdentity = (item: Pick<MenuManagementItem, 'sourceType' | 'sourceCode' | 'code'>) =>
  `${item.sourceType}:${item.sourceCode || item.code}`

export { MANAGEMENT_COPY, resolveIcon, normalizeIconList }
