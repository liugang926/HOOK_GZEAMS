# Layout Type Unification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create unified metadata type definitions in `frontend/src/types/metadata.ts` and update all imports to eliminate duplicate type definitions across the layout designer module.

**Architecture:** Centralized type definition module following the DRY principle. All metadata-related types (FieldMetadata, SectionConfig, TabConfig, LayoutConfig, etc.) will be exported from a single source of truth file.

**Tech Stack:** TypeScript 5.x, Vue 3, Vite

---

## Context & Background

The layout designer module has duplicate type definitions across multiple files:
- `services/layoutMerge.ts` defines `SectionConfig`, `TabConfig`, `FieldOverride`
- `services/layoutSchema.ts` defines `SectionConfig`, `TabConfig`, `FieldOverride`, `ValidationResult`
- `types/layout.ts` defines `LayoutSection`, `LayoutTab`, `LayoutField`
- Component files define inline interfaces

These files import from `@/types/metadata` which doesn't exist, causing TypeScript compilation errors.

---

## Phase 1: Create Metadata Types Module (Low Risk)

### Task 1: Create types/metadata.ts file

**Files:**
- Create: `frontend/src/types/metadata.ts`

**Step 1: Create the file with all type definitions**

Write the complete file:

```typescript
/**
 * metadata.ts - Unified metadata type definitions
 *
 * This file consolidates all metadata-related types for the layout designer.
 * Types use camelCase to match the frontend coding standard.
 *
 * Backend Integration Note:
 * - Backend uses djangorestframework-camel-case for API serialization
 * - All API responses should be in camelCase format
 * - If backend returns snake_case, configure djangorestframework-camel-case
 */

// ============================================================================
// Field Metadata Types
// ============================================================================

/**
 * Field metadata from backend API
 * Represents a field definition in a business object
 */
export interface FieldMetadata {
  /** Unique field identifier */
  code: string

  /** Human-readable field name */
  name: string

  /** Field type (text, number, reference, enum, etc.) */
  fieldType: string

  /** Whether field is required */
  isRequired: boolean

  /** Whether field is read-only */
  isReadonly: boolean

  /** Display sort order */
  sortOrder: number

  /** Section this field belongs to */
  sectionName?: string

  /** Whether this is a reverse relation field */
  isReverseRelation?: boolean

  /** How reverse relation is displayed */
  relationDisplayMode?: string

  /** Related object code (for reference fields) */
  relatedObject?: string

  /** Whether field is visible in form */
  showInForm?: boolean

  /** Whether field is visible in list */
  showInList?: boolean

  /** Custom CSS class */
  customClass?: string

  /** Field span (1-24, based on 24-column grid) */
  span?: number

  /** Default value */
  defaultValue?: any

  /** Help text for field */
  helpText?: string

  /** Placeholder text */
  placeholder?: string

  /** Readonly flag (alias for isReadonly for compatibility) */
  readonly?: boolean
}

/**
 * Field definition for layout designer
 * Used in designer components for field configuration
 */
export interface FieldDefinition extends FieldMetadata {
  /** Internal component ID */
  id: string

  /** Field label (can override name) */
  label: string

  /** Grid column span (1-24) */
  span: number

  /** Whether field is currently visible */
  visible?: boolean

  /** Field width (CSS value) */
  width?: string

  /** Visible rules (conditional visibility) */
  visibleRules?: Array<{ field: string; value: any }>

  /** Validation rules */
  validationRules?: Array<{ logic: string; message: string }>

  /** Regex pattern for validation */
  regexPattern?: string

  /** Minimum value (for numbers) */
  minValue?: number

  /** Maximum value (for numbers) */
  maxValue?: number

  /** Reference filters (for reference fields) */
  referenceFilters?: Record<string, any>
}

// ============================================================================
// Layout Configuration Types
// ============================================================================

/**
 * Complete layout configuration
 * Top-level container for all layout settings
 */
export interface LayoutConfig {
  /** Layout sections */
  sections?: SectionConfig[]

  /** Column configuration (for list layouts) */
  columns?: LayoutColumn[]

  /** Action buttons */
  actions?: LayoutAction[]

  /** Page title */
  title?: string

  /** Page icon */
  icon?: string

  /** Field order override */
  fieldOrder?: string[]

  /** Field-specific overrides */
  fieldOverrides?: Record<string, FieldOverride>

  /** Tab configurations */
  tabs?: TabConfig[]

  /** Container configurations */
  containers?: ContainerConfig[]

  /** Additional metadata */
  [key: string]: any
}

/**
 * Differential configuration for layout customization
 * Represents changes from default layout
 */
export interface DifferentialConfig {
  /** Custom field order */
  fieldOrder?: string[]

  /** Field-specific overrides */
  fieldOverrides?: Record<string, FieldOverride>

  /** Section configurations */
  sections?: SectionConfig[]

  /** Tab configurations */
  tabs?: TabConfig[]

  /** Container configurations */
  containers?: ContainerConfig[]
}

/**
 * Field override in differential config
 * Allows overriding default field properties
 */
export interface FieldOverride {
  /** Visibility override */
  visible?: boolean

  /** Read-only override */
  readonly?: boolean

  /** Required override */
  required?: boolean

  /** Column span override */
  span?: number

  /** Default value override */
  defaultValue?: any

  /** Label override */
  label?: string

  /** Placeholder override */
  placeholder?: string

  /** Help text override */
  helpText?: string
}

// ============================================================================
// Section Types
// ============================================================================

/**
 * Section configuration
 * Groups related fields together
 */
export interface SectionConfig {
  /** Section identifier */
  id: string

  /** Section title */
  title: string

  /** Field codes in this section */
  fields: string[]

  /** Number of columns (1-4) */
  columns?: number

  /** Whether section is collapsed by default */
  collapsed?: boolean

  /** Background color */
  backgroundColor?: string

  /** Border visibility */
  border?: boolean

  /** Section icon name */
  icon?: string

  /** Custom CSS class */
  customClass?: string

  /** Whether section is visible */
  visible?: boolean
}

/**
 * Layout section (from types/layout.ts)
 * Similar to SectionConfig but with additional properties
 */
export interface LayoutSection {
  /** Section identifier */
  id: string

  /** Section name/key */
  name: string

  /** Section display title */
  title?: string

  /** Section type */
  type?: SectionType

  /** Whether section is collapsible */
  collapsible?: boolean

  /** Whether section is collapsed by default */
  collapsed?: boolean

  /** Number of columns in the section */
  columnCount?: number

  /** Fields in this section (field codes or field objects) */
  fields: (string | LayoutField)[]

  /** Display order */
  order?: number

  /** Whether section is visible */
  visible?: boolean

  /** Whether to show border */
  border?: boolean

  /** Section icon */
  icon?: string

  /** Whether to show title */
  showTitle?: boolean

  /** Shadow effect */
  shadow?: string

  /** Section span (grid columns) */
  span?: number
}

/** Section types */
export type SectionType = 'default' | 'card' | 'fieldset' | 'tab' | 'collapse'

// ============================================================================
// Tab Types
// ============================================================================

/**
 * Tab configuration
 * Defines a tab in tabbed layout
 */
export interface TabConfig {
  /** Tab identifier */
  id: string

  /** Tab title */
  title: string

  /** Field codes in this tab */
  fields?: string[]

  /** Related object codes in this tab */
  relations?: string[]

  /** Whether tab is disabled */
  disabled?: boolean

  /** Tab icon name */
  icon?: string
}

/**
 * Layout tab (from types/layout.ts)
 * Similar to TabConfig but with sections support
 */
export interface LayoutTab {
  /** Tab identifier */
  id: string

  /** Tab name/key */
  name: string

  /** Tab title */
  title: string

  /** Tab icon */
  icon?: string

  /** Sections in this tab */
  sections: LayoutSection[]

  /** Whether tab is disabled */
  disabled?: boolean

  /** Display order */
  order?: number
}

// ============================================================================
// Container Types
// ============================================================================

/**
 * Container configuration
 * Defines layout containers for organizing content
 */
export interface ContainerConfig {
  /** Container type */
  type: ContainerType

  /** Container identifier */
  id: string

  /** Container title */
  title?: string

  /** Container items */
  items?: ContainerConfig[]

  /** Additional properties */
  [key: string]: any
}

/** Container types */
export type ContainerType = 'tab' | 'column' | 'collapse' | 'divider'

// ============================================================================
// Field Types
// ============================================================================

/**
 * Layout field (from types/layout.ts)
 * Used within sections to configure individual field display
 */
export interface LayoutField {
  /** Field code */
  fieldCode: string

  /** Grid span */
  span?: number

  /** Whether field is read-only */
  readonly?: boolean

  /** Whether field is visible */
  visible?: boolean

  /** Display order */
  order?: number

  /** Field-specific props */
  props?: Record<string, any>
}

/**
 * Preview field (for layout preview)
 * Extends LayoutField with simulated values
 */
export interface PreviewField extends FieldDefinition {
  /** Simulated value for preview */
  simulatedValue?: any
}

// ============================================================================
// Column Types (for List Layouts)
// ============================================================================

/**
 * Layout column definition
 * Used for list view columns
 */
export interface LayoutColumn {
  /** Field code */
  fieldCode: string

  /** Column span */
  span?: number

  /** Whether column is read-only */
  readonly?: boolean

  /** Whether column is visible */
  visible?: boolean

  /** Display order */
  order?: number

  /** Column width */
  width?: number

  /** Whether column is sortable */
  sortable?: boolean

  /** Fixed position */
  fixed?: 'left' | 'right'
}

/**
 * List column (from PropertyPanel.vue)
 * Used in list layout designer
 */
export interface ListColumn {
  /** Field code */
  fieldCode: string

  /** Column label */
  label: string

  /** Column width (px) */
  width?: number

  /** Fixed position */
  fixed?: string

  /** Whether sortable */
  sortable?: boolean
}

// ============================================================================
// Action Types
// ============================================================================

/**
 * Layout action definition
 * Defines action buttons on the page
 */
export interface LayoutAction {
  /** Action code */
  code: string

  /** Action label */
  label: string

  /** Button type */
  type: ActionType

  /** Action type */
  actionType: ActionCategory

  /** API endpoint for custom actions */
  apiEndpoint?: string

  /** HTTP method */
  method?: 'POST' | 'GET' | 'PUT' | 'DELETE' | 'PATCH'

  /** Confirmation message */
  confirmMessage?: string

  /** Display order */
  order: number

  /** Whether action is visible */
  visible?: boolean

  /** Whether action is disabled */
  disabled?: boolean

  /** Button icon */
  icon?: string

  /** Additional props */
  props?: Record<string, any>
}

/** Action button types */
export type ActionType = 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'

/** Action categories */
export type ActionCategory = 'submit' | 'cancel' | 'custom' | 'workflow'

// ============================================================================
// Validation Types
// ============================================================================

/**
 * Validation result
 */
export interface ValidationResult {
  /** Whether validation passed */
  valid: boolean

  /** Validation errors */
  errors: ValidationError[]
}

/**
 * Validation error detail
 */
export interface ValidationError {
  /** Error path (dot notation) */
  path: string

  /** Error message */
  message: string

  /** Error code */
  code: string
}

/** Standard error codes */
export const ERROR_CODES = {
  REQUIRED_FIELD: 'REQUIRED_FIELD',
  INVALID_TYPE: 'INVALID_TYPE',
  INVALID_VALUE: 'INVALID_VALUE',
  DUPLICATE_ID: 'DUPLICATE_ID',
  UNKNOWN_FIELD: 'UNKNOWN_FIELD',
  INVALID_STRUCTURE: 'INVALID_STRUCTURE'
} as const
```

**Step 2: Verify file creation**

Run: `ls -la frontend/src/types/metadata.ts`

Expected: File exists and is readable

**Step 3: Commit**

```bash
git add frontend/src/types/metadata.ts
git commit -m "feat(types): create unified metadata type definitions

- Add FieldMetadata, FieldDefinition interfaces
- Add LayoutConfig, DifferentialConfig interfaces
- Add SectionConfig, TabConfig, LayoutSection, LayoutTab
- Add FieldOverride, ContainerConfig, LayoutColumn
- Add LayoutAction, ValidationResult, ValidationError
- Add ERROR_CODES constant
- All types use camelCase naming convention
"
```

---

### Task 2: Update types/index.ts to export metadata

**Files:**
- Modify: `frontend/src/types/index.ts:1-43`

**Step 1: Add metadata export after line 23**

Find the section after `export * from './businessObject'` and add:

```typescript
// ========================================
// Metadata Types (NEW)
// ========================================
export * from './metadata'
```

The updated file should look like:

```typescript
/**
 * Unified Type Exports
 *
 * Single source of truth for all low-code platform types.
 * All types use camelCase to match backend djangorestframework-camel-case output.
 *
 * Reference: docs/plans/frontend/TYPE_UNIFICATION_EXECUTION_PLAN.md
 */

// ========================================
// Field Types
// ========================================
export * from './field'

// ========================================
// Layout Types
// ========================================
export * from './layout'

// ========================================
// Business Object Types
// ========================================
export * from './businessObject'

// ========================================
// Metadata Types (NEW)
// ========================================
export * from './metadata'

// ========================================
// Common Types (existing)
// ========================================
export * from './common'

// ========================================
// Other Existing Types
// ========================================
export * from './api'
export * from './assets'
export * from './auth'
export * from './error'
export * from './finance'
export * from './inventory'
export * from './softwareLicenses'
export * from './workflow'
export * from './depreciation'
export * from './models'
```

**Step 2: Verify export works**

Run: `cd frontend && npx tsc --noEmit`

Expected: No errors (the import should resolve)

**Step 3: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat(types): export metadata module from index"
```

---

### Task 3: Update layoutMerge.ts to use unified types

**Files:**
- Modify: `frontend/src/components/designer/services/layoutMerge.ts:10-46`

**Step 1: Remove duplicate type definitions**

Delete lines 16-39 (the duplicate `FieldOverride`, `SectionConfig`, `TabConfig`, `MergedLayout` interfaces).

**Step 2: Update the import statement**

Change line 10 from:
```typescript
import type { FieldMetadata, DifferentialConfig, LayoutConfig } from '@/types/metadata'
```

To:
```typescript
import type {
  FieldMetadata,
  FieldOverride,
  SectionConfig,
  TabConfig,
  DifferentialConfig,
  LayoutConfig
} from '@/types/metadata'
```

**Step 3: Add MergedLayout interface after imports**

Add after the import block (around line 11):

```typescript
// ============================================================================
// Types
// ============================================================================

export interface MergedLayout {
  fields: FieldMetadata[]
  sections: SectionConfig[]
  tabs: TabConfig[]
}
```

**Step 4: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`

Expected: No type errors

**Step 5: Commit**

```bash
git add frontend/src/components/designer/services/layoutMerge.ts
git commit -m "refactor(services): layoutMerge use unified metadata types

- Remove duplicate FieldOverride, SectionConfig, TabConfig definitions
- Import all types from @/types/metadata
- Keep MergedLayout as module-specific export
"
```

---

### Task 4: Update layoutSchema.ts to use unified types

**Files:**
- Modify: `frontend/src/components/designer/services/layoutSchema.ts:10-47`

**Step 1: Remove duplicate type definitions**

Delete lines 16-34 (the duplicate `ValidationResult`, `ValidationError`, `FieldOverride` interfaces).

**Step 2: Update the import statement**

Change line 10 from:
```typescript
import type { DifferentialConfig, SectionConfig, TabConfig, ContainerConfig } from '@/types/metadata'
```

To:
```typescript
import type {
  DifferentialConfig,
  SectionConfig,
  TabConfig,
  ContainerConfig,
  FieldOverride,
  ValidationResult,
  ValidationError
} from '@/types/metadata'
```

**Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`

Expected: No type errors

**Step 4: Commit**

```bash
git add frontend/src/components/designer/services/layoutSchema.ts
git commit -m "refactor(services): layoutSchema use unified metadata types

- Remove duplicate ValidationResult, ValidationError, FieldOverride definitions
- Import all types from @/types/metadata
- Keep module-specific functions unchanged
"
```

---

### Task 5: Update PropertyPanel.vue imports

**Files:**
- Modify: `frontend/src/components/designer/PropertyPanel.vue:1-50`

**Step 1: Read current imports**

Run: `head -50 frontend/src/components/designer/PropertyPanel.vue`

**Step 2: Add metadata type import**

Add after existing type imports (around line 15-20):

```typescript
import type {
  FieldDefinition,
  SectionConfig,
  TabConfig,
  FieldOverride,
  LayoutConfig
} from '@/types/metadata'
```

**Step 3: Remove duplicate local type definitions**

If there are local `LayoutField`, `LayoutSection`, `LayoutTab` interface definitions, delete them and use the imported types instead.

**Step 4: Verify TypeScript compiles**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: No type errors in PropertyPanel.vue

**Step 5: Commit**

```bash
git add frontend/src/components/designer/PropertyPanel.vue
git commit -m "refactor(designer): PropertyPanel use unified metadata types

- Add imports from @/types/metadata
- Remove duplicate local type definitions
"
```

---

### Task 6: Update CanvasArea.vue imports

**Files:**
- Modify: `frontend/src/components/designer/CanvasArea.vue:1-100`

**Step 1: Read current type definitions**

Run: `head -100 frontend/src/components/designer/CanvasArea.vue | grep -A 20 "interface"`

**Step 2: Add metadata type imports**

Find the script setup section and add:

```typescript
import type {
  FieldDefinition,
  SectionConfig,
  TabConfig,
  LayoutConfig
} from '@/types/metadata'
```

**Step 3: Update local interfaces to extend or use imported types**

If there are local interfaces that match the imported ones, update them to extend:

```typescript
// For LayoutField - use imported type
import type { LayoutField } from '@/types/metadata'

// For component-specific field interface with runtime data
interface CanvasField extends LayoutField {
  id: string
}
```

**Step 4: Verify TypeScript compiles**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: No type errors in CanvasArea.vue

**Step 5: Commit**

```bash
git add frontend/src/components/designer/CanvasArea.vue
git commit -m "refactor(designer): CanvasArea use unified metadata types

- Add imports from @/types/metadata
- Update local interfaces to extend imported types
"
```

---

### Task 7: Update LayoutPreview.vue imports

**Files:**
- Modify: `frontend/src/components/designer/LayoutPreview.vue:1-50`

**Step 1: Read current imports**

Run: `head -50 frontend/src/components/designer/LayoutPreview.vue`

**Step 2: Update or add metadata type imports**

Ensure the file imports from `@/types/metadata`:

```typescript
import type {
  FieldDefinition,
  SectionConfig,
  TabConfig,
  LayoutConfig,
  PreviewField
} from '@/types/metadata'
```

**Step 3: Remove duplicate local type definitions**

Delete any local `PreviewField` interface definition since it's now imported.

**Step 4: Verify TypeScript compiles**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: No type errors in LayoutPreview.vue

**Step 5: Commit**

```bash
git add frontend/src/components/designer/LayoutPreview.vue
git commit -m "refactor(designer): LayoutPreview use unified metadata types

- Add imports from @/types/metadata
- Remove duplicate PreviewField definition
"
```

---

### Task 8: Verify TypeScript compilation across entire project

**Files:**
- Test: All frontend TypeScript files

**Step 1: Run full TypeScript check**

Run: `cd frontend && npx tsc --noEmit`

Expected: Zero type errors

**Step 2: Run Vue component type check**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: Zero type errors

**Step 3: Run build**

Run: `cd frontend && npm run build`

Expected: Build completes successfully

**Step 4: Create phase 1 completion tag**

```bash
git tag -a type-unification-phase1 -m "Phase 1 complete: metadata types unified"
git push origin type-unification-phase1
```

**Step 5: Commit verification results**

Create verification log:

```bash
echo "Phase 1 Verification - $(date)" > frontend/type-unification-phase1.log
echo "TypeScript: PASS" >> frontend/type-unification-phase1.log
echo "Vue TSC: PASS" >> frontend/type-unification-phase1.log
echo "Build: PASS" >> frontend/type-unification-phase1.log
git add frontend/type-unification-phase1.log
git commit -m "test: phase 1 verification complete"
```

---

## Phase 2: Naming Convention Unification (Higher Risk)

> **PREREQUISITE:** Verify backend API returns camelCase OR configure backend to do so.
> Run the API format check script before proceeding.

### Task 9: Verify backend API format

**Files:**
- Create: `frontend/scripts/check-api-format.sh`

**Step 1: Create API format verification script**

```bash
#!/bin/bash
# Check backend API response format

echo "=== Checking Backend API Format ==="

# Check if backend is running
if ! curl -s http://localhost:8000/api/ > /dev/null; then
    echo "⚠️ Backend not accessible at http://localhost:8000"
    echo "Skipping API format check"
    exit 0
fi

# Get a sample response (adjust token as needed)
RESPONSE=$(curl -s http://localhost:8000/api/system/field-definitions/?limit=1)

echo "Sample API response:"
echo "$RESPONSE" | head -20

# Check format
if echo "$RESPONSE" | jq -e '.results[0].fieldCode' > /dev/null 2>&1; then
    echo "✅ API returns camelCase format"
    exit 0
elif echo "$RESPONSE" | jq -e '.results[0].field_code' > /dev/null 2>&1; then
    echo "❌ API returns snake_case format"
    echo ""
    echo "Before proceeding with Phase 2, configure backend:"
    echo "1. pip install djangorestframework-camel-case"
    echo "2. Add to settings.REST_FRAMEWORK:"
    echo "   'DEFAULT_RENDERER_CLASSES': ['djangorestframework_camel_case.render.CamelCaseJSONRenderer']"
    echo "   'DEFAULT_PARSER_CLASSES': ['djangorestframework_camel_case.parser.CamelCaseJSONParser']"
    exit 1
else
    echo "⚠️ Could not determine API format"
    exit 0
fi
```

**Step 2: Make executable and run**

Run:
```bash
chmod +x frontend/scripts/check-api-format.sh
cd frontend
./scripts/check-api-format.sh
```

Expected: API returns camelCase OR warning to configure backend

**Step 3: Commit**

```bash
git add frontend/scripts/check-api-format.sh
git commit -m "test(script): add API format verification script"
```

---

### Task 10: Update PropertyPanel.vue property names to camelCase

**Files:**
- Modify: `frontend/src/components/designer/PropertyPanel.vue`

**Step 1: Find all snake_case property usages**

Run:
```bash
grep -n "field_code\|default_value\|help_text\|custom_class\|sort_order\|section_name\|is_required\|is_readonly\|is_reverse_relation\|relation_display_mode\|show_in_form\|show_in_list" \
  frontend/src/components/designer/PropertyPanel.vue
```

**Step 2: Replace snake_case with camelCase in template**

For each occurrence, replace:
- `field_code` → `fieldCode`
- `default_value` → `defaultValue`
- `help_text` → `helpText`
- `custom_class` → `customClass`
- `sort_order` → `sortOrder`
- `section_name` → `sectionName`
- `is_required` → `isRequired`
- `is_readonly` → `isReadonly` (already correct in FieldMetadata)
- `is_reverse_relation` → `isReverseRelation`
- `relation_display_mode` → `relationDisplayMode`
- `show_in_form` → `showInForm`
- `show_in_list` → `showInList`

**Step 3: Replace in script section**

Same replacements as above.

**Step 4: Verify TypeScript compiles**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: No type errors

**Step 5: Commit**

```bash
git add frontend/src/components/designer/PropertyPanel.vue
git commit -m "refactor(designer): PropertyPanel use camelCase property names

- Replace field_code with fieldCode
- Replace default_value with defaultValue
- Replace help_text with helpText
- Replace custom_class with customClass
- Replace sort_order with sortOrder
- Replace section_name with sectionName
- Replace is_required with isRequired
- Replace is_reverse_relation with isReverseRelation
- Replace relation_display_mode with relationDisplayMode
- Replace show_in_form with showInForm
- Replace show_in_list with showInList
"
```

---

### Task 11: Update CanvasArea.vue property names to camelCase

**Files:**
- Modify: `frontend/src/components/designer/CanvasArea.vue`

**Step 1: Find all snake_case property usages**

Run:
```bash
grep -n "field_code\|default_value\|help_text\|custom_class\|span\|readonly\|visible\|required" \
  frontend/src/components/designer/CanvasArea.vue
```

**Step 2: Replace snake_case with camelCase**

Same replacements as Task 10.

**Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: No type errors

**Step 4: Commit**

```bash
git add frontend/src/components/designer/CanvasArea.vue
git commit -m "refactor(designer): CanvasArea use camelCase property names

- Replace field_code with fieldCode
- Replace default_value with defaultValue
- Replace help_text with helpText
- Replace custom_class with customClass
"
```

---

### Task 12: Update LayoutPreview.vue property names to camelCase

**Files:**
- Modify: `frontend/src/components/designer/LayoutPreview.vue`

**Step 1: Find all snake_case property usages**

Run:
```bash
grep -n "field_code\|default_value\|help_text\|custom_class" \
  frontend/src/components/designer/LayoutPreview.vue
```

**Step 2: Replace snake_case with camelCase**

Same replacements as Task 10.

**Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: No type errors

**Step 4: Commit**

```bash
git add frontend/src/components/designer/LayoutPreview.vue
git commit -m "refactor(designer): LayoutPreview use camelCase property names

- Replace field_code with fieldCode
- Replace default_value with defaultValue
- Replace help_text with helpText
- Replace custom_class with customClass
"
```

---

### Task 13: Update layoutMerge.ts property names to camelCase

**Files:**
- Modify: `frontend/src/components/designer/services/layoutMerge.ts:60-245`

**Step 1: Find all snake_case property usages**

Run:
```bash
grep -n "sort_order\|section_name\|is_reverse_relation\|relation_display_mode\|default_value" \
  frontend/src/components/designer/services/layoutMerge.ts
```

**Step 2: Replace in code**

Replace:
- Line 80: `a.sort_order ?? 0` → `a.sortOrder ?? 0`
- Line 80: `b.sort_order ?? 0` → `b.sortOrder ?? 0`
- Line 135: `a.sort_order ?? 0` → `a.sortOrder ?? 0`
- Line 135: `b.sort_order ?? 0` → `b.sortOrder ?? 0`
- Line 155: `f.is_reverse_relation` → `f.isReverseRelation`
- Line 165: `field.section_name` → `field.sectionName`
- Line 204: `f.is_reverse_relation` → `f.isReverseRelation`
- Line 214: `relation.relation_display_mode` → `relation.relationDisplayMode`

**Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`

Expected: No type errors

**Step 4: Commit**

```bash
git add frontend/src/components/designer/services/layoutMerge.ts
git commit -m "refactor(services): layoutMerge use camelCase property names

- Replace sort_order with sortOrder
- Replace section_name with sectionName
- Replace is_reverse_relation with isReverseRelation
- Replace relation_display_mode with relationDisplayMode
"
```

---

### Task 14: Update layoutSchema.ts property names to camelCase

**Files:**
- Modify: `frontend/src/components/designer/services/layoutSchema.ts`

**Step 1: Find all snake_case property usages**

Run:
```bash
grep -n "default_value" frontend/src/components/designer/services/layoutSchema.ts
```

**Step 2: Replace in code**

Replace `default_value` with `defaultValue` in FieldOverride references.

**Step 3: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit`

Expected: No type errors

**Step 4: Commit**

```bash
git add frontend/src/components/designer/services/layoutSchema.ts
git commit -m "refactor(services): layoutSchema use camelCase property names

- Replace default_value with defaultValue in FieldOverride usage
"
```

---

### Task 15: Final verification and cleanup

**Files:**
- Test: All modified files

**Step 1: Run full TypeScript check**

Run: `cd frontend && npx tsc --noEmit`

Expected: Zero errors

**Step 2: Run Vue component type check**

Run: `cd frontend && npx vue-tsc --noEmit`

Expected: Zero errors

**Step 3: Run build**

Run: `cd frontend && npm run build`

Expected: Build completes successfully

**Step 4: Check for remaining snake_case**

Run:
```bash
grep -r "field_code\|default_value\|help_text\|custom_class\|sort_order\|section_name\|is_required\|is_readonly\|is_reverse_relation\|relation_display_mode\|show_in_form\|show_in_list" \
  frontend/src/components/designer/ \
  --include="*.vue" --include="*.ts" \
  | grep -v "// " | grep -v "^\s*//" | grep -v "\.camelCase" || echo "No remaining snake_case found"
```

Expected: No remaining snake_case property references (excluding comments)

**Step 5: Run linting**

Run: `cd frontend && npm run lint`

Expected: No lint errors (or only auto-fixable warnings)

**Step 6: Create completion tag**

```bash
git tag -a type-unification-complete -m "Type unification complete - Phase 1 & 2"
git push origin type-unification-complete
```

**Step 7: Final commit**

```bash
git add -A
git commit -m "feat: complete layout type unification

Phase 1 (Type File Creation):
- Created frontend/src/types/metadata.ts with all unified types
- Updated types/index.ts to export metadata module
- Removed duplicate types from layoutMerge.ts
- Removed duplicate types from layoutSchema.ts
- Updated all designer components to use unified types

Phase 2 (Naming Convention Unification):
- Updated PropertyPanel.vue to use camelCase
- Updated CanvasArea.vue to use camelCase
- Updated LayoutPreview.vue to use camelCase
- Updated layoutMerge.ts to use camelCase
- Updated layoutSchema.ts to use camelCase

All TypeScript compilation passes.
All Vue component type checks pass.
Build completes successfully.
"
```

---

## Testing Checklist

After completing all tasks, verify the following:

### Manual Testing

- [ ] Open layout designer page (`/system/layouts/designer`)
- [ ] Verify no console errors
- [ ] Drag a field to canvas - should work
- [ ] Click field to open property panel - should display properties
- [ ] Edit field properties - should update preview
- [ ] Save layout - should succeed
- [ ] Load saved layout - should display correctly

### Automated Testing

- [ ] `npx tsc --noEmit` - No errors
- [ ] `npx vue-tsc --noEmit` - No errors
- [ ] `npm run build` - Success
- [ ] `npm run lint` - No errors (or warnings only)

### Regression Testing

- [ ] Asset list page loads correctly
- [ ] Asset form renders with correct layout
- [ ] Asset detail page displays correctly
- [ ] Other business objects work correctly

---

## Rollback Plan

If issues arise:

```bash
# Rollback to Phase 1 completion
git checkout type-unification-phase1

# Or rollback to before any changes
git checkout main
```

---

## References

- PRD: `docs/plans/2026-02-04-layout-type-unification.md`
- Backend settings: `backend/config/settings/base.py`
- Django camelCase package: https://github.com/vbabiy/djangorestframework-camel-case
