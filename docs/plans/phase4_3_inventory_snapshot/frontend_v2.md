# Phase 4.3: Inventory Snapshot - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement inventory snapshot functionality including snapshot generation, difference management, and reconciliation.

**Key Fix from v1**: All field names now use camelCase consistently.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/inventory.ts

export interface InventorySnapshot {
  id: string
  taskId: string
  task?: InventoryTask
  snapshotAt: string
  totalAssets: number
  snapshotData: SnapshotAsset[]
  organizationId: string
  createdAt: string
  createdBy: string
}

export interface SnapshotAsset {
  assetId: string
  assetCode: string
  assetName: string
  categoryId: string
  categoryName: string
  locationId: string
  locationName: string
  custodianId: string
  custodianName: string
  status: string
  qrCode: string
}

export interface InventoryDifference {
  id: string
  taskId: string
  assetId: string
  asset?: SnapshotAsset
  differenceType: 'normal' | 'missing' | 'extra' | 'damaged' | 'location_mismatch'
  expectedData?: SnapshotAsset
  actualData?: SnapshotAsset
  status: 'pending' | 'confirmed' | 'resolved'
  remark?: string
  resolvedAt?: string
  createdAt: string
}

export interface DifferenceResolution {
  differenceIds: string[]
  action: 'confirm' | 'adjust'
  remark?: string
}

export interface InventoryTask {
  id: string
  taskNo: string
  name: string
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  startDate?: string
  completedAt?: string
  totalAssets: number
  scannedCount: number
  normalCount: number
  missingCount: number
  extraCount: number
  damagedCount: number
  organizationId: string
}
```

### API Service

```typescript
// frontend/src/api/inventory.ts

import request from '@/utils/request'
import type { PaginatedResponse, BatchResponse } from '@/types/api'
import type {
  InventorySnapshot,
  InventoryDifference,
  DifferenceResolution,
  InventoryTask
} from '@/types/inventory'

export const inventoryApi = {
  // Snapshots
  createSnapshot(taskId: string): Promise<InventorySnapshot> {
    return request.post('/inventory/snapshots/', { taskId })
  },

  getSnapshot(id: string): Promise<InventorySnapshot> {
    return request.get(`/inventory/snapshots/${id}/`)
  },

  getSnapshotByTask(taskId: string): Promise<InventorySnapshot> {
    return request.get('/inventory/snapshots/', { params: { taskId } })
  },

  // Differences
  getDifferences(params?: any): Promise<PaginatedResponse<InventoryDifference>> {
    return request.get('/inventory/differences/', { params })
  },

  resolveDifferences(data: DifferenceResolution): Promise<BatchResponse> {
    return request.post('/inventory/differences/resolve/', data)
  },

  confirmDifference(id: string, remark?: string): Promise<void> {
    return request.post(`/inventory/differences/${id}/confirm/`, { remark })
  },

  adjustAsset(differenceId: string, adjustData: any): Promise<void> {
    return request.post(`/inventory/differences/${differenceId}/adjust/`, adjustData)
  },

  // Tasks
  getTasks(params?: any): Promise<PaginatedResponse<InventoryTask>> {
    return request.get('/inventory/tasks/', { params })
  },

  getTask(id: string): Promise<InventoryTask> {
    return request.get(`/inventory/tasks/${id}/`)
  }
}
```

---

## Component: Difference List

```vue
<!-- frontend/src/views/inventory/DifferenceList.vue -->
<template>
  <div class="difference-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>盘点差异</span>
          <div class="header-actions">
            <el-select v-model="filterStatus" placeholder="状态" clearable @change="loadDifferences">
              <el-option label="全部" value="" />
              <el-option label="待处理" value="pending" />
              <el-option label="已确认" value="confirmed" />
              <el-option label="已解决" value="resolved" />
            </el-select>
            <el-select v-model="filterType" placeholder="差异类型" clearable @change="loadDifferences">
              <el-option label="全部" value="" />
              <el-option label="正常" value="normal" />
              <el-option label="盘亏" value="missing" />
              <el-option label="盘盈" value="extra" />
              <el-option label="损坏" value="damaged" />
              <el-option label="位置不符" value="location_mismatch" />
            </el-select>
            <el-button @click="handleBatchResolve">批量处理</el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="differences"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />

        <el-table-column prop="asset.assetCode" label="资产编码" width="150" />

        <el-table-column prop="asset.assetName" label="资产名称" width="200" />

        <el-table-column prop="differenceType" label="差异类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getDiffTagType(row.differenceType)">
              {{ getDiffLabel(row.differenceType) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="asset.locationName" label="系统位置" width="150" />

        <el-table-column prop="asset.custodianName" label="系统保管人" width="120" />

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="remark" label="备注" show-overflow-tooltip />

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.status === 'pending'"
              link
              type="primary"
              @click="handleConfirm(row)"
            >
              确认
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              link
              type="warning"
              @click="handleAdjust(row)"
            >
              调整
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        @current-change="loadDifferences"
        @size-change="loadDifferences"
      />
    </el-card>

    <!-- Batch Resolve Dialog -->
    <BatchResolveDialog
      v-model="batchDialogVisible"
      :differences="selectedDifferences"
      @resolved="handleResolved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { inventoryApi } from '@/api/inventory'
import BatchResolveDialog from './components/BatchResolveDialog.vue'
import type { InventoryDifference } from '@/types/inventory'

const loading = ref(false)
const differences = ref<InventoryDifference[]>([])
const selectedDifferences = ref<InventoryDifference[]>([])

const filterStatus = ref('')
const filterType = ref('')
const batchDialogVisible = ref(false)

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const loadDifferences = async () => {
  loading.value = true
  try {
    const response = await inventoryApi.getDifferences({
      page: pagination.page,
      pageSize: pagination.pageSize,
      status: filterStatus.value || undefined,
      differenceType: filterType.value || undefined
    })

    differences.value = response.results
    pagination.total = response.count
  } catch (error) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

const handleSelectionChange = (selection: InventoryDifference[]) => {
  selectedDifferences.value = selection
}

const handleConfirm = async (row: InventoryDifference) => {
  try {
    await inventoryApi.confirmDifference(row.id)
    ElMessage.success('已确认')
    loadDifferences()
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleAdjust = (row: InventoryDifference) => {
  // Open adjust dialog
}

const handleBatchResolve = () => {
  if (selectedDifferences.value.length === 0) {
    ElMessage.warning('请先选择要处理的差异')
    return
  }
  batchDialogVisible.value = true
}

const handleResolved = () => {
  batchDialogVisible.value = false
  selectedDifferences.value = []
  loadDifferences()
}

const getDiffTagType = (type: string) => {
  const typeMap: Record<string, string> = {
    normal: 'success',
    missing: 'danger',
    extra: 'warning',
    damaged: 'danger',
    location_mismatch: 'info'
  }
  return typeMap[type] || ''
}

const getDiffLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    normal: '正常',
    missing: '盘亏',
    extra: '盘盈',
    damaged: '损坏',
    location_mismatch: '位置不符'
  }
  return labelMap[type] || type
}

const getStatusTagType = (status: string) => {
  const typeMap: Record<string, string> = {
    pending: 'warning',
    confirmed: 'info',
    resolved: 'success'
  }
  return typeMap[status] || ''
}

const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    pending: '待处理',
    confirmed: '已确认',
    resolved: '已解决'
  }
  return labelMap[status] || status
}

onMounted(() => {
  loadDifferences()
})
</script>

<style scoped>
.difference-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/inventory.ts` | Inventory type definitions |
| `frontend/src/api/inventory.ts` | Inventory API service |
| `frontend/src/views/inventory/DifferenceList.vue` | Difference list page |
| `frontend/src/views/inventory/SnapshotDetail.vue` | Snapshot detail page |
| `frontend/src/components/inventory/BatchResolveDialog.vue` | Batch resolve dialog |
