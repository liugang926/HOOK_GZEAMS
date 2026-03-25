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

import { ref, computed, onMounted, onUnmounted, watch, useSlots } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessageBox } from 'element-plus'
import type { TableColumn, SearchField, ColumnItem } from '@/types/common'
import { formatDate } from '@/utils/dateFormat'
import ColumnManager from '@/components/common/ColumnManager.vue'
import FieldRenderer from '@/components/common/FieldRenderer.vue'
import ObjectAvatar from '@/components/common/ObjectAvatar.vue'
import { dynamicApi } from '@/api/dynamic'
import { extractLayoutConfig } from '@/adapters/layoutAdapter'
import { buildColumnsFromLayout } from '@/adapters/listColumnAdapter'
import {
  applyBaseListFieldDefinitions,
  buildBaseListRequestParams,
  buildBaseListSearchResetPatch,
  getBaseListSearchFieldKey,
  needsBaseListFieldDefinitions,
  normalizeBaseListColumnSaveInput,
  normalizeBaseListSearchField,
  prepareBaseListColumns,
  resolveBaseListResponsePayload,
} from './baseListPageModel'
import {
  applyBaseListColumnWidth,
  reorderBaseListColumnsAfterDrag,
} from './baseListPageColumnModel'
import {
  buildBaseListRendererField,
  filterBaseListDataColumns,
  isBaseListActionColumn,
  resolveBaseListColumnDisplayValue,
  resolveBaseListColumnValue,
  resolveBaseListSlotName,
} from './baseListPageRenderModel'
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
  /** The business object code, used to scope user preferences (optional) */
  objectCode?: string
  /** Associated icon for the object avatar */
  objectIcon?: string
  /** Whether to show index column */
  showIndex?: boolean
  /** Where toolbar actions should be rendered */
  toolbarPlacement?: 'header' | 'table'
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  searchFields: () => [],
  selectable: true,
  defaultPageSize: 20,
  pageSizes: () => [10, 20, 50, 100],
  showIndex: true,
  batchActions: () => [],
  toolbarPlacement: 'header'
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

// Get current route for watching navigation changes
const route = useRoute()
const { t } = useI18n()

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
import { useColumnConfig } from '@/composables/useColumnConfig'
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

/** Slots */
const slots = useSlots()

/** Field definitions (for static lists to enrich column types) */
const fieldDefinitions = ref<any[]>([])

/** Dynamic Actions */
const objectActions = ref<any[]>([])
import { getBusinessObject, getFieldDefinitions } from '@/api/system'
import { useAction } from '@/components/engine/hooks/useAction' // Adjust path if needed

const { executeAction } = useAction()

const handleDynamicAction = async (action: any) => {
    await executeAction(action, { formData: { selectedRows: selectedRows.value } })
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

/** Whether the main action toolbar should be rendered */
const shouldRenderToolbar = computed(() => {
  return Boolean(slots.toolbar) || objectActions.value.length > 0 || activeColumns.value.length > 0
})

/** Pagination layout */
const paginationLayout = computed(() => {
  return 'total, sizes, prev, pager, next, jumper'
})

const normalizedSearchFields = computed(() => {
  return (props.searchFields || [])
    .map(normalizeBaseListSearchField)
    .filter(Boolean) as SearchField[]
})

const getSearchFieldKey = getBaseListSearchFieldKey

/** Visible search fields (non-expanded shows first 4) */
const visibleSearchFields = computed(() => {
  if (searchExpanded.value) {
    return normalizedSearchFields.value
  }
  return normalizedSearchFields.value.slice(0, 4)
})

/** Whether expand button is needed */
const needExpand = computed(() => {
  return normalizedSearchFields.value.length > 4
})

/** Filtered Columns for Table Render */
const visibleTableColumns = computed(() => {
  return activeColumns.value.filter(col => col.visible !== false)
})

const getColumnValue = (row: any, column: TableColumn) => {
  return resolveBaseListColumnValue(row, column)
}

const getColumnDisplayValue = (row: any, column: TableColumn) => {
  return resolveBaseListColumnDisplayValue(row, column)
}

const resolveSlotName = (column: TableColumn) => {
  return resolveBaseListSlotName(column, slots)
}

const isActionColumn = (column: TableColumn) => {
  return isBaseListActionColumn(column, slots)
}

const hasActionsColumn = computed(() => {
  return activeColumns.value.some(isActionColumn)
})

const visibleDataColumns = computed(() => {
  return filterBaseListDataColumns(visibleTableColumns.value, slots)
})

const getColumnField = (column: TableColumn) => {
  return buildBaseListRendererField(column)
}

const prepareBaseColumns = (cols: TableColumn[]) => {
  return prepareBaseListColumns(applyBaseListFieldDefinitions(cols, fieldDefinitions.value))
}

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
    const params = buildBaseListRequestParams({
      currentPage: currentPage.value,
      pageSize: pageSize.value,
      visibleColumns: visibleTableColumns.value,
      searchForm: searchForm.value,
      sortState: sortState.value,
    })
    const response = await props.api(params)
    const payload = resolveBaseListResponsePayload(response)
    tableData.value = payload.tableData
    total.value = payload.total
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

const getSearchFieldValue = (key: string) => {
  if (!key) return undefined
  return searchForm.value[key]
}

const setSearchFieldValue = (key: string, value: any) => {
  if (!key) return
  searchForm.value[key] = value
}

/**
 * Handle reset
 */
const handleReset = () => {
  Object.assign(searchForm.value, buildBaseListSearchResetPatch(normalizedSearchFields.value))
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
    try {
      await ElMessageBox.confirm(
        action.confirmMessage,
        action.label || t('common.actions.confirm'),
        {
          type: 'warning',
          confirmButtonText: t('common.actions.confirm'),
          cancelButtonText: t('common.actions.cancel')
        }
      )
    } catch {
      return
    }
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
const handleColumnSave = async (newColumns: ColumnItem[]) => {
  const normalizedColumns = normalizeBaseListColumnSaveInput(newColumns)
  activeColumns.value = normalizedColumns
  if (columnConfig) {
      await columnConfig.saveConfig(normalizedColumns as any)
  }
}

const handleColumnReset = async () => {
    if (columnConfig) {
        await columnConfig.resetConfig()
        activeColumns.value = columnConfig.applyConfig(prepareBaseListColumns(props.tableColumns) as any) as any
    } else {
        activeColumns.value = prepareBaseListColumns(props.tableColumns)
    }
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
      if (evt.oldIndex === evt.newIndex) return

      const nextColumns = reorderBaseListColumnsAfterDrag({
        activeColumns: activeColumns.value,
        visibleColumns: visibleTableColumns.value,
        oldIndex: evt.oldIndex,
        newIndex: evt.newIndex,
        selectable: props.selectable,
        showIndex: props.showIndex,
      })

      if (!nextColumns) return

      activeColumns.value = nextColumns
      if (columnConfig) {
        columnConfig.saveConfig(activeColumns.value as any)
      }
    }
  })
}

/**
 * Handle manual column resize
 */
const handleHeaderDragend = (newWidth: number, _oldWidth: number, column: any, _event: MouseEvent) => {
   const nextColumns = applyBaseListColumnWidth(activeColumns.value, column.property, newWidth)
   if (nextColumns === activeColumns.value) return

   activeColumns.value = nextColumns
   if (columnConfig) {
     columnConfig.saveConfig(activeColumns.value as any)
   }
}

const handleRefreshEvent = () => {
  fetchData()
}

// ============================================================================
// Lifecycle
// ============================================================================

onMounted(async () => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
  window.addEventListener('refresh-base-list', handleRefreshEvent)

  // Initialize search form default values
  normalizedSearchFields.value.forEach(field => {
    const key = field.prop || field.field
    if (!key || field.defaultValue === undefined) return
    searchForm.value[key] = field.defaultValue
  })

  // Initialize columns with persistence
  // NOTE:
  // Parent pages (e.g. DynamicListPage) may provide columns asynchronously.
  // Avoid capturing an early empty snapshot that can race with later updates.
  const defaultCols = props.tableColumns

  if (props.objectCode && defaultCols.length > 0) {
      // If tableColumns are already provided (from DynamicListPage metadata),
      // use them directly without fetching additional fields
      // This avoids duplicate API calls and respects the metadata-driven columns
      try {
          // Still fetch dynamic actions (buttons, etc.)
          const res: any = await getBusinessObject(props.objectCode)
          objectActions.value = res.data?.actions || res.actions || []
      } catch (e) {
          console.warn('Failed to load object actions', e)
      }

      if (needsBaseListFieldDefinitions(defaultCols)) {
        try {
          const fieldRes: any = await getFieldDefinitions(props.objectCode)
          fieldDefinitions.value = fieldRes?.results || fieldRes?.data || fieldRes || []
        } catch (e) {
          fieldDefinitions.value = []
        }
      }

      // Use the provided columns directly
      const latestDefaultCols = props.tableColumns
      if (columnConfig) {
          await columnConfig.fetchConfig()
          activeColumns.value = columnConfig.applyConfig(prepareBaseColumns(latestDefaultCols) as any) as any
      } else {
          activeColumns.value = prepareBaseColumns(latestDefaultCols)
      }
  } else if (props.objectCode) {
      // No columns provided, try to fetch from field definitions
      // This is for pages that don't have pre-defined columns
      try {
          // 1. Fetch dynamic actions
          const res: any = await getBusinessObject(props.objectCode)
          objectActions.value = res.data?.actions || res.actions || []

          let columnsFromLayout: TableColumn[] = []
          try {
              const runtime = await dynamicApi.getRuntime(props.objectCode, 'list')
              const fieldsPayload = runtime?.fields || {}
              const editable = fieldsPayload.editableFields || fieldsPayload.editable_fields || fieldsPayload.fields || []
              const reverse = fieldsPayload.reverseRelations || fieldsPayload.reverse_relations || []
              const fieldDefs = [...editable, ...reverse]
              const layoutConfig = extractLayoutConfig(runtime?.layout)
              const layoutColumns = layoutConfig?.columns || []
              if (Array.isArray(layoutColumns) && layoutColumns.length > 0) {
                  columnsFromLayout = buildColumnsFromLayout(layoutColumns, fieldDefs)
              }
          } catch (e) {
              columnsFromLayout = []
          }

          const latestDefaultCols = props.tableColumns
          if (latestDefaultCols.length > 0) {
              // Parent provided canonical columns after mount; always prefer these
              if (columnConfig) {
                  await columnConfig.fetchConfig()
                  activeColumns.value = columnConfig.applyConfig(prepareBaseColumns(latestDefaultCols) as any) as any
              } else {
                  activeColumns.value = prepareBaseColumns(latestDefaultCols)
              }
          } else if (columnsFromLayout.length > 0) {
              const baseCols = prepareBaseListColumns(columnsFromLayout)
              if (columnConfig) {
                  await columnConfig.fetchConfig()
                  activeColumns.value = columnConfig.applyConfig(baseCols as any) as any
              } else {
                  activeColumns.value = baseCols
              }
          } else {
              console.warn('List layout columns missing; using default columns only')
              activeColumns.value = prepareBaseColumns(props.tableColumns)
          }
      } catch (e: any) {
          console.warn('Failed to load object metadata', e)
          activeColumns.value = prepareBaseColumns(props.tableColumns)
      }
  } else {
      // No object code, just use defaults
      if (columnConfig) {
          await columnConfig.fetchConfig()
          activeColumns.value = columnConfig.applyConfig(prepareBaseColumns(props.tableColumns) as any) as any
      } else {
          activeColumns.value = prepareBaseColumns(props.tableColumns)
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
  window.removeEventListener('refresh-base-list', handleRefreshEvent)
})

// Watch for route changes to refresh data when navigating back from form pages
// This handles the case where a user creates/edits a record and returns to the list
watch(() => route.path, (newPath, oldPath) => {
  // Only refresh if we're navigating to the same route (component reuse)
  // This happens when router.push() is called with the same route path
  if (oldPath && newPath === oldPath) {
    // Same route path, refresh data
    fetchData()
  }
}, { flush: 'post' })

// Watch for external data changes
watch(() => props.tableColumns, (newCols) => {
    // Re-apply config to new columns definitions if possible
    const defaultCols = prepareBaseColumns(newCols)
    if (columnConfig) {
        activeColumns.value = columnConfig.applyConfig(defaultCols as any) as any
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
    <!-- Unified List Card -->
    <div class="list-card">
      <!-- Page Header -->
      <div
        v-if="title"
        class="page-header"
      >
        <div class="page-title-group">
          <ObjectAvatar
            v-if="objectCode"
            :object-code="objectCode"
            :icon="objectIcon"
            size="md"
            class="list-page-avatar"
          />
          <h2 class="page-title">
            {{ title }}
          </h2>
          <span
            v-if="total > 0"
            class="record-count"
          >
            {{ total }} {{ $t('common.messages.records') }}
          </span>
        </div>
        <div class="page-toolbar">
          <template v-if="props.toolbarPlacement === 'header' && shouldRenderToolbar">
            <slot
              name="toolbar"
              :selected-rows="selectedRows"
              :has-selection="hasSelection"
            />

            <el-button
              v-for="action in objectActions"
              :key="action.code"
              :type="action.type === 'primary' ? 'primary' : 'default'"
              @click="handleDynamicAction(action)"
            >
              {{ action.label }}
            </el-button>

            <ColumnManager
              :columns="activeColumns"
              :object-code="objectCode"
              @save="handleColumnSave"
              @reset="handleColumnReset"
            />
          </template>
        </div>
      </div>

      <!-- Search Form -->
      <div
        v-if="normalizedSearchFields.length > 0"
        class="search-form-container"
      >
        <el-form
          :model="searchForm"
          class="search-form"
          label-width="auto"
          label-position="right"
        >
          <div class="search-grid">
            <template
              v-for="field in visibleSearchFields"
              :key="getSearchFieldKey(field)"
            >
              <el-form-item
                v-if="!field.type || field.type === 'text'"
                :label="field.label"
              >
                <el-input
                  v-model="searchForm[getSearchFieldKey(field)]"
                  :placeholder="field.placeholder || $t('common.placeholders.input', { field: field.label })"
                  clearable
                  @keyup.enter="handleSearch"
                />
              </el-form-item>

              <el-form-item
                v-else-if="field.type === 'select'"
                :label="field.label"
              >
                <el-select
                  v-model="searchForm[getSearchFieldKey(field)]"
                  :placeholder="field.placeholder || $t('common.placeholders.select', { field: field.label })"
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

              <el-form-item
                v-else-if="field.type === 'dateRange'"
                :label="field.label"
              >
                <el-date-picker
                  v-model="searchForm[getSearchFieldKey(field)]"
                  type="daterange"
                  range-separator="-"
                  :start-placeholder="$t('common.placeholders.startDate')"
                  :end-placeholder="$t('common.placeholders.endDate')"
                  value-format="YYYY-MM-DD"
                />
              </el-form-item>

              <el-form-item
                v-else-if="field.type === 'date'"
                :label="field.label"
              >
                <el-date-picker
                  v-model="searchForm[getSearchFieldKey(field)]"
                  type="date"
                  :placeholder="field.placeholder || $t('common.placeholders.select', { field: field.label })"
                  value-format="YYYY-MM-DD"
                />
              </el-form-item>

              <el-form-item
                v-else-if="field.type === 'month'"
                :label="field.label"
              >
                <el-date-picker
                  v-model="searchForm[getSearchFieldKey(field)]"
                  type="month"
                  :placeholder="field.placeholder || $t('common.placeholders.select', { field: field.label })"
                  value-format="YYYY-MM"
                />
              </el-form-item>

              <el-form-item
                v-else-if="field.type === 'year'"
                :label="field.label"
              >
                <el-date-picker
                  v-model="searchForm[getSearchFieldKey(field)]"
                  type="year"
                  :placeholder="field.placeholder || $t('common.placeholders.select', { field: field.label })"
                  value-format="YYYY"
                />
              </el-form-item>

              <el-form-item
                v-else-if="field.type === 'numberRange'"
                :label="field.label"
              >
                <div class="number-range">
                  <el-input
                    v-model="searchForm[`${field.prop}_min`]"
                    :placeholder="$t('common.placeholders.minValue')"
                  />
                  <span class="separator">-</span>
                  <el-input
                    v-model="searchForm[`${field.prop}_max`]"
                    :placeholder="$t('common.placeholders.maxValue')"
                  />
                </div>
              </el-form-item>

              <el-form-item
                v-else-if="field.type === 'slot'"
                :label="field.label"
              >
                <slot
                  :name="`search-${field.prop}`"
                  :field="field"
                  :form="searchForm"
                  :get-value="getSearchFieldValue"
                  :set-value="setSearchFieldValue"
                  :search="handleSearch"
                  :reset="handleReset"
                />
              </el-form-item>
            </template>
          </div>

          <div class="search-toolbar-row">
            <ul class="search-toolbar-list">
              <li class="search-toolbar-list__item search-toolbar-list__item--left">
                <div class="search-actions">
                  <el-button
                    type="primary"
                    @click="handleSearch"
                  >
                    {{ $t('common.actions.search') }}
                  </el-button>
                  <el-button @click="handleReset">
                    {{ $t('common.actions.reset') }}
                  </el-button>
                  <el-button
                    v-if="needExpand"
                    link
                    type="primary"
                    @click="toggleSearchExpand"
                  >
                    {{ searchExpanded ? $t('common.actions.collapse') : $t('common.actions.expand') }}
                    <el-icon>
                      <component :is="searchExpanded ? 'arrow-up' : 'arrow-down'" />
                    </el-icon>
                  </el-button>
                </div>
              </li>

              <li
                v-if="props.toolbarPlacement === 'table' && shouldRenderToolbar"
                class="search-toolbar-list__item search-toolbar-list__item--right"
              >
                <slot
                  name="toolbar"
                  :selected-rows="selectedRows"
                  :has-selection="hasSelection"
                />

                <el-button
                  v-for="action in objectActions"
                  :key="action.code"
                  :type="action.type === 'primary' ? 'primary' : 'default'"
                  @click="handleDynamicAction(action)"
                >
                  {{ action.label }}
                </el-button>

                <ColumnManager
                  :columns="activeColumns"
                  :object-code="objectCode"
                  @save="handleColumnSave"
                  @reset="handleColumnReset"
                />
              </li>
            </ul>
          </div>
        </el-form>
      </div>

      <div
        v-if="props.toolbarPlacement === 'table' && shouldRenderToolbar && normalizedSearchFields.length === 0"
        class="table-toolbar"
      >
        <slot
          name="toolbar"
          :selected-rows="selectedRows"
          :has-selection="hasSelection"
        />

        <el-button
          v-for="action in objectActions"
          :key="action.code"
          :type="action.type === 'primary' ? 'primary' : 'default'"
          @click="handleDynamicAction(action)"
        >
          {{ action.label }}
        </el-button>

        <ColumnManager
          :columns="activeColumns"
          :object-code="objectCode"
          @save="handleColumnSave"
          @reset="handleColumnReset"
        />
      </div>

      <!-- Batch Actions Toolbar -->
      <div
        v-if="hasBatchActions && hasSelection"
        class="batch-toolbar"
      >
        <span class="selection-info">{{ $t('common.messages.selected', { count: selectedRows.length }) }}</span>
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
                v-for="col in visibleDataColumns.slice(0, 4)"
                :key="col.prop"
                class="card-item"
              >
                <span class="label">{{ col.label }}:</span>
                <span class="value">
                  <template v-if="resolveSlotName(col)">
                    <slot
                      :name="resolveSlotName(col)"
                      :row="row"
                      :column="col"
                      :index="index"
                    />
                  </template>
                  <template v-else>
                    <template v-if="col.format">
                      {{ getColumnDisplayValue(row, col) }}
                    </template>
                    <FieldRenderer 
                      v-else
                      :field="getColumnField(col)" 
                      :model-value="getColumnValue(row, col)" 
                      mode="table" 
                    />
                  </template>
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
                :index="index"
              />
            </div>
          </div>
          <el-empty
            v-if="tableData.length === 0"
            :description="$t('common.messages.noData')"
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
              :description="$t('common.messages.noData')"
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
            :label="$t('common.table.index')"
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
              v-if="resolveSlotName(column)"
              v-bind="column"
            >
              <template #default="scope">
                <slot
                  :name="resolveSlotName(column)"
                  :row="scope.row"
                  :column="column"
                  :index="scope.$index"
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
                  {{ getColumnDisplayValue(scope.row, column) }}
                </el-tag>
              </template>
            </el-table-column>

            <!-- Date Column -->
            <el-table-column
              v-else-if="column.dateFormatter"
              v-bind="column"
            >
              <template #default="scope">
                {{ formatDate(getColumnValue(scope.row, column), column.dateFormatter) }}
              </template>
            </el-table-column>

            <!-- Custom Format Column -->
            <el-table-column
              v-else-if="column.format"
              v-bind="column"
            >
              <template #default="scope">
                {{ getColumnDisplayValue(scope.row, column) }}
              </template>
            </el-table-column>

            <!-- Standard Column using FieldRenderer -->
            <el-table-column
              v-else
              v-bind="column"
            >
              <template #default="scope">
                <FieldRenderer 
                  :field="getColumnField(column)" 
                  :model-value="getColumnValue(scope.row, column)" 
                  mode="table" 
                />
              </template>
            </el-table-column>
          </template>

          <!-- Actions Column -->
          <el-table-column
            v-if="$slots.actions && !hasActionsColumn"
            :label="$t('common.table.operations')"
            width="180"
            fixed="right"
          >
            <template #default="scope">
              <slot
                name="actions"
                :row="scope.row"
                :index="scope.$index"
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
    </div><!-- end .list-card -->
  </div>
</template>

<style scoped lang="scss">
@use '@/styles/variables.scss' as *;

.base-list-page {
  padding: $spacing-lg;
  background-color: $bg-body;
  min-height: 100%;
}

/* ==== Unified Card ==== */
.list-card {
  background-color: $bg-card;
  border: 1px solid rgba(148, 163, 184, 0.16);
  border-radius: 22px;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

/* ==== Page Header ==== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 22px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.14);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 252, 0.92));

  .page-title-group {
    display: flex;
    align-items: baseline;
    gap: 12px;
  }

  .page-title {
    margin: 0;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: $text-main;
  }

  .record-count {
    font-size: 13px;
    color: $text-secondary;
    font-weight: 400;
  }

  .page-toolbar {
    display: flex;
    gap: 10px;
    align-items: center;
    flex-wrap: wrap;
  }
}

/* ==== Search ==== */
.search-form-container {
  padding: 18px 22px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);

  .search-form {
    .search-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 0 16px;

      @media (max-width: 1200px) {
        grid-template-columns: repeat(3, 1fr);
      }
      @media (max-width: 900px) {
        grid-template-columns: repeat(2, 1fr);
      }
      @media (max-width: 600px) {
        grid-template-columns: 1fr;
      }
    }

    :deep(.el-form-item) {
      margin-bottom: 14px;
    }

    .search-toolbar-row {
      padding-top: 6px;
    }

    .search-toolbar-list {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      width: 100%;
      margin: 0;
      padding: 0;
      list-style: none;
      flex-wrap: wrap;

      @media (max-width: 1200px) {
        align-items: flex-start;
      }
    }

    .search-toolbar-list__item {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
      flex-wrap: wrap;
    }

    .search-toolbar-list__item--right {
      margin-left: auto;
      justify-content: flex-end;

      @media (max-width: 1200px) {
        width: 100%;
        margin-left: 0;
        justify-content: flex-start;
      }
    }

    .search-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }
  }
}

.number-range {
  display: flex;
  align-items: center;
  gap: $spacing-sm;

  .el-input {
    width: 120px;
  }

  .separator {
    color: $text-secondary;
  }
}

/* ==== Table Toolbar ==== */
.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 0 22px 18px;
  background: linear-gradient(180deg, #ffffff 0%, #fbfdff 100%);
  flex-wrap: wrap;
}

/* ==== Batch Toolbar ==== */
.batch-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 22px;
  background: linear-gradient(180deg, rgba(59, 130, 246, 0.08), rgba(255, 255, 255, 0.92));
  border-bottom: 1px solid rgba(59, 130, 246, 0.14);
  flex-wrap: wrap;

  .selection-info {
    margin-right: 10px;
    font-size: 14px;
    color: $primary-color;
    font-weight: 500;
  }
}

/* ==== Table ==== */
.table-container {
  overflow: auto;

  :deep(.el-table) {
    --el-table-border-color: rgba(148, 163, 184, 0.14);
    --el-table-header-bg-color: #f8fafc;
    --el-table-row-hover-bg-color: rgba(37, 99, 235, 0.03);

    /* Compact rows */
    .el-table__row {
      td {
        padding: 10px 0;
      }
    }

    /* Header */
    th.el-table__cell {
      color: $text-main;
      font-weight: 700;
      font-size: 13px;
      letter-spacing: 0.3px;
      padding: 12px 0;
      border-bottom: 2px solid $border-color;
    }

    /* Row hover */
    .el-table__body tr:hover > td {
      background-color: rgba(37, 99, 235, 0.03) !important;
    }

    /* Alternating rows */
    .el-table__body tr.el-table__row--striped td {
      background-color: #fafbfc;
    }

    /* Cell text */
    td .cell {
      font-size: 14px;
      color: $text-regular;
    }
  }
}

/* ==== Pagination ==== */
.pagination-container {
  display: flex;
  justify-content: flex-end;
  padding: 16px 22px;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(248, 250, 252, 0.72);
}

/* ==== Mobile Cards ==== */
.mobile-card-container {
  padding: 18px;

  .mobile-card {
    background: $bg-card;
    margin-bottom: 12px;
    padding: 14px;
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 18px;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);

    .card-header-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: $spacing-sm;
      font-weight: 600;
    }
    
    .card-item {
      display: flex;
      margin-bottom: $spacing-xs;
      font-size: 14px;
      
      .label {
        color: $text-secondary;
        width: 80px;
        flex-shrink: 0;
      }
      .value {
        color: $text-main;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }

    .card-actions {
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid $border-color;
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }
  }
}
</style>
