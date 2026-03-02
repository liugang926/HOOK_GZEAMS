# Frontend Unit Testing Framework Design

## Document Information
| Project | Description |
|---------|-------------|
| Document Version | v1.0 |
| Created Date | 2026-02-03 |
| Author | Claude Code |
| Status | Design Complete - Ready for Implementation |

---

## 1. Overview

### 1.1 Purpose
Design and implement a comprehensive unit testing framework for the GZEAMS frontend application with the following goals:
- **Full Coverage**: Test all composables and components
- **Complete API Mock**: Mock all HTTP requests using MSW
- **Critical 100%**: 100% coverage for critical business logic

### 1.2 Current State
| Dependency | Version | Status |
|------------|---------|--------|
| Vitest | 4.0.18 | ✅ Installed |
| @vue/test-utils | 2.4.6 | ✅ Installed |
| happy-dom | 20.3.7 | ✅ Installed |
| jsdom | 27.4.0 | ✅ Installed |
| @vitest/coverage-v8 | 4.0.18 | ✅ Installed |
| @vitest/ui | 4.0.18 | ✅ Installed |
| **MSW** | - | ❌ Not Installed (needs: `npm install -D msw@^2.0.0`) |

### 1.3 Existing Tests
| File | Location | Type |
|------|----------|------|
| BaseListPage.spec.ts | src/components/common/__tests__/ | Component |
| layoutValidation.test.ts | src/utils/ | Utility |
| MyApprovals.spec.ts | src/views/workflow/__tests__/ | Component |

---

## 2. Architecture

### 2.1 Directory Structure
```
frontend/src/__tests__/
├── setup.ts                    # Global test setup
├── fixtures/                   # Mock data
│   ├── business-objects.ts     # Business object fixtures
│   ├── field-definitions.ts    # Field definition fixtures
│   ├── page-layouts.ts         # Page layout fixtures
│   ├── users.ts                # User and auth fixtures
│   └── index.ts                # Central export
├── mocks/                      # MSW API mocks
│   ├── handlers.ts             # Request handlers
│   └── msw-setup.ts            # MSW server setup
├── utils/                      # Test utilities
│   └── test-helpers.ts         # Helper functions
├── unit/                       # Unit tests
│   ├── composables/            # Composable tests
│   │   ├── useMetadata.spec.ts
│   │   ├── useCrud.spec.ts
│   │   ├── useFileField.spec.ts
│   │   ├── useBusinessRules.spec.ts
│   │   ├── useLayoutHistory.spec.ts
│   │   ├── useTableConfig.spec.ts
│   │   ├── useColumnConfig.spec.ts
│   │   └── useLoading.spec.ts
│   └── utils/                  # Utility tests
│       └── layoutValidation.spec.ts
└── components/                 # Component tests
    ├── common/                 # Common component tests
    │   ├── BaseForm.spec.ts
    │   ├── BaseListPage.spec.ts
    │   ├── BaseTable.spec.ts
    │   ├── ColumnManager.spec.ts
    │   ├── DynamicTabs.spec.ts
    │   └── SectionBlock.spec.ts
    └── engine/                 # Engine component tests
        ├── DynamicForm.spec.ts
        └── FieldRenderer.spec.ts
```

### 2.2 Testing Layers
```
┌─────────────────────────────────────────────────┐
│              E2E Tests (Playwright)             │
│            (Separate - Already exists)          │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│           Component Tests (Vitest)              │
│       @vue/test-utils + happy-dom               │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│          API Mock Layer (MSW)                   │
│         HTTP Request Interception               │
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│            Unit Tests (Vitest)                  │
│              Composables Only                   │
└─────────────────────────────────────────────────┘
```

---

## 3. Configuration

### 3.1 Enhanced vitest.config.ts
```typescript
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue(), vueJsx()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  test: {
    setupFiles: ['./src/__tests__/setup.ts'],
    globals: true,
    environment: 'happy-dom',
    environmentOptions: {
      jsdom: {
        url: 'http://localhost:3000'
      }
    },
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/__tests__/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData/**',
        'src/main.ts',
        'src/e2e/'
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 75,
        statements: 80
      },
      perFile: true
    },
    include: ['src/**/*.{test,spec}.{ts,tsx,vue}'],
    testTimeout: 10000,
    hookTimeout: 10000,
    threads: true,
    ui: true
  }
})
```

### 3.2 NPM Scripts
```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage",
    "test:watch": "vitest watch",
    "test:unit": "vitest run src/__tests__/unit",
    "test:component": "vitest run src/__tests__/components"
  }
}
```

---

## 4. Test Fixtures

### 4.1 Business Objects Fixtures
```typescript
// src/__tests__/fixtures/business-objects.ts
export const mockBusinessObjects = [
  {
    id: 'bo-001',
    code: 'asset',
    name: '固定资产',
    module: 'assets',
    is_active: true,
    icon: 'files',
    description: '固定资产主数据',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  },
  {
    id: 'bo-002',
    code: 'asset_requisition',
    name: '资产领用',
    module: 'assets',
    is_active: true,
    icon: 'document-copy',
    description: '资产领用单据',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z'
  }
]
```

### 4.2 User Fixtures
```typescript
// src/__tests__/fixtures/users.ts
export const mockCurrentUser = {
  id: 'user-001',
  username: 'admin',
  email: 'admin@example.com',
  first_name: 'System',
  last_name: 'Administrator',
  is_active: true,
  organization: {
    id: 'org-001',
    code: 'org-001',
    name: '测试组织',
    is_active: true
  },
  role: {
    id: 'role-001',
    code: 'admin',
    name: 'Administrator',
    permissions: ['*']
  }
}
```

---

## 5. MSW API Mock Layer

### 5.1 Handlers Setup
```typescript
// src/__tests__/mocks/handlers.ts
import { http, HttpResponse } from 'msw'
import { mockBusinessObjects } from '../fixtures/business-objects'

export const handlers = [
  // Business Objects API
  http.get('/api/system/business-objects/', () => {
    return HttpResponse.json({
      success: true,
      data: {
        results: mockBusinessObjects,
        count: mockBusinessObjects.length
      }
    })
  }),

  http.get('/api/system/business-objects/:id/', ({ params }) => {
    const obj = mockBusinessObjects.find(b => b.id === params.id)
    if (!obj) {
      return HttpResponse.json(
        { success: false, error: { code: 'NOT_FOUND', message: 'Business object not found' } },
        { status: 404 }
      )
    }
    return HttpResponse.json({ success: true, data: obj })
  }),

  // Field Definitions API
  http.get('/api/system/field-definitions/', () => {
    return HttpResponse.json({
      success: true,
      data: {
        results: mockFieldDefinitions,
        count: mockFieldDefinitions.length
      }
    })
  }),

  // Page Layouts API
  http.get('/api/system/page-layouts/', () => {
    return HttpResponse.json({
      success: true,
      data: {
        results: mockPageLayouts,
        count: mockPageLayouts.length
      }
    })
  }),

  // Error Scenarios
  http.get('/api/system/error-500/', () => {
    return HttpResponse.json(
      { success: false, error: { code: 'SERVER_ERROR', message: 'Internal server error' } },
      { status: 500 }
    )
  })
]
```

### 5.2 MSW Server Setup
```typescript
// src/__tests__/mocks/msw-setup.ts
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const mswServer = setupServer(...handlers)

// Setup before all tests
beforeAll(() => {
  mswServer.listen({ onUnhandledRequest: 'error' })
})

// Reset handlers after each test
afterEach(() => {
  mswServer.resetHandlers()
})

// Cleanup after all tests
afterAll(() => {
  mswServer.close()
})
```

---

## 6. Test Examples

### 6.1 Composable Test: useMetadata.spec.ts
```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@hookform/devtools' // or custom hook testing
import { useMetadata } from '@/composables/useMetadata'
import { mswServer } from '../mocks/msw-setup'

describe('useMetadata', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('fetchBusinessObjects', () => {
    it('should fetch business objects successfully', async () => {
      const { result } = renderHook(() => useMetadata())

      await act(async () => {
        await result.current.fetchBusinessObjects()
      })

      expect(result.current.businessObjects.value).toEqual(mockBusinessObjects)
      expect(result.current.loading.value).toBe(false)
      expect(result.current.error.value).toBeNull()
    })

    it('should handle API errors gracefully', async () => {
      // Mock error response
      mswServer.use(
        http.get('/api/system/business-objects/', () => {
          return HttpResponse.json(
            { success: false, error: { code: 'SERVER_ERROR', message: 'API Error' } },
            { status: 500 }
          )
        })
      )

      const { result } = renderHook(() => useMetadata())

      await act(async () => {
        await result.current.fetchBusinessObjects()
      })

      expect(result.current.error.value).not.toBeNull()
      expect(result.current.businessObjects.value).toEqual([])
    })
  })

  describe('Cache Invalidation', () => {
    it('should invalidate cache and refetch', async () => {
      const { result } = renderHook(() => useMetadata())

      await act(async () => {
        await result.current.invalidateCache()
      })

      expect(result.current.businessObjects.value).toBeDefined()
    })
  })
})
```

### 6.2 Component Test: DynamicForm.spec.ts
```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DynamicForm from '@/components/engine/DynamicForm.vue'

describe('DynamicForm', () => {
  const mockLayout = {
    id: 'layout-001',
    object_code: 'asset',
    layout_type: 'form',
    config: {
      sections: [
        {
          id: 'section-1',
          title: 'Basic Information',
          fields: [
            { field_code: 'asset_code', required: true },
            { field_code: 'asset_name', required: true }
          ]
        }
      ]
    }
  }

  describe('Rendering', () => {
    it('should render form sections', () => {
      const wrapper = mount(DynamicForm, {
        props: {
          layout: mockLayout,
          objectCode: 'asset'
        },
        global: {
          stubs: {
            'el-form': true,
            'el-form-item': true,
            'el-input': true
          }
        }
      })

      expect(wrapper.find('.form-section').exists()).toBe(true)
    })
  })

  describe('Validation', () => {
    it('should validate required fields', async () => {
      const wrapper = mount(DynamicForm, {
        props: {
          layout: mockLayout,
          objectCode: 'asset'
        }
      })

      const isValid = await wrapper.vm.validate()
      expect(isValid).toBe(false)
    })
  })

  describe('Submission', () => {
    it('should emit submit event with form data', async () => {
      const wrapper = mount(DynamicForm, {
        props: {
          layout: mockLayout,
          objectCode: 'asset'
        }
      })

      await wrapper.vm.setData({ asset_code: 'A001', asset_name: 'Test Asset' })
      await wrapper.vm.submit()

      expect(wrapper.emitted('submit')).toBeTruthy()
      expect(wrapper.emitted('submit')[0]).toEqual([
        { asset_code: 'A001', asset_name: 'Test Asset' }
      ])
    })
  })
})
```

---

## 7. Test Helpers

### 7.1 Test Utilities
```typescript
// src/__tests__/utils/test-helpers.ts
import { VueWrapper, DOMWrapper } from '@vue/test-utils'

/**
 * Wait for async updates to complete
 */
export async function flushPromises(): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, 0))
}

/**
 * Wait for next tick
 */
export async function nextTick(): Promise<void> {
  return await new Promise(resolve => setTimeout(resolve, 10))
}

/**
 * Find element by test id
 */
export function findByTestId(
  wrapper: VueWrapper<any> | DOMWrapper<any>,
  id: string
): DOMWrapper<any> | null {
  return wrapper.find(`[data-testid="${id}"]`)
}

/**
 * Mock console methods to reduce noise in tests
 */
export function mockConsole(): { restore: () => void } {
  const originalError = console.error
  const originalWarn = console.warn

  console.error = vi.fn()
  console.warn = vi.fn()

  return {
    restore: () => {
      console.error = originalError
      console.warn = originalWarn
    }
  }
}

/**
 * Create a mock file for upload testing
 */
export function createMockFile(
  name: string = 'test.pdf',
  size: number = 1024,
  type: string = 'application/pdf'
): File {
  const file = new File(['mock content'], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}
```

---

## 8. Coverage Thresholds

| Category | Target | Critical Path |
|----------|--------|---------------|
| Lines | 80% | 100% |
| Functions | 80% | 100% |
| Branches | 75% | 90% |
| Statements | 80% | 100% |

**Critical Path Files (100% Required):**
- `src/composables/useMetadata.ts`
- `src/composables/useCrud.ts`
- `src/composables/useBusinessRules.ts`
- `src/components/engine/DynamicForm.vue`
- `src/components/engine/FieldRenderer.vue`

---

## 9. Implementation Plan

### Phase 1: Foundation (Setup)
1. Install MSW: `npm install -D msw@^2.0.0`
2. Create `src/__tests__/` directory structure
3. Create `setup.ts` for global test configuration
4. Enhance `vitest.config.ts` with complete configuration

### Phase 2: Fixtures and Mocks
1. Create `fixtures/business-objects.ts`
2. Create `fixtures/field-definitions.ts`
3. Create `fixtures/page-layouts.ts`
4. Create `fixtures/users.ts`
5. Create `mocks/handlers.ts` with MSW handlers
6. Create `mocks/msw-setup.ts` for MSW server lifecycle

### Phase 3: Composable Tests
1. Create `unit/composables/useMetadata.spec.ts`
2. Create `unit/composables/useCrud.spec.ts`
3. Create `unit/composables/useFileField.spec.ts`
4. Create `unit/composables/useBusinessRules.spec.ts`
5. Create `unit/composables/useTableConfig.spec.ts`
6. Create `unit/composables/useColumnConfig.spec.ts`
7. Create `unit/composables/useLoading.spec.ts`

### Phase 4: Component Tests
1. Create `components/common/BaseForm.spec.ts`
2. Create `components/common/BaseTable.spec.ts`
3. Create `components/common/ColumnManager.spec.ts`
4. Create `components/common/DynamicTabs.spec.ts`
5. Create `components/common/SectionBlock.spec.ts`
6. Create `components/engine/DynamicForm.spec.ts`
7. Create `components/engine/FieldRenderer.spec.ts`

### Phase 5: CI/CD Integration
1. Create `.github/workflows/test.yml`
2. Configure coverage reporting to Codecov
3. Add coverage thresholds to CI pipeline

---

## 10. Success Criteria

- [ ] All critical composables have 100% test coverage
- [ ] All API calls are mocked using MSW
- [ ] Tests run in under 10 seconds
- [ ] CI/CD pipeline passes on every PR
- [ ] Coverage report is generated and viewable

---

## Appendix A: Installation Commands

```bash
# Install MSW for API mocking
cd frontend
npm install -D msw@^2.0.0
```

## Appendix B: Running Tests

```bash
# Run all tests
npm run test

# Run tests with UI
npm run test:ui

# Run tests with coverage
npm run test:coverage

# Run only unit tests
npm run test:unit

# Run only component tests
npm run test:component
```

## Appendix C: References

- [Vitest Documentation](https://vitest.dev/)
- [Vue Test Utils Documentation](https://test-utils.vuejs.org/)
- [MSW Documentation](https://mswjs.io/)
- [happy-dom Documentation](https://github.com/capricorn86/happy-dom)
