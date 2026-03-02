# Frontend Type Unification - Execution Plan

## 1. Overview

### Problem Analysis

Found **duplicate `FieldDefinition` interfaces** in 4 locations with **inconsistent property names**:

| File | Property Naming | Issue |
|------|-----------------|-------|
| `hooks/useMetadata.ts` | `snake_case` (field_type, is_required) | ❌ Inconsistent |
| `api/dynamic.ts` | `camelCase` (fieldType, isRequired) | ✅ Correct |
| `components/engine/hooks/useDynamicForm.ts` | `camelCase` (fieldType, isRequired) | ✅ Correct |

### Root Cause

- Backend uses `djangorestframework-camel-case` to return `camelCase` JSON
- `hooks/useMetadata.ts` uses outdated `snake_case` types
- Multiple definitions cause type inconsistency and maintenance issues

---

## 2. Target Architecture

```
frontend/src/
├── types/                        # Single source of truth
│   ├── index.ts                  # Export all types
│   ├── field.ts                  # FieldDefinition, FieldType (NEW)
│   ├── layout.ts                 # PageLayout, LayoutConfig (NEW)
│   ├── businessObject.ts         # BusinessObject, ObjectMetadata (NEW)
│   ├── common.ts                 # Existing common types
│   └── ...                       # Other existing types
│
├── composables/                  # Business logic composables
│   ├── useMetadata.ts            # Move from hooks/ (UPDATED)
│   ├── useCrud.ts                # Existing
│   ├── useLayoutHistory.ts       # Existing
│   └── useBusinessRules.ts       # Existing
│
├── hooks/                        # Technical utility hooks (KEEP)
│   ├── index.ts                  # Central export
│   ├── useLoading.ts             # Existing
│   ├── useTableConfig.ts         # Existing
│   ├── useColumnConfig.ts        # Existing
│   ├── useFileField.ts           # New (file field handling)
│   └── ...                       # Other utility hooks
│
└── api/
    └── dynamic.ts                # Import from @/types (UPDATED)
```

---

## 3. Phase 1: Create Unified Types (High Priority)

### 3.1 Create `types/field.ts`

```typescript
// Unified field definition using camelCase (matches backend)
export interface FieldDefinition {
  id?: string
  code: string
  name: string
  label?: string
  fieldType: FieldType
  fieldTypeDisplay?: string

  // Validation
  isRequired?: boolean
  isReadonly?: boolean
  isSystem?: boolean
  isSearchable?: boolean
  isUnique?: boolean
  isHidden?: boolean
  isVisible?: boolean
  sortable?: boolean

  // Display
  showInList?: boolean
  showInDetail?: boolean
  showInFilter?: boolean
  showInForm?: boolean

  // Layout
  sortOrder?: number
  columnWidth?: number
  minColumnWidth?: number
  maxColumnWidth?: number
  fixed?: 'left' | 'right'
  span?: number

  // Validation rules
  minValue?: number
  maxValue?: number
  maxLength?: number
  minLength?: number
  regexPattern?: string

  // Options & Reference
  options?: FieldOption[]
  defaultValue?: any
  referenceObject?: string
  referenceDisplayField?: string

  // Special
  formula?: string
  subTableFields?: FieldDefinition[]
  validationRules?: ValidationRule[]
  componentProps?: Record<string, any>

  // UI
  placeholder?: string
  description?: string
  helpText?: string
}

export type FieldType =
  | 'text' | 'textarea' | 'richtext'
  | 'number' | 'currency' | 'percent'
  | 'date' | 'datetime' | 'time'
  | 'boolean' | 'switch'
  | 'select' | 'multi_select' | 'radio' | 'checkbox'
  | 'reference' | 'user' | 'department'
  | 'file' | 'image' | 'attachment'
  | 'qr_code' | 'barcode'
  | 'formula' | 'subtable'
  | 'location' | 'organization'

export interface FieldOption {
  label: string
  value: any
  disabled?: boolean
  icon?: string
}

export interface ValidationRule {
  type: 'required' | 'pattern' | 'min' | 'max' | 'minLength' | 'maxLength' | 'custom'
  value?: any
  message: string
  trigger?: 'blur' | 'change'
}
```

### 3.2 Create `types/layout.ts`

```typescript
export interface PageLayout {
  id: string
  name: string
  code: string
  layoutType: 'form' | 'list' | 'detail' | 'search'
  businessObject: string
  layoutConfig: LayoutConfig
  isActive?: boolean
  isDefault?: boolean
  description?: string
}

export interface LayoutConfig {
  sections?: LayoutSection[]
  columns?: LayoutColumn[]
  actions?: LayoutAction[]
  title?: string
  icon?: string
}

export interface LayoutSection {
  id: string
  name: string
  title?: string
  type?: 'default' | 'card' | 'fieldset' | 'tab' | 'collapse'
  collapsible?: boolean
  collapsed?: boolean
  columnCount?: number
  fields: (string | LayoutField)[]
  order?: number
  visible?: boolean
  border?: boolean
  icon?: string
  showTitle?: boolean
  shadow?: string
}

export interface LayoutColumn {
  fieldCode: string
  span?: number
  readonly?: boolean
  visible?: boolean
  order?: number
}

export interface LayoutField {
  fieldCode: string
  span?: number
  readonly?: boolean
  visible?: boolean
  order?: number
}

export interface LayoutAction {
  code: string
  label: string
  type: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  actionType: 'submit' | 'cancel' | 'custom' | 'workflow'
  apiEndpoint?: string
  method?: 'POST' | 'GET' | 'PUT' | 'DELETE' | 'PATCH'
  confirmMessage?: string
  order: number
  visible?: boolean
  disabled?: boolean
}
```

### 3.3 Create `types/businessObject.ts`

```typescript
import type { FieldDefinition } from './field'

export interface BusinessObject {
  id: string
  code: string
  name: string
  nameEn?: string
  description?: string
  icon?: string
  module?: string
  isActive?: boolean
  isHardcoded?: boolean
  djangoModelPath?: string

  // Workflow
  enableWorkflow?: boolean
  enableVersion?: boolean
  enableSoftDelete?: boolean

  // Layouts
  defaultFormLayout?: string
  defaultListLayout?: string
  tableName?: string

  // Metadata
  fieldCount?: number
  layoutCount?: number

  // Nested (when populated)
  fields?: FieldDefinition[]
  pageLayouts?: PageLayout[]
}

export interface ObjectMetadata {
  code: string
  name: string
  isHardcoded: boolean
  djangoModelPath?: string
  enableWorkflow: boolean
  enableVersion: boolean
  enableSoftDelete: boolean
  fields: FieldDefinition[]
  layouts: {
    form?: PageLayout
    list?: PageLayout
    detail?: PageLayout
    search?: PageLayout
  }
  permissions: {
    view: boolean
    add: boolean
    change: boolean
    delete: boolean
  }
}
```

### 3.4 Create `types/index.ts`

```typescript
// Field types
export * from './field'

// Layout types
export * from './layout'

// Business object types
export * from './businessObject'

// Common types (existing)
export * from './common'
```

---

## 4. Phase 2: Update Imports (Medium Priority)

### 4.1 Update `api/dynamic.ts`

**Changes:**
- Remove local `FieldDefinition` and `ObjectMetadata` definitions
- Import from `@/types`

```typescript
// Remove lines 23-69 (local type definitions)
// Add at top:
import type { FieldDefinition, ObjectMetadata } from '@/types'
```

### 4.2 Update `components/engine/hooks/useDynamicForm.ts`

**Changes:**
- Remove local `FieldDefinition` definition
- Import from `@/types`

```typescript
// Remove lines 18-36 (local FieldDefinition)
// Add:
import type { FieldDefinition } from '@/types'
```

### 4.3 Update `hooks/useMetadata.ts`

**Changes:**
- Remove ALL local type definitions (lines 8-87)
- Import from `@/types`
- **CRITICAL**: Change snake_case to camelCase in API calls

```typescript
// Remove lines 8-87
// Add:
import type {
  FieldDefinition,
  BusinessObject,
  PageLayout,
  LayoutConfig,
  LayoutSection,
  LayoutAction,
  ValidationRule
} from '@/types'

// Update API response handling to use camelCase properties
```

---

## 5. Phase 3: Migration (Low Priority)

### 5.1 Move `hooks/useMetadata.ts` → `composables/useMetadata.ts`

**Reason:** `useMetadata` is business logic related, belongs in `composables/`

**Steps:**
1. Create `composables/useMetadata.ts`
2. Copy content from `hooks/useMetadata.ts` with updated imports
3. Update all imports across codebase
4. Delete `hooks/useMetadata.ts`

### 5.2 Update `hooks/index.ts`

```typescript
// Technical utility hooks only
export * from './useLoading'
export * from './useTableConfig'
export * from './useColumnConfig'
export * from './useFileField'
// useMetadata is moved to composables/
```

### 5.3 Create `composables/index.ts`

```typescript
export * from './useMetadata'
export * from './useCrud'
export * from './useLayoutHistory'
export * from './useBusinessRules'
```

---

## 6. File Change Summary

| Action | File | Status |
|--------|------|--------|
| **CREATE** | `types/field.ts` | New |
| **CREATE** | `types/layout.ts` | New |
| **CREATE** | `types/businessObject.ts` | New |
| **CREATE** | `types/index.ts` | New |
| **UPDATE** | `api/dynamic.ts` | Remove duplicate types |
| **UPDATE** | `components/engine/hooks/useDynamicForm.ts` | Remove duplicate types |
| **UPDATE** | `hooks/useMetadata.ts` | Remove duplicate types, fix naming |
| **MOVE** | `hooks/useMetadata.ts` → `composables/useMetadata.ts` | Migration |
| **UPDATE** | `hooks/index.ts` | Update exports |
| **CREATE** | `composables/index.ts` | New |

---

## 7. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking changes | High | Use TypeScript incremental adoption |
| Missing properties | Medium | Compare all 4 definitions carefully |
| Import errors | Medium | Run `npm run lint` after each phase |
| Runtime errors | Low | Backend already returns camelCase |

---

## 8. Execution Order

1. **Phase 1**: Create all type files first (no breaking changes)
2. **Phase 2**: Update imports in API files
3. **Phase 3**: Move useMetadata to composables
4. **Verification**: Run `npm run lint` and `npm run build`

---

## 9. Success Criteria

- [ ] No duplicate `FieldDefinition` definitions
- [ ] All files import from `@/types`
- [ ] `npm run lint` passes with 0 errors
- [ ] `npm run build` succeeds
- [ ] No runtime type errors in console
