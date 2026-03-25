# Phase 2.4: Organization Enhancement - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement enhanced organization management features including department tree management and cross-organization asset transfer.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/organization.ts

export interface Department {
  id: string
  name: string
  code: string
  parentId: string | null
  parentPath: string[]
  level: number
  hasChildren: boolean
  children?: Department[]
  managerId?: string
  manager?: User
  organizationId: string
  isActive: boolean
  sortOrder: number
}

export interface DepartmentCreate {
  name: string
  code: string
  parentId?: string | null
  managerId?: string
  sortOrder?: number
}

export interface DepartmentUpdate extends Partial<DepartmentCreate> {}

export interface OrganizationTransfer {
  fromDepartmentId: string
  toDepartmentId: string
  assetIds: string[]
  reason?: string
}

export interface TransferApproval {
  transferId: string
  action: 'approve' | 'reject'
  comment?: string
}

export interface TransferRequest {
  id: string
  transferNo: string
  fromDepartment: Department
  toDepartment: Department
  assetCount: number
  reason: string
  status: 'pending' | 'approved' | 'rejected' | 'completed'
  createdAt: string
}
```

### API Service

```typescript
// frontend/src/api/organizations.ts

import request from '@/utils/request'
import type { PaginatedResponse, BatchResponse } from '@/types/api'
import type {
  Department,
  DepartmentCreate,
  DepartmentUpdate,
  OrganizationTransfer,
  TransferRequest
} from '@/types/organization'

export const organizationApi = {
  // Department Tree
  getDepartmentTree(params?: any): Promise<Department[]> {
    return request.get('/organizations/departments/tree/', { params })
  },

  // Department CRUD
  getDepartments(params?: any): Promise<PaginatedResponse<Department>> {
    return request.get('/organizations/departments/', { params })
  },

  getDepartment(id: string): Promise<Department> {
    return request.get(`/organizations/departments/${id}/`)
  },

  createDepartment(data: DepartmentCreate): Promise<Department> {
    return request.post('/organizations/departments/', data)
  },

  updateDepartment(id: string, data: DepartmentUpdate): Promise<Department> {
    return request.put(`/organizations/departments/${id}/`, data)
  },

  deleteDepartment(id: string): Promise<void> {
    return request.delete(`/organizations/departments/${id}/`)
  },

  // Cross-Organization Transfer
  initiateTransfer(data: OrganizationTransfer): Promise<void> {
    return request.post('/assets/transfers/', data)
  },

  getTransferRequests(params?: any): Promise<PaginatedResponse<TransferRequest>> {
    return request.get('/organizations/transfers/', { params })
  },

  approveTransfer(transferId: string, data: TransferApproval): Promise<void> {
    return request.post(`/organizations/transfers/${transferId}/approve/`, data)
  }
}
```

---

## Component: Department Selector

```vue
<!-- frontend/src/components/organization/DepartmentSelector.vue -->
<template>
  <el-tree-select
    v-model="selectedValue"
    :data="departments"
    :props="treeProps"
    :render-after-expand="false"
    check-strictly
    clearable
    filterable
    :filter-node-method="filterNode"
    :placeholder="placeholder"
    node-key="id"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { organizationApi } from '@/api/organizations'
import type { Department } from '@/types/organization'

interface Props {
  modelValue: string | null
  placeholder?: string
  excludeId?: string
}

interface Emits {
  (e: 'update:modelValue', value: string | null): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const departments = ref<Department[]>([])
const selectedValue = ref<string | null>(props.modelValue)

const treeProps = {
  label: 'name',
  value: 'id',
  children: 'children'
}

const filterNode = (value: string, data: Department) => {
  if (!value) return true
  return data.name.toLowerCase().includes(value.toLowerCase()) ||
         data.code.toLowerCase().includes(value.toLowerCase())
}

const loadDepartments = async () => {
  try {
    let tree = await organizationApi.getDepartmentTree()

    if (props.excludeId) {
      tree = excludeNode(tree, props.excludeId)
    }

    departments.value = tree
  } catch (error) {
    // Error handled by interceptor
  }
}

const excludeNode = (nodes: Department[], excludeId: string): Department[] => {
  return nodes
    .filter(node => node.id !== excludeId)
    .map(node => ({
      ...node,
      children: node.children ? excludeNode(node.children, excludeId) : undefined
    }))
}

watch(() => props.modelValue, (val) => {
  selectedValue.value = val
})

watch(selectedValue, (val) => {
  emit('update:modelValue', val)
})

onMounted(() => {
  loadDepartments()
})
</script>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/organization.ts` | Organization type definitions |
| `frontend/src/api/organizations.ts` | Organization API service |
| `frontend/src/components/organization/DepartmentSelector.vue` | Department selector |
| `frontend/src/components/organization/DepartmentTree.vue` | Department tree component |
| `frontend/src/views/organization/DepartmentManagement.vue` | Department management page |
