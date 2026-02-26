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
      :title="t('inventory.taskList')"
      object-code="InventoryTask"
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
          {{ t('inventory.createTask') }}
        </el-button>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click.stop="handleStart(row)"
        >
          {{ t('inventory.actions.start') }}
        </el-button>
        <el-button
          link
          type="info"
          @click.stop="handleView(row)"
        >
          {{ t('common.actions.detail') }}
        </el-button>
        <el-button
          link
          type="danger"
          @click.stop="handleDelete(row)"
        >
          {{ t('common.actions.delete') }}
        </el-button>
      </template>
    </BaseListPage>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { inventoryApi } from '@/api/inventory'
import type { TableColumn, SearchField } from '@/types/common'
import { formatDate } from '@/utils/dateFormat'

const router = useRouter()
const { t } = useI18n()

const columns = computed<TableColumn[]>(() => [
  { prop: 'taskNo', label: t('inventory.columns.taskNo'), width: 160, fixed: 'left' },
  { prop: 'name', label: t('inventory.columns.name'), minWidth: 200 },
  { prop: 'startDate', label: t('common.placeholders.startDate'), width: 140, format: (value: any) => formatDate(value) },
  { prop: 'endDate', label: t('common.placeholders.endDate'), width: 140, format: (value: any) => formatDate(value) },
  { prop: 'status', label: t('inventory.columns.status'), width: 100, tagType: (row: any) => getStatusType(row.status), format: (value: any, row: any) => row?.statusLabel || getStatusLabel(value), fixed: 'right' }
])

const searchFields = computed<SearchField[]>(() => [
  {
    field: 'search',
    label: t('common.actions.search'),
    type: 'text',
    placeholder: `${t('inventory.columns.taskNo')}/${t('inventory.columns.name')}`
  },
  {
    field: 'status',
    label: t('inventory.columns.status'),
    type: 'select',
    options: [
      { label: t('inventory.status.pending'), value: 'pending' },
      { label: t('inventory.status.in_progress'), value: 'in_progress' },
      { label: t('inventory.status.completed'), value: 'completed' },
      { label: t('inventory.status.canceled'), value: 'cancelled' }
    ]
  },
  {
    field: 'dateRange',
    label: t('common.placeholders.startDate'),
    type: 'dateRange'
  }
])

const batchActions = computed(() => [
  {
    label: t('common.actions.delete'),
    type: 'danger' as const,
    action: (rows: any[]) => handleBatchDelete(rows),
    confirm: true,
    confirmMessage: t('common.messages.confirmDelete', { count: '{count}' })
  },
  {
    label: t('common.actions.export'),
    type: 'primary' as const,
    action: (rows: any[]) => handleBatchExport(rows)
  }
])

const fetchTasks = async (params: any) => {
  const next = { ...(params || {}) }
  if (next.dateRange) {
    next.startDateFrom = next.dateRange[0]
    next.startDateTo = next.dateRange[1]
    delete next.dateRange
  }
  return inventoryApi.listTasks(next)
}

const getStatusType = (status: string) => {
  const typeMap: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'> = {
    pending: 'info',
    in_progress: 'primary',
    completed: 'success',
    cancelled: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    pending: t('inventory.status.pending'),
    in_progress: t('inventory.status.in_progress'),
    completed: t('inventory.status.completed'),
    cancelled: t('inventory.status.canceled')
  }
  return labelMap[status] || status
}

const handleRowClick = (row: any) => handleView(row)

const handleCreate = () => {
  router.push('/inventory/create')
}

const handleView = (row: any) => {
  router.push(`/inventory/task/${row.id}`)
}

const handleStart = (row: any) => {
  router.push({ name: 'TaskExecute', params: { id: row.id } })
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      t('common.messages.confirmDelete', { count: 1 }),
      t('common.messages.confirmTitle'),
      {
        type: 'warning',
        confirmButtonText: t('common.actions.confirm'),
        cancelButtonText: t('common.actions.cancel')
      }
    )
    await inventoryApi.deleteTask(row.id)
    ElMessage.success(t('common.messages.operationSuccess'))
    refreshList()
  } catch (error: any) {
    if (error !== 'cancel') console.error('Delete failed:', error)
  }
}

const handleBatchDelete = async (selectedRows: any[]) => {
  try {
    const ids = (selectedRows || []).map((r) => r.id).filter(Boolean)
    if (ids.length === 0) return
    await inventoryApi.batchDeleteTasks(ids)
    ElMessage.success(t('common.messages.operationSuccess'))
    refreshList()
  } catch (error) {
    console.error('Batch delete failed:', error)
  }
}

const handleBatchExport = async (selectedRows: any[]) => {
  const ids = (selectedRows || []).map((r) => r.id).filter(Boolean)
  ElMessage.info(t('inventory.messages.exportDeveloping', { count: ids.length }))
}

const refreshList = () => {
  window.dispatchEvent(new CustomEvent('refresh-base-list'))
}
</script>

<style scoped lang="scss">
.inventory-task-list {
  height: 100%;
}
</style>
