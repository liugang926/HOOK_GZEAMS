import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

const mockGetMe = vi.fn()
const mockGetActiveLanguages = vi.fn()

vi.mock('@/api/users', () => ({
  userApi: {
    getMe: mockGetMe,
    updateProfile: vi.fn(),
  },
}))

vi.mock('@/api/translations', () => ({
  languageApi: {
    getActive: mockGetActiveLanguages,
  },
}))

const storageState = new Map<string, string>()

const bindStorage = () => {
  vi.mocked(localStorage.getItem).mockImplementation((key: string) => {
    return storageState.has(key) ? storageState.get(key)! : null
  })
  vi.mocked(localStorage.setItem).mockImplementation((key: string, value: string) => {
    storageState.set(key, value)
  })
  vi.mocked(localStorage.removeItem).mockImplementation((key: string) => {
    storageState.delete(key)
  })
  vi.mocked(localStorage.clear).mockImplementation(() => {
    storageState.clear()
  })
}

const bootstrapStores = async () => {
  vi.resetModules()
  setActivePinia(createPinia())
  const { useLocaleStore } = await import('@/stores/locale')
  const { useUserStore } = await import('@/stores/user')
  return {
    localeStore: useLocaleStore(),
    userStore: useUserStore(),
  }
}

describe('Locale/User Locale Flow', () => {
  beforeEach(() => {
    storageState.clear()
    bindStorage()
    mockGetActiveLanguages.mockResolvedValue({
      data: [
        { id: '1', code: 'zh-CN', name: 'Chinese', nativeName: '中文', isDefault: true, isActive: true, sortOrder: 1 },
        { id: '2', code: 'en-US', name: 'English', nativeName: 'English', isDefault: false, isActive: true, sortOrder: 2 },
      ],
    })
    mockGetMe.mockResolvedValue({
      id: 'u1',
      username: 'tester',
      fullName: 'Tester',
      isActive: true,
    })
  })

  it('keeps local cached locale when locale_source is local', async () => {
    storageState.set('locale', 'zh-CN')
    storageState.set('locale_source', 'local')
    mockGetMe.mockResolvedValueOnce({
      id: 'u1',
      username: 'tester',
      fullName: 'Tester',
      isActive: true,
      preferredLanguage: 'en-US',
    })

    const { localeStore, userStore } = await bootstrapStores()
    await userStore.getUserInfo()

    expect(localeStore.currentLocale).toBe('zh-CN')
    expect(storageState.get('locale_source')).toBe('local')
  })

  it('applies profile locale when local source is not locked', async () => {
    storageState.set('locale', 'zh-CN')
    mockGetMe.mockResolvedValueOnce({
      id: 'u2',
      username: 'tester2',
      fullName: 'Tester2',
      isActive: true,
      preferredLanguage: 'en-US',
    })

    const { localeStore, userStore } = await bootstrapStores()
    await userStore.getUserInfo()

    expect(localeStore.currentLocale).toBe('en-US')
    expect(storageState.get('locale_source')).toBe('profile')
  })

  it('falls back to system default locale when no cache and no profile locale', async () => {
    const { localeStore, userStore } = await bootstrapStores()
    await userStore.getUserInfo()

    expect(localeStore.currentLocale).toBe('zh-CN')
    expect(storageState.get('locale')).toBe('zh-CN')
  })
})

