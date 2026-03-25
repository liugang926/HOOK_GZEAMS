/**
 * getLocalizedLabel.ts
 *
 * Utility: resolve the best human-readable label from a field definition
 * that may carry multilingual variants (label_zh, label_en, etc.).
 *
 * Priority order for each locale:
 *   zh-CN  鈫?label_zh 鈫?label_zh_cn 鈫?label 鈫?name
 *   en-US  鈫?label_en 鈫?label_en_us 鈫?label 鈫?name
 *   other  鈫?label 鈫?name
 *
 * Usage (pure, no store dependency 鈥?works in any context):
 *   getLocalizedLabel(field, 'zh-CN')  // returns '璧勪骇鍚嶇О'
 *   getLocalizedLabel(field, 'en-US')  // returns 'Asset Name'
 *
 * The function also reads the current locale from localStorage as a
 * fallback when no locale is passed, so it works in non-reactive contexts
 * (e.g. export column definitions built outside Vue components).
 */

import { getStoredLocale } from '@/platform/i18n/localePreference'

export type LocaleCode = 'zh-CN' | 'en-US' | string

/** Map of locale code 鈫?ordered list of field keys to try */
const LABEL_KEY_MAP: Record<string, string[]> = {
    'zh-CN': ['labelZh', 'label_zh', 'labelZhCn', 'label_zh_cn', 'label', 'name', 'displayName'],
    'zh': ['labelZh', 'label_zh', 'label', 'name', 'displayName'],
    'en-US': ['labelEn', 'label_en', 'labelEnUs', 'label_en_us', 'label', 'name', 'displayName'],
    'en': ['labelEn', 'label_en', 'label', 'name', 'displayName'],
}

const DEFAULT_KEYS = ['label', 'name', 'displayName', 'title']

/**
 * Get the most appropriate display label for a field given the current locale.
 *
 * @param field   - Any object (FieldDefinition, raw API schema, etc.)
 * @param locale  - BCP-47 locale tag; falls back to localStorage['locale'] then 'zh-CN'
 */
export function getLocalizedLabel(field: Record<string, any>, locale?: LocaleCode): string {
    const resolvedLocale = locale || getStoredLocale()
    const keys =
        LABEL_KEY_MAP[resolvedLocale] ||
        LABEL_KEY_MAP[resolvedLocale.split('-')[0]] ||
        DEFAULT_KEYS

    for (const key of keys) {
        const val = field[key]
        if (val && typeof val === 'string' && val.trim()) return val.trim()
    }

    // Final fallback: code / field_name
    return field.code || field.fieldCode || field.field || field.field_name || ''
}

/**
 * Get the placeholder text for a field, locale-aware.
 */
export function getLocalizedPlaceholder(field: Record<string, any>, locale?: LocaleCode): string {
    const resolvedLocale = locale || getStoredLocale()

    if (resolvedLocale.startsWith('zh')) {
        return field.placeholderZh || field.placeholder_zh || field.placeholder || ''
    }
    return field.placeholderEn || field.placeholder_en || field.placeholder || ''
}

/**
 * Get the help text for a field, locale-aware.
 */
export function getLocalizedHelpText(field: Record<string, any>, locale?: LocaleCode): string {
    const resolvedLocale = locale || getStoredLocale()

    if (resolvedLocale.startsWith('zh')) {
        return field.helpTextZh || field.help_text_zh || field.helpText || field.description || ''
    }
    return field.helpTextEn || field.help_text_en || field.helpText || field.description || ''
}


