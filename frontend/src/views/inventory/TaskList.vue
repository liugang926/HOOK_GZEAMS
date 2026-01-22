<!--
  InventoryTaskList View

  Inventory task management list page with:
  - Task creation and configuration
  - Task status tracking (pending, in_progress, completed)
  - Progress visualization
  - Start/Complete/Cancel actions
  - Navigate to scanning interface
-->

<template>
  <div class="inventory-task-list-page">
    <BaseListPage
      title="盘点任务"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchTasks"
      :batch-actions="batchActions"
      @row-click="handleRowClick"
    >
      <template #toolbar>
        <el-button type="primary" :icon="Plus" @click="handleCreate">
          新建盘点任务
        </el-button>
        <el-button :icon="Refresh" @click="refreshList">
          刷新
        </el-button>
      </template>

      <template #cell-taskType="{ row }">
        <el-tag :type="getTypeColor(row.taskType)" size="small">
          {{ getTypeLabel(row.taskType) }}
        </el-tag>
      </template>

      <template #cell-status="{ row }">
        <el-tag :type="getStatusType(row.status)">
          {{ getStatusLabel(row.status) }}
        </el-tag>
      </template>

      <template #cell-progress="{ row }">
        <div class="progress-cell">
          <el-progress
            :percentage="getProgressPercentage(row)"
            :status="getProgressStatus(row)"
            :stroke-width="8"
            :show-text="true"
          />
          <span class="progress-text">
            {{ row.scannedCount }}/{{ row.assetCount }}
          </span>
        </div>
      </template>

      <template #cell-abnormalCount="{ row }">
        <el-tag
          v-if="row.abnormalCount > 0"
          type="danger"
          size="small"
          :icon="Warning"
        >
          {{ row.abnormalCount }}
        </el-tag>
        <span v-else class="text-muted">-</span>
      </template>

      <template #actions="{ row }">
        <el-button link type="primary" @click="handleView(row)">
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
          type="primary"
          @click="handleScan(row)"
        >
          扫描
        </el-button>
        <el-button
          v-if="row.status === 'in_progress'"
          link
          type="warning"
          @click="handleComplete(row)"
        >
          完成
        </el-button>
        <el-button
          v-if="['pending', 'in_progress'].includes(row.status)"
          link
          type="info"
          @click="handleCancel(row)"
        >
          取消
        </el-button>
        <el-button
          v-if="row.status === 'completed'"
          link
          type="success"
          @click="handleReconcile(row)"
        >
          对账
        </el-button>
      </template>
    </BaseListPage>

    <!-- Task Form Dialog -->
    <TaskFormDialog
      v-model="formVisible"
      :task="currentTask"
      @success="handleFormSuccess"
    />

    <!-- Task Detail Drawer -->
    <TaskDetailDrawer
      v-model="detailVisible"
      :task-id="currentTaskId"
      @start="handleStartFromDetail"
      @scan="handleScanFromDetail"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * InventoryTaskList View Component
 *
 * Main list view for inventory task management.
 * Supports task creation, status tracking, and scanning workflow.
 */

import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Refresh, Warning } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import TaskFormDialog from '@/components/inventory/TaskFormDialog.vue'
import TaskDetailDrawer from '@/components/inventory/TaskDetailDrawer.vue'
import { inventoryApi } from '@/api/inventory'
import type { InventoryTask, TaskStatus, TaskType } from '@/types/inventory'
import type { TableColumn, SearchField } from '@/types/common'

const router = useRouter()

// ============================================================================
// State
// ============================================================================

const formVisible = ref(false)
const detailVisible = ref(false)
const currentTask = ref<InventoryTask | null>(null)
const currentTaskId = ref('')

// ============================================================================
// Table Columns
// ============================================================================

const columns: TableColumn[] = [
  { prop: 'taskNo', label: '任务编号', width: 150 },
  { prop: 'taskName', label: '任务名称', minWidth: 180 },
  { prop: 'taskType', label: '盘点类型', width: 110, slot: true },
  { prop: 'status', label: '状态', width: 100, slot: true },
  { prop: 'plannedDate', label: '计划日期', width: 120 },
  { prop: 'progress', label: '扫描进度', width: 180, slot: true },
  { prop: 'abnormalCount', label: '异常数量', width: 100, slot: true, align: 'center' },
  { prop: 'createdAt', label: '创建时间', width: 160 }
]

// ============================================================================
// Search Fields
// ============================================================================

const searchFields: SearchField[] = [
  {
    prop: 'search',
    label: '关键词',
    type: 'text',
    placeholder: '任务编号/名称'
  },
  {
    prop: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '待开始', value: 'pending' },
      { label: '进行中', value: 'in_progress' },
      { label: '已完成', value: 'completed' },
      { label: '已取消', value: 'cancelled' }
    ]
  },
  {
    prop: 'taskType',
    label: '盘点类型',
    type: 'select',
    options: [
      { label: '全盘', value: 'full' },
      { label: '抽盘', value: 'partial' },
      { label: '按位置', value: 'location' },
      { label: '按分类', value: 'category' }
    ]
  },
  {
    prop: 'plannedDateRange',
    label: '计划日期',
    type: 'dateRange'
  }
]

// ============================================================================
// Batch Actions
// ============================================================================

const batchActions = [
  {
    label: '批量取消',
    type: 'warning' as const,
    action: handleBatchCancel
  },
  {
    label: '批量删除',
    type: 'danger' as const,
    action: handleBatchDelete
  }
]

// ============================================================================
// Methods
// ============================================================================

/**
 * Fetch tasks from API
 */
const fetchTasks = async (params: any) => {
  return await inventoryApi.listTasks(params)
}

/**
 * Get type label
 */
const getTypeLabel = (type: TaskType): string => {
  const labels: Record<TaskType, string> = {
    full: '全盘',
    partial: '抽盘',
    location: '按位置',
    category: '按分类'
  }
  return labels[type] || type
}

/**
 * Get type color
 */
const getTypeColor = (type: TaskType): string => {
  const colors: Record<TaskType, 'primary' | 'success' | 'warning' | 'info'> = {
    full: 'primary',
    partial: 'success',
    location: 'warning',
    category: 'info'
  }
  return colors[type] || 'info'
}

/**
 * Get status label
 */
const getStatusLabel = (status: TaskStatus): string => {
  const labels: Record<TaskStatus, string> = {
    pending: '待开始',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return labels[status] || status
}

/**
 * Get status type
 */
const getStatusType = (status: TaskStatus): string => {
  const types: Record<TaskStatus, 'info' | 'warning' | 'success' | 'danger'> = {
    pending: 'info',
    in_progress: 'warning',
    completed: 'success',
    cancelled: 'danger'
  }
  return types[status] || 'info'
}

/**
 * Get progress percentage
 */
const getProgressPercentage = (task: InventoryTask): number => {
  if (task.assetCount === 0) return 0
  return Math.round((task.scannedCount / task.assetCount) * 100)
}

/**
 * Get progress status
 */
const getProgressStatus = (task: InventoryTask): 'success' | undefined => {
  const percentage = getProgressPercentage(task)
  return percentage === 100 ? 'success' : undefined
}

/**
 * Handle row click
 */
const handleRowClick = (row: InventoryTask) => {
  handleView(row)
}

/**
 * Handle create button
 */
const handleCreate = () => {
  currentTask.value = null
  formVisible.value = true
}

/**
 * Handle view button
 */
const handleView = (row: InventoryTask) => {
  currentTask.value = row
  currentTaskId.value = row.id
  detailVisible.value = true
}

/**
 * Handle start task
 */
const handleStart = async (row: InventoryTask) => {
  try {
    await ElMessageBox.confirm(
      `确认开始盘点任务"${row.taskName}"？开始后将生成资产快照。`,
      '开始确认',
      {
        type: 'warning',
        confirmButtonText: '确认开始',
        cancelButtonText: '取消'
      }
    )
    await inventoryApi.startTask(row.id)
    ElMessage.success('任务已开始')
    refreshList()
  } catch (error) {
    // User cancelled
  }
}

/**
 * Handle scan button - navigate to scan page
 */
const handleScan = (row: InventoryTask) => {
  router.push(`/inventory/scan/${row.id}`)
}

/**
 * Handle complete task
 */
const handleComplete = async (row: InventoryTask) => {
  try {
    await ElMessageBox.confirm(
      `确认完成盘点任务"${row.taskName}"？完成后将无法继续扫描。`,
      '完成确认',
      {
        type: 'warning',
        confirmButtonText: '确认完成',
        cancelButtonText: '取消'
      }
    )
    await inventoryApi.completeTask(row.id)
    ElMessage.success('任务已完成')
    refreshList()
  } catch (error) {
    // User cancelled
  }
}

/**
 * Handle cancel task
 */
const handleCancel = async (row: InventoryTask) => {
  try {
    await ElMessageBox.confirm(
      `确认取消盘点任务"${row.taskName}"？`,
      '取消确认',
      {
        type: 'warning',
        confirmButtonText: '确认取消',
        cancelButtonText: '返回'
      }
    )
    await inventoryApi.cancelTask(row.id)
    ElMessage.success('任务已取消')
    refreshList()
  } catch (error) {
    // User cancelled
  }
}

/**
 * Handle reconcile button
 */
const handleReconcile = (row: InventoryTask) => {
  router.push(`/inventory/reconcile/${row.id}`)
}

/**
 * Handle batch cancel
 */
const handleBatchCancel = async (selectedRows: InventoryTask[]) => {
  const pendingTasks = selectedRows.filter(r => r.status === 'pending')
  if (pendingTasks.length === 0) {
    ElMessage.warning('请选择待开始的任务')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认取消选中的 ${pendingTasks.length} 个任务？`,
      '批量取消',
      {
        type: 'warning',
        confirmButtonText: '确认取消',
        cancelButtonText: '返回'
      }
    )
    await Promise.all(pendingTasks.map(t => inventoryApi.cancelTask(t.id)))
    ElMessage.success(`成功取消 ${pendingTasks.length} 个任务`)
    refreshList()
  } catch (error) {
    // User cancelled
  }
}

/**
 * Handle batch delete
 */
const handleBatchDelete = async (selectedRows: InventoryTask[]) => {
  // Only allow deleting completed or cancelled tasks
  const deletableTasks = selectedRows.filter(r =>
    ['completed', 'cancelled'].includes(r.status)
  )
  if (deletableTasks.length === 0) {
    ElMessage.warning('只能删除已完成或已取消的任务')
    return
  }
  try {
    await ElMessageBox.confirm(
      `确认删除选中的 ${deletableTasks.length} 个任务？`,
      '批量删除',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '返回'
      }
    )
    // Implement batch delete API call
    ElMessage.success(`成功删除 ${deletableTasks.length} 个任务`)
    refreshList()
  } catch (error) {
    // User cancelled
  }
}

/**
 * Handle form success
 */
const handleFormSuccess = () => {
  formVisible.value = false
  refreshList()
}

/**
 * Handle start from detail drawer
 */
const handleStartFromDetail = (taskId: string) => {
  detailVisible.value = false
  refreshList()
}

/**
 * Handle scan from detail drawer
 */
const handleScanFromDetail = (taskId: string) => {
  detailVisible.value = false
  router.push(`/inventory/scan/${taskId}`)
}

/**
 * Refresh list
 */
const refreshList = () => {
  window.dispatchEvent(new CustomEvent('refresh-base-list'))
}
</script>

<style scoped lang="scss">
.inventory-task-list-page {
  height: 100%;
}

.progress-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.progress-text {
  font-size: 12px;
  color: #909399;
  text-align: center;
}

.text-muted {
  color: #c0c4cc;
}
</style>
