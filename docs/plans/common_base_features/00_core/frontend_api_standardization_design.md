# Frontend API Standardization Design Document

## Document Information

| Project | Details |
|---------|---------|
| Design Version | v1.0 |
| Created Date | 2026-01-22 |
| Author/Agent | Claude Code (Opus 4.5) |
| Status | Draft for Review |
| Related PRDs | All Phase Frontend PRDs |

---

## 1. Executive Summary

This design document addresses the **critical inconsistencies** found across all frontend PRD documents in the GZEAMS project. The analysis revealed issues with API response format handling, field naming conventions, error handling patterns, and missing infrastructure components.

### Key Issues Identified

| Issue | Severity | Impact |
|-------|----------|--------|
| API Response Format Inconsistency | HIGH | Breaking API contract |
| Field Naming Mixed (camelCase/snake_case) | MEDIUM | Code confusion |
| Missing Error Code Standards | HIGH | No standardized error handling |
| Missing Transformation Layer | HIGH | Data integrity issues |
| Inconsistent Request Patterns | MEDIUM | Maintenance burden |

### Design Goals

1. **Unified API Response Handling**: All API calls return standardized format
2. **Automatic Field Transformation**: Backend snake_case → Frontend camelCase
3. **Standardized Error Handling**: Consistent error code mapping
4. **Type Safety**: Full TypeScript support for API contracts
5. **Developer Experience**: Simple, predictable API for all modules

---

## 2. Architecture Overview

### 2.1 Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Components/Views                          │
│  (BaseListPage, BaseFormPage, Business Components)              │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API Service Layer                            │
│  (assets.js, inventory.js, portal.js - typed APIs)              │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Request Interceptor Layer                     │
│  - Response transformation (wrapper + field naming)             │
│  - Error handling (code mapping + user messages)                │
│  - Token injection + Organization header                        │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Axios HTTP Client                        │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend APIs                               │
│  (Django REST Framework - Unified Response Format)              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Diagram

```
Request Flow:
Component → API Service → requestInstance.transformRequest()
           → Axios → Backend (snake_case)
           → Backend Response → Axios Interceptor
           → transformResponse() → snake_case to camelCase
           → unwrapResponse() → { success, data, error }
           → API Service → Component (camelCase data)

Error Flow:
API Error → Axios Error Interceptor → extractError()
          → mapErrorCode() → showError()
          → Component (handled error)
```

---

## 3. API Response Standardization

### 3.1 Unified Response Interface

All API responses MUST conform to this interface:

```typescript
// frontend/src/types/api.ts

/**
 * Unified API response interface for all endpoints
 */
export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  error?: ApiError
}

/**
 * Standard error structure
 */
export interface ApiError {
  code: ErrorCode
  message: string
  details?: Record<string, string[]>
}

/**
 * Paginated response data
 */
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

/**
 * Batch operation response
 */
export interface BatchResponse {
  summary: {
    total: number
    succeeded: number
    failed: number
  }
  results: BatchResultItem[]
}

export interface BatchResultItem {
  id: string
  success: boolean
  error?: string
}
```

### 3.2 Error Code Enum

```typescript
// frontend/src/types/error.ts

/**
 * Standard error codes matching backend definition
 */
export enum ErrorCode {
  // Client errors (4xx)
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  UNAUTHORIZED = 'UNAUTHORIZED',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  NOT_FOUND = 'NOT_FOUND',
  METHOD_NOT_ALLOWED = 'METHOD_NOT_ALLOWED',
  CONFLICT = 'CONFLICT',
  ORGANIZATION_MISMATCH = 'ORGANIZATION_MISMATCH',
  SOFT_DELETED = 'SOFT_DELETED',

  // Server errors (5xx)
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  SERVER_ERROR = 'SERVER_ERROR'
}

/**
 * Error code to HTTP status mapping
 */
export const ErrorCodeStatusMap: Record<ErrorCode, number> = {
  [ErrorCode.VALIDATION_ERROR]: 400,
  [ErrorCode.UNAUTHORIZED]: 401,
  [ErrorCode.PERMISSION_DENIED]: 403,
  [ErrorCode.NOT_FOUND]: 404,
  [ErrorCode.METHOD_NOT_ALLOWED]: 405,
  [ErrorCode.CONFLICT]: 409,
  [ErrorCode.ORGANIZATION_MISMATCH]: 403,
  [ErrorCode.SOFT_DELETED]: 410,
  [ErrorCode.RATE_LIMIT_EXCEEDED]: 429,
  [ErrorCode.SERVER_ERROR]: 500
}

/**
 * Error code to user message mapping (i18n support)
 */
export const ErrorCodeMessages: Record<ErrorCode, string> = {
  [ErrorCode.VALIDATION_ERROR]: '请求数据验证失败',
  [ErrorCode.UNAUTHORIZED]: '未授权访问，请重新登录',
  [ErrorCode.PERMISSION_DENIED]: '权限不足',
  [ErrorCode.NOT_FOUND]: '请求的资源不存在',
  [ErrorCode.METHOD_NOT_ALLOWED]: '请求方法不允许',
  [ErrorCode.CONFLICT]: '数据冲突，请刷新后重试',
  [ErrorCode.ORGANIZATION_MISMATCH]: '组织不匹配',
  [ErrorCode.SOFT_DELETED]: '资源已被删除',
  [ErrorCode.RATE_LIMIT_EXCEEDED]: '请求过于频繁，请稍后再试',
  [ErrorCode.SERVER_ERROR]: '服务器错误，请稍后再试'
}
```

---

## 4. Field Naming Transformation

### 4.1 Transformation Utilities

```typescript
// frontend/src/utils/transform.ts

/**
 * Convert snake_case to camelCase
 * @example parent_id → parentId
 */
export function toCamelCase<T = any>(obj: any): T {
  if (obj === null || obj === undefined) return obj

  // Handle arrays
  if (Array.isArray(obj)) {
    return obj.map(item => toCamelCase(item)) as any
  }

  // Handle dates
  if (obj instanceof Date) return obj as any

  // Handle primitives
  if (typeof obj !== 'object') return obj

  // Convert object keys
  return Object.keys(obj).reduce((acc, key) => {
    const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
    acc[camelKey] = toCamelCase(obj[key])
    return acc
  }, {} as any)
}

/**
 * Convert camelCase to snake_case
 * @example parentId → parent_id
 */
export function toSnakeCase<T = any>(obj: any): T {
  if (obj === null || obj === undefined) return obj

  if (Array.isArray(obj)) {
    return obj.map(item => toSnakeCase(item)) as any
  }

  if (obj instanceof Date) return obj as any

  if (typeof obj !== 'object') return obj

  return Object.keys(obj).reduce((acc, key) => {
    const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)
    acc[snakeKey] = toSnakeCase(obj[key])
    return acc
  }, {} as any)
}

/**
 * Field mapping for special cases where auto-conversion fails
 */
export const FieldMapping = {
  // Add any special mappings here
  // 'backend_field': 'frontendField'
}
```

### 4.2 Field Naming Convention Rules

| Context | Convention | Examples |
|---------|-----------|----------|
| **Frontend Components** | camelCase | `userId`, `createdAt`, `isActive` |
| **Backend API** | snake_case | `user_id`, `created_at`, `is_active` |
| **HTML Attributes** | kebab-case | `data-user-id`, `@update:model-value` |
| **CSS Classes** | kebab-case | `.user-card`, `.btn-primary` |
| **Constants** | SCREAMING_SNAKE_CASE | `MAX_FILE_SIZE`, `DEFAULT_TIMEOUT` |
| **Types/Interfaces** | PascalCase | `ApiResponse`, `UserData` |

---

## 5. Request Interceptor Implementation

### 5.1 Axios Instance Configuration

```typescript
// frontend/src/utils/request.ts

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse } from '@/types/api'
import { toCamelCase, toSnakeCase } from '@/utils/transform'
import { handleApiError } from '@/utils/errorHandler'

/**
 * Create base axios instance
 */
const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

/**
 * Request interceptor
 * - Add authorization token
 * - Add organization header
 * - Transform request data from camelCase to snake_case
 */
request.interceptors.request.use(
  (config) => {
    // Add authorization header
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add organization header
    const orgId = localStorage.getItem('current_org_id')
    if (orgId) {
      config.headers['X-Organization-ID'] = orgId
    }

    // Transform request data to snake_case
    if (config.data && typeof config.data === 'object') {
      config.data = toSnakeCase(config.data)
    }

    // Transform request params to snake_case
    if (config.params && typeof config.params === 'object') {
      config.params = toSnakeCase(config.params)
    }

    return config
  },
  (error) => Promise.reject(error)
)

/**
 * Response interceptor
 * - Transform response data from snake_case to camelCase
 * - Handle unified response format
 * - Handle errors consistently
 */
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response

    // Handle empty responses (204 No Content)
    if (!data) {
      return response
    }

    // Transform snake_case to camelCase
    const camelData = toCamelCase(data)

    // Unwrap unified response format
    if (typeof camelData === 'object' && 'success' in camelData) {
      const apiResponse = camelData as ApiResponse

      // Handle error responses
      if (!apiResponse.success && apiResponse.error) {
        return Promise.reject(new ApiErrorWrapper(apiResponse.error))
      }

      // Return data directly for success responses
      return apiResponse.data
    }

    // Return data as-is for non-unified responses (legacy endpoints)
    return camelData
  },
  (error) => {
    // Handle API errors
    return handleApiError(error)
  }
)

/**
 * Custom error class for API errors
 */
class ApiErrorWrapper extends Error {
  code: string
  details?: Record<string, string[]>

  constructor(apiError: any) {
    super(apiError.message)
    this.code = apiError.code
    this.details = apiError.details
    this.name = 'ApiError'
  }
}

export default request
```

### 5.2 Error Handler Implementation

```typescript
// frontend/src/utils/errorHandler.ts

import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router'
import type { ErrorCode } from '@/types/error'
import ErrorCodeMessages from '@/locales/errorMessages'

/**
 * Handle API errors with standardized behavior
 */
export function handleApiError(error: any): Promise<never> {
  const status = error.response?.status
  const data = error.response?.data

  // Extract error information
  let errorCode: ErrorCode = 'SERVER_ERROR'
  let message = '服务器错误，请稍后再试'
  let details: Record<string, string[]> | undefined

  if (data?.error) {
    errorCode = data.error.code
    message = data.error.message || ErrorCodeMessages[errorCode] || message
    details = data.error.details
  } else if (error.code) {
    errorCode = error.code
    message = error.message || ErrorCodeMessages[errorCode] || message
    details = error.details
  }

  // Handle specific status codes
  switch (status) {
    case 401:
      // Unauthorized - redirect to login
      ElMessageBox.confirm(
        '登录已过期，是否重新登录？',
        '提示',
        {
          confirmButtonText: '重新登录',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(() => {
        localStorage.clear()
        router.push('/login')
      })
      return Promise.reject(error)

    case 403:
      // Permission denied
      ElMessage.error(message || '权限不足')
      return Promise.reject(error)

    case 404:
      // Not found
      ElMessage.error(message || '请求的资源不存在')
      return Promise.reject(error)

    case 410:
      // Soft deleted
      ElMessage.error(message || '资源已被删除')
      return Promise.reject(error)

    case 429:
      // Rate limit exceeded
      ElMessage.error(message || '请求过于频繁，请稍后再试')
      return Promise.reject(error)

    default:
      // Show error message
      if (details) {
        // Show validation errors
        const firstError = Object.values(details)[0]?.[0]
        ElMessage.error(firstError || message)
      } else {
        ElMessage.error(message)
      }
      return Promise.reject(error)
  }
}

/**
 * Extract error message from error object
 */
export function getErrorMessage(error: any): string {
  if (error?.response?.data?.error?.message) {
    return error.response.data.error.message
  }
  if (error?.response?.data?.message) {
    return error.response.data.message
  }
  if (error?.message) {
    return error.message
  }
  return '操作失败'
}
```

---

## 6. API Service Layer Pattern

### 6.1 Standard API Service Template

```typescript
// frontend/src/api/assets.ts

/**
 * Asset API service
 * All methods return camelCase data
 * All request parameters accept camelCase and convert to snake_case
 */

import request from '@/utils/request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type { Asset, AssetCreate, AssetUpdate, AssetFilters } from '@/types/models'

/**
 * Asset API methods
 */
export const assetApi = {
  /**
   * Get asset list with pagination and filters
   * @param filters - Filter parameters (camelCase)
   * @returns Paginated asset list
   */
  list(filters?: AssetFilters): Promise<PaginatedResponse<Asset>> {
    return request.get('/assets/', { params: filters })
  },

  /**
   * Get single asset by ID
   * @param id - Asset UUID
   * @returns Asset detail
   */
  get(id: string): Promise<Asset> {
    return request.get(`/assets/${id}/`)
  },

  /**
   * Create new asset
   * @param data - Asset creation data (camelCase)
   * @returns Created asset
   */
  create(data: AssetCreate): Promise<Asset> {
    return request.post('/assets/', data)
  },

  /**
   * Update asset
   * @param id - Asset UUID
   * @param data - Asset update data (camelCase)
   * @returns Updated asset
   */
  update(id: string, data: AssetUpdate): Promise<Asset> {
    return request.put(`/assets/${id}/`, data)
  },

  /**
   * Partial update asset
   * @param id - Asset UUID
   * @param data - Partial asset data (camelCase)
   * @returns Updated asset
   */
  partialUpdate(id: string, data: Partial<AssetUpdate>): Promise<Asset> {
    return request.patch(`/assets/${id}/`, data)
  },

  /**
   * Delete asset (soft delete)
   * @param id - Asset UUID
   */
  delete(id: string): Promise<void> {
    return request.delete(`/assets/${id}/`)
  },

  /**
   * Batch delete assets
   * @param ids - Array of asset UUIDs
   * @returns Batch operation result
   */
  batchDelete(ids: string[]): Promise<{ summary: { total: number; succeeded: number; failed: number } }> {
    return request.post('/assets/batch-delete/', { ids })
  },

  /**
   * Restore deleted asset
   * @param id - Asset UUID
   */
  restore(id: string): Promise<void> {
    return request.post(`/assets/${id}/restore/`)
  },

  /**
   * Get deleted assets
   * @param filters - Filter parameters
   * @returns Paginated deleted asset list
   */
  getDeleted(filters?: AssetFilters): Promise<PaginatedResponse<Asset>> {
    return request.get('/assets/deleted/', { params: filters })
  },

  /**
   * Get asset categories tree
   * @returns Category tree structure
   */
  getCategories(): Promise<CategoryTree[]> {
    return request.get('/assets/categories/tree/')
  }
}

/**
 * Type definitions for Asset API
 */
export interface Asset {
  id: string
  code: string
  name: string
  categoryId: string
  category?: Category
  status: AssetStatus
  locationId?: string
  location?: Location
  custodianId?: string
  custodian?: User
  organizationId: string
  organization?: Organization
  isDeleted: boolean
  deletedAt?: string
  createdAt: string
  updatedAt: string
  createdBy: string
  updatedBy?: string
  customFields?: Record<string, any>
}

export interface AssetCreate {
  code: string
  name: string
  categoryId: string
  status?: AssetStatus
  locationId?: string
  custodianId?: string
}

export interface AssetUpdate extends Partial<AssetCreate> {}

export interface AssetFilters {
  page?: number
  pageSize?: number
  search?: string
  status?: AssetStatus
  categoryId?: string
  locationId?: string
  custodianId?: string
  createdAtFrom?: string
  createdAtTo?: string
}

export enum AssetStatus {
  IDLE = 'idle',
  IN_USE = 'in_use',
  MAINTENANCE = 'maintenance',
  SCRAPPED = 'scrapped'
}
```

### 6.2 Portal API Example (User Portal)

```typescript
// frontend/src/api/portal.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'

/**
 * User Portal API
 * All endpoints use /portal/ base path (no /api prefix)
 */
export const portalApi = {
  /**
   * Get portal overview statistics
   */
  getOverview(): Promise<PortalOverview> {
    return request.get('/portal/overview/')
  },

  /**
   * Get user's assets
   * @param params - Query parameters (camelCase)
   */
  getMyAssets(params?: MyAssetsParams): Promise<PaginatedResponse<MyAsset>> {
    return request.get('/portal/my-assets/', { params })
  },

  /**
   * Get asset detail for portal view
   * @param id - Asset ID
   */
  getAssetDetail(id: string): Promise<MyAssetDetail> {
    return request.get(`/portal/my-assets/${id}/`)
  },

  /**
   * Get user's requests (aggregated across types)
   * @param params - Query parameters
   */
  getMyRequests(params?: MyRequestsParams): Promise<MyRequestsResponse> {
    return request.get('/portal/my-requests/', { params })
  },

  /**
   * Urge a pending request
   * @param type - Request type (pickup/loan/transfer/return)
   * @param id - Request ID
   */
  urgeRequest(type: string, id: string, comment?: string): Promise<void> {
    return request.post(`/portal/my-requests/${type}/${id}/urge/`, { comment })
  },

  /**
   * Withdraw a pending request
   * @param type - Request type
   * @param id - Request ID
   */
  withdrawRequest(type: string, id: string): Promise<void> {
    return request.post(`/portal/my-requests/${type}/${id}/withdraw/`)
  },

  /**
   * Get user's tasks
   * @param params - Query parameters
   */
  getMyTasks(params?: MyTasksParams): Promise<PaginatedResponse<MyTask>> {
    return request.get('/portal/my-tasks/', { params })
  },

  /**
   * Batch action on tasks
   * @param data - Batch action data
   */
  batchTaskAction(data: BatchTaskAction): Promise<BatchActionResult> {
    return request.post('/portal/my-tasks/batch-action/', data)
  },

  /**
   * Get user profile with statistics
   */
  getProfile(): Promise<UserProfile> {
    return request.get('/portal/profile/')
  },

  /**
   * Update user profile
   * @param data - Profile data
   */
  updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    return request.put('/portal/profile/', data)
  },

  /**
   * Switch current department
   * @param departmentId - Target department ID
   */
  switchDepartment(departmentId: string): Promise<{ token: string }> {
    return request.post('/portal/profile/switch-department/', { departmentId })
  },

  /**
   * Update user preferences
   * @param preferences - Preferences object
   */
  updatePreferences(preferences: UserPreferences): Promise<void> {
    return request.put('/portal/profile/preferences/', preferences)
  }
}

/**
 * Type definitions for Portal API
 */
export interface PortalOverview {
  totalAssets: number
  myAssets: number
  pendingRequests: number
  pendingTasks: number
  recentActivities: Activity[]
}

export interface MyAsset {
  id: string
  assetCode: string
  assetName: string
  categoryName: string
  status: string
  locationName: string
  acquireDate: string
}

export interface MyRequestsResponse {
  summary: RequestSummary
  groupBy: string
  groups: RequestGroup[]
}

export interface RequestSummary {
  total: number
  pending: number
  approved: number
  rejected: number
}

export interface RequestGroup {
  type: string
  typeName: string
  count: number
  items: RequestItem[]
}

export interface MyTask {
  id: string
  taskType: string
  title: string
  description: string
  status: string
  createdAt: string
  dueDate?: string
}
```

---

## 7. Component Integration Pattern

### 7.1 BaseListPage Integration

```vue
<!-- frontend/src/views/assets/AssetList.vue -->
<template>
  <BaseListPage
    title="资产列表"
    :fetch-method="assetApi.list"
    :delete-method="handleDelete"
    :batch-delete-method="assetApi.batchDelete"
    :columns="columns"
    :search-fields="searchFields"
    :filter-fields="filterFields"
    :custom-slots="['status', 'actions']"
    @row-click="handleRowClick"
    @create="handleCreate"
  >
    <!-- Status column slot -->
    <template #status="{ row }">
      <el-tag :type="getStatusType(row.status)">
        {{ getStatusLabel(row.status) }}
      </el-tag>
    </template>

    <!-- Actions column slot -->
    <template #actions="{ row }">
      <el-button link type="primary" @click.stop="handleEdit(row)">
        编辑
      </el-button>
      <el-button link type="danger" @click.stop="handleDelete(row)">
        删除
      </el-button>
    </template>
  </BaseListPage>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { assetApi, AssetStatus } from '@/api/assets'
import { ElMessage } from 'element-plus'

const router = useRouter()

// Column definitions - all use camelCase
const columns = [
  { prop: 'assetCode', label: '资产编码', width: 150, fixed: 'left' },
  { prop: 'assetName', label: '资产名称', minWidth: 200 },
  { prop: 'categoryName', label: '分类', width: 120 },
  { prop: 'status', label: '状态', width: 100, slot: true },
  { prop: 'locationName', label: '存放位置', width: 150 },
  { prop: 'custodianName', label: '保管人', width: 120 },
  { prop: 'createdAt', label: '创建时间', width: 180, type: 'datetime' },
  { prop: 'actions', label: '操作', width: 150, slot: true, fixed: 'right' }
]

// Search fields - camelCase
const searchFields = [
  { prop: 'keyword', label: '搜索', placeholder: '编码/名称' }
]

// Filter fields - camelCase
const filterFields = [
  {
    prop: 'status',
    label: '状态',
    type: 'select',
    options: [
      { value: AssetStatus.IDLE, label: '闲置' },
      { value: AssetStatus.IN_USE, label: '在用' },
      { value: AssetStatus.MAINTENANCE, label: '维修中' },
      { value: AssetStatus.SCRAPPED, label: '已报废' }
    ]
  },
  { prop: 'categoryId', label: '分类', type: 'select', options: [] }
]

// Event handlers - data is already in camelCase
const handleRowClick = (row: any) => {
  router.push(`/assets/${row.id}`)
}

const handleCreate = () => {
  router.push('/assets/create')
}

const handleEdit = (row: any) => {
  router.push(`/assets/${row.id}/edit`)
}

const handleDelete = async (row: any) => {
  try {
    await assetApi.delete(row.id)
    ElMessage.success('删除成功')
  } catch (error) {
    // Error already handled by interceptor
  }
}

// Utility functions
const getStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    [AssetStatus.IDLE]: 'info',
    [AssetStatus.IN_USE]: 'success',
    [AssetStatus.MAINTENANCE]: 'warning',
    [AssetStatus.SCRAPPED]: 'danger'
  }
  return typeMap[status] || ''
}

const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    [AssetStatus.IDLE]: '闲置',
    [AssetStatus.IN_USE]: '在用',
    [AssetStatus.MAINTENANCE]: '维修中',
    [AssetStatus.SCRAPPED]: '已报废'
  }
  return labelMap[status] || status
}
</script>
```

### 7.2 BaseFormPage Integration

```vue
<!-- frontend/src/views/assets/AssetForm.vue -->
<template>
  <BaseFormPage
    :title="isEdit ? '编辑资产' : '新建资产'"
    :submit-method="handleSubmit"
    :initial-data="formData"
    :rules="rules"
    submit-text="保存"
    redirect-path="/assets"
  >
    <template #default="{ data }">
      <!-- All field bindings use camelCase -->
      <el-form-item label="资产编码" prop="assetCode">
        <el-input v-model="data.assetCode" placeholder="请输入资产编码" />
      </el-form-item>

      <el-form-item label="资产名称" prop="assetName">
        <el-input v-model="data.assetName" placeholder="请输入资产名称" />
      </el-form-item>

      <el-form-item label="资产分类" prop="categoryId">
        <CategorySelect v-model="data.categoryId" />
      </el-form-item>

      <el-form-item label="状态" prop="status">
        <el-select v-model="data.status" placeholder="请选择状态">
          <el-option label="闲置" :value="AssetStatus.IDLE" />
          <el-option label="在用" :value="AssetStatus.IN_USE" />
          <el-option label="维修中" :value="AssetStatus.MAINTENANCE" />
          <el-option label="已报废" :value="AssetStatus.SCRAPPED" />
        </el-select>
      </el-form-item>

      <el-form-item label="存放位置" prop="locationId">
        <LocationSelect v-model="data.locationId" />
      </el-form-item>

      <el-form-item label="保管人" prop="custodianId">
        <UserSelect v-model="data.custodianId" />
      </el-form-item>
    </template>
  </BaseFormPage>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import BaseFormPage from '@/components/common/BaseFormPage.vue'
import { assetApi, AssetStatus } from '@/api/assets'
import { ElMessage } from 'element-plus'

const route = useRoute()
const assetId = computed(() => route.params.id as string)
const isEdit = computed(() => !!assetId.value)

// Form data - all camelCase
const formData = ref({
  assetCode: '',
  assetName: '',
  categoryId: '',
  status: AssetStatus.IDLE,
  locationId: '',
  custodianId: ''
})

// Validation rules
const rules = {
  assetCode: [
    { required: true, message: '请输入资产编码', trigger: 'blur' }
  ],
  assetName: [
    { required: true, message: '请输入资产名称', trigger: 'blur' }
  ],
  categoryId: [
    { required: true, message: '请选择分类', trigger: 'change' }
  ]
}

// Load asset data for edit mode
onMounted(async () => {
  if (isEdit.value) {
    try {
      const asset = await assetApi.get(assetId.value)
      // Data is already camelCase from API
      formData.value = {
        assetCode: asset.code,
        assetName: asset.name,
        categoryId: asset.categoryId,
        status: asset.status,
        locationId: asset.locationId || '',
        custodianId: asset.custodianId || ''
      }
    } catch (error) {
      // Error already handled by interceptor
    }
  }
})

// Submit handler - data automatically converted to snake_case
const handleSubmit = async (data: any) => {
  if (isEdit.value) {
    return await assetApi.update(assetId.value, data)
  } else {
    return await assetApi.create(data)
  }
}
</script>
```

---

## 8. Field Configuration System Design

### 8.1 Backend Model (Missing - Critical)

```python
# apps/system/models.py

from apps.common.models import BaseModel

class FieldTemplate(BaseModel):
    """
    Field configuration template for list/form/detail views
    Supports system/organization/user scoped configurations
    """
    SCOPE_CHOICES = [
        ('system', 'System Level'),
        ('organization', 'Organization Level'),
        ('user', 'User Level'),
    ]

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=100, unique=True)
    module = models.CharField(max_length=50)  # my_assets, my_requests, etc.
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default='user')
    scope_id = models.UUIDField(null=True, blank=True)  # org_id or user_id
    config = models.JSONField(default=dict)  # Field configuration
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'system_field_templates'
        verbose_name = 'Field Template'
        verbose_name_plural = 'Field Templates'
        unique_together = [['code', 'scope', 'scope_id']]
```

### 8.2 Field Configuration API

```typescript
// frontend/src/api/fieldConfig.ts

import request from '@/utils/request'

/**
 * Field Configuration API
 * Manages user-customizable field layouts for list/form/detail views
 */
export const fieldConfigApi = {
  /**
   * Get field template for a module
   * @param module - Module code (my_assets, my_requests, etc.)
   * @param view - View type (list/form/detail)
   */
  getTemplate(module: string, view: string): Promise<FieldTemplate> {
    return request.get('/system/field-templates/', {
      params: { module, view }
    })
  },

  /**
   * Get user's field configuration
   * @param module - Module code
   * @param view - View type
   */
  getMyConfig(module: string, view: string): Promise<FieldConfig> {
    return request.get('/system/my-field-config/', {
      params: { module, view }
    })
  },

  /**
   * Save field configuration
   * @param config - Field configuration object
   */
  saveConfig(config: FieldConfig): Promise<void> {
    return request.post('/system/my-field-config/', config)
  },

  /**
   * Reset field configuration to default
   * @param module - Module code
   * @param view - View type
   */
  resetConfig(module: string, view: string): Promise<void> {
    return request.post('/system/my-field-config/reset/', { module, view })
  },

  /**
   * Set template as default
   * @param templateId - Template ID
   */
  setAsDefault(templateId: string): Promise<void> {
    return request.post(`/system/field-templates/${templateId}/set-default/`)
  }
}

/**
 * Type definitions
 */
export interface FieldTemplate {
  id: string
  name: string
  code: string
  module: string
  scope: 'system' | 'organization' | 'user'
  scopeId?: string
  config: FieldConfig
  isDefault: boolean
}

export interface FieldConfig {
  module: string
  view: 'list' | 'form' | 'detail'
  columns: FieldColumn[]
  sortBy: string
  sortOrder: 'asc' | 'desc'
  pageSize: number
}

export interface FieldColumn {
  field: string
  label: string
  width: number
  visible: boolean
  sortable: boolean
  fixed?: 'left' | 'right'
}
```

### 8.3 Field Config Panel Component

```vue
<!-- frontend/src/components/common/FieldConfigPanel.vue -->
<template>
  <el-drawer v-model="visible" title="字段配置" size="400px">
    <div class="field-config-panel">
      <!-- Available fields -->
      <div class="section">
        <h4>可用字段</h4>
        <draggable
          v-model="availableFields"
          :group="{ name: 'fields', pull: 'clone', put: false }"
          item-key="field"
        >
          <template #item="{ element }">
            <div class="field-item">
              <el-icon><Rank /></el-icon>
              <span>{{ element.label }}</span>
            </div>
          </template>
        </draggable>
      </div>

      <!-- Selected fields -->
      <div class="section">
        <h4>显示字段</h4>
        <draggable
          v-model="selectedFields"
          group="fields"
          item-key="field"
        >
          <template #item="{ element }">
            <div class="field-item selected">
              <el-icon><Rank /></el-icon>
              <span>{{ element.label }}</span>
              <el-button
                link
                type="danger"
                @click="removeField(element)"
              >
                删除
              </el-button>
            </div>
          </template>
        </draggable>
      </div>

      <!-- Actions -->
      <div class="actions">
        <el-button @click="handleReset">重置默认</el-button>
        <el-button type="primary" @click="handleSave">保存配置</el-button>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import draggable from 'vuedraggable'
import { fieldConfigApi } from '@/api/fieldConfig'
import { ElMessage } from 'element-plus'

interface Props {
  modelValue: boolean
  module: string
  view: 'list' | 'form' | 'detail'
  fields: FieldDefinition[]
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'saved', config: FieldConfig): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const visible = ref(false)
const availableFields = ref<FieldColumn[]>([])
const selectedFields = ref<FieldColumn[]>([])

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    loadConfig()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const loadConfig = async () => {
  try {
    const config = await fieldConfigApi.getMyConfig(props.module, props.view)
    selectedFields.value = config.columns

    // Available fields = all fields - selected fields
    const selectedFieldNames = new Set(config.columns.map(c => c.field))
    availableFields.value = props.fields
      .filter(f => !selectedFieldNames.has(f.field))
      .map(f => ({
        field: f.field,
        label: f.label,
        width: f.width || 120,
        visible: true,
        sortable: f.sortable !== false
      }))
  } catch (error) {
    // Load default from props
    availableFields.value = props.fields.map(f => ({
      field: f.field,
      label: f.label,
      width: 120,
      visible: true,
      sortable: true
    }))
  }
}

const removeField = (field: FieldColumn) => {
  selectedFields.value = selectedFields.value.filter(f => f.field !== field.field)
  availableFields.value.push(field)
}

const handleReset = async () => {
  try {
    await fieldConfigApi.resetConfig(props.module, props.view)
    await loadConfig()
    ElMessage.success('已重置为默认配置')
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleSave = async () => {
  try {
    const config: FieldConfig = {
      module: props.module,
      view: props.view,
      columns: selectedFields.value,
      sortBy: 'createdAt',
      sortOrder: 'desc',
      pageSize: 20
    }
    await fieldConfigApi.saveConfig(config)
    emit('saved', config)
    visible.value = false
    ElMessage.success('配置已保存')
  } catch (error) {
    // Error handled by interceptor
  }
}
</script>

<style scoped>
.field-config-panel {
  padding: 16px;
}

.section {
  margin-bottom: 24px;
}

.section h4 {
  margin-bottom: 12px;
  font-weight: 600;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
  margin-bottom: 8px;
  cursor: move;
}

.field-item.selected {
  background: var(--el-color-primary-light-9);
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color);
}
</style>
```

---

## 9. Missing Backend APIs Specification

### 9.1 Portal Module APIs

| Endpoint | Method | Description | Priority |
|----------|--------|-------------|----------|
| `/portal/my-requests/` | GET | Aggregate user requests across types | HIGH |
| `/portal/my-requests/{type}/{id}/detail/` | GET | Get request detail | HIGH |
| `/portal/my-requests/{type}/{id}/urge/` | POST | Send urge notification | MEDIUM |
| `/portal/my-requests/{type}/{id}/withdraw/` | POST | Withdraw pending request | MEDIUM |
| `/portal/my-tasks/` | GET | Get user's approval tasks | HIGH |
| `/portal/my-tasks/batch-action/` | POST | Batch approve/reject tasks | HIGH |
| `/portal/my-tasks/{id}/transfer/` | POST | Transfer task to another user | MEDIUM |
| `/portal/profile/` | GET | Get user profile with stats | MEDIUM |
| `/portal/profile/` | PUT | Update user profile | MEDIUM |
| `/portal/profile/switch-department/` | POST | Switch current department | LOW |
| `/portal/profile/preferences/` | PUT | Update user preferences | LOW |

### 9.2 Field Configuration APIs

| Endpoint | Method | Description | Priority |
|----------|--------|-------------|----------|
| `/system/field-templates/` | GET | List field templates | CRITICAL |
| `/system/field-templates/` | POST | Create field template | CRITICAL |
| `/system/field-templates/{id}/` | PUT | Update field template | CRITICAL |
| `/system/field-templates/{id}/` | DELETE | Delete field template | CRITICAL |
| `/system/field-templates/{id}/set-default/` | POST | Set template as default | CRITICAL |
| `/system/my-field-config/` | GET | Get user's field config | CRITICAL |
| `/system/my-field-config/` | POST | Save user's field config | CRITICAL |
| `/system/my-field-config/reset/` | POST | Reset to default config | CRITICAL |

### 9.3 Global Search APIs

| Endpoint | Method | Description | Priority |
|----------|--------|-------------|----------|
| `/search/` | GET | Unified search across modules | HIGH |
| `/search/suggest/` | GET | Search autocomplete | MEDIUM |
| `/search/history/` | GET | Get search history | LOW |
| `/search/history/` | POST | Add search history | LOW |
| `/search/history/` | DELETE | Clear search history | LOW |

---

## 10. Implementation Roadmap

### Phase 1: Infrastructure (Week 1)

- [ ] Create TypeScript type definitions (`types/api.ts`, `types/error.ts`)
- [ ] Implement field transformation utilities (`utils/transform.ts`)
- [ ] Implement error handler (`utils/errorHandler.ts`)
- [ ] Configure axios interceptor (`utils/request.ts`)

### Phase 2: API Service Layer (Week 1-2)

- [ ] Create standard API service template
- [ ] Implement asset API (`api/assets.ts`)
- [ ] Implement inventory APIs (`api/inventory/`)
- [ ] Implement portal API (`api/portal.ts`)

### Phase 3: Backend Implementation (Week 2-3)

- [ ] Implement FieldTemplate model
- [ ] Implement field template CRUD endpoints
- [ ] Implement my-requests aggregation endpoint
- [ ] Implement my-tasks endpoints
- [ ] Implement profile endpoints
- [ ] Implement search endpoints

### Phase 4: Frontend Components (Week 3)

- [ ] Implement FieldConfigPanel component
- [ ] Implement FieldSelector component
- [ ] Update BaseListPage to use field config
- [ ] Update BaseFormPage to use field config

### Phase 5: Integration & Testing (Week 4)

- [ ] Update all existing components to use new API pattern
- [ ] Update all PRD documents with standardized examples
- [ ] Integration testing
- [ ] Documentation update

---

## 11. Migration Guide

### 11.1 Updating Existing Components

**Before (Non-compliant):**
```vue
<script setup>
import { ref } from 'vue'
import request from '@/utils/request'

const tableData = ref([])

const loadData = async () => {
  const res = await request.get('/api/assets/')
  tableData.value = res.results  // ❌ No transformation
  // ❌ No error handling
}
</script>
```

**After (Compliant):**
```vue
<script setup lang="ts">
import { ref } from 'vue'
import { assetApi } from '@/api/assets'
import { ElMessage } from 'element-plus'

const tableData = ref<Asset[]>([])

const loadData = async () => {
  try {
    const response = await assetApi.list({ page: 1, pageSize: 20 })
    tableData.value = response.results  // ✅ Already camelCase
  } catch (error) {
    // ✅ Error handled by interceptor
  }
}
</script>
```

### 11.2 Updating API Service Files

**Before (Non-compliant):**
```javascript
// api/assets.js
import request from '@/utils/request'

export function getAssets(params) {
  return request({
    url: '/api/assets/',
    method: 'get',
    params  // ❌ snake_case in frontend
  })
}
```

**After (Compliant):**
```typescript
// api/assets.ts
import request from '@/utils/request'
import type { PaginatedResponse, AssetFilters } from '@/types/api'

export const assetApi = {
  list(filters?: AssetFilters): Promise<PaginatedResponse<Asset>> {
    // ✅ Accepts camelCase, converts to snake_case automatically
    return request.get('/assets/', { params: filters })
  }
}
```

---

## 12. Testing Strategy

### 12.1 Unit Tests

```typescript
// tests/unit/utils/transform.spec.ts
import { describe, it, expect } from 'vitest'
import { toCamelCase, toSnakeCase } from '@/utils/transform'

describe('Field Transformation', () => {
  describe('toCamelCase', () => {
    it('should convert simple snake_case to camelCase', () => {
      expect(toCamelCase({ user_id: 123 })).toEqual({ userId: 123 })
    })

    it('should handle nested objects', () => {
      expect(toCamelCase({
        user: { first_name: 'John', last_name: 'Doe' }
      })).toEqual({
        user: { firstName: 'John', lastName: 'Doe' }
      })
    })

    it('should handle arrays', () => {
      expect(toCamelCase([
        { user_id: 1, user_name: 'Alice' },
        { user_id: 2, user_name: 'Bob' }
      ])).toEqual([
        { userId: 1, userName: 'Alice' },
        { userId: 2, userName: 'Bob' }
      ])
    })
  })

  describe('toSnakeCase', () => {
    it('should convert camelCase to snake_case', () => {
      expect(toSnakeCase({ userId: 123 })).toEqual({ user_id: 123 })
    })
  })
})
```

### 12.2 Integration Tests

```typescript
// tests/integration/api/assets.spec.ts
import { describe, it, expect, beforeAll } from 'vitest'
import { assetApi } from '@/api/assets'

describe('Asset API', () => {
  it('should return camelCase data from list endpoint', async () => {
    const response = await assetApi.list({ page: 1, pageSize: 10 })

    expect(response.results).toBeDefined()
    expect(response.results[0].assetCode).toBeDefined()  // camelCase
    expect(response.results[0].asset_name).toBeUndefined()  // No snake_case
  })

  it('should convert request params to snake_case', async () => {
    const response = await assetApi.list({
      categoryId: 'uuid-here',  // camelCase in request
      status: 'idle'
    })

    // Backend receives category_id, status
    expect(response.results).toBeDefined()
  })
})
```

---

## 13. Compliance Checklist

Use this checklist to verify PRD compliance:

- [ ] All API calls go through typed API service functions
- [ ] All component state uses camelCase property names
- [ ] All API responses are unwrapped (data extracted from response)
- [ ] All error handling uses ElMessage (no native alerts)
- [ ] All request/response transformations are automatic
- [ ] TypeScript types are defined for all API contracts
- [ ] Error codes match the standardized ErrorCode enum
- [ ] Batch operations follow the standard summary/results format

---

## Appendix A: File Structure

```
frontend/src/
├── api/
│   ├── assets.ts              # Asset API service
│   ├── inventory/
│   │   ├── tasks.ts           # Inventory task API
│   │   ├── differences.ts     # Inventory difference API
│   │   └── index.ts
│   ├── portal.ts              # User portal API
│   ├── system.ts              # System/metadata API
│   ├── fieldConfig.ts         # Field configuration API
│   └── index.ts
├── types/
│   ├── api.ts                 # API response types
│   ├── error.ts               # Error code types
│   ├── models.ts              # Data model types
│   └── index.ts
├── utils/
│   ├── request.ts             # Axios instance with interceptors
│   ├── transform.ts           # Field naming transformation
│   ├── errorHandler.ts        # Error handling utilities
│   └── validation.ts          # Form validation helpers
├── components/
│   ├── common/
│   │   ├── BaseListPage.vue
│   │   ├── BaseFormPage.vue
│   │   ├── BaseDetailPage.vue
│   │   ├── FieldConfigPanel.vue
│   │   └── ...
│   └── metadata/
│       └── ...
└── composables/
    ├── useListPage.ts         # List page composable
    ├── useFormPage.ts         # Form page composable
    └── usePermission.ts       # Permission composable
```

---

## Appendix B: References

- [CLAUDE.md](../../../CLAUDE.md) - Project development standards
- [common_base_features/00_core/api.md](./api.md) - Backend API standards
- [common_base_features/00_core/frontend.md](./frontend.md) - Frontend component standards
- Frontend PRD Analysis Report - Issue identification and recommendations
