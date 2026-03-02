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
      :title="$t('assets.list.title')"
      :search-fields="searchFields"
      :table-columns="columns"
      :api="fetchAssets"
      :batch-actions="batchActions"
      :selectable="true"
      object-code="Asset"
      @row-click="handleRowClick"
    >
      <template #toolbar>
        <el-button
          type="primary"
          :icon="Plus"
          @click="handleCreate"
        >
          {{ $t('assets.list.createButton') }}
        </el-button>
        <el-button
          :icon="Download"
          @click="handleExport()"
        >
          {{ $t('common.actions.export') }}
        </el-button>
      </template>

      <template #batch-actions="{ selectedRows }">
        <span
          v-if="(selectedRows as any[]).length > 0"
          class="selection-info"
        >
          {{ $t('assets.list.selected', { count: (selectedRows as any[]).length }) }}
        </span>
      </template>

      <template #actions="{ row }">
        <el-button
          link
          type="primary"
          @click="handleView(row)"
        >
          {{ $t('common.actions.view') }}
        </el-button>
        <el-button
          link
          type="primary"
          @click="handleEdit(row)"
        >
          {{ $t('common.actions.edit') }}
        </el-button>
        <el-button
          link
          type="danger"
          @click="handleDelete(row)"
        >
          {{ $t('common.actions.delete') }}
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

import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Plus, Download } from '@element-plus/icons-vue'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { assetApi } from '@/api/assets'
import { categoryApi } from '@/api/assets'
import type { Asset, AssetStatus } from '@/types/assets'
import type { TableColumn, SearchField } from '@/types/common'
import { useCrud } from '@/composables/useCrud'

const router = useRouter()
const { t } = useI18n()

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
  name: t('assets.detail.title'), // Use a generic name or "Asset"
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
const handleDelete = (row: Asset) => crudDelete(row.id as any).then((success) => {
  if (success) refreshList()
})

const handleExport = (ids?: any[]) => crudExport(ids as any)

// ============================================================================
// Table Columns
// ============================================================================

const columns = computed<TableColumn[]>(() => [
  { prop: 'assetCode', label: t('assets.fields.assetCode'), width: 140, fixed: 'left' },
  { prop: 'assetName', label: t('assets.fields.assetName'), minWidth: 180 },
  { prop: 'assetCategoryName', label: t('assets.fields.category'), width: 120, tagType: () => 'info', format: (value: any) => value || '-' },
  { prop: 'purchasePrice', label: t('assets.fields.purchasePrice'), width: 120, align: 'right' },
  { prop: 'purchaseDate', label: t('assets.fields.purchaseDate'), width: 120 },
  { prop: 'locationPath', label: t('assets.fields.location'), width: 140 },
  { prop: 'custodianName', label: t('assets.fields.user'), width: 100 },
  { prop: 'assetStatus', label: t('common.labels.status'), width: 100, tagType: (row: any) => getStatusType(row.assetStatus), format: (value: any, row: any) => row?.statusLabel || getStatusLabel(value), fixed: 'right' },
  // Hidden columns (available in settings)
  { prop: 'brand', label: t('assets.fields.brand'), width: 120, visible: false },
  { prop: 'model', label: t('assets.fields.model'), width: 120, visible: false },
  { prop: 'serialNumber', label: t('assets.fields.serialNumber'), width: 140, visible: false },
  { prop: 'supplierName', label: t('assets.fields.supplier'), width: 150, visible: false },
  { prop: 'departmentName', label: t('assets.fields.department'), width: 120, visible: false },
  { prop: 'currentValue', label: t('assets.fields.currentValue'), width: 120, visible: false, type: 'currency' },
  { prop: 'usefulLife', label: t('assets.fields.usefulLife'), width: 100, visible: false },
  { prop: 'remarks', label: t('common.labels.remark'), minWidth: 200, visible: false }
])

// ============================================================================
// Search Fields
// ============================================================================

const searchFields = computed<SearchField[]>(() => [
  {
    field: 'search',
    label: t('assets.search.keyword'),
    type: 'input',
    placeholder: t('assets.search.keywordPlaceholder')
  },
  {
    field: 'categoryId',
    label: t('assets.fields.category'),
    type: 'select',
    options: categoryOptions.value,
    multiple: true
  },
  {
    field: 'status',
    label: t('assets.search.status'),
    type: 'select',
    options: [
      { label: t('assets.status.inUse'), value: 'in_use' },
      { label: t('assets.status.idle'), value: 'idle' },
      { label: t('assets.status.maintenance'), value: 'maintenance' },
      { label: t('assets.status.scrapped'), value: 'scrapped' },
      { label: t('assets.status.draft'), value: 'draft' }
    ]
  },
  {
    field: 'locationId',
    label: t('assets.fields.location'),
    type: 'select',
    options: [] // Will be loaded from API
  },
  {
    field: 'purchaseDateRange',
    label: t('assets.search.dateRange'),
    type: 'daterange'
  }
])

// ============================================================================
// Batch Actions
// ============================================================================

const batchActions = computed(() => [
  {
    label: t('assets.list.batchDelete'),
    type: 'danger' as const,
    action: async (rows: Asset[]) => {
      const success = await crudBatchDelete(rows)
      if (success) refreshList()
    }
  },
  {
    label: t('assets.list.batchExport'),
    type: 'primary' as const,
    action: (rows: Asset[]) => crudBatchExport(rows)
  }
])

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
  const keyMap: Record<AssetStatus, string> = {
    draft: 'assets.status.draft',
    in_use: 'assets.status.inUse',
    idle: 'assets.status.idle',
    maintenance: 'assets.status.maintenance',
    scrapped: 'assets.status.scrapped'
  }
  return keyMap[status] ? t(keyMap[status]) : status
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
    
    // Note: Since searchFields is computed, we don't need to manually update it anymore
    // strict reactivity will handle it, provided searchFields depends on categoryOptions.value using computed
    // But currently searchFields is a computed that returns a new array, it should be fine.
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
  router.push(`/assets/${row.id}?action=edit`)
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

.selection-info {
  margin-right: 16px;
  color: #409eff;
  font-size: 14px;
}
</style>
