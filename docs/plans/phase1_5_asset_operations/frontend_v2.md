# Phase 1.5: Asset Operations - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement asset operations: pickup (领用), loan (借用), transfer (调拨), return (归还).

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/operations.ts

export interface Pickup {
  id: string
  pickupNo: string
  departmentId: string
  department?: Department
  pickupDate: string
  expectedReturnDate?: string
  pickupReason: string
  status: OperationStatus
  items: PickupItem[]
  approvals: ApprovalRecord[]
  organizationId: string
  createdAt: string
  createdBy: string
}

export interface PickupItem {
  assetId: string
  asset?: Asset
  quantity: number
  remark?: string
}

export interface Transfer {
  id: string
  transferNo: string
  fromDepartmentId: string
  toDepartmentId: string
  fromCustodianId?: string
  toCustodianId?: string
  transferDate: string
  transferReason: string
  status: OperationStatus
  items: TransferItem[]
  approvals: ApprovalRecord[]
  organizationId: string
  createdAt: string
}

export interface TransferItem {
  assetId: string
  asset?: Asset
  quantity: number
  remark?: string
}

export interface Loan {
  id: string
  loanNo: string
  borrowerId: string
  borrower?: User
  loanDate: string
  expectedReturnDate: string
  loanReason: string
  status: OperationStatus
  items: LoanItem[]
  approvals: ApprovalRecord[]
  organizationId: string
  createdAt: string
}

export interface LoanItem {
  assetId: string
  asset?: Asset
  quantity: number
  remark?: string
}

export enum OperationStatus {
  DRAFT = 'draft',
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

export interface CreatePickupData {
  departmentId: string
  pickupDate: string
  expectedReturnDate?: string
  pickupReason: string
  items: PickupItem[]
}

export interface CreateTransferData {
  fromDepartmentId: string
  toDepartmentId: string
  transferDate: string
  transferReason: string
  items: TransferItem[]
}

export interface CreateLoanData {
  borrowerId: string
  loanDate: string
  expectedReturnDate: string
  loanReason: string
  items: LoanItem[]
}

export interface ApprovalData {
  action: 'approve' | 'reject'
  comment?: string
}
```

### API Service

```typescript
// frontend/src/api/operations.ts

import request from '@/utils/request'
import type { PaginatedResponse, BatchResponse } from '@/types/api'
import type {
  Pickup,
  Transfer,
  Loan,
  CreatePickupData,
  CreateTransferData,
  CreateLoanData,
  ApprovalData
} from '@/types/operations'

export const pickupApi = {
  list(params?: any): Promise<PaginatedResponse<Pickup>> {
    return request.get('/assets/pickups/', { params })
  },

  get(id: string): Promise<Pickup> {
    return request.get(`/assets/pickups/${id}/`)
  },

  create(data: CreatePickupData): Promise<Pickup> {
    return request.post('/assets/pickups/', data)
  },

  update(id: string, data: CreatePickupData): Promise<Pickup> {
    return request.put(`/assets/pickups/${id}/`, data)
  },

  submit(id: string): Promise<void> {
    return request.post(`/assets/pickups/${id}/submit/`)
  },

  approve(id: string, data: ApprovalData): Promise<void> {
    return request.post(`/assets/pickups/${id}/approve/`, data)
  },

  complete(id: string): Promise<void> {
    return request.post(`/assets/pickups/${id}/complete/`)
  },

  cancel(id: string): Promise<void> {
    return request.post(`/assets/pickups/${id}/cancel/`)
  }
}

export const transferApi = {
  list(params?: any): Promise<PaginatedResponse<Transfer>> {
    return request.get('/assets/transfers/', { params })
  },

  get(id: string): Promise<Transfer> {
    return request.get(`/assets/transfers/${id}/`)
  },

  create(data: CreateTransferData): Promise<Transfer> {
    return request.post('/assets/transfers/', data)
  },

  submit(id: string): Promise<void> {
    return request.post(`/assets/transfers/${id}/submit/`)
  },

  approveFrom(id: string, data: ApprovalData): Promise<void> {
    return request.post(`/assets/transfers/${id}/approve_from/`, data)
  },

  approveTo(id: string, data: ApprovalData): Promise<void> {
    return request.post(`/assets/transfers/${id}/approve_to/`, data)
  },

  complete(id: string): Promise<void> {
    return request.post(`/assets/transfers/${id}/complete/`)
  }
}

export const loanApi = {
  list(params?: any): Promise<PaginatedResponse<Loan>> {
    return request.get('/assets/loans/', { params })
  },

  get(id: string): Promise<Loan> {
    return request.get(`/assets/loans/${id}/`)
  },

  create(data: CreateLoanData): Promise<Loan> {
    return request.post('/assets/loans/', data)
  },

  submit(id: string): Promise<void> {
    return request.post(`/assets/loans/${id}/submit/`)
  },

  approve(id: string, data: ApprovalData): Promise<void> {
    return request.post(`/assets/loans/${id}/approve/`, data)
  },

  returnAsset(id: string, returnData: any): Promise<void> {
    return request.post(`/assets/loans/${id}/return/`, returnData)
  }
}
```

---

## Component: Asset Selector

```vue
<!-- frontend/src/components/assets/AssetSelector.vue -->
<template>
  <el-dialog v-model="visible" title="选择资产" width="800px">
    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="assets"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="code" label="资产编码" width="150" />
      <el-table-column prop="name" label="资产名称" />
      <el-table-column prop="category.name" label="分类" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusLabel(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" @click="handleConfirm">
        确定 ({{ selectedAssets.length }})
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { assetApi, AssetStatus } from '@/api/assets'
import type { Asset } from '@/types/models/asset'

interface Props {
  modelValue: boolean
  status?: AssetStatus
  multiple?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', assets: Asset[]): void
}

const props = withDefaults(defineProps<Props>(), {
  multiple: true
})

const emit = defineEmits<Emits>()

const visible = ref(false)
const loading = ref(false)
const assets = ref<Asset[]>([])
const selectedAssets = ref<Asset[]>([])

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    loadAssets()
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const loadAssets = async () => {
  loading.value = true
  try {
    const response = await assetApi.list({
      status: props.status || AssetStatus.IDLE,
      pageSize: 100
    })
    assets.value = response.results
  } catch (error) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

const handleSelectionChange = (selection: Asset[]) => {
  selectedAssets.value = selection
}

const handleConfirm = () => {
  emit('confirm', selectedAssets.value)
  visible.value = false
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
| `frontend/src/types/operations.ts` | Operations type definitions |
| `frontend/src/api/operations.ts` | Operations API service |
| `frontend/src/views/operations/PickupForm.vue` | Pickup form page |
| `frontend/src/views/operations/TransferForm.vue` | Transfer form page |
| `frontend/src/views/operations/LoanForm.vue` | Loan form page |
| `frontend/src/components/assets/AssetSelector.vue` | Asset selector component |
