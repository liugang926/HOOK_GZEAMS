# Frontend Architecture Unification PRD

## Status: ✅ COMPLETED (2026-02-03)

---

## 1. Overview

### 1.1 Objective

**合并类型定义，统一命名规范** - 已完成

### 1.2 Completed Work

| ✅ 操作 | 说明 |
|---------|------|
| 合并 `FieldDefinition` 接口 | 3 处定义 → 1 处 (`types/field.ts`) |
| 统一命名为 camelCase | `field_type` → `fieldType` |
| 整理目录结构 | `hooks/` → `composables/` |
| 布局设计器更新 | `field_code` → `fieldCode` |

---

## 2. Final Architecture

```
frontend/src/
├── types/                        # ✅ Single source of truth
│   ├── field.ts                  # 287 lines - FieldDefinition, FieldType
│   ├── layout.ts                 # 292 lines - PageLayout, LayoutConfig
│   ├── businessObject.ts         # 273 lines - BusinessObject, ObjectMetadata
│   └── index.ts                  # Re-exports all types
│
├── composables/                  # ✅ Migrated from hooks/
│   ├── useMetadata.ts            # 465 lines - Metadata operations
│   ├── useCrud.ts
│   ├── useLayoutHistory.ts
│   ├── useBusinessRules.ts
│   ├── useFileField.ts
│   ├── useTableConfig.ts
│   ├── useColumnConfig.ts
│   ├── useLoading.ts
│   └── index.ts                  # Central exports
│
├── api/
│   └── dynamic.ts                # ✅ Imports from @/types
│
└── components/engine/hooks/
    ├── useDynamicForm.ts         # ✅ Imports from @/types
    ├── useFormula.ts             # ✅ Imports from @/types
    └── useFieldPermissions.ts    # ✅ Imports from @/types
```

---

## 3. Migration Completed

| Phase | Status | Details |
|-------|--------|---------|
| Phase 1: Create Types | ✅ | `types/field.ts`, `layout.ts`, `businessObject.ts` |
| Phase 2: Update Imports | ✅ | 5 files updated to use `@/types` |
| Phase 3: Move Files | ✅ | `hooks/` deleted, `useMetadata` moved to `composables/` |
| Phase 4: Layout Designer | ✅ | All snake_case converted to camelCase |
| Phase 5: Database Migration | ⏳ | Optional - existing data compatible |

---

## 4. Files Using `@/types`

| File | Imports |
|------|---------|
| `composables/useMetadata.ts` | FieldDefinition, BusinessObject, PageLayout, LayoutConfig, etc. |
| `components/engine/hooks/useDynamicForm.ts` | FieldDefinition, LayoutSection |
| `components/engine/hooks/useFormula.ts` | FieldDefinition |
| `components/engine/hooks/useFieldPermissions.ts` | FieldDefinition |
| `api/dynamic.ts` | FieldDefinition, ObjectMetadata |

---

## 5. Verification

- [x] TypeScript compilation passes
- [x] Layout designer preview works
- [x] Dynamic forms render correctly
- [x] No snake_case in layout designer
- [x] `hooks/` directory removed
- [x] `composables/index.ts` exports useMetadata

---

## 6. Optional Cleanup

`api/system.ts` still has local type definitions that could be migrated to `@/types`:
- Line 182: `interface FieldDefinition`
- Line 201: `interface PageLayout`

These are not blocking issues as they are API-layer specific definitions.

---

**Completed by**: User + AI Assistant  
**Completion Date**: 2026-02-03
