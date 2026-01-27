<!--
  Inventory Task List View

  Uses BaseListPage component for standardized:
  - Search and filter functionality
  - Data table with pagination
  - Batch operations support
  - Mobile-responsive card view
-->

<template>
  <div class="inventory-task-list">
    <BaseListPage
      title="盘点任务"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchTasks"
      :selectable="true"
      :batch-actions="batchActions"
      @row-click="handleRowClick"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          新建任务
        </el-button>
      </template>

      <template #cell-status="{ row }">
        <el-tag :type="getStatusType(row.status)">
          {{ getStatusLabel(row.status) }}
        </el-tag>
      </template>

      <template #cell-startDate="{ row }">
        {{ formatDate(row.startDate) }}
      </template>

      <template #cell-endDate="{ row }">
        {{ formatDate(row.endDate) }}
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click="handleStart(row)"
        >
          开始盘点
        </el-button>
        <el-button
          link
          type="info"
          @click="handleView(row)"
        >
          详情
        </el-button>
        <el-button
          link
          type="danger"
          @click="handleDelete(row)"
        >
          删除
        </el-button>
      </template>
    </BaseListPage>
  </div>
</template>

<script setup lang="ts">
/**
 * TaskList View Component
 *
 * List view for inventory tasks using BaseListPage.
 * Provides search, filter, and CRUD operations.
 */

import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { inventoryApi } from '@/api/inventory'
import type { TableColumn, SearchField } from '@/types/common'
import { formatDate } from '@/utils/dateFormat'

const router = useRouter()

// ============================================================================
// State
// ============================================================================

// ============================================================================
// Table Columns
// ============================================================================

const columns: TableColumn[] = [
  { prop: 'taskNo', label: '任务编号', width: 160, fixed: 'left' },
  { prop: 'name', label: '任务名称', minWidth: 200 },
  { prop: 'startDate', label: '开始时间', width: 140, slot: true },
  { prop: 'endDate', label: '结束时间', width: 140, slot: true },
  { prop: 'status', label: '状态', width: 100, slot: true, fixed: 'right' }
]

// ============================================================================
// Search Fields
// ============================================================================

const searchFields: SearchField[] = [
  {
    field: 'search',
    label: '关键词',
    type: 'text',
    placeholder: '任务编号/名称'
  },
  {
    field: 'status',
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
    field: 'dateRange',
    label: '日期范围',
    type: 'dateRange'
  }
]

// ============================================================================
// Batch Actions
// ============================================================================

const batchActions = [
  {
    label: '批量删除',
    type: 'danger' as const,
    action: (rows: any[]) => handleBatchDelete(rows),
    confirm: true,
    confirmMessage: '确认删除选中的盘点任务？'
  },
  {
    label: '批量导出',
    type: 'primary' as const,
    action: (rows: any[]) => handleBatchExport(rows)
  }
]

// ============================================================================
// Methods
// ============================================================================

/**
 * Fetch tasks from API
 */
const fetchTasks = async (params: any) => {
  // Map date range if needed
  if (params.dateRange) {
    params.startDateFrom = params.dateRange[0]
    params.startDateTo = params.dateRange[1]
    delete params.dateRange
  }
  return await inventoryApi.listTasks(params)
}

/**
 * Get status tag type
 */
const getStatusType = (status: string) => {
  const typeMap: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'> = {
    pending: 'info',
    in_progress: 'primary',
    completed: 'success',
    cancelled: 'danger'
  }
  return typeMap[status] || 'info'
}

/**
 * Get status label
 */
const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    pending: '待开始',
    in_progress: '进行中',
    completed: '已完成',
    cancelled: '已取消'
  }
  return labelMap[status] || status
}

/**
 * Handle row click
 */
const handleRowClick = (row: any) => {
  handleView(row)
}

/**
 * Handle create button click
 */
const handleCreate = () => {
  router.push('/inventory/create')
}

/**
 * Handle view button click
 */
const handleView = (row: any) => {
  router.push(`/inventory/task/${row.id}`)
}

/**
 * Handle start inventory
 */
const handleStart = (row: any) => {
  router.push({ name: 'TaskExecute', params: { id: row.id } })
}

/**
 * Handle delete button click
 */
const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确认删除盘点任务"${row.name}"？此操作可恢复。`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消'
      }
    )
    await inventoryApi.deleteTask(row.id)
    ElMessage.success('删除成功')
    refreshList()
  } catch (error) {
    // User cancelled or error occurred
    if (error !== 'cancel') {
      console.error('Delete failed:', error)
    }
  }
}

/**
 * Handle batch delete
 */
const handleBatchDelete = async (selectedRows: any[]) => {
  try {
    const ids = selectedRows.map(r => r.id)
    await inventoryApi.batchDeleteTasks(ids)
    ElMessage.success(`成功删除 ${ids.length} 项盘点任务`)
    refreshList()
  } catch (error) {
    console.error('Batch delete failed:', error)
  }
}

/**
 * Handle batch export
 */
const handleBatchExport = async (selectedRows: any[]) => {
  try {
    const ids = selectedRows.map(r => r.id)
    // TODO: Implement export API
    ElMessage.info(`导出 ${ids.length} 项盘点任务 - 功能开发中`)
  } catch (error) {
    console.error('Batch export failed:', error)
  }
}

/**
 * Refresh list
 */
const refreshList = () => {
  window.dispatchEvent(new CustomEvent('refresh-base-list'))
}
</script>

<style scoped lang="scss">
.inventory-task-list {
  height: 100%;
}
</style>
