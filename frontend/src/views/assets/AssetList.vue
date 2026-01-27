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
      object-code="ASSET"
      @row-click="handleRowClick"
    >
      <template #toolbar>
        <el-button type="primary" :icon="Plus" @click="handleCreate">
          新增资产
        </el-button>
        <el-button :icon="Download" @click="handleExport()">
          导出
        </el-button>
      </template>

      <template #batch-actions="{ selectedRows }">
        <span v-if="selectedRows.length > 0" class="selection-info">
          已选择 {{ selectedRows.length }} 项
        </span>
      </template>

      <template #cell-assetCategoryName="{ row }">
        <el-tag v-if="row.assetCategoryName" type="info" size="small">
          {{ row.assetCategoryName }}
        </el-tag>
        <span v-else>-</span>
      </template>

      <template #cell-purchasePrice="{ row }">
        <span class="money-text">¥{{ formatMoney(row.purchasePrice) }}</span>
      </template>

      <template #cell-assetStatus="{ row }">
        <el-tag :type="getStatusType(row.assetStatus)">
          {{ getStatusLabel(row.assetStatus) }}
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
import { ElMessage } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { assetApi } from '@/api/assets'
import { categoryApi } from '@/api/assets'
import type { Asset, AssetStatus } from '@/types/assets'
import type { TableColumn, SearchField } from '@/types/common'
import { formatMoney } from '@/utils/numberFormat'
import { useCrud } from '@/composables/useCrud'

const router = useRouter()

// ============================================================================
// State
// ============================================================================

const categoryOptions = ref<Array<{ label: string; value: string }>>([])

// ============================================================================
// API wrapper (bound function to preserve 'this' context)
// ============================================================================

const fetchAssets = (params: any) => assetApi.list(params)

// ============================================================================
// CRUD Composable
// ============================================================================

const { 
  handleDelete: crudDelete,
  handleBatchDelete: crudBatchDelete,
  handleExport: crudExport,
  handleBatchExport: crudBatchExport
} = useCrud({
  name: '资产',
  api: {
    list: assetApi.list,
    delete: assetApi.delete,
    batchDelete: assetApi.batchDelete,
    export: (params: any) => {
      // Adapter for assetApi.export which expects assetIds for batch
      if (params && params.ids) {
        return assetApi.export({ ...params, assetIds: params.ids })
      }
      return assetApi.export(params)
    }
  }
})

// Wrappers or Direct usage
const handleDelete = (row: Asset) => crudDelete(row).then((success) => {
  if (success) refreshList()
})

const handleExport = () => crudExport()

// ============================================================================
// Table Columns
// ============================================================================

const columns: TableColumn[] = [
  { prop: 'assetCode', label: '资产编码', width: 140, fixed: 'left' },
  { prop: 'assetName', label: '资产名称', minWidth: 180 },
  { prop: 'assetCategoryName', label: '分类', width: 120, slot: true },
  { prop: 'purchasePrice', label: '采购金额', width: 120, slot: true, align: 'right' },
  { prop: 'purchaseDate', label: '采购日期', width: 120 },
  { prop: 'locationPath', label: '存放位置', width: 140 },
  { prop: 'custodianName', label: '使用人', width: 100 },
  { prop: 'assetStatus', label: '状态', width: 100, slot: true, fixed: 'right' },
  // Hidden columns (available in settings)
  { prop: 'brand', label: '品牌', width: 120, visible: false },
  { prop: 'model', label: '规格型号', width: 120, visible: false },
  { prop: 'serialNumber', label: '序列号', width: 140, visible: false },
  { prop: 'supplierName', label: '供应商', width: 150, visible: false },
  { prop: 'departmentName', label: '所属部门', width: 120, visible: false },
  { prop: 'currentValue', label: '当前净值', width: 120, visible: false, type: 'currency' },
  { prop: 'usefulLife', label: '使用年限(月)', width: 100, visible: false },
  { prop: 'remarks', label: '备注', minWidth: 200, visible: false }
]

// ============================================================================
// Search Fields
// ============================================================================

const searchFields: SearchField[] = [
  {
    field: 'search',
    label: '关键词',
    type: 'input',
    placeholder: '资产编码/名称'
  },
  {
    field: 'categoryId',
    label: '资产分类',
    type: 'select',
    options: categoryOptions.value,
    multiple: true
  },
  {
    field: 'status',
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
    field: 'locationId',
    label: '存放位置',
    type: 'select',
    options: [] // Will be loaded from API
  },
  {
    field: 'purchaseDateRange',
    label: '采购日期',
    type: 'daterange'
  }
]

// ============================================================================
// Batch Actions
// ============================================================================

const batchActions = [
  {
    label: '批量删除',
    type: 'danger' as const,
    action: async (rows: Asset[]) => {
      const success = await crudBatchDelete(rows)
      if (success) refreshList()
    }
  },
  {
    label: '批量导出',
    type: 'primary' as const,
    action: (rows: Asset[]) => crudBatchExport(rows)
  }
]

// ============================================================================
// Methods
// ============================================================================

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
    const res: any = await categoryApi.list()
    // Handle both array and paginated response
    const categories = Array.isArray(res) ? res : (res.results || [])
    
    categoryOptions.value = categories.map((cat: any) => ({
      label: cat.name,
      value: cat.id
    }))
    // Update search fields
    const categoryField = searchFields.find(f => f.field === 'categoryId')
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
  router.push('/assets/create')
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
  router.push(`/assets/edit/${row.id}`)
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
