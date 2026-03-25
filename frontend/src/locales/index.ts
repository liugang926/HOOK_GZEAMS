import { createI18n } from 'vue-i18n'
import zhCN from './zh-CN'
import enUS from './en-US'
import { getStoredLocale, setStoredLocale } from '@/platform/i18n/localePreference'

export const SUPPORT_LOCALES = ['zh-CN', 'en-US'] as const
export type LocaleType = (typeof SUPPORT_LOCALES)[number]

export const normalizeLocale = (locale?: string | null): LocaleType => {
    if (locale === 'zh') return 'zh-CN'
    if (locale === 'en') return 'en-US'
    if (locale && SUPPORT_LOCALES.includes(locale as LocaleType)) return locale as LocaleType
    return 'zh-CN'
}

const initialLocale = normalizeLocale(getStoredLocale())
setStoredLocale(initialLocale)

const i18n = createI18n({
    legacy: false, // 使用 Composition API 模式
    locale: initialLocale,
    fallbackLocale: 'zh-CN',
    messages: {
        'zh-CN': zhCN,
        zh: zhCN,
        'en-US': enUS,
        en: enUS
    },
    globalInjection: true // 允许在模板中使用 $t
})

export default i18n

