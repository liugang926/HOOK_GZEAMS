# Phase 4.4: Inventory Assignment - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement inventory task assignment functionality including personnel assignment and task management.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/inventory.ts (additional)

export interface InventoryTaskAssignment {
  id: string
  taskId: string
  task?: InventoryTask
  assigneeId: string
  assignee?: User
  assignedBy: string
  assignedAt: string
  status: 'pending' | 'in_progress' | 'completed'
  completedAt?: string
  scanCount: number
  assetCount: number
}

export interface TaskAssignment {
  taskId: string
  assigneeIds: string[]
  region?: string
  locationIds?: string[]
}

export interface AssignmentProgress {
  assignmentId: string
  assigneeId: string
  assigneeName: string
  totalAssets: number
  scannedCount: number
  normalCount: number
  abnormalCount: number
  progress: number
}

export interface ReassignmentRequest {
  fromAssigneeId: string
  toAssigneeId: string
  taskIds: string[]
  reason?: string
}
```

### API Service

```typescript
// frontend/src/api/inventory.ts (additional methods)

export const inventoryApi = {
  // Assignments
  getAssignments(taskId: string): Promise<InventoryTaskAssignment[]> {
    return request.get(`/inventory/tasks/${taskId}/assignments/`)
  },

  createAssignment(data: TaskAssignment): Promise<void> {
    return request.post(`/inventory/tasks/${taskId}/assignments/`, data)
  },

  removeAssignment(taskId: string, assigneeId: string): Promise<void> {
    return request.delete(`/inventory/tasks/${taskId}/assignments/${assigneeId}/`)
  },

  reassign(data: ReassignmentRequest): Promise<void> {
    return request.post('/inventory/assignments/reassign/', data)
  },

  getAssignmentProgress(taskId: string): Promise<AssignmentProgress[]> {
    return request.get(`/inventory/tasks/${taskId}/progress/`)
  }
}
```

---

## Component: Assignment Panel

```vue
<!-- frontend/src/views/inventory/AssignmentPanel.vue -->
<template>
  <div class="assignment-panel">
    <el-card>
      <template #header>
        <span>盘点人员分配</span>
      </template>

      <!-- Assignment Form -->
      <el-form :model="assignmentForm" label-width="120px">
        <el-form-item label="分配人员">
          <UserSelector
            v-model="assignmentForm.assigneeIds"
            :multiple="true"
            placeholder="选择盘点人员"
          />
        </el-form-item>

        <el-form-item label="盘点区域">
          <el-input v-model="assignmentForm.region" placeholder="留空表示全部区域" />
        </el-form-item>

        <el-form-item label="指定位置">
          <LocationSelector
            v-model="assignmentForm.locationIds"
            :multiple="true"
            placeholder="选择盘点位置"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleAssign">
            分配任务
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- Assignment Progress -->
    <el-card class="progress-card">
      <template #header>
        <span>盘点进度</span>
        <el-button link @click="handleRefreshProgress">刷新</el-button>
      </template>

      <el-table :data="progressData" v-loading="loadingProgress">
        <el-table-column prop="assigneeName" label="人员" width="150" />

        <el-table-column prop="totalAssets" label="分配数量" width="120" />

        <el-table-column prop="scannedCount" label="已扫描" width="120" />

        <el-table-column prop="progress" label="进度" width="200">
          <template #default="{ row }">
            <el-progress :percentage="row.progress" :color="getProgressColor(row.progress)" />
          </template>
        </el-table-column>

        <el-table-column prop="abnormalCount" label="异常" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.abnormalCount > 0" type="danger">
              {{ row.abnormalCount }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { inventoryApi } from '@/api/inventory'
import UserSelector from '@/components/organization/UserSelector.vue'
import LocationSelector from '@/components/assets/LocationSelector.vue'
import type { AssignmentProgress, TaskAssignment } from '@/types/inventory'

interface Props {
  taskId: string
}

const props = defineProps<Props>()

const assignmentForm = ref<TaskAssignment>({
  taskId: props.taskId,
  assigneeIds: [],
  locationIds: []
})

const progressData = ref<AssignmentProgress[]>([])
const loadingProgress = ref(false)

const handleAssign = async () => {
  if (assignmentForm.value.assigneeIds.length === 0) {
    ElMessage.warning('请选择盘点人员')
    return
  }

  try {
    await inventoryApi.createAssignment(assignmentForm.value)
    ElMessage.success('分配成功')
    await loadProgress()
  } catch (error) {
    // Error handled by interceptor
  }
}

const loadProgress = async () => {
  loadingProgress.value = true
  try {
    progressData.value = await inventoryApi.getAssignmentProgress(props.taskId)
  } catch (error) {
    // Error handled by interceptor
  } finally {
    loadingProgress.value = false
  }
}

const handleRefreshProgress = () => {
  loadProgress()
}

const getProgressColor = (progress: number) => {
  if (progress >= 100) return '#67c23a'
  if (progress >= 80) return '#409eff'
  if (progress >= 50) return '#e6a23c'
  return '#f56c6c'
}

onMounted(() => {
  loadProgress()
})
</script>

<style scoped>
.assignment-panel {
  padding: 20px;
}

.assignment-panel .el-card {
  margin-bottom: 20px;
}

.progress-card {
  margin-top: 20px;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/inventory.ts` | Extended inventory types |
| `frontend/src/api/inventory.ts` | Extended inventory API |
| `frontend/src/views/inventory/AssignmentPanel.vue` | Assignment panel |
| `frontend/src/views/inventory/ProgressList.vue` | Progress list page |
