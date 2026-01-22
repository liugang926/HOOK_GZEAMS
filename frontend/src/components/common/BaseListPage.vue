<!--
  BaseListPage Component

  A reusable list page component that provides:
  - Search form with dynamic field rendering
  - Data table with pagination
  - Slot-based customization for actions and cell rendering
  - Selection support for batch operations

  Usage:
  <BaseListPage
    title="Asset List"
    :search-fields="searchFields"
    :table-columns="columns"
    :api="fetchData"
    :batch-actions="batchActions"
  >
    <template #toolbar>
      <el-button type="primary">Add New</el-button>
    </template>
    <template #actions="{ row }">
      <el-button link @click="handleEdit(row)">Edit</el-button>
    </template>
  </BaseListPage>
-->

<script setup lang="ts">
/**
 * BaseListPage Component
 *
 * A standardized list page component for all module listing views.
 * Provides search, pagination, batch operations, and customizable rendering.
 */

import { ref, computed, onMounted, watch } from 'vue'
import type { TableColumn, SearchField } from '@/types/common'
import { formatDate } from '@/utils/dateFormat'

// ============================================================================
// Props
// ============================================================================

interface Props {
  /** Page title */
  title?: string
  /** Search field definitions */
  searchFields?: SearchField[]
  /** Table column definitions */
  tableColumns: TableColumn[]
  /** API function to fetch data */
  api: (params: any) => Promise<any>
  /** Available batch actions */
  batchActions?: Array<{
    label: string
    type?: 'primary' | 'success' | 'warning' | 'danger'
    icon?: string
    action: (selectedRows: any[]) => void | Promise<void>
    confirm?: boolean
    confirmMessage?: string
  }>
  /** Enable row selection */
  selectable?: boolean
  /** Default page size */
  defaultPageSize?: number
  /** Page size options */
  pageSizes?: number[]
  /** Show index column */
  showIndex?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  searchFields: () => [],
  selectable: true,
  defaultPageSize: 20,
  pageSizes: () => [10, 20, 50, 100],
  showIndex: true,
  batchActions: () => []
})

// ============================================================================
// Emits
// ============================================================================

interface Emits {
  (e: 'row-click', row: any): void
  (e: 'selection-change', selection: any[]): void
}

const emit = defineEmits<Emits>()

// ============================================================================
// State
// ============================================================================

/** Table loading state */
const loading = ref(false)

/** Table data */
const tableData = ref<any[]>([])

/** Total count for pagination */
const total = ref(0)

/** Current page number */
const currentPage = ref(1)

/** Page size */
const pageSize = ref(props.defaultPageSize)

/** Search form values */
const searchForm = ref<Record<string, any>>({})

/** Selected rows */
const selectedRows = ref<any[]>([])

/** Search form expanded state */
const searchExpanded = ref(false)

/** Table ref */
const tableRef = ref()

// ============================================================================
// Computed
// ============================================================================

/** Whether any rows are selected */
const hasSelection = computed(() => selectedRows.value.length > 0)

/** Whether batch actions are available */
const hasBatchActions = computed(() => props.batchActions && props.batchActions.length > 0)

/** Pagination layout */
const paginationLayout = computed(() => {
  return 'total, sizes, prev, pager, next, jumper'
})

/** Visible search fields (non-expanded shows first 4) */
const visibleSearchFields = computed(() => {
  if (searchExpanded.value) {
    return props.searchFields
  }
  return props.searchFields.slice(0, 4)
})

/** Whether expand button is needed */
const needExpand = computed(() => {
  return props.searchFields.length > 4
})

// ============================================================================
// Methods
// ============================================================================

/**
 * Fetch table data from API
 */
const fetchData = async () => {
  loading.value = true
  try {
    // Build request params
    const params: Record<string, any> = {
      page: currentPage.value,
      pageSize: pageSize.value
    }

    // Add search filters
    Object.keys(searchForm.value).forEach(key => {
      const value = searchForm.value[key]
      if (value !== undefined && value !== null && value !== '') {
        params[key] = value
      }
    })

    const response = await props.api(params)

    // Handle paginated response
    if (response.results) {
      tableData.value = response.results
      total.value = response.count || 0
    } else if (Array.isArray(response)) {
      tableData.value = response
      total.value = response.length
    } else {
      tableData.value = []
      total.value = 0
    }
  } catch (error) {
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

/**
 * Handle search
 */
const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

/**
 * Handle reset
 */
const handleReset = () => {
  Object.keys(searchForm.value).forEach(key => {
    searchForm.value[key] = undefined
  })
  currentPage.value = 1
  fetchData()
}

/**
 * Handle page size change
 */
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchData()
}

/**
 * Handle current page change
 */
const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchData()
}

/**
 * Handle row click
 */
const handleRowClick = (row: any) => {
  emit('row-click', row)
}

/**
 * Handle selection change
 */
const handleSelectionChange = (selection: any[]) => {
  selectedRows.value = selection
  emit('selection-change', selection)
}

/**
 * Handle batch action
 */
const handleBatchAction = async (action: Props['batchActions'][number]) => {
  if (!action) return

  // Show confirmation if required
  if (action.confirm && action.confirmMessage) {
    // TODO: Use ElMessageBox for confirmation
    const confirmed = confirm(action.confirmMessage)
    if (!confirmed) return
  }

  try {
    await action.action(selectedRows.value)
    // Clear selection after action
    tableRef.value?.clearSelection()
    // Refresh data
    fetchData()
  } catch (error) {
    // Error handled by error handler
  }
}

/**
 * Toggle search form expand
 */
const toggleSearchExpand = () => {
  searchExpanded.value = !searchExpanded.value
}

/**
 * Refresh table data
 */
const refresh = () => {
  fetchData()
}

/**
 * Clear selection
 */
const clearSelection = () => {
  tableRef.value?.clearSelection()
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(() => {
  // Initialize search form default values
  props.searchFields.forEach(field => {
    if (field.defaultValue !== undefined) {
      searchForm.value[field.prop] = field.defaultValue
    }
  })

  fetchData()
})

// Watch for external data changes
watch(() => props.tableColumns, fetchData, { deep: true })

// ============================================================================
// Expose public methods
// ============================================================================

defineExpose({
  refresh,
  clearSelection,
  fetchData
})
</script>

<template>
  <div class="base-list-page">
    <!-- Page Header -->
    <div v-if="title" class="page-header">
      <h2 class="page-title">{{ title }}</h2>
      <div class="page-toolbar">
        <slot name="toolbar" :selected-rows="selectedRows" :has-selection="hasSelection" />
      </div>
    </div>

    <!-- Search Form -->
    <div v-if="searchFields.length > 0" class="search-form-container">
      <el-form :model="searchForm" inline class="search-form">
        <template v-for="field in visibleSearchFields" :key="field.prop">
          <!-- Text Input -->
          <el-form-item v-if="field.type === 'text'" :label="field.label">
            <el-input
              v-model="searchForm[field.prop]"
              :placeholder="field.placeholder || `请输入${field.label}`"
              clearable
              @keyup.enter="handleSearch"
            />
          </el-form-item>

          <!-- Select -->
          <el-form-item v-else-if="field.type === 'select'" :label="field.label">
            <el-select
              v-model="searchForm[field.prop]"
              :placeholder="field.placeholder || `请选择${field.label}`"
              clearable
              :multiple="field.multiple"
            >
              <el-option
                v-for="option in field.options"
                :key="option.value"
                :label="option.label"
                :value="option.value"
              />
            </el-select>
          </el-form-item>

          <!-- Date Range -->
          <el-form-item v-else-if="field.type === 'dateRange'" :label="field.label">
            <el-date-picker
              v-model="searchForm[field.prop]"
              type="daterange"
              range-separator="-"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>

          <!-- Date Picker -->
          <el-form-item v-else-if="field.type === 'date'" :label="field.label">
            <el-date-picker
              v-model="searchForm[field.prop]"
              type="date"
              :placeholder="field.placeholder || `请选择${field.label}`"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>

          <!-- Number Range -->
          <el-form-item v-else-if="field.type === 'numberRange'" :label="field.label">
            <div class="number-range">
              <el-input v-model="searchForm[`${field.prop}_min`]" placeholder="最小值" />
              <span class="separator">-</span>
              <el-input v-model="searchForm[`${field.prop}_max`]" placeholder="最大值" />
            </div>
          </el-form-item>

          <!-- Custom Slot -->
          <el-form-item v-else-if="field.type === 'slot'" :label="field.label">
            <slot :name="`search-${field.prop}`" :field="field" :form="searchForm" />
          </el-form-item>
        </template>

        <!-- Actions -->
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
          <el-button
            v-if="needExpand"
            link
            type="primary"
            @click="toggleSearchExpand"
          >
            {{ searchExpanded ? '收起' : '展开' }}
            <el-icon>
              <component :is="searchExpanded ? 'arrow-up' : 'arrow-down'" />
            </el-icon>
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- Batch Actions Toolbar -->
    <div v-if="hasBatchActions && hasSelection" class="batch-toolbar">
      <span class="selection-info">已选择 {{ selectedRows.length }} 项</span>
      <el-button
        v-for="action in batchActions"
        :key="action.label"
        :type="action.type || 'default'"
        :icon="action.icon"
        size="small"
        @click="handleBatchAction(action)"
      >
        {{ action.label }}
      </el-button>
    </div>

    <!-- Data Table -->
    <div class="table-container">
      <el-table
        ref="tableRef"
        v-loading="loading"
        :data="tableData"
        border
        stripe
        @row-click="handleRowClick"
        @selection-change="handleSelectionChange"
      >
        <!-- Selection Column -->
        <el-table-column
          v-if="selectable"
          type="selection"
          width="55"
          fixed="left"
        />

        <!-- Index Column -->
        <el-table-column
          v-if="showIndex"
          type="index"
          label="序号"
          width="60"
          fixed="left"
        />

        <!-- Dynamic Columns -->
        <template v-for="column in tableColumns" :key="column.prop">
          <!-- Slot Column -->
          <el-table-column
            v-if="column.slot"
            v-bind="column"
          >
            <template #default="scope">
              <slot :name="column.slot" :row="scope.row" :column="column" :$index="scope.$index" />
            </template>
          </el-table-column>

          <!-- Tag Column -->
          <el-table-column
            v-else-if="column.tagType"
            v-bind="column"
          >
            <template #default="scope">
              <el-tag :type="column.tagType(scope.row)">
                {{ scope.row[column.prop] }}
              </el-tag>
            </template>
          </el-table-column>

          <!-- Date Column -->
          <el-table-column
            v-else-if="column.dateFormatter"
            v-bind="column"
          >
            <template #default="scope">
              {{ formatDate(scope.row[column.prop], column.dateFormatter) }}
            </template>
          </el-table-column>

          <!-- Standard Column -->
          <el-table-column
            v-else
            v-bind="column"
          />
        </template>

        <!-- Actions Column -->
        <el-table-column
          v-if="$slots.actions"
          label="操作"
          width="180"
          fixed="right"
        >
          <template #default="scope">
            <slot name="actions" :row="scope.row" :$index="scope.$index" />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Pagination -->
    <div v-if="total > 0" class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="pageSizes"
        :layout="paginationLayout"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- Empty State -->
    <div v-if="!loading && tableData.length === 0" class="empty-state">
      <el-empty description="暂无数据" />
    </div>
  </div>
</template>

<style scoped lang="scss">
.base-list-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100%;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 20px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

  .page-title {
    margin: 0;
    font-size: 18px;
    font-weight: 500;
    color: #303133;
  }

  .page-toolbar {
    display: flex;
    gap: 10px;
  }
}

.search-form-container {
  margin-bottom: 20px;
  padding: 16px 20px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

  .search-form {
    :deep(.el-form-item) {
      margin-bottom: 12px;
    }
  }
}

.number-range {
  display: flex;
  align-items: center;
  gap: 8px;

  .el-input {
    width: 120px;
  }

  .separator {
    color: #909399;
  }
}

.batch-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 12px 20px;
  background-color: #ecf5ff;
  border: 1px solid #d9ecff;
  border-radius: 4px;

  .selection-info {
    margin-right: 10px;
    font-size: 14px;
    color: #409eff;
  }
}

.table-container {
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  overflow: hidden;

  :deep(.el-table) {
    th {
      background-color: #f5f7fa;
      color: #606266;
      font-weight: 500;
    }
  }
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
  padding: 16px 20px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.empty-state {
  margin-top: 60px;
  padding: 40px 20px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
</style>
