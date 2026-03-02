# Phase 3.2: Workflow Engine - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement workflow engine integration including workflow designer, task management, and approval handling.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/workflow.ts

export interface WorkflowDefinition {
  id: string
  name: string
  code: string
  description?: string
  businessObject: string
  version: number
  isActive: boolean
  graphData: LogicFlowGraphData
  organizationId: string
  createdAt: string
  createdBy: string
}

export interface LogicFlowGraphData {
  nodes: FlowNode[]
  edges: FlowEdge[]
}

export interface FlowNode {
  id: string
  type: string
  x: number
  y: number
  text?: string
  properties?: Record<string, any>
}

export interface FlowEdge {
  id: string
  sourceNodeId: string
  targetNodeId: string
  type?: string
  properties?: Record<string, any>
}

export interface WorkflowInstance {
  id: string
  definitionId: string
  definitionName: string
  businessKey: string
  businessData: Record<string, any>
  status: 'running' | 'completed' | 'cancelled' | 'terminated'
  currentNodes: string[]
  startedAt: string
  completedAt?: string
  startedBy: string
}

export interface WorkflowTask {
  id: string
  instanceId: string
  instance: WorkflowInstance
  taskId: string
  taskName: string
  taskKey: string
  assigneeId: string
  assignee?: User
  status: 'pending' | 'approved' | 'rejected' | 'returned'
  createdAt: string
  dueDate?: string
  formData?: Record<string, any>
  fieldPermissions?: Record<string, FieldPermissionEntry>
}

export interface ApprovalAction {
  action: 'approve' | 'reject' | 'return'
  comment?: string
  formData?: Record<string, any>
}

export interface WorkflowStatistics {
  totalInstances: number
  runningInstances: number
  completedInstances: number
  pendingTasks: number
  avgCompletionTime: number
}
```

### API Service

```typescript
// frontend/src/api/workflows.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type {
  WorkflowDefinition,
  WorkflowInstance,
  WorkflowTask,
  ApprovalAction,
  WorkflowStatistics
} from '@/types/workflow'

export const workflowApi = {
  // Workflow Definitions
  getDefinitions(params?: any): Promise<PaginatedResponse<WorkflowDefinition>> {
    return request.get('/workflows/definitions/', { params })
  },

  getDefinition(id: string): Promise<WorkflowDefinition> {
    return request.get(`/workflows/definitions/${id}/`)
  },

  createDefinition(data: Partial<WorkflowDefinition>): Promise<WorkflowDefinition> {
    return request.post('/workflows/definitions/', data)
  },

  updateDefinition(id: string, data: Partial<WorkflowDefinition>): Promise<WorkflowDefinition> {
    return request.put(`/workflows/definitions/${id}/`, data)
  },

  activateDefinition(id: string): Promise<void> {
    return request.post(`/workflows/definitions/${id}/activate/`)
  },

  deactivateDefinition(id: string): Promise<void> {
    return request.post(`/workflows/definitions/${id}/deactivate/`)
  },

  // Workflow Instances
  getInstances(params?: any): Promise<PaginatedResponse<WorkflowInstance>> {
    return request.get('/workflows/instances/', { params })
  },

  getInstance(id: string): Promise<WorkflowInstance> {
    return request.get(`/workflows/instances/${id}/`)
  },

  startWorkflow(definitionCode: string, businessData: any): Promise<WorkflowInstance> {
    return request.post('/workflows/execution/start/', {
      definitionCode,
      businessData
    })
  },

  cancelInstance(id: string, reason?: string): Promise<void> {
    return request.post(`/workflows/instances/${id}/cancel/`, { reason })
  },

  // Tasks
  getMyTasks(params?: any): Promise<PaginatedResponse<WorkflowTask>> {
    return request.get('/workflows/execution/my_tasks/', { params })
  },

  getTaskDetail(taskId: string): Promise<WorkflowTask> {
    return request.get(`/workflows/execution/tasks/${taskId}/detail/`)
  },

  approveTask(taskId: string, data: ApprovalAction): Promise<void> {
    return request.post(`/workflows/execution/${taskId}/approve/`, data)
  },

  batchApproveTasks(data: {
    taskIds: string[]
    action: 'approve' | 'reject'
    comment?: string
  }): Promise<BatchResponse> {
    return request.post('/workflows/execution/batch-approve/', data)
  },

  // Statistics
  getStatistics(): Promise<WorkflowStatistics> {
    return request.get('/workflows/execution/statistics/')
  }
}
```

---

## Component: Workflow Task List

```vue
<!-- frontend/src/views/workflow/MyTasks.vue -->
<template>
  <div class="my-tasks-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>我的待办</span>
          <el-button type="primary" @click="handleRefresh">刷新</el-button>
        </div>
      </template>

      <!-- Statistics -->
      <el-row :gutter="16" class="stats-row">
        <el-col :span="6">
          <el-statistic :value="stats.pendingTasks" title="待处理任务" />
        </el-col>
        <el-col :span="6">
          <el-statistic :value="stats.runningInstances" title="进行中流程" />
        </el-col>
        <el-col :span="6">
          <el-statistic :value="stats.completedInstances" title="已完成流程" />
        </el-col>
        <el-col :span="6">
          <el-statistic :value="stats.avgCompletionTime" title="平均处理时长(h)" />
        </el-col>
      </el-row>
    </el-card>

    <!-- Task List -->
    <el-card class="tasks-card">
      <BaseListPage
        title="待办任务"
        :fetch-method="workflowApi.getMyTasks"
        :columns="columns"
        :custom-slots="['actions']"
        @row-click="handleRowClick"
      >
        <template #actions="{ row }">
          <el-button type="primary" size="small" @click.stop="handleApprove(row)">
            审批
          </el-button>
          <el-button size="small" @click.stop="handleDetail(row)">
            详情
          </el-button>
        </template>
      </BaseListPage>
    </el-card>

    <!-- Approval Dialog -->
    <ApprovalDialog
      v-model="approvalVisible"
      :task="selectedTask"
      @approved="handleApproved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { workflowApi } from '@/api/workflows'
import ApprovalDialog from './components/ApprovalDialog.vue'
import type { WorkflowTask, WorkflowStatistics } from '@/types/workflow'

const stats = ref<WorkflowStatistics>({
  totalInstances: 0,
  runningInstances: 0,
  completedInstances: 0,
  pendingTasks: 0,
  avgCompletionTime: 0
})

const selectedTask = ref<WorkflowTask>()
const approvalVisible = ref(false)

const columns = [
  { prop: 'taskName', label: '任务名称', width: 200 },
  { prop: 'definitionName', label: '流程类型', width: 150 },
  { prop: 'assignee.realName', label: '处理人', width: 120 },
  { prop: 'createdAt', label: '创建时间', width: 180, type: 'datetime' },
  { prop: 'dueDate', label: '截止时间', width: 180, type: 'datetime' },
  { prop: 'actions', label: '操作', width: 180, slot: true }
]

const loadStatistics = async () => {
  try {
    stats.value = await workflowApi.getStatistics()
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleRefresh = () => {
  loadStatistics()
}

const handleRowClick = (row: WorkflowTask) => {
  handleDetail(row)
}

const handleApprove = (row: WorkflowTask) => {
  selectedTask.value = row
  approvalVisible.value = true
}

const handleDetail = (row: WorkflowTask) => {
  // Navigate to detail page
}

const handleApproved = () => {
  approvalVisible.value = false
  loadStatistics()
}

onMounted(() => {
  loadStatistics()
})
</script>

<style scoped>
.my-tasks-page {
  padding: 20px;
}

.my-tasks-page .el-card {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 16px;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/workflow.ts` | Workflow type definitions |
| `frontend/src/api/workflows.ts` | Workflow API service |
| `frontend/src/views/workflow/MyTasks.vue` | My tasks page |
| `frontend/src/views/workflow/WorkflowDesigner.vue` | Workflow designer page |
| `frontend/src/components/workflow/ApprovalDialog.vue` | Approval dialog component |
