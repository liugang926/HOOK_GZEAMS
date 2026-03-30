/**
 * Global test setup for Vitest
 * Mocks browser APIs and provides global test utilities
 */

import { vi, beforeEach, afterEach } from 'vitest'
import { config } from '@vue/test-utils'
import { defineComponent } from 'vue'
import i18n from '@/locales'

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock IntersectionObserver
class MockIntersectionObserver {
  observe = vi.fn()
  disconnect = vi.fn()
  unobserve = vi.fn()
  takeRecords = vi.fn(() => [])
}

global.IntersectionObserver = MockIntersectionObserver as any

// Mock ResizeObserver
class MockResizeObserver {
  observe = vi.fn()
  disconnect = vi.fn()
  unobserve = vi.fn()
}

global.ResizeObserver = MockResizeObserver as any

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
}
global.localStorage = localStorageMock as Storage

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn(),
}
global.sessionStorage = sessionStorageMock as Storage

const noopDirective = {
  mounted: () => undefined,
  updated: () => undefined,
  unmounted: () => undefined
}

config.global.directives = {
  ...(config.global.directives || {}),
  focusTrap: noopDirective,
  'focus-trap': noopDirective
}

const createStub = (name: string, template = '<div><slot /></div>') => defineComponent({
  name,
  props: ['modelValue', 'value', 'label', 'name', 'type', 'options'],
  emits: ['update:modelValue', 'change', 'click', 'tab-click'],
  template,
})

config.global.stubs = {
  ...(config.global.stubs || {}),
  'el-badge': createStub('ElBadge', '<span class="el-badge"><slot /></span>'),
  'el-tabs': createStub('ElTabs'),
  'el-tab-pane': createStub('ElTabPane'),
  'el-icon': createStub('ElIcon', '<i><slot /></i>'),
  'el-select': createStub('ElSelect'),
  'el-option': createStub('ElOption'),
  'el-option-group': createStub('ElOptionGroup'),
  'el-segmented': createStub('ElSegmented'),
  'el-collapse-transition': createStub('ElCollapseTransition'),
}

const existingPlugins = Array.isArray(config.global.plugins) ? config.global.plugins : []
config.global.plugins = existingPlugins.includes(i18n) ? existingPlugins : [...existingPlugins, i18n]
config.global.mocks = {
  ...(config.global.mocks || {}),
  $t: (key: string, params?: Record<string, unknown>) => String(i18n.global.t(key, params || {}))
}

const originalConsoleWarn = console.warn.bind(console)
const suppressedWarnPatterns = [
  'Component "i18n-t" has already been registered',
  'Component "I18nT" has already been registered',
  'Component "i18n-n" has already been registered',
  'Component "I18nN" has already been registered',
  'Component "i18n-d" has already been registered',
  'Component "I18nD" has already been registered',
  'Directive "t" has already been registered',
  'Plugin has already been applied to target app.',
  'injection "Symbol(router)" not found.',
  'Failed to resolve component: el-',
]

// Reset mocks before each test
beforeEach(() => {
  i18n.global.locale.value = 'zh-CN'
  vi.clearAllMocks()
  vi.spyOn(console, 'warn').mockImplementation((...args: unknown[]) => {
    const message = args.map((item) => String(item)).join(' ')
    if (suppressedWarnPatterns.some((pattern) => message.includes(pattern))) {
      return
    }
    originalConsoleWarn(...args)
  })
})

// Cleanup after each test
afterEach(() => {
  // Restore any spies
  vi.restoreAllMocks()
})
