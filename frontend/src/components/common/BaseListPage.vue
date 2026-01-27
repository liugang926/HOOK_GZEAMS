<!--
  BaseListPage Component

  A reusable list page component that provides:
  - Search form with dynamic field rendering
  - Data table with pagination
  - Slot-based customization for actions and cell rendering
  - Selection support for batch operations
  - [New] Column Customization (Visibility & Order)
  - [New] Server-side Sorting

  Usage:
  <BaseListPage
    title="Asset List"
    :search-fields="searchFields"
    :table-columns="columns"
    :api="fetchData"
    :batch-actions="batchActions"
  >
    ...
  </BaseListPage>
-->

<script setup lang="ts">
/**
 * BaseListPage Component
 *
 * A standardized list page component for all module listing views.
 * Provides search, pagination, batch operations, customizable rendering,
 * and now supports user-defined fields and sorting.
 */

import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import type { TableColumn, SearchField } from '@/types/common'
import { formatDate } from '@/utils/dateFormat'
import ColumnManager from '@/components/common/ColumnManager.vue'
import FieldRenderer from '@/components/common/FieldRenderer.vue'
// import { useRouter, useRoute } from 'vue-router'

// ============================================================================
// Props
// ============================================================================

export interface BatchAction {
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  icon?: any
  action: (selectedRows: any[]) => void | Promise<void>
  confirm?: boolean
  confirmMessage?: string
}

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
  batchActions?: BatchAction[]
  /** Enable row selection */
  selectable?: boolean
  /** Default page size */
  defaultPageSize?: number
  /** Page size options */
  pageSizes?: number[]
  /** Object Code for column persistence (required for saving settings) */
  objectCode?: string
  /** Whether to show index column */
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

/** Sorting State */
const sortState = ref<{ prop: string, order: string } | null>(null)

/** Internal Columns (Managed by ColumnManager) */
const activeColumns = ref<TableColumn[]>([])

/** Column Config Hook */
import { useColumnConfig } from '@/hooks/useColumnConfig'
import Sortable from 'sortablejs'
import { nextTick } from 'vue'

// Initialize hook only if objectCode is present, otherwise dummy
const columnConfig = props.objectCode ? useColumnConfig(props.objectCode) : null

/** Mobile detection */
const isMobile = ref(false)

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
}

/** Search form values */
const searchForm = ref<Record<string, any>>({})

/** Selected rows */
const selectedRows = ref<any[]>([])

/** Search form expanded state */
const searchExpanded = ref(false)

/** Table ref */
const tableRef = ref()

/** Dynamic Actions */
const objectActions = ref<any[]>([])
import { getBusinessObject, getFieldDefinitions } from '@/api/system'
import { useAction } from '@/components/engine/hooks/useAction' // Adjust path if needed

const { executeAction } = useAction()

const handleDynamicAction = async (action: any) => {
    await executeAction(action, { selectedRows: selectedRows.value })
    // Refresh if needed
    if (action.refresh) {
        fetchData()
    }
}

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

/** Filtered Columns for Table Render */
const visibleTableColumns = computed(() => {
  return activeColumns.value.filter(col => col.visible !== false)
})

// ============================================================================
// Methods
// ============================================================================

/**
 * Fetch table data from API
 */
const fetchData = async () => {
  loading.value = true
  tableData.value = [] // Clear data to show skeleton
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

    // Add Sorting
    if (sortState.value && sortState.value.prop) {
      const { prop, order } = sortState.value
      // Django usually uses 'ordering' param
      // -field for desc, field for asc
      const prefix = order === 'descending' ? '-' : ''
      params.ordering = `${prefix}${prop}`
    }

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
  sortState.value = null
  tableRef.value?.clearSort()
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
 * Handle sorting change from Element Table
 */
const handleSortChange = ({ prop, order }: { prop: string, order: string }) => {
  if (!prop) {
    sortState.value = null
  } else {
    sortState.value = { prop, order }
  }
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
const handleBatchAction = async (action: BatchAction) => {
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

/**
 * Handle Column Configuration Save
 */
const handleColumnSave = async (newColumns: TableColumn[]) => {
  activeColumns.value = newColumns
  if (columnConfig) {
      await columnConfig.saveConfig(newColumns)
  }
}

const handleColumnReset = async () => {
    if (columnConfig) {
        await columnConfig.resetConfig()
        activeColumns.value = columnConfig.applyConfig(prepareColumns(props.tableColumns))
    } else {
        activeColumns.value = prepareColumns(props.tableColumns)
    }
}

/**
 * Prepare columns with defaults (e.g. enable sortable)
 */
const prepareColumns = (cols: TableColumn[]): TableColumn[] => {
  return cols.map(col => ({
    ...col,
    // Enable sorting by default if not strictly disabled or already set
    // Note: We use 'custom' for server-side sorting
    sortable: (col.sortable === undefined || col.sortable === true) ? 'custom' : col.sortable,
    visible: col.visible !== false
  }))
}

/**
 * Initialize Column Drag and Drop
 */
const columnDrop = () => {
  if (isMobile.value) return 
  
  const wrapperTr = tableRef.value?.$el.querySelector('.el-table__header-wrapper tr')
  if (!wrapperTr) return
  
  Sortable.create(wrapperTr, {
    animation: 180,
    delay: 0,
    handle: 'th', // Make the whole header draggable? or just specific handle? Using 'th' acts as full header.
    filter: '.ignore-elements', // Filter out selection/index columns if needed? usually they are fixed or first.
    draggable: 'th',
    onEnd: (evt: any) => {
      if (evt.oldIndex === evt.newIndex) return;

      // Element Plus renders fixed columns in separate tables sometimes, 
      // but usually the main header works for main columns.
      // Be careful with Fixed columns.
      
      // Calculate indices excluding persistent fixed columns if necessary
      // For now, simple index mapping assuming main "visibleTableColumns" maps to <th>s in order.
      // Note: "Selection" and "Index" columns might offset the index.
      
      let offset = 0
      if (props.selectable) offset++
      if (props.showIndex) offset++
      
      const oldIndex = evt.oldIndex - offset
      const newIndex = evt.newIndex - offset
      
      if (oldIndex < 0 || newIndex < 0) return // Dragging fixed col?
      if (oldIndex >= visibleTableColumns.value.length || newIndex >= visibleTableColumns.value.length) return

      // We need to reorder "activeColumns" but based on the "visible" ones changing position.
      // This is tricky because "activeColumns" contains hidden columns too.
      // We will reorder "activeColumns" by finding the corresponding activeColumn of the visible one.
      
      const visibleCols = [...visibleTableColumns.value]
      const movedItem = visibleCols.splice(oldIndex, 1)[0]
      visibleCols.splice(newIndex, 0, movedItem)
      
      // Now reconstruct activeColumns preserving hidden ones in their relative places? 
      // Or just put visible ones in new order and append hidden ones? 
      // Easier: Rebuild activeColumns as visibleCols + hiddenCols
      
      const hiddenCols = activeColumns.value.filter(c => c.visible === false)
      // This might lose the relative position of hidden columns, but acceptable.
      const newActiveColumns = [...visibleCols, ...hiddenCols]
      
      activeColumns.value = newActiveColumns
      
      // Save
      if (columnConfig) {
        columnConfig.saveConfig(activeColumns.value)
      }
    }
  })
}

/**
 * Handle manual column resize
 */
const handleHeaderDragend = (newWidth: number, _oldWidth: number, column: any, _event: MouseEvent) => {
   // Find the column in activeColumns and update width
   const prop = column.property
   const colIndex = activeColumns.value.findIndex(c => c.prop === prop)
   if (colIndex !== -1) {
     activeColumns.value[colIndex].width = newWidth
     // Save
     if (columnConfig) {
       columnConfig.saveConfig(activeColumns.value)
     }
   }
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(async () => {
  // Initialize search form default values
  props.searchFields.forEach(field => {
    if (field.defaultValue !== undefined) {
      searchForm.value[field.prop] = field.defaultValue
    }
  })

  // Initialize columns with persistence
  const defaultCols = prepareColumns(props.tableColumns)
  
  if (props.objectCode) {
      try {
          // 1. Fetch dynamic actions
          const res: any = await getBusinessObject(props.objectCode)
          objectActions.value = res.data?.actions || res.actions || []

          // 2. Fetch all available fields for this object
          const fieldsRes: any = await getFieldDefinitions(props.objectCode)
          const allFields = fieldsRes.data?.results || fieldsRes.results || []
          
          // 3. Merge fields into columns
          // Filter out fields that are already in defaultCols to avoid duplicates
          const existingProps = new Set(defaultCols.map(c => c.prop))
          const newColCandidates = allFields.filter((f: any) => !existingProps.has(f.code) && !existingProps.has(f.name)) // name might be prop in some cases? unlikely, rely on code.

          const newCols: TableColumn[] = newColCandidates.map((f: any) => ({
              prop: f.code,
              label: f.name,
              type: f.field_type?.toLowerCase() || 'text',
              width: 120,
              visible: false, // Default to hidden for non-hardcoded fields
              sortable: true
          }))

          // Append new columns to default set
          const fullColSet = [...defaultCols, ...newCols]
          
          // Apply user config on top of the FULL set
          if (columnConfig) {
              await columnConfig.fetchConfig()
              activeColumns.value = columnConfig.applyConfig(fullColSet)
          } else {
              activeColumns.value = prepareColumns(fullColSet)
          }

      } catch (e: any) {
          // Silent fail or warning for 404 (metadata not found)
          if (e.response && e.response.status === 404) {
              console.warn('Backend metadata not found for', props.objectCode, '- using default columns.')
          } else {
              console.error('Failed to load object metadata', e)
          }
          
          // Fallback to defaults
          if (columnConfig) {
              await columnConfig.fetchConfig()
              activeColumns.value = columnConfig.applyConfig(defaultCols)
          } else {
              activeColumns.value = defaultCols
          }
      }
  } else {
      // No object code, just use defaults
      if (columnConfig) {
          await columnConfig.fetchConfig()
          activeColumns.value = columnConfig.applyConfig(defaultCols)
      } else {
          activeColumns.value = defaultCols
      }
  }

  // Init drag after DOM update
  nextTick(() => {
    columnDrop()
  })

  // Fetch initial data
  fetchData()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})

// Watch for external data changes
watch(() => props.tableColumns, (newCols) => {
    // Re-apply config to new columns definitions if possible
    const defaultCols = prepareColumns(newCols)
    if (columnConfig) {
        activeColumns.value = columnConfig.applyConfig(defaultCols)
    } else {
        activeColumns.value = defaultCols
    }
    fetchData()
    // Re-init drag in case headers changed
    nextTick(() => {
        columnDrop()
    })
}, { deep: true })


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
    <div
      v-if="title"
      class="page-header"
    >
      <h2 class="page-title">
        {{ title }}
      </h2>
      <div class="page-toolbar">
        <slot
          name="toolbar"
          :selected-rows="selectedRows"
          :has-selection="hasSelection"
        />
        
        <!-- Dynamic Actions -->
        <el-button
          v-for="action in objectActions"
          :key="action.code"
          :type="action.type === 'primary' ? 'primary' : 'default'"
          @click="handleDynamicAction(action)"
        >
          {{ action.label }}
        </el-button>
        
        <!-- Column Manager Integration -->
        <ColumnManager 
          :columns="activeColumns" 
          :object-code="objectCode"
          @save="handleColumnSave"
          @reset="handleColumnReset"
        />
      </div>
    </div>

    <!-- Search Form -->
    <div
      v-if="searchFields.length > 0"
      class="search-form-container"
    >
      <el-form
        :model="searchForm"
        inline
        class="search-form"
      >
        <template
          v-for="field in visibleSearchFields"
          :key="field.prop"
        >
          <!-- Text Input -->
          <el-form-item
            v-if="field.type === 'text'"
            :label="field.label"
          >
            <el-input
              v-model="searchForm[field.prop]"
              :placeholder="field.placeholder || `请输入${field.label}`"
              clearable
              @keyup.enter="handleSearch"
            />
          </el-form-item>

          <!-- Select -->
          <el-form-item
            v-else-if="field.type === 'select'"
            :label="field.label"
          >
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
          <el-form-item
            v-else-if="field.type === 'dateRange'"
            :label="field.label"
          >
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
          <el-form-item
            v-else-if="field.type === 'date'"
            :label="field.label"
          >
            <el-date-picker
              v-model="searchForm[field.prop]"
              type="date"
              :placeholder="field.placeholder || `请选择${field.label}`"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>

          <!-- Number Range -->
          <el-form-item
            v-else-if="field.type === 'numberRange'"
            :label="field.label"
          >
            <div class="number-range">
              <el-input
                v-model="searchForm[`${field.prop}_min`]"
                placeholder="最小值"
              />
              <span class="separator">-</span>
              <el-input
                v-model="searchForm[`${field.prop}_max`]"
                placeholder="最大值"
              />
            </div>
          </el-form-item>

          <!-- Custom Slot -->
          <el-form-item
            v-else-if="field.type === 'slot'"
            :label="field.label"
          >
            <slot
              :name="`search-${field.prop}`"
              :field="field"
              :form="searchForm"
            />
          </el-form-item>
        </template>

        <!-- Actions -->
        <el-form-item>
          <el-button
            type="primary"
            @click="handleSearch"
          >
            搜索
          </el-button>
          <el-button @click="handleReset">
            重置
          </el-button>
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
    <div
      v-if="hasBatchActions && hasSelection"
      class="batch-toolbar"
    >
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

    <!-- Mobile Card View -->
    <div
      v-if="isMobile"
      class="mobile-card-container"
    >
      <div
        v-if="loading"
        class="skeleton-container"
        style="padding: 20px;"
      >
        <el-skeleton
          :rows="3"
          animated
          count="3"
        />
      </div>
      <div v-else>
        <div
          v-for="(row, index) in tableData"
          :key="index"
          class="mobile-card"
          @click="handleRowClick(row)"
        >
          <div class="card-header-row">
            <span class="card-title">#{{ index + 1 }}</span>
            <el-tag
              v-if="row.status"
              size="small"
            >
              {{ row.status }}
            </el-tag>
          </div>
          <div class="card-body">
            <div
              v-for="col in visibleTableColumns.slice(0, 4)"
              :key="col.prop"
              class="card-item"
            >
              <span class="label">{{ col.label }}:</span>
              <span class="value">
                <!-- Simple text rendering fallback -->
                {{ row[col.prop] }}
              </span>
            </div>
          </div>
          <div
            v-if="$slots.actions"
            class="card-actions"
          >
            <slot
              name="actions"
              :row="row"
              :$index="index"
            />
          </div>
        </div>
        <el-empty
          v-if="tableData.length === 0"
          description="暂无数据"
        />
      </div>
    </div>

    <!-- Data Table (Desktop) -->
    <div
      v-else
      class="table-container"
    >
      <el-table
        ref="tableRef"
        :data="tableData"
        border
        stripe
        class="base-list-table"
        @row-click="handleRowClick"
        @selection-change="handleSelectionChange"
        @sort-change="handleSortChange"
        @header-dragend="handleHeaderDragend"
      >
        <template #empty>
          <div
            v-if="loading"
            class="skeleton-container"
          >
            <el-skeleton
              :rows="pageSize"
              animated
            />
          </div>
          <el-empty
            v-else
            description="暂无数据"
          />
        </template>
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
        <template
          v-for="column in visibleTableColumns"
          :key="column.prop"
        >
          <!-- Slot Column -->
          <el-table-column
            v-if="column.slot"
            v-bind="column"
          >
            <template #default="scope">
              <slot
                :name="column.slot"
                :row="scope.row"
                :column="column"
                :$index="scope.$index"
              />
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

          <!-- Standard Column using FieldRenderer -->
          <el-table-column
            v-else
            v-bind="column"
          >
            <template #default="scope">
              <FieldRenderer 
                :field="{ ...column, type: column.type || 'text', label: column.label }" 
                :model-value="scope.row[column.prop]" 
                mode="table" 
              />
            </template>
          </el-table-column>
        </template>

        <!-- Actions Column -->
        <el-table-column
          v-if="$slots.actions"
          label="操作"
          width="180"
          fixed="right"
        >
          <template #default="scope">
            <slot
              name="actions"
              :row="scope.row"
              :$index="scope.$index"
            />
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Pagination -->
    <div
      v-if="total > 0"
      class="pagination-container"
    >
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
    <div
      v-if="!loading && tableData.length === 0"
      class="empty-state"
    >
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
    align-items: center; // Ensure align with ColumnManager
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

.mobile-card-container {
  .mobile-card {
    background: #fff;
    margin-bottom: 12px;
    padding: 12px;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);

    .card-header-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-weight: bold;
    }
    
    .card-item {
      display: flex;
      margin-bottom: 4px;
      font-size: 14px;
      
      .label {
        color: #909399;
        width: 80px;
        flex-shrink: 0;
      }
      .value {
        color: #303133;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }

    .card-actions {
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid #EBEEF5;
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }
  }
}
</style>
