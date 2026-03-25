# Frontend Architecture Unification - Implementation Plan

## Document Information
| Project | Details |
|---------|---------|
| Plan Version | v1.0 |
| Created | 2026-02-02 |
| Status | Ready for Execution |
| PRD Reference | docs/plans/2026-02-02-frontend-architecture-unification.md |

---

## Executive Summary

**Goal**: Consolidate type definitions and unify directory structure for the low-code frontend.

**Current State Assessment**:
- ✅ Types folder already exists (`types/field.ts`, `types/layout.ts`, `types/businessObject.ts`)
- ✅ `composables/` folder exists with some composables
- ⚠️ `hooks/` folder still exists with duplicate functionality
- ⚠️ Some imports still use old patterns

**Remaining Work**:
1. Move `useMetadata.ts` from `hooks/` to `composables/`
2. Update import paths across the codebase
3. Consolidate remaining hooks (useFileField, useTableConfig, useColumnConfig, useLoading)
4. Remove empty `hooks/` directory after migration

---

## Current File Inventory

### Already Unified ✅
| File | Location | Status |
|------|----------|--------|
| Field types | `types/field.ts` | ✅ Complete - 287 lines |
| Layout types | `types/layout.ts` | ✅ Complete - 292 lines |
| Business Object types | `types/businessObject.ts` | ✅ Complete - 273 lines |
| Types index | `types/index.ts` | ✅ Complete - exports all types |

### Need Migration ⚠️
| File | From | To | Priority |
|-----|------|-----|----------|
| useMetadata.ts | `hooks/useMetadata.ts` | `composables/useMetadata.ts` | HIGH |
| useFileField.ts | `hooks/useFileField.ts` | `composables/useFileField.ts` | MEDIUM |
| useTableConfig.ts | `hooks/useTableConfig.ts` | `composables/useTableConfig.ts` | MEDIUM |
| useColumnConfig.ts | `hooks/useColumnConfig.ts` | `composables/useColumnConfig.ts` | MEDIUM |
| useLoading.ts | `hooks/useLoading.ts` | `composables/useLoading.ts` | LOW |

### Existing Composables ✅
| File | Location | Status |
|------|----------|--------|
| useLayoutHistory.ts | `composables/useLayoutHistory.ts` | ✅ Already in place |
| useCrud.ts | `composables/useCrud.ts` | ✅ Already in place |
| useBusinessRules.ts | `composables/useBusinessRules.ts` | ✅ Already in place |

---

## Import Dependencies Analysis

### Files importing from `@/hooks`:
| File | Import | Needs Update |
|------|--------|--------------|
| `components/engine/hooks/useDynamicForm.ts` | `import { useMetadata } from '@/hooks/useMetadata'` | ✅ Yes |
| `components/engine/fields/FileDisplayField.vue` | `import { useFileField, type FileDisplayItem } from '@/hooks'` | ✅ Yes |
| `components/engine/fields/ImageField.vue` | `import { useFileField, type FileDisplayItem, type FileUploadContext } from '@/hooks'` | ✅ Yes |

### Files importing from `@/hooks/useMetadata` directly:
| File | Import | Needs Update |
|------|--------|--------------|
| `components/engine/hooks/useDynamicForm.ts` | `from '@/hooks/useMetadata'` | ✅ Yes |

---

## Implementation Phases

### Phase 1: Move useMetadata (HIGH PRIORITY)

**Objective**: Move `useMetadata.ts` to `composables/` and update all imports.

#### Step 1.1: Create composables/index.ts
**File**: `frontend/src/composables/index.ts`

```typescript
/**
 * Composables index - Central export point for all Vue composables
 */

// Metadata composables
export * from './useMetadata'

// CRUD composables
export * from './useCrud'

// Layout composables
export * from './useLayoutHistory'

// Business rules composables
export * from './useBusinessRules'
```

**Command**:
```bash
# Create the index file
cd frontend/src
New-Item -Path composables -Name index.ts -Value (Get-Content composables\index_template.txt)
```

#### Step 1.2: Move useMetadata.ts to composables/
**File**: `frontend/src/composables/useMetadata.ts`

**Action**: Copy the entire file from `hooks/useMetadata.ts` to `composables/useMetadata.ts`

**Command**:
```bash
cd frontend/src
Copy-Item hooks\useMetadata.ts composables\useMetadata.ts
```

#### Step 1.3: Update imports in useDynamicForm.ts
**File**: `frontend/src/components/engine/hooks/useDynamicForm.ts`

**Change line 12**:
```typescript
// Before:
import { useMetadata } from '@/hooks/useMetadata'

// After:
import { useMetadata } from '@/composables/useMetadata'
```

**Edit command**:
```bash
# In useDynamicForm.ts, line 12
# Replace: import { useMetadata } from '@/hooks/useMetadata'
# With: import { useMetadata } from '@/composables/useMetadata'
```

#### Step 1.4: Verify TypeScript compilation
**Command**:
```bash
cd frontend
npm run build -- --mode development
```

**Expected output**: No TypeScript errors related to useMetadata imports.

---

### Phase 2: Consolidate useFileField (MEDIUM PRIORITY)

**Objective**: Move `useFileField.ts` and update imports.

#### Step 2.1: Copy useFileField.ts to composables/
**File**: `frontend/src/composables/useFileField.ts`

**Command**:
```bash
cd frontend/src
Copy-Item hooks\useFileField.ts composables\useFileField.ts
```

#### Step 2.2: Update imports in FileDisplayField.vue
**File**: `frontend/src/components/engine/fields/FileDisplayField.vue`

**Change line 108**:
```typescript
// Before:
import { useFileField, type FileDisplayItem } from '@/hooks'

// After:
import { useFileField, type FileDisplayItem } from '@/composables'
```

#### Step 2.3: Update imports in ImageField.vue
**File**: `frontend/src/components/engine/fields/ImageField.vue`

**Change line 185**:
```typescript
// Before:
import { useFileField, type FileDisplayItem, type FileUploadContext } from '@/hooks'

// After:
import { useFileField, type FileDisplayItem, type FileUploadContext } from '@/composables'
```

#### Step 2.4: Update composables/index.ts
**File**: `frontend/src/composables/index.ts`

Add line:
```typescript
// File field composables
export * from './useFileField'
```

---

### Phase 3: Move Remaining Hooks (MEDIUM PRIORITY)

#### Step 3.1: Move useTableConfig.ts
**Command**:
```bash
cd frontend/src
Copy-Item hooks\useTableConfig.ts composables\useTableConfig.ts
```

#### Step 3.2: Move useColumnConfig.ts
**Command**:
```bash
cd frontend/src
Copy-Item hooks\useColumnConfig.ts composables\useColumnConfig.ts
```

#### Step 3.3: Move useLoading.ts
**Command**:
```bash
cd frontend/src
Copy-Item hooks\useLoading.ts composables\useLoading.ts
```

#### Step 3.4: Update composables/index.ts
**File**: `frontend/src/composables/index.ts`

```typescript
/**
 * Composablesables index - Central export point for all Vue composables
 */

// Metadata composables
export * from './useMetadata'

// CRUD composables
export * from './useCrud'

// Layout composables
export * from './useLayoutHistory'

// Business rules composables
export * from './useBusinessRules'

// File field composables
export * from './useFileField'

// Table config composables
export * from './useTableConfig'

// Column config composables
export * from './useColumnConfig'

// Loading composables
export * from './useLoading'
```

---

### Phase 4: Find and Update All Remaining Imports

#### Step 4.1: Search for remaining `@/hooks` imports
**Command**:
```bash
cd frontend/src
Select-String -Path "*.ts","*.vue" -Pattern "from ['"]@/hooks" -Recurse
```

#### Step 4.2: Search for remaining `@/hooks/useMetadata` imports
**Command**:
```bash
cd frontend/src
Select-String -Path "*.ts","*.vue" -Pattern "from ['"]@/hooks/useMetadata" -Recurse
```

#### Step 4.3: Update all found imports
For each file found, replace:
- `from '@/hooks'` → `from '@/composables'`
- `from '@/hooks/useMetadata'` → `from '@/composables/useMetadata'`
- `from '@/hooks/useFileField'` → `from '@/composables/useFileField'`
- etc.

---

### Phase 5: Cleanup (LOW PRIORITY)

#### Step 5.1: Remove old hooks directory
**Command**:
```bash
cd frontend/src
Remove-Item hooks\useMetadata.ts
Remove-Item hooks\useFileField.ts
Remove-Item hooks\useTableConfig.ts
Remove-Item hooks\useColumnConfig.ts
Remove-Item hooks\useLoading.ts
Remove-Item hooks\index.ts
Remove-Item hooks\
```

**⚠️ WARNING**: Only do this after verifying all imports are updated!

---

## Verification Checklist

After each phase, run the following checks:

### 1. TypeScript Compilation
```bash
cd frontend
npm run build
```
**Expected**: No TypeScript errors

### 2. Lint Check
```bash
cd frontend
npm run lint
```
**Expected**: No lint errors related to imports

### 3. Development Server
```bash
cd frontend
npm run dev
```
**Expected**: Server starts without errors

### 4. Runtime Tests
```bash
# Test that forms load correctly
# Test that metadata is fetched
# Test that file uploads work
```

---

## Rollback Plan

If anything breaks, rollback steps:

### Rollback Phase 1:
```bash
cd frontend/src
# Revert useDynamicForm.ts import
# Delete composables/useMetadata.ts
```

### Rollback Phase 2:
```bash
cd frontend/src
# Revert FileDisplayField.vue import
# Revert ImageField.vue import
# Delete composables/useFileField.ts
```

### Full Rollback:
```bash
git checkout frontend/src/hooks
git checkout frontend/src/composables
git checkout frontend/src/components
```

---

## File-by-File Changes Summary

### Files to Create
| File | Lines | Description |
|------|-------|-------------|
| `composables/index.ts` | ~25 | Central export point |
| `composables/useMetadata.ts` | ~465 | Moved from hooks |
| `composables/useFileField.ts` | ~200 | Moved from hooks |
| `composables/useTableConfig.ts` | ~100 | Moved from hooks |
| `composables/useColumnConfig.ts` | ~150 | Moved from hooks |
| `composables/useLoading.ts` | ~50 | Moved from hooks |

### Files to Modify
| File | Lines Changed | Description |
|------|---------------|-------------|
| `components/engine/hooks/useDynamicForm.ts` | 1 | Import path |
| `components/engine/fields/FileDisplayField.vue` | 1 | Import path |
| `components/engine/fields/ImageField.vue` | 1 | Import path |

### Files to Delete (After Verification)
| File | Action |
|------|--------|
| `hooks/useMetadata.ts` | Delete |
| `hooks/useFileField.ts` | Delete |
| `hooks/useTableConfig.ts` | Delete |
| `hooks/useColumnConfig.ts` | Delete |
| `hooks/useLoading.ts` | Delete |
| `hooks/index.ts` | Delete |
| `hooks/` directory | Delete if empty |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Import path errors | Medium | High | Comprehensive testing after each phase |
| Runtime errors | Low | High | Development server verification |
| Breaking existing code | Low | Medium | Git checkpoints after each phase |
| Incomplete migration | Low | Medium | Grep search for remaining imports |

---

## Success Criteria

- [ ] All imports use `@/composables` or `@/types`
- [ ] No TypeScript errors
- [ ] No lint errors
- [ ] Development server runs without errors
- [ ] All forms render correctly
- [ ] Metadata fetching works
- [ ] File uploads work
- [ ] No `@/hooks` imports remain in codebase
- [ ] `hooks/` directory can be safely removed

---

## Next Steps

1. **Execute Phase 1** (useMetadata migration)
2. **Verify and test**
3. **Execute Phase 2** (useFileField migration)
4. **Verify and test**
5. **Execute Phase 3** (Remaining hooks)
6. **Execute Phase 4** (Find all remaining imports)
7. **Execute Phase 5** (Cleanup)

---

## Related Documents

- PRD: `docs/plans/2026-02-02-frontend-architecture-unification.md`
- Type Definitions: `frontend/src/types/`
- Existing Composables: `frontend/src/composables/`
