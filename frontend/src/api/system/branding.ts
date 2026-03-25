import request from '@/utils/request'
import { resolveSystemFileUrl } from '@/api/systemFile'

export interface BrandingAssetRef {
  id: string
  fileName: string
  fileType: string
  url: string
  thumbnailUrl?: string
}

export interface BrandingThemeSettings {
  primaryColor: string
  accentColor: string
  sidebarGradientStart: string
  sidebarGradientEnd: string
  borderRadius: number
  darkMode: boolean
}

export interface BrandingAssetIds {
  sidebarLogoFileId: string | null
  loginLogoFileId: string | null
  faviconFileId: string | null
  loginBackgroundFileId: string | null
}

export interface BrandingLoginSettings {
  title: string
  subtitle: string
  copyright: string
}

export interface BrandingSettings {
  appName: string
  appShortName: string
  appTagline: string
  appIconText: string
  theme: BrandingThemeSettings
  assets: BrandingAssetIds
  login: BrandingLoginSettings
  loginI18n: Record<string, BrandingLoginSettings>
  resolvedAssets?: {
    sidebarLogo?: BrandingAssetRef
    loginLogo?: BrandingAssetRef
    favicon?: BrandingAssetRef
    loginBackground?: BrandingAssetRef
  }
}

const normalizeResolvedAssets = (settings: BrandingSettings): BrandingSettings => {
  const resolvedAssets = settings.resolvedAssets
  if (!resolvedAssets) return settings

  return {
    ...settings,
    resolvedAssets: {
      sidebarLogo: resolvedAssets.sidebarLogo
        ? {
          ...resolvedAssets.sidebarLogo,
          url: resolveSystemFileUrl(resolvedAssets.sidebarLogo.url),
          thumbnailUrl: resolveSystemFileUrl(resolvedAssets.sidebarLogo.thumbnailUrl || resolvedAssets.sidebarLogo.url),
        }
        : undefined,
      loginLogo: resolvedAssets.loginLogo
        ? {
          ...resolvedAssets.loginLogo,
          url: resolveSystemFileUrl(resolvedAssets.loginLogo.url),
          thumbnailUrl: resolveSystemFileUrl(resolvedAssets.loginLogo.thumbnailUrl || resolvedAssets.loginLogo.url),
        }
        : undefined,
      favicon: resolvedAssets.favicon
        ? {
          ...resolvedAssets.favicon,
          url: resolveSystemFileUrl(resolvedAssets.favicon.url),
          thumbnailUrl: resolveSystemFileUrl(resolvedAssets.favicon.thumbnailUrl || resolvedAssets.favicon.url),
        }
        : undefined,
      loginBackground: resolvedAssets.loginBackground
        ? {
          ...resolvedAssets.loginBackground,
          url: resolveSystemFileUrl(resolvedAssets.loginBackground.url),
          thumbnailUrl: resolveSystemFileUrl(resolvedAssets.loginBackground.thumbnailUrl || resolvedAssets.loginBackground.url),
        }
        : undefined,
    }
  }
}

export const brandingApi = {
  get() {
    return request<BrandingSettings>({
      url: '/system/branding/',
      method: 'get',
      noAuth: true,
    } as any).then(normalizeResolvedAssets)
  },

  update(data: BrandingSettings) {
    return request<BrandingSettings>({
      url: '/system/branding/',
      method: 'put',
      data,
    }).then(normalizeResolvedAssets)
  },

  patch(data: Partial<BrandingSettings>) {
    return request<BrandingSettings>({
      url: '/system/branding/',
      method: 'patch',
      data,
    }).then(normalizeResolvedAssets)
  },
}
