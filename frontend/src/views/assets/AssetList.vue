<!--
  AssetList View

  Main asset management list page with:
  - Search and filter functionality
  - Batch operations (export, delete)
  - Create/Edit/Delete actions
  - Status visualization
  - Integration with BaseListPage component
-->

<template>
  <div class="asset-list-page">
    <BaseListPage
      title="固定资产"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchAssets"
      :batch-actions="batchActions"
      :selectable="true"
      @row-click="handleRowClick"
    >
      <template #toolbar>
        <el-button type="primary" :icon="Plus" @click="handleCreate">
          新增资产
        </el-button>
        <el-button :icon="Download" @click="handleExport">
          导出
        </el-button>
      </template>

      <template #actions="{ selectedRows }">
        <span v-if="selectedRows.length > 0" class="selection-info">
          已选择 {{ selectedRows.length }} 项
        </span>
      </template>

      <template #cell-categoryName="{ row }">
        <el-tag v-if="row.categoryName" type="info" size="small">
          {{ row.categoryName }}
        </el-tag>
        <span v-else>-</span>
      </template>

      <template #cell-purchasePrice="{ row }">
        <span class="money-text">¥{{ formatMoney(row.purchasePrice) }}</span>
      </template>

      <template #cell-status="{ row }">
        <el-tag :type="getStatusType(row.status)">
          {{ getStatusLabel(row.status) }}
        </el-tag>
      </template>

      <template #actions="{ row }">
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

    <!-- Asset Form Dialog -->
    <AssetFormDialog
      v-model="formVisible"
      :asset="currentAsset"
      @success="handleFormSuccess"
    />
  </div>
</template>

<script setup lang="ts">
/**
 * AssetList View Component
 *
 * Main list view for asset management with search, filter,
 * and CRUD operations.
 */

import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import AssetFormDialog from '@/components/assets/AssetFormDialog.vue'
import { assetApi } from '@/api/assets'
import { categoryApi } from '@/api/assets'
import type { Asset, AssetStatus } from '@/types/assets'
import type { TableColumn, SearchField } from '@/types/common'
import { formatMoney } from '@/utils/numberFormat'

const router = useRouter()

// ============================================================================
// State
// ============================================================================

const formVisible = ref(false)
const currentAsset = ref<Asset | null>(null)
const categoryOptions = ref<Array<{ label: string; value: string }>>([])

// ============================================================================
// Table Columns
// ============================================================================

const columns: TableColumn[] = [
  { prop: 'code', label: '资产编码', width: 140, fixed: 'left' },
  { prop: 'name', label: '资产名称', minWidth: 180 },
  { prop: 'categoryName', label: '分类', width: 120, slot: true },
  { prop: 'purchasePrice', label: '采购金额', width: 120, slot: true, align: 'right' },
  { prop: 'purchaseDate', label: '采购日期', width: 120 },
  { prop: 'locationName', label: '存放位置', width: 140 },
  { prop: 'custodianName', label: '使用人', width: 100 },
  { prop: 'status', label: '状态', width: 100, slot: true, fixed: 'right' }
]

// ============================================================================
// Search Fields
// ============================================================================

const searchFields: SearchField[] = [
  {
    prop: 'search',
    label: '关键词',
    type: 'text',
    placeholder: '资产编码/名称'
  },
  {
    prop: 'categoryId',
    label: '资产分类',
    type: 'select',
    options: categoryOptions.value,
    multiple: true
  },
  {
    prop: 'status',
    label: '状态',
    type: 'select',
    options: [
      { label: '使用中', value: 'in_use' },
      { label: '闲置', value: 'idle' },
      { label: '维修中', value: 'maintenance' },
      { label: '已报废', value: 'scrapped' },
      { label: '草稿', value: 'draft' }
    ]
  },
  {
    prop: 'locationId',
    label: '存放位置',
    type: 'select',
    options: [] // Will be loaded from API
  },
  {
    prop: 'purchaseDateRange',
    label: '采购日期',
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
    action: handleBatchDelete
  },
  {
    label: '批量导出',
    type: 'primary' as const,
    action: handleBatchExport
  }
]

// ============================================================================
// Methods
// ============================================================================

/**
 * Fetch assets from API
 */
const fetchAssets = async (params: any) => {
  return await assetApi.list(params)
}

/**
 * Get status tag type
 */
const getStatusType = (status: AssetStatus) => {
  const typeMap: Record<AssetStatus, 'success' | 'warning' | 'danger' | 'info' | 'primary'> = {
    draft: 'info',
    in_use: 'success',
    idle: 'warning',
    maintenance: 'danger',
    scrapped: 'info'
  }
  return typeMap[status] || 'info'
}

/**
 * Get status label
 */
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

/**
 * Load category options
 */
const loadCategories = async () => {
  try {
    const categories = await categoryApi.list()
    categoryOptions.value = categories.map((cat: any) => ({
      label: cat.name,
      value: cat.id
    }))
    // Update search fields
    const categoryField = searchFields.find(f => f.prop === 'categoryId')
    if (categoryField) {
      categoryField.options = categoryOptions.value
    }
  } catch (error) {
    console.error('Failed to load categories:', error)
  }
}

/**
 * Handle row click
 */
const handleRowClick = (row: Asset) => {
  handleView(row)
}

/**
 * Handle create button click
 */
const handleCreate = () => {
  currentAsset.value = null
  formVisible.value = true
}

/**
 * Handle view button click
 */
const handleView = (row: Asset) => {
  router.push(`/assets/${row.id}`)
}

/**
 * Handle edit button click
 */
const handleEdit = (row: Asset) => {
  currentAsset.value = row
  formVisible.value = true
}

/**
 * Handle delete button click
 */
const handleDelete = async (row: Asset) => {
  try {
    await ElMessageBox.confirm(
      `确认删除资产"${row.name}"？此操作可恢复。`,
      '删除确认',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消'
      }
    )
    await assetApi.delete(row.id)
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
const handleBatchDelete = async (selectedRows: Asset[]) => {
  try {
    await ElMessageBox.confirm(
      `确认删除选中的 ${selectedRows.length} 项资产？`,
      '批量删除确认',
      {
        type: 'warning',
        confirmButtonText: '确认删除',
        cancelButtonText: '取消'
      }
    )
    const ids = selectedRows.map(r => r.id)
    await assetApi.batchDelete(ids)
    ElMessage.success(`成功删除 ${ids.length} 项资产`)
    refreshList()
  } catch (error) {
    // User cancelled
  }
}

/**
 * Handle export
 */
const handleExport = async () => {
  try {
    const blob = await assetApi.export()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `固定资产_${new Date().toLocaleDateString()}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

/**
 * Handle batch export
 */
const handleBatchExport = async (selectedRows: Asset[]) => {
  if (selectedRows.length === 0) {
    ElMessage.warning('请先选择要导出的资产')
    return
  }
  try {
    const ids = selectedRows.map(r => r.id)
    const blob = await assetApi.export({ assetIds: ids })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `固定资产_${new Date().toLocaleDateString()}.xlsx`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
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
 * Refresh list
 */
const refreshList = () => {
  // Emit custom event that BaseListPage will catch
  window.dispatchEvent(new CustomEvent('refresh-base-list'))
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  loadCategories()
})
</script>

<style scoped lang="scss">
.asset-list-page {
  height: 100%;
}

.money-text {
  font-family: 'Monaco', 'Consolas', monospace;
  font-weight: 500;
  color: #303133;
}

.selection-info {
  margin-right: 16px;
  color: #409eff;
  font-size: 14px;
}
</style>
