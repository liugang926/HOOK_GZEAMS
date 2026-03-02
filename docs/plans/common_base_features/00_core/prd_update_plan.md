# Frontend PRD Update Plan - API Standardization

## Document Information

| Project | Details |
|---------|---------|
| Plan Version | v1.0 |
| Created Date | 2026-01-22 |
| Purpose | Update all frontend PRDs to align with API standardization design |
| Reference | [frontend_api_standardization_design.md](./frontend_api_standardization_design.md) |

---

## 1. Update Strategy

### 1.1 Standard Sections to Add/Update

Each frontend PRD will be updated with the following standardized sections:

| Section | Content | Status |
|---------|---------|--------|
| **API Service Layer** | Typed API service functions | To Add |
| **Type Definitions** | TypeScript interfaces for models | To Add |
| **Component Examples** | Updated with camelCase usage | To Update |
| **Error Handling** | Standardized error code usage | To Add |
| **Request/Response** | Unified format examples | To Add |

### 1.2 Standard Code Template

All PRD code examples MUST follow this template:

```typescript
// API Service Template
import request from '@/utils/request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'

export const {moduleName}Api = {
  list(filters?: {ModuleName}Filters): Promise<PaginatedResponse<{ModuleName}>> {
    return request.get('/{api-path}/', { params: filters })
  },

  get(id: string): Promise<{ModuleName}> {
    return request.get(`/{api-path}/${id}/`)
  },

  create(data: {ModuleName}Create): Promise<{ModuleName}> {
    return request.post('/{api-path}/', data)
  },

  update(id: string, data: {ModuleName}Update): Promise<{ModuleName}> {
    return request.put(`/{api-path}/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/{api-path}/${id}/`)
  }
}
```

---

## 2. PRD Files Requiring Updates

### Phase 1: Core Asset Management

| File | Priority | Changes Required |
|------|----------|------------------|
| `phase1_1_asset_category/frontend.md` | HIGH | Fix mixed naming, add types, update error handling |
| `phase1_2_multi_organization/frontend.md` | HIGH | Add types, update error handling |
| `phase1_2_organizations_module/frontend.md` | HIGH | Add types, unify API pattern |
| `phase1_3_business_metadata/frontend.md` | HIGH | Add types, document metadata APIs |
| `phase1_4_asset_crud/frontend.md` | HIGH | Add types, standardize CRUD |
| `phase1_5_asset_operations/frontend.md` | HIGH | Add types, standardize operations |
| `phase1_6_consumables/frontend.md` | MEDIUM | Add types, standardize APIs |
| `phase1_7_asset_lifecycle/frontend.md` | MEDIUM | Add types, document lifecycle |
| `phase1_8_mobile_enhancement/frontend.md` | HIGH | Fix sync response format, add types |
| `phase1_9_notification_enhancement/frontend.md` | MEDIUM | Add types, standardize notification APIs |

### Phase 2: Organization & SSO

| File | Priority | Changes Required |
|------|----------|------------------|
| `phase2_1_wework_sso/frontend.md` | HIGH | Add types, unify auth handling |
| `phase2_2_wework_sync/frontend.md` | HIGH | Add types, fix polling patterns |
| `phase2_3_notification/frontend.md` | MEDIUM | Add types, standardize APIs |
| `phase2_4_org_enhancement/frontend.md` | HIGH | Add types, unify org APIs |
| `phase2_5_permission_enhancement/frontend.md` | HIGH | Add types, document permission APIs |

### Phase 3: Workflow Engine

| File | Priority | Changes Required |
|------|----------|------------------|
| `phase3_1_logicflow/frontend.md` | MEDIUM | Add types, document workflow APIs |
| `phase3_2_workflow_engine/frontend.md` | HIGH | Add types, unify task APIs |

### Phase 4: Inventory Management

| File | Priority | Changes Required |
|------|----------|------------------|
| `phase4_1_inventory_qr/frontend.md` | HIGH | Add types, fix snake_case usage |
| `phase4_2_inventory_rfid/frontend.md` | MEDIUM | Add types, standardize RFID APIs |
| `phase4_3_inventory_snapshot/frontend.md` | HIGH | Fix snake_case, add types |
| `phase4_4_inventory_assignment/frontend.md` | MEDIUM | Add types, standardize APIs |
| `phase4_5_inventory_reconciliation/frontend.md` | HIGH | Fix snake_case, add types |

### Phase 5: Integration & Finance

| File | Priority | Changes Required |
|------|----------|------------------|
| `phase5_0_integration_framework/frontend.md` | HIGH | Add types, standardize integration APIs |
| `phase5_1_m18_adapter/frontend.md` | HIGH | Add types, document M18 APIs |
| `phase5_2_finance_integration/frontend.md` | MEDIUM | Add types, standardize finance APIs |
| `phase5_3_depreciation/frontend.md` | MEDIUM | Add types, document depreciation |
| `phase5_4_finance_reports/frontend.md` | LOW | Add types, document reports |

### Phase 6: User Portal

| File | Priority | Changes Required |
|------|----------|------------------|
| `phase6_user_portal/frontend.md` | CRITICAL | Add missing backend APIs, types |

### Phase 7: Enhancements

| File | Priority | Changes Required |
|------|----------|------------------|
| `phase7_1_asset_loan_enhancement/frontend.md` | MEDIUM | Add types, standardize loan APIs |
| `phase7_2_asset_project/frontend.md` | LOW | Add types, document project APIs |
| `phase7_3_asset_tags/frontend.md` | LOW | Add types, standardize tag APIs |
| `phase7_4_smart_search/frontend.md` | HIGH | Add types, document search APIs |

---

## 3. Standard PRD Section Template

### 3.1 API Service Layer Section

```markdown
## API Service Layer

All API calls MUST go through typed service functions in `src/api/{module}.ts`.

### Type Definitions

```typescript
// src/types/models/{module}.ts
export interface {Model} {
  id: string
  // All fields in camelCase
  createdAt: string
  updatedAt: string
  organizationId: string
  isDeleted: boolean
}

export interface {Model}Create {
  // Create fields
}

export interface {Model}Update extends Partial<{Model}Create> {}

export interface {Model}Filters {
  page?: number
  pageSize?: number
  search?: string
  // Module-specific filters
}
```

### API Methods

```typescript
// src/api/{module}.ts
import request from '@/utils/request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type { {Model}, {Model}Create, {Model}Update, {Model}Filters } from '@/types/models/{module}'

export const {module}Api = {
  // List with pagination
  list(filters?: {Module}Filters): Promise<PaginatedResponse<{Model}>> {
    return request.get('/{api-path}/', { params: filters })
  },

  // Get single record
  get(id: string): Promise<{Model}> {
    return request.get(`/{api-path}/${id}/`)
  },

  // Create new record
  create(data: {Model}Create): Promise<{Model}> {
    return request.post('/{api-path}/', data)
  },

  // Update record
  update(id: string, data: {Model}Update): Promise<{Model}> {
    return request.put(`/{api-path}/${id}/`, data)
  },

  // Partial update
  partialUpdate(id: string, data: Partial<{Model}Update>): Promise<{Model}> {
    return request.patch(`/{api-path}/${id}/`, data)
  },

  // Delete (soft delete)
  delete(id: string): Promise<void> {
    return request.delete(`/{api-path}/${id}/`)
  },

  // Batch delete
  batchDelete(ids: string[]): Promise<BatchResponse> {
    return request.post('/{api-path}/batch-delete/', { ids })
  }
}
```
```

### 3.2 Error Handling Section

```markdown
## Error Handling

All API calls are automatically handled by the axios interceptor. Components should use try-catch for specific error handling:

```vue
<script setup lang="ts">
import { ElMessage } from 'element-plus'

const handleSubmit = async () => {
  try {
    await moduleApi.create(formData.value)
    ElMessage.success('创建成功')
    // Navigate or refresh
  } catch (error) {
    // Error already handled by interceptor
    // Optional: Add specific handling here
  }
}
</script>
```

### Standard Error Codes

| Error Code | HTTP Status | User Message |
|------------|-------------|--------------|
| VALIDATION_ERROR | 400 | 请求数据验证失败 |
| UNAUTHORIZED | 401 | 未授权访问，请重新登录 |
| PERMISSION_DENIED | 403 | 权限不足 |
| NOT_FOUND | 404 | 请求的资源不存在 |
| ORGANIZATION_MISMATCH | 403 | 组织不匹配 |
| SOFT_DELETED | 410 | 资源已被删除 |
| SERVER_ERROR | 500 | 服务器错误，请稍后再试 |
```

### 3.3 Component Integration Section

```markdown
## Component Integration

### Using BaseListPage

```vue
<template>
  <BaseListPage
    title="{Module} List"
    :fetch-method="moduleApi.list"
    :delete-method="handleDelete"
    :batch-delete-method="moduleApi.batchDelete"
    :columns="columns"
    :search-fields="searchFields"
  />
</template>

<script setup lang="ts">
import { moduleApi } from '@/api/{module}'

// All field names in camelCase
const columns = [
  { prop: 'fieldName', label: 'Field Label', width: 150 },
  // ...
]

const searchFields = [
  { prop: 'keyword', label: 'Search', placeholder: '...' }
]
</script>
```
```

---

## 4. Execution Plan

### Week 1: High Priority (Phase 1-2)

1. Update `phase1_1_asset_category/frontend.md`
2. Update `phase1_2_multi_organization/frontend.md`
3. Update `phase1_2_organizations_module/frontend.md`
4. Update `phase1_3_business_metadata/frontend.md`
5. Update `phase1_5_asset_operations/frontend.md`
6. Update `phase2_1_wework_sso/frontend.md`
7. Update `phase2_4_org_enhancement/frontend.md`
8. Update `phase2_5_permission_enhancement/frontend.md`

### Week 2: High Priority (Phase 3-6)

1. Update `phase3_2_workflow_engine/frontend.md`
2. Update `phase4_1_inventory_qr/frontend.md`
3. Update `phase4_3_inventory_snapshot/frontend.md`
4. Update `phase4_5_inventory_reconciliation/frontend.md`
5. Update `phase5_0_integration_framework/frontend.md`
6. Update `phase5_1_m18_adapter/frontend.md`
7. Update `phase6_user_portal/frontend.md` (CRITICAL - includes missing APIs)

### Week 3: Medium Priority

1. Update remaining Phase 1 PRDs
2. Update remaining Phase 2 PRDs
3. Update remaining Phase 3 PRDs
4. Update remaining Phase 4 PRDs

### Week 4: Low Priority (Phase 5-7)

1. Update remaining Phase 5 PRDs
2. Update Phase 7 PRDs
3. Update user interaction design PRDs

---

## 5. Update Checklist

For each PRD file, verify:

- [ ] All API code examples use TypeScript
- [ ] All field names are camelCase in frontend code
- [ ] API service follows the standard template
- [ ] Type definitions are provided
- [ ] Error handling examples are included
- [ ] Component examples use BaseListPage/BaseFormPage
- [ ] Batch operations follow standard format
- [ ] References to common components are correct

---

## 6. Notes for Each Phase

### Phase 1 Notes
- Asset category PRD has the worst field naming issues (mixed camelCase/snake_case)
- Organization module uses different API pattern - needs unification
- Mobile sync response format doesn't match standard

### Phase 2 Notes
- SSO login needs careful handling of token management
- Permission system has complex field-level permission types
- Organization enhancement has duplicate endpoints with Phase 1.2

### Phase 3 Notes
- LogicFlow is a third-party library - document integration carefully
- Workflow engine needs to align with user portal task APIs

### Phase 4 Notes
- Inventory modules have the most snake_case leakage
- Snapshot and reconciliation PRDs need field name fixes

### Phase 5 Notes
- Integration framework needs async operation handling
- M18 adapter needs specific error handling for external API failures

### Phase 6 Notes
- **CRITICAL**: Many APIs are missing - backend needs to implement first
- Field configuration system is a dependency for all modules

### Phase 7 Notes
- Smart search overlaps with global search - needs coordination
- Asset tags depend on Tag model which needs documentation
