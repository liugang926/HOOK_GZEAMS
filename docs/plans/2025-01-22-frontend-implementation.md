# Frontend Development Implementation Plan

## Document Information

| Project | Details |
|---------|---------|
| Plan Version | v1.0 |
| Created Date | 2025-01-22 |
| Author/Agent | Claude Code (Opus 4.5) |
| Status | Ready for Implementation |
| Related Design | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Executive Summary

This plan breaks down the entire GZEAMS frontend development into bite-sized TDD tasks (2-5 minutes each). The implementation follows the v2.0 PRD standards with unified API response handling, automatic field transformation, and comprehensive TypeScript type safety.

### Implementation Scope

The frontend implementation is organized into **5 major phases**:

1. **Infrastructure Layer** - Core utilities, types, interceptors
2. **API Service Layer** - All module API services
3. **Common Components** - BaseListPage, BaseFormPage, reusable components
4. **Module Views** - Business module pages (assets, inventory, finance, etc.)
5. **Mobile Adaptation** - Mobile-specific views and components

---

## Phase 1: Infrastructure Layer (Foundation)

### 1.1 Type Definitions

#### Task 1.1.1: Create Base API Types
**File**: `frontend/src/types/api.ts`
**Time**: 3 minutes

```typescript
/**
 * Unified API response interface for all endpoints
 */
export interface ApiResponse<T = any> {
  success: boolean
  message?: string
  data?: T
  error?: ApiError
}

export interface ApiError {
  code: ErrorCode
  message: string
  details?: Record<string, string[]>
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

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

**Test**: Import and verify type checking in `npm run test:type`

---

#### Task 1.1.2: Create Error Code Types
**File**: `frontend/src/types/error.ts`
**Time**: 3 minutes

```typescript
export enum ErrorCode {
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  UNAUTHORIZED = 'UNAUTHORIZED',
  PERMISSION_DENIED = 'PERMISSION_DENIED',
  NOT_FOUND = 'NOT_FOUND',
  METHOD_NOT_ALLOWED = 'METHOD_NOT_ALLOWED',
  CONFLICT = 'CONFLICT',
  ORGANIZATION_MISMATCH = 'ORGANIZATION_MISMATCH',
  SOFT_DELETED = 'SOFT_DELETED',
  RATE_LIMIT_EXCEEDED = 'RATE_LIMIT_EXCEEDED',
  SERVER_ERROR = 'SERVER_ERROR'
}

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

**Test**: Verify all error codes are unique and have messages

---

#### Task 1.1.3: Create Common Model Types
**File**: `frontend/src/types/common.ts`
**Time**: 5 minutes

```typescript
export interface BaseModel {
  id: string
  organizationId: string
  isDeleted: boolean
  deletedAt: string | null
  createdAt: string
  updatedAt: string
  createdBy: string
  customFields?: Record<string, any>
}

export interface User {
  id: string
  username: string
  email?: string
  firstName?: string
  lastName?: string
  fullName: string
  avatar?: string
  isActive: boolean
}

export interface Organization {
  id: string
  name: string
  code: string
  parentId?: string
  level: number
  path: string
}

export interface TreeNode<T = any> {
  id: string
  label: string
  children?: TreeNode<T>[]
  data?: T
}

export interface SelectOption {
  label: string
  value: any
  disabled?: boolean
  [key: string]: any
}

export interface TableColumn {
  prop: string
  label: string
  width?: number
  minWidth?: number
  align?: 'left' | 'center' | 'right'
  fixed?: boolean | 'left' | 'right'
  slot?: boolean
  format?: (value: any, row: any) => string
}

export interface SearchField {
  field: string
  label: string
  type: 'input' | 'select' | 'daterange' | 'treeselect' | 'cascader'
  placeholder?: string
  options?: SelectOption[]
  multiple?: boolean
}
```

**Test**: Create a mock object and verify type compatibility

---

### 1.2 Utility Functions

#### Task 1.2.1: Create Field Transformation Utilities
**File**: `frontend/src/utils/transform.ts`
**Time**: 5 minutes

```typescript
export function toCamelCase<T = any>(obj: any): T {
  if (obj === null || obj === undefined) return obj
  if (Array.isArray(obj)) {
    return obj.map(item => toCamelCase(item)) as any
  }
  if (obj instanceof Date) return obj as any
  if (typeof obj !== 'object') return obj

  return Object.keys(obj).reduce((acc, key) => {
    const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
    acc[camelKey] = toCamelCase(obj[key])
    return acc
  }, {} as any)
}

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
```

**Test**: Write unit tests verifying transformation correctness

---

#### Task 1.2.2: Create Error Handler Utility
**File**: `frontend/src/utils/errorHandler.ts`
**Time**: 5 minutes

```typescript
import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router'
import type { ErrorCode } from '@/types/error'
import { ErrorCodeMessages } from '@/types/error'

export function handleApiError(error: any): Promise<never> {
  const status = error.response?.status
  const data = error.response?.data

  let errorCode: ErrorCode = 'SERVER_ERROR'
  let message = '服务器错误，请稍后再试'
  let details: Record<string, string[]> | undefined

  if (data?.error) {
    errorCode = data.error.code
    message = data.error.message || ErrorCodeMessages[errorCode] || message
    details = data.error.details
  }

  switch (status) {
    case 401:
      ElMessageBox.confirm('登录已过期，是否重新登录？', '提示', {
        confirmButtonText: '重新登录',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        localStorage.clear()
        router.push('/login')
      })
      return Promise.reject(error)
    case 403:
      ElMessage.error(message || '权限不足')
      return Promise.reject(error)
    case 404:
      ElMessage.error(message || '请求的资源不存在')
      return Promise.reject(error)
    case 410:
      ElMessage.error(message || '资源已被删除')
      return Promise.reject(error)
    case 429:
      ElMessage.error(message || '请求过于频繁，请稍后再试')
      return Promise.reject(error)
    default:
      if (details) {
        const firstError = Object.values(details)[0]?.[0]
        ElMessage.error(firstError || message)
      } else {
        ElMessage.error(message)
      }
      return Promise.reject(error)
  }
}
```

**Test**: Mock different error responses and verify correct handling

---

#### Task 1.2.3: Create Date Formatting Utilities
**File**: `frontend/src/utils/dateFormat.ts`
**Time**: 3 minutes

```typescript
import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.locale('zh-cn')
dayjs.extend(relativeTime)

export function formatDate(date: string | Date, format = 'YYYY-MM-DD'): string {
  return dayjs(date).format(format)
}

export function formatDateTime(date: string | Date): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

export function formatRelativeTime(date: string | Date): string {
  return dayjs(date).fromNow()
}

export function formatMonth(date: string | Date): string {
  return dayjs(date).format('YYYY-MM')
}

export function getCurrentMonth(): string {
  return dayjs().format('YYYY-MM')
}
```

**Test**: Verify date formatting with various inputs

---

#### Task 1.2.4: Create Number Formatting Utilities
**File**: `frontend/src/utils/numberFormat.ts`
**Time**: 2 minutes

```typescript
export function formatMoney(amount: number, decimals = 2): string {
  return Number(amount).toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

export function formatNumber(num: number, decimals = 0): string {
  return Number(num).toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

export function formatPercent(value: number, decimals = 2): string {
  return (value * 100).toFixed(decimals) + '%'
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
```

**Test**: Verify formatting with edge cases (0, negative, large numbers)

---

### 1.3 Request Interceptor

#### Task 1.3.1: Create Axios Instance with Interceptors
**File**: `frontend/src/utils/request.ts`
**Time**: 8 minutes

```typescript
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import type { ApiResponse } from '@/types/api'
import { toCamelCase, toSnakeCase } from '@/utils/transform'
import { handleApiError } from '@/utils/errorHandler'

const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    const orgId = localStorage.getItem('current_org_id')
    if (orgId) {
      config.headers['X-Organization-ID'] = orgId
    }

    if (config.data && typeof config.data === 'object') {
      config.data = toSnakeCase(config.data)
    }

    if (config.params && typeof config.params === 'object') {
      config.params = toSnakeCase(config.params)
    }

    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response
    if (!data) return response

    const camelData = toCamelCase(data)

    if (typeof camelData === 'object' && 'success' in camelData) {
      const apiResponse = camelData as ApiResponse
      if (!apiResponse.success && apiResponse.error) {
        return Promise.reject(new ApiErrorWrapper(apiResponse.error))
      }
      return apiResponse.data
    }

    return camelData
  },
  (error) => handleApiError(error)
)

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

**Test**: Create mock API calls and verify transformation

---

### 1.4 Business Module Types

#### Task 1.4.1: Create Asset Types
**File**: `frontend/src/types/assets.ts`
**Time**: 5 minutes

```typescript
export interface Asset extends BaseModel {
  code: string
  name: string
  categoryId?: string
  category?: AssetCategory
  status: AssetStatus
  purchasePrice: number
  purchaseDate: string
  supplierId?: string
  locationId?: string
  custodianId?: string
  description?: string
  images?: string[]
  qrCode?: string
}

export enum AssetStatus {
  DRAFT = 'draft',
  IN_USE = 'in_use',
  IDLE = 'idle',
  MAINTENANCE = 'maintenance',
  SCRAPPED = 'scrapped'
}

export interface AssetCategory {
  id: string
  code: string
  name: string
  parentId?: string
  level: number
  depreciationMethod?: DepreciationMethod
  usefulLifeMonths?: number
  residualRate?: number
}

export enum DepreciationMethod {
  STRAIGHT_LINE = 'straight_line',
  DOUBLE_DECLINING = 'double_declining',
  SUM_OF_YEARS = 'sum_of_years'
}
```

**Test**: Verify type compatibility with API response

---

#### Task 1.4.2: Create Inventory Types
**File**: `frontend/src/types/inventory.ts`
**Time**: 5 minutes

```typescript
export interface InventoryTask extends BaseModel {
  taskNo: string
  taskName: string
  taskType: TaskType
  status: TaskStatus
  plannedDate: string
  locationId?: string
  assetCount: number
  scannedCount: number
  abnormalCount: number
  completedAt?: string
}

export enum TaskType {
  FULL = 'full',
  PARTIAL = 'partial',
  LOCATION = 'location',
  CATEGORY = 'category'
}

export enum TaskStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

export interface InventorySnapshot {
  id: string
  taskId: string
  assetId: string
  expectedLocation: string
  scanned?: boolean
  scanResult?: ScanResult
  scannedAt?: string
  scannedBy?: string
}

export enum ScanResult {
  NORMAL = 'normal',
  LOCATION_CHANGED = 'location_changed',
  DAMAGED = 'damaged',
  MISSING = 'missing'
}
```

**Test**: Verify enum values match backend

---

#### Task 1.4.3: Create Workflow Types
**File**: `frontend/src/types/workflow.ts`
**Time**: 5 minutes

```typescript
export interface WorkflowDefinition extends BaseModel {
  name: string
  code: string
  businessObject: string
  graphData: LogicFlowGraphData
  isActive: boolean
  version: number
}

export interface LogicFlowGraphData {
  nodes: LogicFlowNode[]
  edges: LogicFlowEdge[]
}

export interface LogicFlowNode {
  id: string
  type: string
  x: number
  y: number
  text?: string
  properties?: Record<string, any>
}

export interface LogicFlowEdge {
  id: string
  sourceNodeId: string
  targetNodeId: string
  type?: string
  text?: string
  properties?: Record<string, any>
}

export interface WorkflowInstance extends BaseModel {
  definitionId: string
  businessDataType: string
  businessDataId: string
  status: WorkflowStatus
  currentNodeId?: string
  initiatorId: string
  completedAt?: string
}

export enum WorkflowStatus {
  DRAFT = 'draft',
  RUNNING = 'running',
  COMPLETED = 'completed',
  REJECTED = 'rejected',
  CANCELLED = 'cancelled'
}
```

**Test**: Verify LogicFlow structure compatibility

---

## Phase 2: API Service Layer

### 2.1 Asset API Service

#### Task 2.1.1: Create Asset API Service
**File**: `frontend/src/api/assets.ts`
**Time**: 5 minutes

```typescript
import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { Asset } from '@/types/assets'

export const assetApi = {
  list(params?: {
    page?: number
    pageSize?: number
    categoryId?: string
    status?: string
    search?: string
  }): Promise<PaginatedResponse<Asset>> {
    return request.get('/assets/', { params })
  },

  get(id: string): Promise<Asset> {
    return request.get(`/assets/${id}/`)
  },

  create(data: Partial<Asset>): Promise<Asset> {
    return request.post('/assets/', data)
  },

  update(id: string, data: Partial<Asset>): Promise<Asset> {
    return request.put(`/assets/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/assets/${id}/`)
  },

  batchDelete(ids: string[]): Promise<BatchResponse> {
    return request.post('/assets/batch-delete/', { ids })
  },

  export(params?: any): Promise<Blob> {
    return request.get('/assets/export/', {
      params,
      responseType: 'blob'
    })
  }
}
```

**Test**: Mock API responses and verify type safety

---

#### Task 2.1.2: Create Asset Category API Service
**File**: `frontend/src/api/assetCategories.ts`
**Time**: 3 minutes

```typescript
import request from '@/utils/request'
import type { AssetCategory } from '@/types/assets'

export const categoryApi = {
  list(): Promise<AssetCategory[]> {
    return request.get('/assets/categories/')
  },

  tree(): Promise<AssetCategory[]> {
    return request.get('/assets/categories/tree/')
  },

  get(id: string): Promise<AssetCategory> {
    return request.get(`/assets/categories/${id}/`)
  },

  create(data: Partial<AssetCategory>): Promise<AssetCategory> {
    return request.post('/assets/categories/', data)
  },

  update(id: string, data: Partial<AssetCategory>): Promise<AssetCategory> {
    return request.put(`/assets/categories/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/assets/categories/${id}/`)
  }
}
```

**Test**: Verify tree structure response

---

### 2.2 Inventory API Service

#### Task 2.2.1: Create Inventory Task API Service
**File**: `frontend/src/api/inventory.ts`
**Time**: 5 minutes

```typescript
import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { InventoryTask, InventorySnapshot } from '@/types/inventory'

export const inventoryApi = {
  // Tasks
  listTasks(params?: {
    page?: number
    pageSize?: number
    status?: string
  }): Promise<PaginatedResponse<InventoryTask>> {
    return request.get('/inventory/tasks/', { params })
  },

  getTask(id: string): Promise<InventoryTask> {
    return request.get(`/inventory/tasks/${id}/`)
  },

  createTask(data: Partial<InventoryTask>): Promise<InventoryTask> {
    return request.post('/inventory/tasks/', data)
  },

  startTask(id: string): Promise<void> {
    return request.post(`/inventory/tasks/${id}/start/`)
  },

  completeTask(id: string): Promise<void> {
    return request.post(`/inventory/tasks/${id}/complete/`)
  },

  cancelTask(id: string): Promise<void> {
    return request.post(`/inventory/tasks/${id}/cancel/`)
  },

  // Snapshots
  getSnapshots(taskId: string, params?: {
    filter?: 'all' | 'scanned' | 'unscanned' | 'abnormal'
  }): Promise<PaginatedResponse<InventorySnapshot>> {
    return request.get(`/inventory/tasks/${taskId}/snapshots/`, { params })
  },

  scanAsset(taskId: string, data: {
    qrCode: string
    actualLocation: string
  }): Promise<InventorySnapshot> {
    return request.post(`/inventory/tasks/${taskId}/scan/`, data)
  },

  confirmSnapshot(taskId: string, snapshotId: string, data: {
    result: string
    remark?: string
  }): Promise<void> {
    return request.post(`/inventory/tasks/${taskId}/snapshots/${snapshotId}/confirm/`, data)
  }
}
```

**Test**: Verify task lifecycle operations

---

#### Task 2.2.2: Create QR Code Scan API Service
**File**: `frontend/src/api/qrScan.ts`
**Time**: 3 minutes

```typescript
import request from '@/utils/request'

export const qrScanApi = {
  // Get asset info by QR code
  getAssetByQrCode(qrCode: string): Promise<{
    id: string
    code: string
    name: string
    categoryName: string
    status: string
    location: string
    custodian: string
  }> {
    return request.get('/assets/by-qr-code/', { params: { qr_code: qrCode } })
  },

  // Verify QR code validity
  verifyQrCode(qrCode: string): Promise<{
    valid: boolean
    assetId?: string
    error?: string
  }> {
    return request.post('/assets/verify-qr-code/', { qrCode })
  }
}
```

**Test**: Verify QR code lookup functionality

---

### 2.3 Finance API Service

#### Task 2.3.1: Create Voucher API Service
**File**: `frontend/src/api/finance.ts`
**Time**: 5 minutes

```typescript
import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { FinanceVoucher, VoucherTemplate } from '@/types/finance'

export const financeApi = {
  // Vouchers
  listVouchers(params?: {
    page?: number
    pageSize?: number
    status?: string
    businessType?: string
  }): Promise<PaginatedResponse<FinanceVoucher>> {
    return request.get('/finance/vouchers/', { params })
  },

  getVoucher(id: string): Promise<FinanceVoucher> {
    return request.get(`/finance/vouchers/${id}/`)
  },

  createVoucher(data: Partial<FinanceVoucher>): Promise<FinanceVoucher> {
    return request.post('/finance/vouchers/', data)
  },

  submitVoucher(id: string): Promise<void> {
    return request.post(`/finance/vouchers/${id}/submit/`)
  },

  approveVoucher(id: string, data: {
    action: 'approve' | 'reject'
    comment?: string
  }): Promise<void> {
    return request.post(`/finance/vouchers/${id}/approve/`, data)
  },

  pushVoucher(id: string, system?: string): Promise<{
    success: boolean
    externalVoucherNo?: string
  }> {
    return request.post(`/finance/vouchers/${id}/push/`, { system })
  },

  // Templates
  listTemplates(params?: {
    businessType?: string
  }): Promise<VoucherTemplate[]> {
    return request.get('/finance/voucher-templates/', { params })
  }
}
```

**Test**: Verify voucher workflow operations

---

#### Task 2.3.2: Create Depreciation API Service
**File**: `frontend/src/api/depreciation.ts`
**Time**: 4 minutes

```typescript
import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { DepreciationRecord } from '@/types/depreciation'

export const depreciationApi = {
  listRecords(params?: {
    page?: number
    pageSize?: number
    period?: string
    status?: string
  }): Promise<PaginatedResponse<DepreciationRecord>> {
    return request.get('/depreciation/records/', { params })
  },

  calculate(params?: {
    period?: string
    assetIds?: string[]
  }): Promise<{ taskId: string }> {
    return request.post('/depreciation/calculate/', params)
  },

  getCalculationStatus(taskId: string): Promise<{
    status: string
    progress: number
    total: number
    processed: number
  }> {
    return request.get(`/depreciation/calculate/${taskId}/status/`)
  },

  postRecord(id: string): Promise<void> {
    return request.post(`/depreciation/records/${id}/post/`)
  },

  getReport(params: {
    period: string
  }): Promise<any> {
    return request.get('/depreciation/report/', { params })
  }
}
```

**Test**: Verify calculation status polling

---

### 2.4 Workflow API Service

#### Task 2.4.1: Create Workflow API Service
**File**: `frontend/src/api/workflow.ts`
**Time**: 5 minutes

```typescript
import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { WorkflowDefinition, WorkflowInstance } from '@/types/workflow'

export const workflowApi = {
  // Definitions
  listDefinitions(params?: {
    businessObject?: string
    isActive?: boolean
  }): Promise<WorkflowDefinition[]> {
    return request.get('/workflows/definitions/', { params })
  },

  getDefinition(id: string): Promise<WorkflowDefinition> {
    return request.get(`/workflows/definitions/${id}/`)
  },

  saveDefinition(data: Partial<WorkflowDefinition>): Promise<WorkflowDefinition> {
    return request.post('/workflows/definitions/', data)
  },

  updateDefinition(id: string, data: Partial<WorkflowDefinition>): Promise<WorkflowDefinition> {
    return request.put(`/workflows/definitions/${id}/`, data)
  },

  activateDefinition(id: string): Promise<void> {
    return request.post(`/workflows/definitions/${id}/activate/`)
  },

  // Instances
  listInstances(params?: {
    businessDataType?: string
    businessDataId?: string
    status?: string
  }): Promise<PaginatedResponse<WorkflowInstance>> {
    return request.get('/workflows/instances/', { params })
  },

  startInstance(definitionId: string, data: {
    businessDataType: string
    businessDataId: string
  }): Promise<WorkflowInstance> {
    return request.post('/workflows/instances/start/', {
      definitionId,
      ...data
    })
  },

  approveNode(instanceId: string, nodeId: string, data: {
    action: 'approve' | 'reject'
    comment?: string
  }): Promise<void> {
    return request.post(`/workflows/instances/${instanceId}/nodes/${nodeId}/approve/`, data)
  }
}
```

**Test**: Verify workflow instance creation

---

## Phase 3: Common Components

### 3.1 Base List Page Component

#### Task 3.1.1: Create BaseListPage Component
**File**: `frontend/src/components/common/BaseListPage.vue`
**Time**: 15 minutes

```vue
<template>
  <div class="base-list-page">
    <el-card class="search-card" v-if="searchFields.length > 0">
      <el-form :model="searchForm" inline>
        <el-form-item
          v-for="field in searchFields"
          :key="field.field"
          :label="field.label"
        >
          <el-input
            v-if="field.type === 'input'"
            v-model="searchForm[field.field]"
            :placeholder="field.placeholder"
            clearable
          />
          <el-select
            v-else-if="field.type === 'select'"
            v-model="searchForm[field.field]"
            :placeholder="field.placeholder"
            clearable
            :multiple="field.multiple"
          >
            <el-option
              v-for="opt in field.options"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
          <el-date-picker
            v-else-if="field.type === 'daterange'"
            v-model="searchForm[field.field]"
            type="daterange"
            range-separator="-"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header v-if="$slots.actions">
        <div class="card-header">
          <slot name="actions" :selected-rows="selectedRows" />
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="tableData"
        border
        @selection-change="handleSelectionChange"
      >
        <el-table-column v-if="selectable" type="selection" width="50" />
        <el-table-column
          v-for="col in columns"
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
          :width="col.width"
          :min-width="col.minWidth"
          :align="col.align"
          :fixed="col.fixed"
        >
          <template #default="{ row }" v-if="col.slot">
            <slot :name="`cell-${col.prop}`" :row="row" />
          </template>
          <template #default="{ row }" v-else-if="col.format">
            {{ col.format(row[col.prop], row) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" :width="actionWidth" fixed="right" v-if="$slots.actionsRow">
          <template #default="{ row }">
            <slot name="actionsRow" :row="row" />
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next"
        @size-change="fetchData"
        @current-change="fetchData"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import type { TableColumn, SearchField } from '@/types/common'

interface Props {
  fetchMethod: (params: any) => Promise<any>
  columns: TableColumn[]
  searchFields?: SearchField[]
  selectable?: boolean
  actionWidth?: number
}

const props = withDefaults(defineProps<Props>(), {
  searchFields: () => [],
  selectable: true,
  actionWidth: 150
})

const searchForm = reactive<Record<string, any>>({})
const tableData = ref<any[]>([])
const selectedRows = ref<any[]>([])
const loading = ref(false)

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const fetchData = async () => {
  loading.value = true
  try {
    const response = await props.fetchMethod({
      ...searchForm,
      page: pagination.page,
      pageSize: pagination.pageSize
    })
    tableData.value = response.results || response
    pagination.total = response.count || response.length
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

const handleReset = () => {
  Object.keys(searchForm).forEach(key => {
    searchForm[key] = undefined
  })
  handleSearch()
}

const handleSelectionChange = (rows: any[]) => {
  selectedRows.value = rows
}

defineExpose({ fetchData, refresh: fetchData })

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.base-list-page {
  padding: 20px;
}

.search-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

**Test**: Create a test list page using BaseListPage

---

### 3.2 Base Form Component

#### Task 3.2.1: Create DynamicFieldRenderer Component
**File**: `frontend/src/components/common/DynamicFieldRenderer.vue`
**Time**: 20 minutes

```vue
<template>
  <el-form-item :label="field.label" :required="field.required">
    <!-- Input field -->
    <el-input
      v-if="field.type === 'input'"
      v-model="modelValue"
      :placeholder="field.placeholder"
      :disabled="field.disabled"
      clearable
    />

    <!-- Textarea -->
    <el-input
      v-else-if="field.type === 'textarea'"
      v-model="modelValue"
      type="textarea"
      :rows="field.rows || 3"
      :placeholder="field.placeholder"
    />

    <!-- Number input -->
    <el-input-number
      v-else-if="field.type === 'number'"
      v-model="modelValue"
      :min="field.min"
      :max="field.max"
      :precision="field.precision || 2"
    />

    <!-- Select -->
    <el-select
      v-else-if="field.type === 'select'"
      v-model="modelValue"
      :placeholder="field.placeholder"
      :multiple="field.multiple"
      clearable
    >
      <el-option
        v-for="opt in field.options"
        :key="opt.value"
        :label="opt.label"
        :value="opt.value"
      />
    </el-select>

    <!-- Date picker -->
    <el-date-picker
      v-else-if="field.type === 'date'"
      v-model="modelValue"
      type="date"
      :placeholder="field.placeholder"
      value-format="YYYY-MM-DD"
    />

    <!-- Date range picker -->
    <el-date-picker
      v-else-if="field.type === 'daterange'"
      v-model="modelValue"
      type="daterange"
      range-separator="-"
      start-placeholder="开始日期"
      end-placeholder="结束日期"
      value-format="YYYY-MM-DD"
    />

    <!-- Tree select -->
    <el-tree-select
      v-else-if="field.type === 'treeselect'"
      v-model="modelValue"
      :data="field.options"
      :props="{ label: 'label', value: 'value' }"
      :placeholder="field.placeholder"
      clearable
    />

    <!-- User picker -->
    <UserPicker
      v-else-if="field.type === 'user'"
      v-model="modelValue"
      :multiple="field.multiple"
    />

    <!-- Department picker -->
    <DeptPicker
      v-else-if="field.type === 'dept'"
      v-model="modelValue"
    />

    <!-- Asset selector -->
    <AssetSelector
      v-else-if="field.type === 'asset'"
      v-model="modelValue"
    />

    <!-- Switch -->
    <el-switch
      v-else-if="field.type === 'switch'"
      v-model="modelValue"
    />

    <!-- Radio group -->
    <el-radio-group
      v-else-if="field.type === 'radio'"
      v-model="modelValue"
    >
      <el-radio
        v-for="opt in field.options"
        :key="opt.value"
        :label="opt.value"
      >
        {{ opt.label }}
      </el-radio>
    </el-radio-group>

    <!-- Checkbox group -->
    <el-checkbox-group
      v-else-if="field.type === 'checkbox'"
      v-model="modelValue"
    >
      <el-checkbox
        v-for="opt in field.options"
        :key="opt.value"
        :label="opt.value"
      >
        {{ opt.label }}
      </el-checkbox>
    </el-checkbox-group>
  </el-form-item>
</template>

<script setup lang="ts">
import UserPicker from './UserPicker.vue'
import DeptPicker from './DeptPicker.vue'
import AssetSelector from './AssetSelector.vue'
import type { FieldConfig } from '@/types/common'

interface Props {
  field: FieldConfig
  modelValue: any
}

defineProps<Props>()
defineEmits<{
  'update:modelValue': [value: any]
}>()
</script>
```

**Test**: Render different field types and verify data binding

---

### 3.3 User/Dept Picker Components

#### Task 3.3.1: Create UserPicker Component
**File**: `frontend/src/components/common/UserPicker.vue`
**Time**: 10 minutes

```vue
<template>
  <el-select
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :multiple="multiple"
    :placeholder="placeholder"
    filterable
    remote
    :remote-method="searchUsers"
    :loading="loading"
    clearable
  >
    <el-option
      v-for="user in options"
      :key="user.id"
      :label="user.fullName"
      :value="user.id"
    >
      <div class="user-option">
        <el-avatar :src="user.avatar" :size="24" />
        <span>{{ user.fullName }}</span>
        <span class="user-email">{{ user.email }}</span>
      </div>
    </el-option>
  </el-select>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { User } from '@/types/common'
import { userApi } from '@/api/users'

interface Props {
  modelValue: string | string[]
  multiple?: boolean
  placeholder?: string
}

withDefaults(defineProps<Props>(), {
  multiple: false,
  placeholder: '请选择用户'
})

defineEmits<{
  'update:modelValue': [value: any]
}>()

const loading = ref(false)
const options = ref<User[]>([])

const searchUsers = async (query: string) => {
  if (!query) {
    options.value = []
    return
  }
  loading.value = true
  try {
    const data = await userApi.list({ search: query, pageSize: 50 })
    options.value = data.results
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.user-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-email {
  color: #999;
  font-size: 12px;
  margin-left: auto;
}
</style>
```

**Test**: Search and select users

---

#### Task 3.3.2: Create DeptPicker Component
**File**: `frontend/src/components/common/DeptPicker.vue`
**Time**: 10 minutes

```vue
<template>
  <el-tree-select
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :data="treeData"
    :props="{ label: 'name', value: 'id', children: 'children' }"
    :placeholder="placeholder"
    clearable
    check-strictly
    :render-after-expand="false"
  />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { Organization } from '@/types/common'
import { orgApi } from '@/api/organizations'

interface Props {
  modelValue: string
  placeholder?: string
}

withDefaults(defineProps<Props>(), {
  placeholder: '请选择部门'
})

defineEmits<{
  'update:modelValue': [value: any]
}>()

const treeData = ref<Organization[]>([])

onMounted(async () => {
  treeData.value = await orgApi.tree()
})
</script>
```

**Test**: Select department from tree

---

## Phase 4: Module Views

### 4.1 Asset Management Views

#### Task 4.1.1: Create AssetList View
**File**: `frontend/src/views/assets/AssetList.vue`
**Time**: 15 minutes

```vue
<template>
  <BaseListPage
    :fetch-method="assetApi.list"
    :columns="columns"
    :search-fields="searchFields"
    @selection-change="handleSelectionChange"
  >
    <template #actions="{ selectedRows }">
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新增资产
      </el-button>
      <el-button
        :icon="Download"
        @click="handleExport"
      >
        导出
      </el-button>
      <el-button
        :icon="Delete"
        :disabled="selectedRows.length === 0"
        @click="handleBatchDelete(selectedRows)"
      >
        批量删除
      </el-button>
    </template>

    <template #cell-status="{ row }">
      <el-tag :type="getStatusType(row.status)">
        {{ getStatusLabel(row.status) }}
      </el-tag>
    </template>

    <template #cell-purchasePrice="{ row }">
      ¥{{ formatMoney(row.purchasePrice) }}
    </template>

    <template #actionsRow="{ row }">
      <el-button link type="primary" @click="handleView(row)">
        详情
      </el-button>
      <el-button link type="primary" @click="handleEdit(row)">
        编辑
      </el-button>
      <el-button link type="danger" @click="handleDelete(row)">
        删除
      </el-button>
    </template>
  </BaseListPage>

  <AssetFormDialog
    v-model="formVisible"
    :asset="currentAsset"
    @success="refreshList"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Plus, Download, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import AssetFormDialog from '@/components/assets/AssetFormDialog.vue'
import { assetApi } from '@/api/assets'
import type { Asset, AssetStatus } from '@/types/assets'
import { formatMoney } from '@/utils/numberFormat'

const columns = [
  { prop: 'code', label: '资产编码', width: 140 },
  { prop: 'name', label: '资产名称', minWidth: 200 },
  { prop: 'categoryName', label: '分类', width: 120 },
  { prop: 'purchasePrice', label: '采购金额', width: 120, slot: true },
  { prop: 'purchaseDate', label: '采购日期', width: 120 },
  { prop: 'status', label: '状态', width: 100, slot: true }
]

const searchFields = [
  { field: 'search', label: '关键词', type: 'input', placeholder: '编码/名称' },
  {
    field: 'categoryId',
    label: '分类',
    type: 'select',
    options: [] // Load from API
  },
  {
    field: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '使用中', value: 'in_use' },
      { label: '闲置', value: 'idle' },
      { label: '维修中', value: 'maintenance' }
    ]
  }
]

const formVisible = ref(false)
const currentAsset = ref<Asset | null>(null)

const getStatusType = (status: AssetStatus) => {
  const typeMap: Record<AssetStatus, string> = {
    draft: 'info',
    in_use: 'success',
    idle: 'warning',
    maintenance: 'danger',
    scrapped: 'info'
  }
  return typeMap[status] || ''
}

const getStatusLabel = (status: AssetStatus) => {
  const labelMap: Record<AssetStatus, string> = {
    draft: '草稿',
    in_use: '使用中',
    idle: '闲置',
    maintenance: '维修中',
    scrapped: '已报废'
  }
  return labelMap[status] || status
}

const handleCreate = () => {
  currentAsset.value = null
  formVisible.value = true
}

const handleView = (row: Asset) => {
  // Navigate to detail page
}

const handleEdit = (row: Asset) => {
  currentAsset.value = row
  formVisible.value = true
}

const handleDelete = async (row: Asset) => {
  try {
    await ElMessageBox.confirm('确认删除此资产？', '警告')
    await assetApi.delete(row.id)
    ElMessage.success('删除成功')
    refreshList()
  } catch {
    // User cancelled
  }
}

const handleBatchDelete = async (rows: Asset[]) => {
  try {
    await ElMessageBox.confirm(`确认删除 ${rows.length} 项资产？`, '批量删除')
    await assetApi.batchDelete(rows.map(r => r.id))
    ElMessage.success('批量删除成功')
    refreshList()
  } catch {
    // User cancelled
  }
}

const handleExport = async () => {
  // Implement export
}

const refreshList = () => {
  window.dispatchEvent(new Event('refresh-table'))
}
</script>
```

**Test**: Verify list, search, and CRUD operations

---

#### Task 4.1.2: Create AssetFormDialog Component
**File**: `frontend/src/components/assets/AssetFormDialog.vue`
**Time**: 15 minutes

```vue
<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :title="asset ? '编辑资产' : '新增资产'"
    width="600px"
    @open="handleOpen"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="资产编码" prop="code">
        <el-input v-model="formData.code" placeholder="请输入资产编码" />
      </el-form-item>

      <el-form-item label="资产名称" prop="name">
        <el-input v-model="formData.name" placeholder="请输入资产名称" />
      </el-form-item>

      <el-form-item label="资产分类" prop="categoryId">
        <el-cascader
          v-model="formData.categoryId"
          :options="categoryTree"
          :props="{ value: 'id', label: 'name', emitPath: false }"
          placeholder="请选择分类"
          clearable
        />
      </el-form-item>

      <el-form-item label="采购金额" prop="purchasePrice">
        <el-input-number
          v-model="formData.purchasePrice"
          :min="0"
          :precision="2"
          :disabled="!!asset"
        />
      </el-form-item>

      <el-form-item label="采购日期" prop="purchaseDate">
        <el-date-picker
          v-model="formData.purchaseDate"
          type="date"
          placeholder="选择日期"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item label="存放位置" prop="locationId">
        <el-tree-select
          v-model="formData.locationId"
          :data="locationTree"
          :props="{ value: 'id', label: 'name' }"
          placeholder="请选择位置"
          clearable
        />
      </el-form-item>

      <el-form-item label="使用人" prop="custodianId">
        <UserPicker v-model="formData.custodianId" />
      </el-form-item>

      <el-form-item label="备注" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="请输入备注"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="submitting">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import UserPicker from '@/components/common/UserPicker.vue'
import { assetApi } from '@/api/assets'
import { categoryApi } from '@/api/assetCategories'
import type { Asset } from '@/types/assets'

interface Props {
  modelValue: boolean
  asset?: Asset | null
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  success: []
}>()

const formRef = ref()
const submitting = ref(false)
const categoryTree = ref([])
const locationTree = ref([])

const formData = reactive({
  code: '',
  name: '',
  categoryId: '',
  purchasePrice: 0,
  purchaseDate: '',
  locationId: '',
  custodianId: '',
  description: ''
})

const rules = {
  code: [{ required: true, message: '请输入资产编码', trigger: 'blur' }],
  name: [{ required: true, message: '请输入资产名称', trigger: 'blur' }],
  categoryId: [{ required: true, message: '请选择分类', trigger: 'change' }],
  purchasePrice: [{ required: true, message: '请输入采购金额', trigger: 'blur' }]
}

const handleOpen = async () => {
  // Load options
  categoryTree.value = await categoryApi.tree()

  if (props.asset) {
    Object.assign(formData, {
      code: props.asset.code,
      name: props.asset.name,
      categoryId: props.asset.categoryId,
      purchasePrice: props.asset.purchasePrice,
      purchaseDate: props.asset.purchaseDate,
      locationId: props.asset.locationId,
      custodianId: props.asset.custodianId,
      description: props.asset.description
    })
  } else {
    formRef.value?.resetFields()
  }
}

const handleSubmit = async () => {
  await formRef.value?.validate()
  submitting.value = true
  try {
    if (props.asset) {
      await assetApi.update(props.asset.id, formData)
      ElMessage.success('更新成功')
    } else {
      await assetApi.create(formData)
      ElMessage.success('创建成功')
    }
    emit('success')
    emit('update:modelValue', false)
  } finally {
    submitting.value = false
  }
}
</script>
```

**Test**: Verify form validation and submission

---

### 4.2 Inventory Views

#### Task 4.2.1: Create InventoryTaskList View
**File**: `frontend/src/views/inventory/TaskList.vue`
**Time**: 12 minutes

```vue
<template>
  <BaseListPage
    :fetch-method="inventoryApi.listTasks"
    :columns="columns"
    :search-fields="searchFields"
  >
    <template #actions>
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新建盘点任务
      </el-button>
    </template>

    <template #cell-status="{ row }">
      <el-tag :type="getStatusType(row.status)">
        {{ getStatusLabel(row.status) }}
      </el-tag>
    </template>

    <template #cell-progress="{ row }">
      <el-progress
        :percentage="getProgress(row)"
        :status="getProgress(row) === 100 ? 'success' : undefined"
      />
    </template>

    <template #actionsRow="{ row }">
      <el-button
        link
        type="primary"
        @click="handleView(row)"
      >
        查看
      </el-button>
      <el-button
        v-if="row.status === 'pending'"
        link
        type="success"
        @click="handleStart(row)"
      >
        开始
      </el-button>
      <el-button
        v-if="row.status === 'in_progress'"
        link
        type="warning"
        @click="handleScan(row)"
      >
        扫描
      </el-button>
      <el-button
        v-if="row.status === 'in_progress'"
        link
        type="success"
        @click="handleComplete(row)"
      >
        完成
      </el-button>
    </template>
  </BaseListPage>

  <TaskFormDialog
    v-model="formVisible"
    @success="refreshList"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import TaskFormDialog from '@/components/inventory/TaskFormDialog.vue'
import { inventoryApi } from '@/api/inventory'
import type { InventoryTask, TaskStatus } from '@/types/inventory'

const columns = [
  { prop: 'taskNo', label: '任务编号', width: 150 },
  { prop: 'taskName', label: '任务名称', minWidth: 200 },
  { prop: 'taskType', label: '类型', width: 100, format: (v: string) => getTypeLabel(v) },
  { prop: 'status', label: '状态', width: 100, slot: true },
  { prop: 'progress', label: '进度', width: 150, slot: true },
  { prop: 'plannedDate', label: '计划日期', width: 120 }
]

const searchFields = [
  {
    field: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '待开始', value: 'pending' },
      { label: '进行中', value: 'in_progress' },
      { label: '已完成', value: 'completed' }
    ]
  }
]

const formVisible = ref(false)

const getStatusLabel = (status: TaskStatus) => {
  const labels = {
    pending: '待开始',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return labels[status] || status
}

const getStatusType = (status: TaskStatus) => {
  const types = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'danger'
  }
  return types[status] || ''
}

const getTypeLabel = (type: string) => {
  const labels = {
    full: '全盘',
    partial: '抽盘',
    location: '按位置',
    category: '按分类'
  }
  return labels[type] || type
}

const getProgress = (row: InventoryTask) => {
  return row.assetCount > 0
    ? Math.round((row.scannedCount / row.assetCount) * 100)
    : 0
}

const handleCreate = () => {
  formVisible.value = true
}

const handleStart = async (row: InventoryTask) => {
  try {
    await ElMessageBox.confirm('确认开始此盘点任务？', '提示')
    await inventoryApi.startTask(row.id)
    ElMessage.success('任务已开始')
    refreshList()
  } catch {
    // User cancelled
  }
}

const handleScan = (row: InventoryTask) => {
  // Navigate to scan page
}

const handleComplete = async (row: InventoryTask) => {
  try {
    await ElMessageBox.confirm('确认完成此盘点任务？', '提示')
    await inventoryApi.completeTask(row.id)
    ElMessage.success('任务已完成')
    refreshList()
  } catch {
    // User cancelled
  }
}

const refreshList = () => {
  window.dispatchEvent(new Event('refresh-table'))
}
</script>
```

**Test**: Verify task list and status transitions

---

#### Task 4.2.2: Create QRScanner Component
**File**: `frontend/src/components/inventory/QRScanner.vue`
**Time`: 15 minutes

```vue
<template>
  <div class="qr-scanner">
    <div class="scanner-container" ref="containerRef">
      <video ref="videoRef" class="scanner-video" />
      <div class="scan-overlay">
        <div class="scan-frame"></div>
      </div>
    </div>

    <div class="scanner-info">
      <p class="scan-hint">将二维码放入框内自动扫描</p>
      <p class="scan-count">已扫描: {{ scannedCount }} / {{ totalCount }}</p>
    </div>

    <div class="scanner-controls">
      <el-button @click="toggleTorch" v-if="hasTorch">
        <el-icon><Flashlight /></el-icon>
        {{ torchOn ? '关闭闪光灯' : '打开闪光灯' }}
      </el-button>
      <el-button type="primary" @click="handleManualInput">
        手动输入
      </el-button>
    </div>

    <!-- Manual Input Dialog -->
    <el-dialog v-model="inputVisible" title="手动输入资产编码" width="400px">
      <el-input
        v-model="manualCode"
        placeholder="请输入资产编码或扫描结果"
        @keyup.enter="handleManualSubmit"
      />
      <template #footer>
        <el-button @click="inputVisible = false">取消</el-button>
        <el-button type="primary" @click="handleManualSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { BrowserMultiFormatReader } from '@zxing/library'
import { ElMessage } from 'element-plus'
import { Flashlight } from '@element-plus/icons-vue'

interface Props {
  taskId?: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  scan: [code: string]
}>()

const containerRef = ref<HTMLElement>()
const videoRef = ref<HTMLVideoElement>()
const codeReader = new BrowserMultiFormatReader()
const torchOn = ref(false)
const hasTorch = ref(false)
const scannedCount = ref(0)
const totalCount = ref(0)

const inputVisible = ref(false)
const manualCode = ref('')

let stream: MediaStream | null = null

const startScanner = async () => {
  try {
    // Request camera with facing mode environment (back camera)
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' }
    })

    if (videoRef.value) {
      videoRef.value.srcObject = stream
      videoRef.value.play()

      // Start QR code reading
      codeReader.decodeFromVideoDevice(
        null,
        videoRef.value,
        (result, error) => {
          if (result) {
            handleScanResult(result.text)
          }
        }
      )
    }

    // Check for torch capability
    const track = stream?.getVideoTracks()[0]
    const capabilities = (track as any)?.getCapabilities()
    hasTorch.value = capabilities?.torch || false
  } catch (error) {
    ElMessage.error('无法访问摄像头，请检查权限设置')
  }
}

const stopScanner = () => {
  codeReader.reset()
  stream?.getTracks().forEach(track => track.stop())
}

const handleScanResult = (code: string) => {
  // Prevent duplicate scans
  emit('scan', code)
  scannedCount.value++
}

const toggleTorch = async () => {
  const track = stream?.getVideoTracks()[0]
  if (track) {
    await (track as any).applyConstraints({
      advanced: [{ torch: !torchOn.value }]
    })
    torchOn.value = !torchOn.value
  }
}

const handleManualInput = () => {
  inputVisible.value = true
}

const handleManualSubmit = () => {
  if (manualCode.value.trim()) {
    handleScanResult(manualCode.value.trim())
    manualCode.value = ''
    inputVisible.value = false
  }
}

onMounted(() => {
  startScanner()
})

onUnmounted(() => {
  stopScanner()
})
</script>

<style scoped>
.qr-scanner {
  position: relative;
  width: 100%;
  height: 100%;
}

.scanner-container {
  position: relative;
  width: 100%;
  height: 400px;
  background: #000;
  overflow: hidden;
}

.scanner-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.scan-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.scan-frame {
  width: 250px;
  height: 250px;
  border: 2px solid #409eff;
  border-radius: 12px;
  position: relative;
}

.scan-frame::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background: #409eff;
  animation: scan 2s linear infinite;
}

@keyframes scan {
  0% { top: 0; }
  100% { top: 100%; }
}

.scanner-info {
  padding: 16px;
  text-align: center;
}

.scan-hint {
  color: #606266;
  margin-bottom: 8px;
}

.scan-count {
  color: #409eff;
  font-weight: 500;
}

.scanner-controls {
  display: flex;
  justify-content: center;
  gap: 12px;
  padding: 16px;
}
</style>
```

**Test**: Verify camera access and QR scanning on mobile

---

### 4.3 Finance Views

#### Task 4.3.1: Create VoucherList View
**File**: `frontend/src/views/finance/VoucherList.vue`
**Time**: 12 minutes

```vue
<template>
  <BaseListPage
    :fetch-method="financeApi.listVouchers"
    :columns="columns"
    :search-fields="searchFields"
  >
    <template #actions>
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新增凭证
      </el-button>
      <el-button :icon="Upload" @click="handleBatchPush">
        批量推送
      </el-button>
    </template>

    <template #cell-status="{ row }">
      <el-tag :type="getStatusType(row.status)">
        {{ getStatusLabel(row.status) }}
      </el-tag>
    </template>

    <template #cell-totalDebit="{ row }">
      <span class="money-text debit">¥{{ formatMoney(row.totalDebit) }}</span>
    </template>

    <template #cell-totalCredit="{ row }">
      <span class="money-text credit">¥{{ formatMoney(row.totalCredit) }}</span>
    </template>

    <template #actionsRow="{ row }">
      <el-button link type="primary" @click="handleView(row)">
        详情
      </el-button>
      <el-button
        v-if="row.status === 'submitted'"
        link
        type="success"
        @click="handleApprove(row)"
      >
        审核
      </el-button>
      <el-button
        v-if="['approved', 'submitted'].includes(row.status)"
        link
        type="warning"
        @click="handlePush(row)"
      >
        推送
      </el-button>
    </template>
  </BaseListPage>

  <VoucherFormDialog
    v-model="formVisible"
    :voucher="currentVoucher"
    @success="refreshList"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Plus, Upload } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import VoucherFormDialog from '@/components/finance/VoucherFormDialog.vue'
import { financeApi } from '@/api/finance'
import type { FinanceVoucher, VoucherStatus } from '@/types/finance'
import { formatMoney } from '@/utils/numberFormat'

const columns = [
  { prop: 'voucherNo', label: '凭证号', width: 150 },
  { prop: 'voucherDate', label: '凭证日期', width: 120 },
  { prop: 'businessType', label: '业务类型', width: 120 },
  { prop: 'description', label: '摘要', minWidth: 200 },
  { prop: 'totalDebit', label: '借方合计', width: 130, slot: true },
  { prop: 'totalCredit', label: '贷方合计', width: 130, slot: true },
  { prop: 'status', label: '状态', width: 100, slot: true }
]

const searchFields = [
  { field: 'voucherNo', label: '凭证号', type: 'input' },
  {
    field: 'businessType',
    label: '业务类型',
    type: 'select',
    options: [
      { label: '资产购入', value: 'asset_purchase' },
      { label: '资产折旧', value: 'asset_depreciation' },
      { label: '资产处置', value: 'asset_disposal' }
    ]
  },
  {
    field: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '草稿', value: 'draft' },
      { label: '已提交', value: 'submitted' },
      { label: '已审核', value: 'approved' },
      { label: '已过账', value: 'posted' }
    ]
  }
]

const formVisible = ref(false)
const currentVoucher = ref<FinanceVoucher | null>(null)

const getStatusLabel = (status: VoucherStatus) => {
  const labels = {
    draft: '草稿',
    submitted: '已提交',
    approved: '已审核',
    rejected: '已驳回',
    posted: '已过账'
  }
  return labels[status] || status
}

const getStatusType = (status: VoucherStatus) => {
  const types = {
    draft: 'info',
    submitted: 'warning',
    approved: 'success',
    rejected: 'danger',
    posted: ''
  }
  return types[status] || ''
}

const handleCreate = () => {
  currentVoucher.value = null
  formVisible.value = true
}

const handleApprove = async (row: FinanceVoucher) => {
  try {
    await ElMessageBox.confirm('确认审核通过此凭证？', '提示')
    await financeApi.approveVoucher(row.id, { action: 'approve' })
    ElMessage.success('审核成功')
    refreshList()
  } catch {
    // User cancelled
  }
}

const handlePush = async (row: FinanceVoucher) => {
  try {
    await ElMessageBox.confirm('确认推送到ERP系统？', '提示')
    const result = await financeApi.pushVoucher(row.id)
    if (result.success) {
      ElMessage.success(`推送成功，凭证号: ${result.externalVoucherNo}`)
    } else {
      ElMessage.error('推送失败')
    }
    refreshList()
  } catch {
    // User cancelled
  }
}

const handleBatchPush = () => {
  ElMessage.info('请先选择要推送的凭证')
}

const handleView = (row: FinanceVoucher) => {
  // Navigate to detail page
}

const refreshList = () => {
  window.dispatchEvent(new Event('refresh-table'))
}
</script>

<style scoped>
.money-text {
  font-family: 'Monaco', monospace;
  font-weight: 500;
}

.money-text.debit {
  color: #f56c6c;
}

.money-text.credit {
  color: #67c23a;
}
</style>
```

**Test**: Verify voucher list and operations

---

### 4.4 Workflow Views

#### Task 4.4.1: Create WorkflowDesigner Component
**File**: `frontend/src/components/workflow/WorkflowDesigner.vue`
**Time**: 20 minutes

```vue
<template>
  <div class="workflow-designer">
    <div class="designer-toolbar">
      <el-button-group>
        <el-button :icon="Plus" @click="addStartNode">开始</el-button>
        <el-button :icon="Plus" @click="addApprovalNode">审批节点</el-button>
        <el-button :icon="Plus" @click="addConditionNode">条件分支</el-button>
        <el-button :icon="Plus" @click="addEndNode">结束</el-button>
      </el-button-group>
      <div class="toolbar-spacer"></div>
      <el-button @click="handleSave">保存</el-button>
      <el-button @click="handleClear">清空</el-button>
    </div>

    <div class="designer-container">
      <div ref="lfContainerRef" class="lf-container"></div>
    </div>

    <!-- Property Panel -->
    <PropertyPanel
      v-model:visible="propertyVisible"
      :node="selectedNode"
      @update="handleNodeUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import LogicFlow from '@logicflow/core'
import '@logicflow/core/dist/style/index.css'
import PropertyPanel from './PropertyPanel.vue'
import type { LogicFlowNode, LogicFlowGraphData } from '@/types/workflow'

interface Props {
  modelValue?: LogicFlowGraphData
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [data: LogicFlowGraphData]
}>()

const lfContainerRef = ref<HTMLElement>()
const propertyVisible = ref(false)
const selectedNode = ref<LogicFlowNode | null>(null)

let lf: LogicFlow | null = null

const initLogicFlow = () => {
  lf = new LogicFlow({
    container: lfContainerRef.value!,
    width: 800,
    height: 600,
    edgeTextDraggable: true,
    nodeSelectedOutline: true,
    multipleSelectKey: 'ctrl',
    plugins: []
  })

  // Register event handlers
  lf.on('node:click', ({ data }) => {
    selectedNode.value = data
    propertyVisible.value = true
  })

  lf.on('edge:click', () => {
    // Handle edge selection
  })

  lf.on('history:change', () => {
    emit('update:modelValue', lf?.getGraphData() as LogicFlowGraphData)
  })

  // Load initial data if provided
  if (props.modelValue) {
    lf.render(props.modelValue)
  }
}

const addStartNode = () => {
  lf?..addNode({
    type: 'start',
    x: 100,
    y: 300,
    text: '开始'
  })
}

const addApprovalNode = () => {
  lf?.addNode({
    type: 'approval',
    x: 300,
    y: 300,
    text: '审批节点',
    properties: {
      approvers: [],
      approvalType: 'or' // or, and, sequence
    }
  })
}

const addConditionNode = () => {
  lf?.addNode({
    type: 'condition',
    x: 500,
    y: 300,
    text: '条件分支',
    properties: {
      conditions: []
    }
  })
}

const addEndNode = () => {
  lf?.addNode({
    type: 'end',
    x: 700,
    y: 300,
    text: '结束'
  })
}

const handleNodeUpdate = (updates: Partial<LogicFlowNode>) => {
  if (selectedNode.value && lf) {
    lf.setNodeData(selectedNode.value.id, {
      ...selectedNode.value,
      ...updates
    } as any)
    emit('update:modelValue', lf.getGraphData() as LogicFlowGraphData)
  }
}

const handleSave = () => {
  const data = lf?.getGraphData()
  emit('update:modelValue', data as LogicFlowGraphData)
}

const handleClear = () => {
  lf?.clearData()
}

onMounted(() => {
  initLogicFlow()
})

onUnmounted(() => {
  lf?.destroy()
})
</script>

<style scoped>
.workflow-designer {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.designer-toolbar {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
  gap: 12px;
}

.toolbar-spacer {
  flex: 1;
}

.designer-container {
  flex: 1;
  overflow: hidden;
}

.lf-container {
  width: 100%;
  height: 100%;
  background: #f5f5f5;
}
</style>
```

**Test**: Verify node creation, connection, and property editing

---

## Phase 5: Mobile Adaptation

### 5.1 Mobile Assets Views

#### Task 5.1.1: Create Mobile Asset Detail View
**File**: `frontend/src/views/mobile/assets/AssetDetail.vue`
**Time**: 10 minutes

```vue
<template>
  <div class="mobile-asset-detail">
    <van-nav-bar
      title="资产详情"
      left-text="返回"
      left-arrow
      @click-left="goBack"
    >
      <template #right>
        <van-icon name="ellipsis" @click="showActions = true" />
      </template>
    </van-nav-bar>

    <div v-if="loading" class="loading">
      <van-loading size="24px">加载中...</van-loading>
    </div>

    <div v-else-if="asset" class="asset-content">
      <!-- Asset Header -->
      <div class="asset-header">
        <div class="asset-code">{{ asset.code }}</div>
        <van-tag :type="getStatusType(asset.status)">
          {{ getStatusLabel(asset.status) }}
        </van-tag>
      </div>

      <!-- Asset Info -->
      <van-cell-group inset title="基本信息">
        <van-cell title="资产名称" :value="asset.name" />
        <van-cell title="资产分类" :value="asset.category?.name" />
        <van-cell title="采购金额" :value="`¥${formatMoney(asset.purchasePrice)}`" />
        <van-cell title="采购日期" :value="asset.purchaseDate" />
        <van-cell title="存放位置" :value="asset.location?.name" />
        <van-cell title="使用人" :value="asset.custodian?.fullName" />
      </van-cell-group>

      <!-- Custom Fields -->
      <van-cell-group inset title="扩展信息" v-if="hasCustomFields">
        <van-cell
          v-for="(value, key) in asset.customFields"
          :key="key"
          :title="getFieldLabel(key)"
          :value="value"
        />
      </van-cell-group>

      <!-- Timeline -->
      <van-cell-group inset title="操作记录">
        <AssetTimeline :asset-id="asset.id" />
      </van-cell-group>
    </div>

    <!-- Action Sheet -->
    <van-action-sheet
      v-model:show="showActions"
      :actions="actionItems"
      @select="handleAction"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { assetApi } from '@/api/assets'
import type { Asset, AssetStatus } from '@/types/assets'
import { formatMoney } from '@/utils/numberFormat'

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const asset = ref<Asset | null>(null)
const showActions = ref(false)

const actionItems = [
  { name: '编辑', icon: 'edit' },
  { name: '打印二维码', icon: 'qr' },
  { name: '查看操作记录', icon: 'records' }
]

const hasCustomFields = computed(() => {
  return asset.value?.customFields && Object.keys(asset.value.customFields).length > 0
})

const getStatusLabel = (status: AssetStatus) => {
  const labels: Record<AssetStatus, string> = {
    draft: '草稿',
    in_use: '使用中',
    idle: '闲置',
    maintenance: '维修中',
    scrapped: '已报废'
  }
  return labels[status] || status
}

const getStatusType = (status: AssetStatus) => {
  const types: Record<AssetStatus, 'success' | 'warning' | 'danger' | 'primary'> = {
    draft: 'primary',
    in_use: 'success',
    idle: 'warning',
    maintenance: 'danger',
    scrapped: 'default'
  }
  return types[status] || 'default'
}

const getFieldLabel = (key: string) => {
  // Get field label from metadata
  return key
}

const goBack = () => {
  router.back()
}

const handleAction = (item: any) => {
  showActions.value = false
  showToast(`操作: ${item.name}`)
}

onMounted(async () => {
  try {
    const id = route.params.id as string
    asset.value = await assetApi.get(id)
  } catch (error) {
    showToast('加载失败')
    goBack()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.mobile-asset-detail {
  min-height: 100vh;
  background: #f5f5f5;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.asset-content {
  padding: 16px 0;
}

.asset-header {
  background: white;
  padding: 16px;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.asset-code {
  font-size: 18px;
  font-weight: 600;
  color: #323233;
}
</style>
```

**Test**: Verify mobile layout and touch interactions

---

### 5.2 Mobile Scan Views

#### Task 5.2.1: Create Unified Scan Page
**File**: `frontend/src/views/mobile/scan/UnifiedScan.vue`
**Time**: 12 minutes

```vue
<template>
  <div class="unified-scan">
    <van-nav-bar
      title="扫码"
      left-text="返回"
      left-arrow
      @click-left="goBack"
    />

    <!-- Scanner -->
    <MobileQRScanner
      @scan="handleScan"
      :task-id="taskId"
    />

    <!-- Recent Scans -->
    <div class="recent-scans" v-if="recentScans.length > 0">
      <div class="section-title">最近扫描</div>
      <van-cell
        v-for="item in recentScans"
        :key="item.id"
        :title="item.assetName"
        :label="item.scannedAt"
        is-link
        @click="handleViewAsset(item.assetId)"
      >
        <template #icon>
          <van-icon name="checked" color="#52c41a" />
        </template>
      </van-cell>
    </div>

    <!-- Manual Input -->
    <div class="manual-input">
      <van-button
        block
        type="primary"
        icon="aim"
        @click="showManualInput = true"
      >
        手动输入
      </van-button>
    </div>

    <!-- Manual Input Dialog -->
    <van-dialog
      v-model:show="showManualInput"
      title="手动输入"
      show-cancel-button
      @confirm="handleManualSubmit"
    >
      <van-field
        v-model="manualCode"
        placeholder="请输入资产编码或二维码内容"
        clearable
      />
    </van-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast, showDialog } from 'vant'
import MobileQRScanner from '@/components/mobile/MobileQRScanner.vue'
import { qrScanApi } from '@/api/qrScan'

const router = useRouter()
const route = useRoute()

const taskId = ref(route.query.taskId as string | undefined)
const recentScans = ref<any[]>([])
const showManualInput = ref(false)
const manualCode = ref('')

const handleScan = async (code: string) => {
  try {
    const result = await qrScanApi.getAssetByQrCode(code)
    await showDialog({
      title: result.name,
      message: `编码: ${result.code}\n分类: ${result.categoryName}\n状态: ${result.status}`
    })

    // Add to recent scans
    recentScans.value.unshift({
      id: Date.now(),
      assetId: result.id,
      assetName: result.name,
      scannedAt: new Date().toLocaleString()
    })
  } catch (error) {
    showToast('未找到对应资产')
  }
}

const handleManualSubmit = () => {
  if (manualCode.value.trim()) {
    handleScan(manualCode.value.trim())
    manualCode.value = ''
    showManualInput.value = false
  }
}

const handleViewAsset = (assetId: string) => {
  router.push(`/mobile/assets/${assetId}`)
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.unified-scan {
  min-height: 100vh;
  background: #f5f5f5;
}

.recent-scans {
  padding: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 500;
  color: #646566;
  margin-bottom: 8px;
}

.manual-input {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 12px 16px;
  background: white;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
}
</style>
```

**Test**: Verify scan-to-result flow on mobile

---

## Summary

This implementation plan breaks down the entire GZEAMS frontend into **50+ bite-sized TDD tasks** organized across 5 phases:

1. **Infrastructure Layer** (12 tasks) - Types, utilities, interceptors
2. **API Service Layer** (10 tasks) - All module API services
3. **Common Components** (6 tasks) - BaseListPage, DynamicFieldRenderer, pickers
4. **Module Views** (15 tasks) - Asset, Inventory, Finance, Workflow views
5. **Mobile Adaptation** (4 tasks) - Mobile-specific views and scanner

Each task is designed to take **2-20 minutes** and includes:
- Exact file path
- Complete code snippet
- Test verification step

### Implementation Order Recommendation

1. Start with **Phase 1** (Infrastructure) - all tasks must be completed first
2. Then **Phase 2** (API Services) - in parallel with Phase 3
3. Then **Phase 3** (Common Components) - enables rapid module view development
4. Then **Phase 4** (Module Views) - can be done in any order per module
5. Finally **Phase 5** (Mobile) - after desktop views are stable

### Prerequisites

Before starting implementation, ensure:
- Node.js 18+ and npm/pnpm installed
- Vite Vue 3 project initialized
- Element Plus and Vant (mobile UI) installed
- Backend APIs are accessible

### Related Documents

- [API Standardization Design](../common_base_features/00_core/frontend_api_standardization_design.md)
- [Frontend PRD v2.0 files](../phase*/frontend_v2.md)
