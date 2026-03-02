/**
 * useTableConfig composable tests
 */

import { describe, it, expect, beforeEach } from 'vitest'
import { useTableConfig, clearAllTableConfigCache, getTableConfigCache } from '@/composables/useTableConfig'

describe('useTableConfig', () => {
  beforeEach(() => {
    // Clear cache before each test
    clearAllTableConfigCache()
  })

  describe('initialization', () => {
    it('should initialize with default values', () => {
      const config = useTableConfig('test-table')

      expect(config.page.value).toBe(1)
      expect(config.pageSize.value).toBe(20)
      expect(config.total.value).toBe(0)
      expect(config.sortField.value).toBeUndefined()
      expect(config.sortOrder.value).toBe(null)
      expect(config.filters.value).toEqual({})
      expect(config.selectedRows.value).toEqual([])
      expect(config.expandedRows.value).toEqual([])
      expect(config.loading.value).toBe(false)
    })

    it('should accept custom options', () => {
      const config = useTableConfig('test-table', {
        defaultPageSize: 50,
        pageSizeOptions: [10, 50, 100],
        showPagination: false,
        showSelection: true,
        showIndex: true,
        rowKey: 'uuid'
      })

      expect(config.pageSize.value).toBe(50)
      expect(config.pageSizeOptions).toEqual([10, 50, 100])
      expect(config.showPagination).toBe(false)
      expect(config.showSelection).toBe(true)
      expect(config.showIndex).toBe(true)
    })
  })

  describe('pagination', () => {
    it('should handle page change', () => {
      const config = useTableConfig('test-table')

      config.handlePageChange(3)

      expect(config.page.value).toBe(3)
    })

    it('should handle page size change', () => {
      const config = useTableConfig('test-table')

      config.handleSizeChange(50)

      expect(config.pageSize.value).toBe(50)
      expect(config.page.value).toBe(1) // Should reset to page 1
    })

    it('should update total count', () => {
      const config = useTableConfig('test-table')

      config.setTotal(100)

      expect(config.total.value).toBe(100)
    })
  })

  describe('sorting', () => {
    it('should handle sort change', () => {
      const config = useTableConfig('test-table')

      config.handleSortChange({ prop: 'name', order: 'ascending' })

      expect(config.sortField.value).toBe('name')
      expect(config.sortOrder.value).toBe('asc')
    })

    it('should handle descending sort', () => {
      const config = useTableConfig('test-table')

      config.handleSortChange({ prop: 'createdAt', order: 'descending' })

      expect(config.sortField.value).toBe('createdAt')
      expect(config.sortOrder.value).toBe('desc')
    })

    it('should clear sort when order is null', () => {
      const config = useTableConfig('test-table')

      config.handleSortChange({ prop: 'name', order: 'ascending' })
      config.handleSortChange({ prop: 'name', order: null })

      expect(config.sortField.value).toBe('name')
      expect(config.sortOrder.value).toBe(null)
    })
  })

  describe('filters', () => {
    it('should set filter value', () => {
      const config = useTableConfig('test-table')

      config.setFilter('status', 'active')

      expect(config.filters.value.status).toBe('active')
      expect(config.page.value).toBe(1) // Should reset to page 1
    })

    it('should clear specific filter', () => {
      const config = useTableConfig('test-table')

      config.setFilter('status', 'active')
      config.setFilter('type', 'asset')
      config.clearFilter('status')

      expect(config.filters.value.status).toBeUndefined()
      expect(config.filters.value.type).toBe('asset')
    })

    it('should clear all filters', () => {
      const config = useTableConfig('test-table')

      config.setFilter('status', 'active')
      config.setFilter('type', 'asset')
      config.clearAllFilters()

      expect(config.filters.value).toEqual({})
    })

    it('should handle filter change with multiple filters', () => {
      const config = useTableConfig('test-table')

      config.handleFilterChange({ status: 'active', type: 'asset' })

      expect(config.filters.value).toEqual({ status: 'active', type: 'asset' })
    })
  })

  describe('row selection', () => {
    it('should handle selection change', () => {
      const config = useTableConfig('test-table')

      const rows = [
        { id: '1', name: 'Item 1' },
        { id: '2', name: 'Item 2' }
      ]

      config.handleSelectionChange(rows)

      expect(config.selectedRows.value).toEqual(rows)
      expect(config.hasSelection.value).toBe(true)
    })

    it('should clear selection', () => {
      const config = useTableConfig('test-table')

      config.selectedRows.value = [{ id: '1', name: 'Item 1' }]
      config.clearSelection()

      expect(config.selectedRows.value).toEqual([])
    })

    it('should toggle row selection', () => {
      const config = useTableConfig('test-table')

      const row = { id: '1', name: 'Item 1' }

      config.toggleRowSelection(row)

      expect(config.selectedRows.value).toHaveLength(1)

      config.toggleRowSelection(row)

      expect(config.selectedRows.value).toHaveLength(0)
    })

    it('should toggle all selection', () => {
      const config = useTableConfig('test-table')

      const rows = [
        { id: '1', name: 'Item 1' },
        { id: '2', name: 'Item 2' }
      ]

      config.toggleAllSelection(rows, true)

      expect(config.selectedRows.value).toHaveLength(2)

      config.toggleAllSelection(rows, false)

      expect(config.selectedRows.value).toHaveLength(0)
    })

    it('should auto-toggle all when not specified', () => {
      const config = useTableConfig('test-table')

      const rows = [
        { id: '1', name: 'Item 1' },
        { id: '2', name: 'Item 2' }
      ]

      // First call should select all (none selected initially)
      config.toggleAllSelection(rows)

      expect(config.selectedRows.value).toHaveLength(2)

      // Second call should deselect all
      config.toggleAllSelection(rows)

      expect(config.selectedRows.value).toHaveLength(0)
    })
  })

  describe('row expansion', () => {
    it('should handle expand change', () => {
      const config = useTableConfig('test-table')

      const row = { id: '1', name: 'Item 1' }
      const expanded = [row]

      config.handleExpandChange(row, expanded)

      expect(config.expandedRows.value).toEqual(expanded)
    })

    it('should toggle row expansion', () => {
      const config = useTableConfig('test-table')

      const row = { id: '1', name: 'Item 1' }

      config.toggleRowExpansion(row)

      expect(config.expandedRows.value).toHaveLength(1)

      config.toggleRowExpansion(row)

      expect(config.expandedRows.value).toHaveLength(0)
    })

    it('should clear all expanded rows', () => {
      const config = useTableConfig('test-table')

      config.expandedRows.value = [{ id: '1', name: 'Item 1' }]
      config.clearExpandRows()

      expect(config.expandedRows.value).toEqual([])
    })
  })

  describe('getRowKey', () => {
    it('should use default id property', () => {
      const config = useTableConfig('test-table')

      const row = { id: 'test-id', name: 'Test' }

      expect(config.getRowKey(row)).toBe('test-id')
    })

    it('should use custom rowKey function', () => {
      const config = useTableConfig('test-table', {
        rowKey: (row: any) => row.uuid
      })

      const row = { uuid: 'custom-id', name: 'Test' }

      expect(config.getRowKey(row)).toBe('custom-id')
    })

    it('should use custom rowKey string', () => {
      const config = useTableConfig('test-table', {
        rowKey: 'code'
      })

      const row = { code: 'CODE-001', name: 'Test' }

      expect(config.getRowKey(row)).toBe('CODE-001')
    })

    it('should fallback to JSON.stringify when no key found', () => {
      const config = useTableConfig('test-table')

      const row = { name: 'Test' }

      expect(config.getRowKey(row)).toBe(JSON.stringify(row))
    })
  })

  describe('getQueryParams', () => {
    it('should return basic pagination params', () => {
      const config = useTableConfig('test-table')

      const params = config.getQueryParams()

      expect(params).toEqual({
        page: 1,
        page_size: 20
      })
    })

    it('should include ordering when sorted', () => {
      const config = useTableConfig('test-table')

      config.handleSortChange({ prop: 'name', order: 'ascending' })

      let params = config.getQueryParams()
      expect(params.ordering).toBe('name')

      config.handleSortChange({ prop: 'createdAt', order: 'descending' })

      params = config.getQueryParams()
      expect(params.ordering).toBe('-createdAt')
    })

    it('should include filters', () => {
      const config = useTableConfig('test-table')

      config.setFilter('status', 'active')
      config.setFilter('type', 'asset')

      const params = config.getQueryParams()

      expect(params.status).toBe('active')
      expect(params.type).toBe('asset')
    })

    it('should exclude empty filter values', () => {
      const config = useTableConfig('test-table')

      config.setFilter('status', 'active')
      config.setFilter('search', '') // Empty string
      config.setFilter('type', null) // Null value

      const params = config.getQueryParams()

      expect(params.status).toBe('active')
      expect(params.search).toBeUndefined()
      expect(params.type).toBeUndefined()
    })
  })

  describe('caching', () => {
    it('should save and load configuration', () => {
      const config1 = useTableConfig('test-table')

      // Note: handleSizeChange and setFilter reset page to 1, so set page last
      config1.handleSizeChange(50)
      config1.setFilter('status', 'active')
      config1.handlePageChange(3) // Set page after other operations

      config1.saveToCache()

      const config2 = useTableConfig('test-table')
      const loaded = config2.loadFromCache()

      expect(loaded).toBeTruthy()
      expect(config2.page.value).toBe(3)
      expect(config2.pageSize.value).toBe(50)
      expect(config2.filters.value.status).toBe('active')
    })

    it('should get cached configuration without loading', () => {
      const config1 = useTableConfig('test-table')

      config1.handlePageChange(5)

      config1.saveToCache()

      const cached = getTableConfigCache('test-table')

      expect(cached).toEqual({
        page: 5,
        pageSize: 20,
        sortField: undefined,
        sortOrder: null,
        filters: {},
        selectedRows: [],
        expandedRows: []
      })
    })

    it('should reset configuration', () => {
      const config = useTableConfig('test-table')

      config.handlePageChange(5)
      config.setFilter('status', 'active')
      config.selectedRows.value = [{ id: '1' }]

      config.resetConfig()

      expect(config.page.value).toBe(1)
      expect(config.pageSize.value).toBe(20)
      expect(config.filters.value).toEqual({})
      expect(config.selectedRows.value).toEqual([])
    })

    it('should not restore selected/expanded rows from cache', () => {
      const config1 = useTableConfig('test-table')

      config1.selectedRows.value = [{ id: '1' }]
      config1.expandedRows.value = [{ id: '1' }]

      config1.saveToCache()

      const config2 = useTableConfig('test-table')
      config2.loadFromCache()

      // Selected and expanded rows should not be restored as data may have changed
      expect(config2.selectedRows.value).toEqual([])
      expect(config2.expandedRows.value).toEqual([])
    })

    it('should clear all cache', () => {
      const config1 = useTableConfig('table1')
      const config2 = useTableConfig('table2')

      config1.handlePageChange(3)
      config2.handlePageChange(5)

      config1.saveToCache()
      config2.saveToCache()

      clearAllTableConfigCache()

      expect(getTableConfigCache('table1')).toBeUndefined()
      expect(getTableConfigCache('table2')).toBeUndefined()
    })
  })

  describe('loading state', () => {
    it('should set loading state', () => {
      const config = useTableConfig('test-table')

      config.setLoading(true)

      expect(config.loading.value).toBe(true)

      config.setLoading(false)

      expect(config.loading.value).toBe(false)
    })
  })

  describe('computed properties', () => {
    it('should calculate hasSelection correctly', () => {
      const config = useTableConfig('test-table')

      expect(config.hasSelection.value).toBe(false)

      config.selectedRows.value = [{ id: '1' }]

      expect(config.hasSelection.value).toBe(true)
    })

    it('should calculate isIndeterminate correctly', () => {
      const config = useTableConfig('test-table')

      config.selectedRows.value = [{ id: '1' }]

      // With selections but not all selected, should be indeterminate
      expect(config.isIndeterminate.value).toBe(true)
    })
  })
})
