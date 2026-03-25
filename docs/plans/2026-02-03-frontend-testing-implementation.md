# Frontend Testing Framework Implementation Plan

## Document Information
| Project | Description |
|---------|-------------|
| Document Version | v1.0 |
| Created Date | 2026-02-03 |
| Related Design | [2026-02-03-frontend-testing-framework.md](./2026-02-03-frontend-testing-framework.md) |
| Status | Ready for Implementation |

---

## Phase 1: Foundation Setup

### Step 1.1: Install MSW
```bash
cd frontend
npm install -D msw@^2.0.0
```

### Step 1.2: Create Directory Structure
```bash
mkdir -p src/__tests__/fixtures
mkdir -p src/__tests__/mocks
mkdir -p src/__tests__/utils
mkdir -p src/__tests__/unit/composables
mkdir -p src/__tests__/unit/utils
mkdir -p src/__tests__/components/common
mkdir -p src/__tests__/components/engine
```

### Step 1.3: Create Global Test Setup
**File:** `frontend/src/__tests__/setup.ts`
```typescript
import { vi } from 'vitest'

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
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
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() { return [] }
  unobserve() {}
} as any

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
} as any
```

### Step 1.4: Enhance vitest.config.ts
Update existing `frontend/vitest.config.ts` to include:
- `setupFiles: ['./src/__tests__/setup.ts']`
- Coverage thresholds (lines: 80%, functions: 80%, branches: 75%, statements: 80%)
- Enhanced exclusion patterns

---

## Phase 2: Fixtures and Mocks

### Step 2.1: Create Business Objects Fixtures
**File:** `frontend/src/__tests__/fixtures/business-objects.ts`
```typescript
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
  }
]

export const mockBusinessObjectDetail = {
  ...mockBusinessObjects[0],
  field_definitions: ['field-001', 'field-002'],
  page_layouts: ['layout-001']
}
```

### Step 2.2: Create Field Definitions Fixtures
**File:** `frontend/src/__tests__/fixtures/field-definitions.ts`
```typescript
export const mockFieldDefinitions = [
  {
    id: 'field-001',
    code: 'asset_code',
    label: '资产编码',
    object_id: 'bo-001',
    field_type: 'text',
    is_required: true,
    is_unique: true,
    config: { max_length: 50 },
    sort_order: 1
  }
]
```

### Step 2.3: Create User Fixtures
**File:** `frontend/src/__tests__/fixtures/users.ts`
```typescript
export const mockCurrentUser = {
  id: 'user-001',
  username: 'admin',
  email: 'admin@example.com',
  is_active: true,
  organization: { id: 'org-001', name: '测试组织' }
}
```

### Step 2.4: Create Fixtures Index
**File:** `frontend/src/__tests__/fixtures/index.ts`
```typescript
export * from './business-objects'
export * from './field-definitions'
export * from './page-layouts'
export * from './users'
```

### Step 2.5: Create MSW Handlers
**File:** `frontend/src/__tests__/mocks/handlers.ts`
```typescript
import { http, HttpResponse } from 'msw'
import { mockBusinessObjects } from '../fixtures/business-objects'

export const handlers = [
  http.get('/api/system/business-objects/', () => {
    return HttpResponse.json({
      success: true,
      data: { results: mockBusinessObjects, count: 1 }
    })
  }),

  http.get('/api/system/business-objects/:id/', ({ params }) => {
    return HttpResponse.json({
      success: true,
      data: mockBusinessObjects[0]
    })
  })
]
```

### Step 2.6: Create MSW Setup
**File:** `frontend/src/__tests__/mocks/msw-setup.ts`
```typescript
import { setupServer } from 'msw/node'
import { handlers } from './handlers'

export const mswServer = setupServer(...handlers)

beforeAll(() => mswServer.listen({ onUnhandledRequest: 'error' }))
afterEach(() => mswServer.resetHandlers())
afterAll(() => mswServer.close())
```

### Step 2.7: Create Test Helpers
**File:** `frontend/src/__tests__/utils/test-helpers.ts`
```typescript
import { VueWrapper, DOMWrapper } from '@vue/test-utils'

export async function flushPromises(): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, 0))
}

export function findByTestId(wrapper: VueWrapper<any>, id: string): DOMWrapper<any> | null {
  return wrapper.find(`[data-testid="${id}"]`)
}

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
```

---

## Phase 3: Composable Tests

### Step 3.1: useMetadata.spec.ts
**File:** `frontend/src/__tests__/unit/composables/useMetadata.spec.ts`
Test coverage:
- fetchBusinessObjects() success and error
- fetchFieldDefinitions() success and error
- fetchPageLayouts() success and error
- Cache invalidation
- Loading states
- Error handling

### Step 3.2: useCrud.spec.ts
**File:** `frontend/src/__tests__/unit/composables/useCrud.spec.ts`
Test coverage:
- create() success and validation
- update() success and error
- delete() soft delete
- fetch() with pagination
- batch operations

### Step 3.3: useFileField.spec.ts
**File:** `frontend/src/__tests__/unit/composables/useFileField.spec.ts`
Test coverage:
- uploadFile() success and error
- upload progress tracking
- file size validation
- deleteFile()

### Step 3.4: useBusinessRules.spec.ts
**File:** `frontend/src/__tests__/unit/composables/useBusinessRules.spec.ts`
Test coverage:
- evaluateRules() with various conditions
- rule precedence
- dependent field updates

### Step 3.5: useTableConfig.spec.ts
**File:** `frontend/src/__tests__/unit/composables/useTableConfig.spec.ts`
Test coverage:
- fetchConfig() from API
- saveConfig() to API
- resetConfig() to defaults
- local storage caching

### Step 3.6: useColumnConfig.spec.ts
**File:** `frontend/src/__tests__/unit/composables/useColumnConfig.spec.ts`
Test coverage:
- column visibility toggle
- column reordering
- column width changes
- save/load configuration

### Step 3.7: useLoading.spec.ts
**File:** `frontend/src/__tests__/unit/composables/useLoading.spec.ts`
Test coverage:
- initial state
- withLoading() wrapper
- loading state changes
- error state propagation

---

## Phase 4: Component Tests

### Step 4.1: BaseForm.spec.ts
**File:** `frontend/src/__tests__/components/common/BaseForm.spec.ts`
Test coverage:
- Form rendering with sections
- Field rendering based on metadata
- Form validation (required, custom rules)
- Form submission success and error
- Reset form functionality

### Step 4.2: BaseTable.spec.ts
**File:** `frontend/src/__tests__/components/common/BaseTable.spec.ts`
Test coverage:
- Table rendering with columns
- Sorting functionality
- Pagination
- Row selection
- Custom slot rendering

### Step 4.3: ColumnManager.spec.ts
**File:** `frontend/src/__tests__/components/common/ColumnManager.spec.ts`
Test coverage:
- Column list rendering
- Drag and drop reordering
- Visibility toggle
- Width adjustment
- Save/Reset configuration

### Step 4.4: DynamicTabs.spec.ts
**File:** `frontend/src/__tests__/components/common/DynamicTabs.spec.ts`
Test coverage:
- Tab rendering from config
- Tab activation
- Drag and drop reordering
- Add/remove tabs
- Tab persistence

### Step 4.5: SectionBlock.spec.ts
**File:** `frontend/src/__tests__/components/common/SectionBlock.spec.ts`
Test coverage:
- Section rendering
- Collapse/expand
- Section actions
- Conditional rendering

### Step 4.6: DynamicForm.spec.ts
**File:** `frontend/src/__tests__/components/engine/DynamicForm.spec.ts`
Test coverage:
- Form layout rendering
- Dynamic field rendering
- Formula calculation
- Sub-table fields
- File upload fields
- Form submission

### Step 4.7: FieldRenderer.spec.ts
**File:** `frontend/src/__tests__/components/engine/FieldRenderer.spec.ts`
Test coverage:
- All field types (text, number, date, select, user, reference)
- Visibility control (hidden, read-only, disabled)
- Field validation
- Event handling (update:modelValue, field-change)

---

## Phase 5: CI/CD Integration

### Step 5.1: Create GitHub Actions Workflow
**File:** `.github/workflows/frontend-test.yml`
```yaml
name: Frontend Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      - name: Install dependencies
        working-directory: ./frontend
        run: npm ci
      - name: Run tests
        working-directory: ./frontend
        run: npm run test:coverage
```

---

## Execution Order

| Phase | Steps | Dependencies |
|-------|-------|--------------|
| 1 | Foundation Setup | None |
| 2 | Fixtures and Mocks | Phase 1 |
| 3 | Composable Tests | Phase 2 |
| 4 | Component Tests | Phase 2 |
| 5 | CI/CD Integration | Phase 3, 4 |

---

## Success Criteria

- [ ] MSW installed and configured
- [ ] All fixtures created
- [ ] All composable tests passing with 100% coverage on critical files
- [ ] All component tests passing
- [ ] Overall coverage >= 80%
- [ ] CI/CD pipeline configured and passing

---

## Notes

1. **Test Files Created**: 7 composables + 7 components = 14 test files
2. **Estimated Time**: 2-3 hours for complete implementation
3. **Priority**: Composable tests first (critical business logic)
4. **Parallel Execution**: Phases 3 and 4 can be done in parallel if needed
