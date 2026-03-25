import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { brandingApi, type BrandingSettings } from '@/api/system/branding'
import { injectTheme } from '@/utils/theme'

const BRANDING_STORAGE_KEY = 'gzeams-branding-settings'

export const DEFAULT_BRANDING_SETTINGS: BrandingSettings = {
  appName: 'GZEAMS',
  appShortName: 'GZEAMS',
  appTagline: 'Enterprise Asset Management System',
  appIconText: 'G',
  theme: {
    primaryColor: '#0f172a',
    accentColor: '#3b82f6',
    sidebarGradientStart: '#1e293b',
    sidebarGradientEnd: '#0f172a',
    borderRadius: 10,
    darkMode: false,
  },
  assets: {
    sidebarLogoFileId: null,
    loginLogoFileId: null,
    faviconFileId: null,
    loginBackgroundFileId: null,
  },
  login: {
    title: 'GZEAMS',
    subtitle: 'Secure workspace for enterprise asset operations',
    copyright: '\u00a9 2026 GZEAMS Enterprise Asset Management System',
  },
  loginI18n: {
    'zh-CN': {
      title: 'GZEAMS',
      subtitle: '\u4f01\u4e1a\u8d44\u4ea7\u8fd0\u8425\u7edf\u4e00\u5de5\u4f5c\u53f0',
      copyright: '\u00a9 2026 GZEAMS \u4f01\u4e1a\u8d44\u4ea7\u7ba1\u7406\u7cfb\u7edf',
    },
    'en-US': {
      title: 'GZEAMS',
      subtitle: 'Secure workspace for enterprise asset operations',
      copyright: '\u00a9 2026 GZEAMS Enterprise Asset Management System',
    },
  },
  resolvedAssets: {},
}

const cloneDefaults = (): BrandingSettings => JSON.parse(JSON.stringify(DEFAULT_BRANDING_SETTINGS))

const mergeBranding = (
  base: BrandingSettings,
  override?: Partial<BrandingSettings> | null
): BrandingSettings => {
  if (!override || typeof override !== 'object') {
    return JSON.parse(JSON.stringify(base))
  }

  return {
    ...base,
    ...override,
    theme: {
      ...base.theme,
      ...(override.theme || {}),
    },
    assets: {
      ...base.assets,
      ...(override.assets || {}),
    },
    login: {
      ...base.login,
      ...(override.login || {}),
    },
    loginI18n: {
      'zh-CN': {
        ...(base.login || {}),
        ...((base.loginI18n || {})['zh-CN'] || {}),
        ...((override.loginI18n || {})['zh-CN'] || {}),
      },
      'en-US': {
        ...(base.login || {}),
        ...((base.loginI18n || {})['en-US'] || {}),
        ...((override.loginI18n || {})['en-US'] || {}),
      },
    },
    resolvedAssets: {
      ...(base.resolvedAssets || {}),
      ...(override.resolvedAssets || {}),
    },
  }
}

const readStoredBranding = (): BrandingSettings => {
  if (typeof window === 'undefined') return cloneDefaults()

  try {
    const raw = window.localStorage.getItem(BRANDING_STORAGE_KEY)
    if (!raw) return cloneDefaults()
    return mergeBranding(cloneDefaults(), JSON.parse(raw))
  } catch {
    return cloneDefaults()
  }
}

const persistBranding = (settings: BrandingSettings) => {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(BRANDING_STORAGE_KEY, JSON.stringify(settings))
}

const upsertFavicon = (href?: string) => {
  if (typeof document === 'undefined' || !href) return

  let favicon = document.querySelector<HTMLLinkElement>('link[rel="icon"]')
  if (!favicon) {
    favicon = document.createElement('link')
    favicon.rel = 'icon'
    document.head.appendChild(favicon)
  }
  favicon.href = href
}

export const useBrandingStore = defineStore('branding', () => {
  const settings = ref<BrandingSettings>(readStoredBranding())
  const isLoaded = ref(false)
  const isLoading = ref(false)

  const applyBranding = (nextSettings: BrandingSettings) => {
    settings.value = mergeBranding(cloneDefaults(), nextSettings)
    persistBranding(settings.value)

    injectTheme({
      primaryColor: settings.value.theme.primaryColor,
      accentColor: settings.value.theme.accentColor,
      sidebarGradientStart: settings.value.theme.sidebarGradientStart,
      sidebarGradientEnd: settings.value.theme.sidebarGradientEnd,
      borderRadius: settings.value.theme.borderRadius,
      darkMode: settings.value.theme.darkMode,
    })

    if (typeof document !== 'undefined') {
      document.title = settings.value.appName || DEFAULT_BRANDING_SETTINGS.appName
      document.documentElement.style.setProperty(
        '--brand-login-background-image',
        settings.value.resolvedAssets?.loginBackground?.url
          ? `url("${settings.value.resolvedAssets.loginBackground.url}")`
          : 'none'
      )
      upsertFavicon(settings.value.resolvedAssets?.favicon?.url)
    }
  }

  const initialize = async (force = false) => {
    if (isLoading.value) return
    if (isLoaded.value && !force) {
      applyBranding(settings.value)
      return
    }

    isLoading.value = true
    try {
      const branding = await brandingApi.get()
      applyBranding(branding)
      isLoaded.value = true
    } catch (error) {
      console.error('[branding] failed to load branding settings', error)
      applyBranding(settings.value)
    } finally {
      isLoading.value = false
    }
  }

  const save = async (nextSettings: BrandingSettings) => {
    const cloned = JSON.parse(JSON.stringify(nextSettings)) as BrandingSettings
    const { resolvedAssets, ...payload } = cloned
    const saved = await brandingApi.update(payload as BrandingSettings)
    applyBranding(saved)
    isLoaded.value = true
    return saved
  }

  const refresh = async () => initialize(true)

  const sidebarLogoUrl = computed(() => settings.value.resolvedAssets?.sidebarLogo?.url || '')
  const loginLogoUrl = computed(() => settings.value.resolvedAssets?.loginLogo?.url || settings.value.resolvedAssets?.sidebarLogo?.url || '')
  const faviconUrl = computed(() => settings.value.resolvedAssets?.favicon?.url || '')
  const loginBackgroundUrl = computed(() => settings.value.resolvedAssets?.loginBackground?.url || '')
  const brandName = computed(() => settings.value.appShortName || settings.value.appName)
  const brandIconText = computed(() => settings.value.appIconText || settings.value.appName.charAt(0) || 'G')

  return {
    settings,
    isLoaded,
    isLoading,
    sidebarLogoUrl,
    loginLogoUrl,
    faviconUrl,
    loginBackgroundUrl,
    brandName,
    brandIconText,
    applyBranding,
    initialize,
    save,
    refresh,
  }
})
