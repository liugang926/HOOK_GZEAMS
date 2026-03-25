import { vi } from 'vitest'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  },
  ElNotification: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

// Mock Vue Router
vi.mock('vue-router', () => ({
  useRoute: () => ({ params: {}, query: {} }),
  useRouter: () => ({ push: vi.fn(), back: vi.fn() })
}))

// Mock Pinia stores
vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    user: { id: '1', username: 'test' },
    token: 'test-token'
  })
}))

// Mock axios request utility
vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: {} })),
    post: vi.fn(() => Promise.resolve({ data: {} })),
    put: vi.fn(() => Promise.resolve({ data: {} })),
    delete: vi.fn(() => Promise.resolve({ data: {} }))
  }
}))
