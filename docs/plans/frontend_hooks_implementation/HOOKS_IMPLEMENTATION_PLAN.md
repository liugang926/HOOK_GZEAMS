# Frontend Hooks Implementation Plan

## Document Information
| Item | Description |
|------|-------------|
| Version | v1.0 |
| Date | 2026-01-28 |
| Author | Claude (Agent) |
| Phase | Frontend Foundation - Hooks Implementation |
| Status | Planning |

---

## 1. Background

### 1.1 Problem Statement

The `DynamicForm.vue` component (the core form rendering engine) imports 4 hooks that do not exist:

```typescript
// Line 203-206 in DynamicForm.vue
import { useDynamicForm } from './hooks/useDynamicForm'
import { useFieldPermissions } from './hooks/useFieldPermissions'
import { useFormula } from './hooks/useFormula'
import { useAction } from './hooks/useAction'
```

This causes runtime failures when the form component is used.

### 1.2 Current Architecture

| Layer | Location | Pattern | Existing Components |
|-------|----------|---------|---------------------|
| Global Hooks | `src/hooks/` | Global reusable composables | useMetadata, useTableConfig, useColumnConfig, useLoading |
| Render Engine | `components/engine/` | Component + local hooks (missing) | DynamicForm.vue, FieldRenderer.vue, 20+ fields/*.vue |
| Field Components | `components/engine/fields/` | Type-based files | TextField, NumberField, SelectField, FormulaField, SubTableField, etc. |
| Page Components | `views/dynamic/` | Global hooks + base components | DynamicListPage, DynamicFormPage, DynamicDetailPage |
| Common Components | `components/common/` | Reusable page-level | BaseListPage, BaseFormPage, BaseDetailPage |

### 1.3 Design Decision

**Chosen Approach:** Create `components/engine/hooks/` directory

**Rationale:**
1. Preserve existing `DynamicForm.vue` import paths (no code changes to component)
2. Separation of concerns: global hooks (business logic) vs. local hooks (render engine logic)
3. Low coupling: these hooks serve the render engine only
4. Reusability: future form components can use these hooks

---

## 2. Hook Specifications

### 2.1 useDynamicForm

**Purpose:** Manage form state, load metadata, generate validation rules

**Signature:**
```typescript
function useDynamicForm(
  businessObject: string,
  layoutCode: string,
  layoutConfig: object | null,
  availableFields: array | null
): {
  formRef: Ref,
  formData: Ref<Record<string, any>>,
  formRules: Ref<FormRules>,
  fieldDefinitions: Ref<Field[]>,
  layoutSections: Ref<Section[]>,
  loading: Ref<boolean>,
  loadMetadata: () => Promise<void>,
  validate: () => Promise<boolean>,
  resetFields: () => void,
  businessObjectActions: Ref<Action[]>
}
```

**Responsibilities:**
1. Load metadata using `useMetadata` hook
2. Extract field definitions from metadata response
3. Transform layout config to sections format
4. Generate Element Plus validation rules from field definitions
5. Initialize form data with default values
6. Load business object actions

**Dependencies:**
- `useMetadata` (global hook) - for metadata fetching
- `userStore` - for authentication

**Data Flow:**
```
useMetadata.fetchFieldDefinitions() → fieldDefinitions
useMetadata.fetchPageLayout() → layoutConfig
transformLayoutConfig() → layoutSections
generateValidationRules() → formRules
```

---

### 2.2 useFieldPermissions

**Purpose:** Calculate field-level permissions (readonly, visible, hidden)

**Signature:**
```typescript
function useFieldPermissions(
  fieldPermissions: Ref<object>,
  fieldDefinitions: Ref<Field[]>
): {
  getFieldPermission: (fieldCode: string) => Permission,
  isFieldReadonly: (field: Field) => boolean,
  isFieldVisible: (field: Field) => boolean
}
```

**Permission Levels:**
| Level | Description |
|-------|-------------|
| `editable` | Field can be edited |
| `readonly` | Field is visible but not editable |
| `hidden` | Field is not visible |

**Logic:**
```typescript
isFieldReadonly(field): boolean {
  // 1. Check field.is_readonly from metadata
  // 2. Check fieldPermissions prop
  // 3. Return true if either is readonly
}

isFieldVisible(field): boolean {
  // 1. Check field.is_hidden from metadata
  // 2. Check fieldPermissions prop
  // 3. Return false if hidden
}
```

---

### 2.3 useFormula

**Purpose:** Calculate formula fields with dependency tracking

**Signature:**
```typescript
function useFormula(
  formData: Ref<Record<string, any>>,
  fieldDefinitions: Ref<Field[]>
): {
  isFormulaField: (fieldCode: string) => boolean,
  getCalculatedValue: (fieldCode: string) => any,
  getDependentFormulas: (fieldCode: string) => Set<string>,
  calculateFormulas: () => void,
  initFormulas: () => void,
  syncFormulasToFormData: () => void,
  calculatedValues: Ref<Record<string, any>>
}
```

**Formula Syntax:**
- Support basic arithmetic: `+`, `-`, `*`, `/`
- Support field references: `{field_code}`
- Support functions: `SUM()`, `AVG()`, `COUNT()`, `IF()`
- Examples:
  - `{quantity} * {unit_price}`
  - `IF({status} == 'active', {amount} * 0.1, 0)`

**Dependency Graph:**
```
Field A ──┐
Field B ──┼──► Formula Field C (depends on A, B)
Field D ──┘
```

**Calculation Flow:**
1. Build dependency graph from formula fields
2. When field changes, get dependent formulas
3. Recalculate only dependent formulas
4. Update formData with calculated values

---

### 2.4 useAction

**Purpose:** Execute form actions (submit, cancel, custom, workflow)

**Signature:**
```typescript
function useAction(): {
  executeAction: (action: Action, context: ActionContext) => Promise<void>
}
```

**Action Types:**
| Type | Description |
|------|-------------|
| `submit` | Submit form data |
| `cancel` | Cancel and navigate back |
| `reset` | Reset form to initial state |
| `custom` | Custom action via API |
| `workflow` | Workflow transition (future) |

**Action Interface:**
```typescript
interface Action {
  code: string
  label: string
  type: 'primary' | 'default' | 'danger'
  actionType: 'submit' | 'cancel' | 'reset' | 'custom' | 'workflow'
  apiEndpoint?: string
  method?: 'POST' | 'GET' | 'PUT' | 'DELETE'
  confirmMessage?: string
}

interface ActionContext {
  formData: Ref<Record<string, any>>
  formRef: Ref
}
```

---

## 3. Implementation Plan

### Phase 1: Create Directory Structure

```
frontend/src/components/engine/
├── hooks/
│   ├── index.ts           # Export all hooks
│   ├── useDynamicForm.ts  # Form state management
│   ├── useFieldPermissions.ts  # Field permissions
│   ├── useFormula.ts      # Formula calculation
│   └── useAction.ts       # Action execution
```

### Phase 2: Implement useDynamicForm

**Steps:**
1. Create `useDynamicForm.ts`
2. Import `useMetadata` from global hooks
3. Implement metadata loading
4. Implement layout transformation
5. Implement validation rule generation
6. Return required interface

**Key Implementation Points:**
- Use `useMetadata.fetchFieldDefinitions()` for fields
- Use `useMetadata.fetchPageLayout()` for layouts
- Transform backend layout format to sections
- Map field types to Element Plus validation rules

### Phase 3: Implement useFieldPermissions

**Steps:**
1. Create `useFieldPermissions.ts`
2. Implement permission checking logic
3. Support both metadata and prop-based permissions
4. Return readonly/visible checkers

### Phase 4: Implement useFormula

**Steps:**
1. Create `useFormula.ts`
2. Parse formula expressions
3. Build dependency graph
4. Implement calculation engine
5. Add change tracking for dependent formulas

**Formula Parsing:**
- Replace `{field_code}` with actual values
- Safe evaluation (avoid eval)
- Handle missing/null values gracefully

### Phase 5: Implement useAction

**Steps:**
1. Create `useAction.ts`
2. Implement built-in actions (submit, cancel, reset)
3. Implement custom action execution
4. Add confirmation dialogs
5. Handle success/error feedback

### Phase 6: Testing

**Test Cases:**
1. Form loads without errors
2. All fields are visible
3. Field permissions work correctly
4. Formula calculations work
5. Form actions execute properly
6. Validation rules trigger correctly

---

## 4. File Manifest

| File Path | Purpose | Lines (Est.) |
|-----------|---------|--------------|
| `frontend/src/components/engine/hooks/index.ts` | Export barrel | 10 |
| `frontend/src/components/engine/hooks/useDynamicForm.ts` | Form state | 200 |
| `frontend/src/components/engine/hooks/useFieldPermissions.ts` | Permissions | 80 |
| `frontend/src/components/engine/hooks/useFormula.ts` | Formula engine | 250 |
| `frontend/src/components/engine/hooks/useAction.ts` | Action handler | 120 |
| **Total** | | **660** |

---

## 5. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| API format mismatch | High | Use existing metadata response as reference |
| Formula complexity | Medium | Start with basic arithmetic, extend later |
| Performance issues | Low | Use dependency graph to minimize recalculations |
| Breaking changes | Low | No changes to existing components |

---

## 6. Success Criteria

1. ✅ DynamicForm.vue loads without import errors
2. ✅ Form fields render correctly from metadata
3. ✅ Validation rules work as expected
4. ✅ Field permissions respected (readonly/visible/hidden)
5. ✅ Formula calculations update on field changes
6. ✅ Form actions execute successfully
7. ✅ No console errors in browser

---

## 7. Future Enhancements

1. **Workflow Integration:** Hook actions to workflow transitions
2. **Advanced Formulas:** Support more formula functions
3. **Field Dependencies:** Show/hide fields based on other field values
4. **Conditional Validation:** Dynamic rules based on field values
5. **Draft/Autosave:** Auto-save form data to localStorage

---

## 8. References

- `frontend/src/hooks/useMetadata.ts` - Global metadata hook pattern
- `frontend/src/hooks/useTableConfig.ts` - State management pattern
- `frontend/src/components/engine/DynamicForm.vue` - Consumer component
- `backend/apps/system/viewsets/object_router.py` - Metadata API
- `docs/plans/common_base_features/` - PRD documentation
