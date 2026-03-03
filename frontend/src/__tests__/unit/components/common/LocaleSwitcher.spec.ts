import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { ElMessageBox } from 'element-plus'

const mockGetActiveLanguages = vi.fn()
const mockUpdateProfile = vi.fn()

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
  },
  ElMessageBox: {
    confirm: vi.fn(),
  },
}))

vi.mock('@/api/translations', () => ({
  languageApi: {
    getActive: mockGetActiveLanguages,
  },
}))

vi.mock('@/api/users', () => ({
  userApi: {
    getMe: vi.fn(),
    updateProfile: mockUpdateProfile,
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
}

const mountLocaleSwitcher = async () => {
  vi.resetModules()
  const pinia = createPinia()
  setActivePinia(pinia)

  const i18n = (await import('@/locales')).default
  const LocaleSwitcher = (await import('@/components/common/LocaleSwitcher.vue')).default
  const { useUserStore } = await import('@/stores/user')
  const { useLocaleStore } = await import('@/stores/locale')

  const wrapper = mount(LocaleSwitcher, {
    global: {
      plugins: [pinia, i18n],
      stubs: {
        'el-dropdown': {
          template: '<div data-test="dropdown" @click="$emit(\'command\', \'en-US\')"><slot /><slot name="dropdown" /></div>',
        },
        'el-dropdown-menu': { template: '<div><slot /></div>' },
        'el-dropdown-item': { template: '<div><slot /></div>' },
        'el-icon': { template: '<i><slot /></i>' },
      },
    },
  })

  return {
    wrapper,
    userStore: useUserStore(),
    localeStore: useLocaleStore(),
  }
}

describe('LocaleSwitcher', () => {
  beforeEach(() => {
    storageState.clear()
    bindStorage()
    mockGetActiveLanguages.mockResolvedValue({
      data: [
        { id: '1', code: 'zh-CN', name: 'Chinese', nativeName: '中文', isDefault: true, isActive: true, sortOrder: 1 },
        { id: '2', code: 'en-US', name: 'English', nativeName: 'English', isDefault: false, isActive: true, sortOrder: 2 },
      ],
    })
    mockUpdateProfile.mockResolvedValue({})
    vi.mocked(ElMessageBox.confirm).mockReset()
  })

  it('switches locale in local-only mode for guest users', async () => {
    storageState.set('locale', 'zh-CN')
    const { wrapper, localeStore } = await mountLocaleSwitcher()

    await wrapper.get('[data-test="dropdown"]').trigger('click')

    expect(localeStore.currentLocale).toBe('en-US')
    expect(storageState.get('locale_source')).toBe('local')
    expect(vi.mocked(ElMessageBox.confirm)).not.toHaveBeenCalled()
    expect(mockUpdateProfile).not.toHaveBeenCalled()
  })

  it('syncs locale to profile when user chooses sync mode', async () => {
    storageState.set('locale', 'zh-CN')
    vi.mocked(ElMessageBox.confirm).mockResolvedValueOnce('confirm')

    const { wrapper, localeStore, userStore } = await mountLocaleSwitcher()
    userStore.token = 'access-token'
    userStore.userInfo = {
      id: 'u1',
      username: 'tester',
      fullName: 'Tester',
      isActive: true,
    }

    await wrapper.get('[data-test="dropdown"]').trigger('click')

    expect(localeStore.currentLocale).toBe('en-US')
    expect(mockUpdateProfile).toHaveBeenCalledWith({ preferredLanguage: 'en-US' })
    expect(storageState.get('locale_source')).toBe('profile')
  })
})

