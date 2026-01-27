import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { ColumnItem } from './useColumnConfig'

/**
 * Table configuration types
 */

export interface TableConfig {
  page: number
  pageSize: number
  sortField?: string
  sortOrder?: 'asc' | 'desc' | null
  filters: Record<string, any>
  selectedRows: any[]
  expandedRows: any[]
}

export interface TableOptions {
  defaultPageSize?: number
  pageSizeOptions?: number[]
  showPagination?: boolean
  showSelection?: boolean
  showIndex?: boolean
  rowKey?: string | ((row: any) => string)
}

const DEFAULT_PAGE_SIZE_OPTIONS = [10, 20, 50, 100]
const DEFAULT_PAGE_SIZE = 20

/**
 * Table config cache for persisting table state across navigation
 */
const tableConfigCache = new Map<string, TableConfig>()

/**
 * useTableConfig - Composable for managing table state and configuration
 *
 * Features:
 * - Pagination management
 * - Sort management
 * - Filter management
 * - Row selection management
 * - Row expansion management
 * - Table state persistence
 */
export function useTableConfig(tableKey: string, options: TableOptions = {}) {
  const {
    defaultPageSize = DEFAULT_PAGE_SIZE,
    pageSizeOptions = DEFAULT_PAGE_SIZE_OPTIONS,
    showPagination = true,
    showSelection = false,
    showIndex = false,
    rowKey = 'id'
  } = options

  // Table state
  const page = ref(1)
  const pageSize = ref(defaultPageSize)
  const total = ref(0)
  const sortField = ref<string | undefined>(undefined)
  const sortOrder = ref<'asc' | 'desc' | null>(null)
  const filters = ref<Record<string, any>>({})
  const selectedRows = ref<any[]>([])
  const expandedRows = ref<any[]>([])
  const loading = ref(false)

  /**
   * Get unique row identifier
   */
  const getRowKey = (row: any): string => {
    if (typeof rowKey === 'function') {
      return rowKey(row)
    }
    return row[rowKey] || JSON.stringify(row)
  }

  /**
   * Computed properties
   */
  const hasSelection = computed(() => selectedRows.value.length > 0)
  const allSelected = computed(() => {
    // This would need to be compared with current page data
    return false
  })
  const isIndeterminate = computed(() => {
    return hasSelection.value && !allSelected.value
  })

  /**
   * Load table configuration from cache
   */
  const loadFromCache = (): TableConfig | null => {
    const cached = tableConfigCache.get(tableKey)
    if (cached) {
      page.value = cached.page
      pageSize.value = cached.pageSize
      sortField.value = cached.sortField
      sortOrder.value = cached.sortOrder
      filters.value = { ...cached.filters }
      // Don't restore selected/expanded rows as data may have changed
    }
    return cached || null
  }

  /**
   * Save table configuration to cache
   */
  const saveToCache = () => {
    tableConfigCache.set(tableKey, {
      page: page.value,
      pageSize: pageSize.value,
      sortField: sortField.value,
      sortOrder: sortOrder.value,
      filters: { ...filters.value },
      selectedRows: [...selectedRows.value],
      expandedRows: [...expandedRows.value]
    })
  }

  /**
   * Reset table configuration to defaults
   */
  const resetConfig = () => {
    page.value = 1
    pageSize.value = defaultPageSize
    sortField.value = undefined
    sortOrder.value = null
    filters.value = {}
    selectedRows.value = []
    expandedRows.value = []
    tableConfigCache.delete(tableKey)
  }

  /**
   * Handle page change
   */
  const handlePageChange = (newPage: number) => {
    page.value = newPage
    saveToCache()
  }

  /**
   * Handle page size change
   */
  const handleSizeChange = (newPageSize: number) => {
    pageSize.value = newPageSize
    page.value = 1 // Reset to first page when changing size
    saveToCache()
  }

  /**
   * Handle sort change
   */
  const handleSortChange = ({ prop, order }: { prop: string; order: string | null }) => {
    sortField.value = prop
    sortOrder.value = order ? (order === 'ascending' ? 'asc' : 'desc') : null
    saveToCache()
  }

  /**
   * Handle filter change
   */
  const handleFilterChange = (newFilters: Record<string, any>) => {
    filters.value = { ...newFilters }
    page.value = 1 // Reset to first page when filtering
    saveToCache()
  }

  /**
   * Set a single filter value
   */
  const setFilter = (key: string, value: any) => {
    filters.value = { ...filters.value, [key]: value }
    page.value = 1
    saveToCache()
  }

  /**
   * Clear a specific filter
   */
  const clearFilter = (key: string) => {
    const newFilters = { ...filters.value }
    delete newFilters[key]
    filters.value = newFilters
    page.value = 1
    saveToCache()
  }

  /**
   * Clear all filters
   */
  const clearAllFilters = () => {
    filters.value = {}
    page.value = 1
    saveToCache()
  }

  /**
   * Handle row selection
   */
  const handleSelectionChange = (selection: any[]) => {
    selectedRows.value = selection
  }

  /**
   * Toggle row selection
   */
  const toggleRowSelection = (row: any, selected?: boolean) => {
    // This would be called from el-table ref
    const rowKey = getRowKey(row)
    const index = selectedRows.value.findIndex(r => getRowKey(r) === rowKey)

    if (selected === undefined) {
      // Toggle
      if (index >= 0) {
        selectedRows.value.splice(index, 1)
      } else {
        selectedRows.value.push(row)
      }
    } else if (selected && index < 0) {
      selectedRows.value.push(row)
    } else if (!selected && index >= 0) {
      selectedRows.value.splice(index, 1)
    }
  }

  /**
   * Select all rows on current page
   */
  const toggleAllSelection = (rows: any[], selected?: boolean) => {
    if (selected === undefined) {
      // Toggle based on current state
      const allSelected = rows.every(row =>
        selectedRows.value.some(r => getRowKey(r) === getRowKey(row))
      )
      selected = !allSelected
    }

    if (selected) {
      // Add all rows that aren't already selected
      rows.forEach(row => {
        const rowKey = getRowKey(row)
        if (!selectedRows.value.some(r => getRowKey(r) === rowKey)) {
          selectedRows.value.push(row)
        }
      })
    } else {
      // Remove all current page rows from selection
      const pageRowKeys = new Set(rows.map(r => getRowKey(r)))
      selectedRows.value = selectedRows.value.filter(r => !pageRowKeys.has(getRowKey(r)))
    }
  }

  /**
   * Clear all selections
   */
  const clearSelection = () => {
    selectedRows.value = []
  }

  /**
   * Handle row expansion
   */
  const handleExpandChange = (row: any, expandedRows: any[]) => {
    expandedRows.value = expandedRows
  }

  /**
   * Toggle row expansion
   */
  const toggleRowExpansion = (row: any, expanded?: boolean) => {
    const rowKey = getRowKey(row)
    const index = expandedRows.value.findIndex(r => getRowKey(r) === rowKey)

    if (expanded === undefined) {
      // Toggle
      if (index >= 0) {
        expandedRows.value.splice(index, 1)
      } else {
        expandedRows.value.push(row)
      }
    } else if (expanded && index < 0) {
      expandedRows.value.push(row)
    } else if (!expanded && index >= 0) {
      expandedRows.value.splice(index, 1)
    }
  }

  /**
   * Clear all expansions
   */
  const clearExpandRows = () => {
    expandedRows.value = []
  }

  /**
   * Get query parameters for API request
   */
  const getQueryParams = () => {
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize.value
    }

    if (sortField.value) {
      params.ordering = sortOrder.value === 'desc' ? `-${sortField.value}` : sortField.value
    }

    // Add filters
    Object.entries(filters.value).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        params[key] = value
      }
    })

    return params
  }

  /**
   * Set loading state
   */
  const setLoading = (value: boolean) => {
    loading.value = value
  }

  /**
   * Set total count
   */
  const setTotal = (count: number) => {
    total.value = count
  }

  // Watch for changes to auto-save cache
  watch([page, pageSize, sortField, sortOrder, filters], () => {
    saveToCache()
  })

  return {
    // State
    page,
    pageSize,
    total,
    sortField,
    sortOrder,
    filters,
    selectedRows,
    expandedRows,
    loading,
    hasSelection,
    allSelected,
    isIndeterminate,

    // Computed
    pageSizeOptions,
    showPagination,
    showSelection,
    showIndex,

    // Methods
    loadFromCache,
    saveToCache,
    resetConfig,
    handlePageChange,
    handleSizeChange,
    handleSortChange,
    handleFilterChange,
    setFilter,
    clearFilter,
    clearAllFilters,
    handleSelectionChange,
    toggleRowSelection,
    toggleAllSelection,
    clearSelection,
    handleExpandChange,
    toggleRowExpansion,
    clearExpandRows,
    getQueryParams,
    setLoading,
    setTotal,
    getRowKey
  }
}

/**
 * Clear all cached table configurations
 */
export function clearAllTableConfigCache() {
  tableConfigCache.clear()
}

/**
 * Get cached table configuration
 */
export function getTableConfigCache(tableKey: string): TableConfig | undefined {
  return tableConfigCache.get(tableKey)
}
