# GZEAMS Frontend Code Analysis & Optimization Report

## 1. Overview
This report analyzes the current state of the GZEAMS frontend codebase, focusing on PRD compliance, common model definitions, and API implementation patterns.

**Date**: 2026-01-26
**Scope**: Frontend (`frontend/src`)

## 2. PRD Compliance & Model Analysis
Based on the review of `FRONTEND_PRD_COMPLIANCE_REPORT.md` and source code:
- **Compliance Rate**: ~93.9%
- **Core Models**: usage of `BaseModel` in `src/types/common.ts` is well-structured and consistent with the backend's base model design (soft delete, organization isolation, audit fields).
- **Type Safety**: TypeScript definitions are generally good, but there is noticeable usage of `any` in API return types (e.g., `LocationApi.list()` returns `Promise<any[]>`).

## 3. Codebase "Smells" & Issues

### 3.1. API Service Design (High Redundancy)
Currently, each API service file (e.g., `assets.ts`, `workflow.ts`) manually implements standard CRUD operations (`list`, `get`, `create`, `update`, `delete`).
- **Issue**: This results in ~80% code duplication across the `api/` directory.
- **Risk**: Inconsistent error handling or parameter formatting (e.g., pagination params) if one file is updated but others are missed.
- **Code Example**:
  ```typescript
  // Repeated in almost every file
  list(params) { return request.get('/resource/', { params }) }
  get(id) { return request.get(`/resource/${id}/`) }
  ```

### 3.2. URL Naming Inconsistencies
- **Finding**: The codebase mixes snake_case and kebab-case for URL segments.
- **Example**: `workflow.ts` uses `/workflows/tasks/my_tasks/` (snake_case) while the standard is typically kebab-case (`my-tasks`). The PRD compliance report identified this as a cause for 404 errors.

### 3.3. Hidden Complexity in Data Transformation
- **Observation**: `src/utils/request.ts` uses interceptors to automatically convert snake_case (Backend) <-> camelCase (Frontend).
- **Pros**: Keeps frontend code clean (camelCase).
- **Cons**: Can obscure bugs where specific fields *must* be snake_case (e.g., specific JSON query parameters or form data). "Magic" behavior can be hard to debug.

## 4. Optimization Recommendations

### 4.1. Refactor API Layer with `BaseApiService` (High Impact)
Create a generic base class to handle standard REST operations. This will drastically reduce code volume and ensure consistency.

**Proposed Implementation**:
```typescript
// src/api/base.ts
export class BaseApiService<T> {
  protected resource: string;

  constructor(resource: string) {
    this.resource = resource;
  }

  list(params?: any): Promise<PaginatedResponse<T>> {
    return request.get(`/${this.resource}/`, { params });
  }

  get(id: string): Promise<T> {
    return request.get(`/${this.resource}/${id}/`);
  }
  
  // ... create, update, delete
}
```

**Usage**:
```typescript
// src/api/assets.ts
export const assetApi = new BaseApiService<Asset>('assets');
// Add custom methods only as needed
assetApi.customMethod = () => { ... }
```

### 4.2. Standardize API Path Naming
- Adopt a strict strict kebab-case policy for URL endpoints (e.g., `/my-tasks` not `/my_tasks`) to match RESTful best practices and likely backend default configurations.
- Verify `backend` `urls.py` configuration to ensure it matches.

### 4.3. Enforce Type Safety
- Audit `src/api/*.ts` files to replace `Promise<any>` with `Promise<ModelType>`.
- Specifically in `assets.ts`, fix `locationApi` and `transferApi` return types.

### 4.4. Component Reusability
- With new modules (Assets Loans, Projects) coming in Phase 7, ensure `AssetSelector`, `UserSelector`, and `DepartmentSelector` are robust, form-compatible (v-model support), and performance-optimized (virtual scrolling for large lists).

## 5. Next Steps
1.  **Refactor**: Implement `BaseApiService` and migrate one module (e.g., Assets) as a pilot.
2.  **Fix**: Correct the URL path in `workflow.ts`.
3.  **Audit**: Scan for `any` types in `api/` and replace with specific interfaces.
