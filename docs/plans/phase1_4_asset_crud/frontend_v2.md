# Phase 1.4: Asset CRUD - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement complete CRUD operations for asset management with BaseListPage/BaseFormPage integration.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/models/asset.ts

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
  description?: string
  specifications?: Record<string, string>
  purchaseDate?: string
  purchasePrice?: number
  supplierId?: string
  supplier?: Supplier
  warrantyExpireDate?: string
  imageUrl?: string
  qrCode: string
  isDeleted: boolean
  createdAt: string
  updatedAt: string
  createdBy: string
  updatedBy?: string
  customFields?: Record<string, any>
}

export enum AssetStatus {
  IDLE = 'idle',
  IN_USE = 'in_use',
  MAINTENANCE = 'maintenance',
  SCRAPPED = 'scrapped'
}

export interface AssetCreate {
  code: string
  name: string
  categoryId: string
  status?: AssetStatus
  locationId?: string
  custodianId?: string
  description?: string
  specifications?: Record<string, string>
  purchaseDate?: string
  purchasePrice?: number
  supplierId?: string
  warrantyExpireDate?: string
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
  purchaseDateFrom?: string
  purchaseDateTo?: string
}
```

### API Service

```typescript
// frontend/src/api/assets.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { Asset, AssetCreate, AssetUpdate, AssetFilters } from '@/types/models/asset'

export const assetApi = {
  list(filters?: AssetFilters): Promise<PaginatedResponse<Asset>> {
    return request.get('/assets/', { params: filters })
  },

  get(id: string): Promise<Asset> {
    return request.get(`/assets/${id}/`)
  },

  create(data: AssetCreate): Promise<Asset> {
    return request.post('/assets/', data)
  },

  update(id: string, data: AssetUpdate): Promise<Asset> {
    return request.put(`/assets/${id}/`, data)
  },

  partialUpdate(id: string, data: Partial<AssetUpdate>): Promise<Asset> {
    return request.patch(`/assets/${id}/`, data)
  },

  delete(id: string): Promise<void> {
    return request.delete(`/assets/${id}/`)
  },

  batchDelete(ids: string[]): Promise<BatchResponse> {
    return request.post('/assets/batch-delete/', { ids })
  },

  restore(id: string): Promise<void> {
    return request.post(`/assets/${id}/restore/`)
  },

  getDeleted(filters?: AssetFilters): Promise<PaginatedResponse<Asset>> {
    return request.get('/assets/deleted/', { params: filters })
  }
}
```

---

## Component: Asset List

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
    <template #status="{ row }">
      <el-tag :type="getStatusType(row.status)">
        {{ getStatusLabel(row.status) }}
      </el-tag>
    </template>
    <template #actions="{ row }">
      <el-button link type="primary" @click.stop="handleEdit(row)">编辑</el-button>
      <el-button link type="danger" @click.stop="handleDelete(row)">删除</el-button>
    </template>
  </BaseListPage>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { assetApi, AssetStatus } from '@/api/assets'
import { ElMessage } from 'element-plus'

const router = useRouter()

const columns = [
  { prop: 'code', label: '资产编码', width: 150, fixed: 'left' },
  { prop: 'name', label: '资产名称', minWidth: 200 },
  { prop: 'category.name', label: '分类', width: 120 },
  { prop: 'status', label: '状态', width: 100, slot: true },
  { prop: 'location.name', label: '存放位置', width: 150 },
  { prop: 'custodian.realName', label: '保管人', width: 120 },
  { prop: 'purchasePrice', label: '采购价格', width: 120 },
  { prop: 'createdAt', label: '创建时间', width: 180, type: 'datetime' },
  { prop: 'actions', label: '操作', width: 150, slot: true, fixed: 'right' }
]

const searchFields = [
  { prop: 'keyword', label: '搜索', placeholder: '编码/名称' }
]

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
  }
]

const handleRowClick = (row: Asset) => {
  router.push(`/assets/${row.id}`)
}

const handleCreate = () => {
  router.push('/assets/create')
}

const handleEdit = (row: Asset) => {
  router.push(`/assets/${row.id}/edit`)
}

const handleDelete = async (row: Asset) => {
  try {
    await assetApi.delete(row.id)
    ElMessage.success('删除成功')
  } catch (error) {
    // Error handled by interceptor
  }
}

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

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/models/asset.ts` | Asset type definitions |
| `frontend/src/api/assets.ts` | Asset API service |
| `frontend/src/views/assets/AssetList.vue` | Asset list page |
| `frontend/src/views/assets/AssetForm.vue` | Asset form page |
| `frontend/src/views/assets/AssetDetail.vue` | Asset detail page |
