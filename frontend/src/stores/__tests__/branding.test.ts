import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useBrandingStore } from '../branding'

vi.mock('@/api/system/branding', () => ({
  brandingApi: {
    get: vi.fn(),
    update: vi.fn(),
  },
}))

import { brandingApi } from '@/api/system/branding'

const mockBranding = {
  appName: 'Newseams',
  appShortName: 'NS',
  appTagline: 'Brand workspace',
  appIconText: 'NS',
  theme: {
    primaryColor: '#112233',
    accentColor: '#3366ff',
    sidebarGradientStart: '#101828',
    sidebarGradientEnd: '#0f172a',
    borderRadius: 14,
    darkMode: false,
  },
  assets: {
    sidebarLogoFileId: null,
    loginLogoFileId: null,
    faviconFileId: null,
    loginBackgroundFileId: null,
  },
  login: {
    title: 'Welcome to Newseams',
    subtitle: 'Unified operations portal',
    copyright: '(c) 2026 Newseams',
  },
  loginI18n: {
    'zh-CN': {
      title: '欢迎来到 Newseams',
      subtitle: '统一运营门户',
      copyright: '(c) 2026 Newseams',
    },
    'en-US': {
      title: 'Welcome to Newseams',
      subtitle: 'Unified operations portal',
      copyright: '(c) 2026 Newseams',
    },
  },
  resolvedAssets: {
    favicon: {
      id: 'fav-1',
      fileName: 'favicon.png',
      fileType: 'image/png',
      url: 'http://localhost:8000/media/favicon.png',
      thumbnailUrl: 'http://localhost:8000/media/favicon.png',
    }
  }
}

describe('useBrandingStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    window.localStorage.clear()
    document.title = 'Test'
    document.documentElement.removeAttribute('style')
    document.head.querySelectorAll('link[rel="icon"]').forEach((node) => node.remove())
  })

  it('loads branding from api and applies it to the document', async () => {
    vi.mocked(brandingApi.get).mockResolvedValue(mockBranding as any)

    const store = useBrandingStore()
    await store.initialize()

    expect(store.settings.appName).toBe('Newseams')
    expect(document.title).toBe('Newseams')
    expect(document.documentElement.style.getPropertyValue('--sys-color-primary')).toBe('#112233')

    const favicon = document.head.querySelector('link[rel="icon"]') as HTMLLinkElement | null
    expect(favicon?.href).toContain('/media/favicon.png')
  })
})
