import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import i18n from '@/locales'
import { useLocaleStore } from '@/stores/locale'
import SystemBranding from '@/views/system/SystemBranding.vue'

const {
  mockBrandingGet,
  mockBrandingUpdate,
  mockGetActiveLanguages,
  mockMessageSuccess,
  mockMessageError,
} = vi.hoisted(() => ({
  mockBrandingGet: vi.fn(),
  mockBrandingUpdate: vi.fn(),
  mockGetActiveLanguages: vi.fn(),
  mockMessageSuccess: vi.fn(),
  mockMessageError: vi.fn(),
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    success: mockMessageSuccess,
    error: mockMessageError,
  },
}))

vi.mock('@/api/system/branding', () => ({
  brandingApi: {
    get: mockBrandingGet,
    update: mockBrandingUpdate,
    patch: vi.fn(),
  },
}))

vi.mock('@/api/translations', () => ({
  languageApi: {
    getActive: mockGetActiveLanguages,
  },
}))

const createBrandingSettings = () => ({
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
  resolvedAssets: {},
})

const createWrapper = () => {
  const pinia = createPinia()
  setActivePinia(pinia)

  return mount(SystemBranding, {
    global: {
      plugins: [pinia, i18n],
      stubs: {
        'el-card': {
          template: '<section><div><slot name="header" /></div><div><slot /></div></section>',
        },
        'el-form': {
          template: '<form><slot /></form>',
        },
        'el-form-item': {
          props: ['label'],
          template: '<label><span>{{ label }}</span><slot /></label>',
        },
        'el-input': {
          props: ['modelValue'],
          emits: ['update:modelValue'],
          template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        'el-color-picker': {
          template: '<div class="color-picker-stub" />',
        },
        'el-slider': {
          template: '<div class="slider-stub" />',
        },
        'el-switch': {
          template: '<div class="switch-stub" />',
        },
        'el-divider': {
          template: '<div><slot /></div>',
        },
        'el-tabs': {
          template: '<div><slot /></div>',
        },
        'el-tab-pane': {
          props: ['label'],
          template: '<section><h4>{{ label }}</h4><slot /></section>',
        },
        'el-upload': {
          template: '<div><slot /></div>',
        },
        'el-button': {
          props: ['type', 'loading', 'text', 'round', 'disabled'],
          emits: ['click'],
          template: '<button :disabled="disabled" @click="$emit(\'click\')"><slot /></button>',
        },
      },
    },
  })
}

describe('SystemBranding i18n', () => {
  beforeEach(() => {
    localStorage.clear()
    mockBrandingGet.mockReset()
    mockBrandingUpdate.mockReset()
    mockGetActiveLanguages.mockReset()
    mockMessageSuccess.mockReset()
    mockMessageError.mockReset()

    i18n.global.locale.value = 'zh-CN'

    mockGetActiveLanguages.mockResolvedValue([
      { id: '1', code: 'zh-CN', name: 'Chinese', nativeName: '中文', isDefault: true, isActive: true, sortOrder: 1 },
      { id: '2', code: 'en-US', name: 'English', nativeName: 'English', isDefault: false, isActive: true, sortOrder: 2 },
    ])
    mockBrandingGet.mockResolvedValue(createBrandingSettings())
    mockBrandingUpdate.mockImplementation(async (payload) => ({
      ...payload,
      resolvedAssets: {},
    }))
  })

  it('keeps sidebar and system config branding entry labels readable in zh-CN', () => {
    expect(i18n.global.t('menu.routes.systemBranding')).toBe('品牌主题管理')
    expect(i18n.global.t('system.branding.entry')).toBe('品牌主题')
  })

  it('updates preview copy and save toast when switching locales', async () => {
    const wrapper = createWrapper()
    await flushPromises()

    expect(wrapper.text()).toContain('品牌主题管理')
    expect(wrapper.text()).toContain('侧边栏 Logo')
    expect(wrapper.text()).toContain('工作台')

    const localeStore = useLocaleStore()
    localeStore.setLocale('en-US')
    await flushPromises()

    expect(wrapper.text()).toContain('Branding Settings')
    expect(wrapper.text()).toContain('Sidebar Logo')
    expect(wrapper.text()).toContain('Dashboard')

    const saveButton = wrapper.findAll('button').find((button) => button.text() === 'Save')
    expect(saveButton).toBeTruthy()

    await saveButton!.trigger('click')
    await flushPromises()

    expect(mockBrandingUpdate).toHaveBeenCalled()
    expect(mockMessageSuccess).toHaveBeenCalledWith('Branding updated.')
  })
})
