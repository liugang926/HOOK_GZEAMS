import { defineStore } from 'pinia'
import { ref, watch, computed } from 'vue'
import i18n, { normalizeLocale, type LocaleType, SUPPORT_LOCALES } from '@/locales'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import { languageApi, type Language } from '@/api/translations'
import { getStoredLocale, setStoredLocale } from '@/platform/i18n/localePreference'

const ELEMENT_LOCALES: Record<string, typeof zhCn> = {
    'zh-CN': zhCn,
    'zh': zhCn,
    'en-US': en,
    'en': en,
    'ja-JP': zhCn, // Fallback to zh-CN for unsupported locales in Element Plus
    'ja': zhCn
}

export const useLocaleStore = defineStore('locale', () => {
    const currentLocale = ref<LocaleType>(normalizeLocale(getStoredLocale()))
    const availableLanguages = ref<Language[]>([])
    const languagesLoaded = ref(false)

    const elementLocale = computed(() => ELEMENT_LOCALES[currentLocale.value] || zhCn)

    // Load available languages from API
    const loadLanguages = async () => {
        try {
            const response = await languageApi.getActive()
            const raw = response as unknown
            const payload = (
                raw && typeof raw === 'object' && 'data' in (raw as Record<string, unknown>)
                    ? (raw as Record<string, unknown>).data
                    : raw
            ) as unknown

            if (Array.isArray(payload)) {
                availableLanguages.value = payload as Language[]
            } else if (
                payload &&
                typeof payload === 'object' &&
                'data' in (payload as Record<string, unknown>) &&
                Array.isArray((payload as Record<string, unknown>).data)
            ) {
                availableLanguages.value = (payload as { data: Language[] }).data
            } else {
                availableLanguages.value = []
            }
            languagesLoaded.value = true
        } catch (error: unknown) {
            console.warn('Failed to load languages from API, using fallback:', error)
            // Fallback to static list
            availableLanguages.value = [
                { id: '', code: 'zh-CN', name: 'zh-CN', nativeName: 'zh-CN', flagEmoji: '🇨🇳', isActive: true, isDefault: true, sortOrder: 0 },
                { id: '', code: 'en-US', name: 'en-US', nativeName: 'en-US', flagEmoji: '🇺🇸', isActive: true, isDefault: false, sortOrder: 1 }
            ]
            languagesLoaded.value = true
        }
    }

    const setLocale = (locale: LocaleType) => {
        currentLocale.value = locale
        i18n.global.locale.value = locale
        setStoredLocale(locale)
        document.documentElement.setAttribute('lang', locale.split('-')[0])
    }

    // Get current language info
    const currentLanguage = computed(() => {
        return availableLanguages.value.find(lang => lang.code === currentLocale.value)
            || availableLanguages.value.find(lang => lang.isDefault)
            || availableLanguages.value[0]
    })

    // Get all active languages
    const activeLanguages = computed(() => {
        return availableLanguages.value.filter(lang => lang.isActive !== false)
    })

    // Initialize: load languages from API
    const initialize = async () => {
        if (!languagesLoaded.value) {
            await loadLanguages()
        }
    }

    // Set HTML lang attribute on mount
    watch(
        currentLocale,
        (newLocale) => {
            document.documentElement.setAttribute('lang', newLocale.split('-')[0])
        },
        { immediate: true }
    )

    return {
        currentLocale,
        elementLocale,
        availableLanguages,
        activeLanguages,
        currentLanguage,
        languagesLoaded,
        setLocale,
        loadLanguages,
        initialize,
        supportedLocales: SUPPORT_LOCALES
    }
})

