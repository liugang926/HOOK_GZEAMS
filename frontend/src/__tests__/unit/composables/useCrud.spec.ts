/**
 * useCrud composable tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useCrud } from '@/composables/useCrud'
import { ElMessage, ElMessageBox } from 'element-plus'

// Mock Element Plus components
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

describe('useCrud', () => {
  let mockApi: any

  beforeEach(() => {
    vi.clearAllMocks()

    // Mock API
    mockApi = {
      list: vi.fn(),
      delete: vi.fn(),
      batchDelete: vi.fn(),
      export: vi.fn()
    }

    // Mock ElMessageBox.confirm to resolve by default
    ;(ElMessageBox.confirm as any).mockResolvedValue('confirm')
  })

  describe('fetchList', () => {
    it('should fetch list with results format', async () => {
      const mockData = {
        results: [
          { id: '1', name: 'Item 1' },
          { id: '2', name: 'Item 2' }
        ],
        count: 2
      }

      mockApi.list.mockResolvedValue(mockData)

      const crud = useCrud({ name: 'test', api: mockApi })
      await crud.fetchList()

      expect(crud.listData.value).toEqual(mockData.results)
      expect(crud.total.value).toBe(2)
      expect(crud.loading.value).toBe(false)
    })

    it('should fetch list with array format', async () => {
      const mockData = [
        { id: '1', name: 'Item 1' },
        { id: '2', name: 'Item 2' }
      ]

      mockApi.list.mockResolvedValue(mockData)

      const crud = useCrud({ name: 'test', api: mockApi })
      await crud.fetchList()

      expect(crud.listData.value).toEqual(mockData)
      expect(crud.total.value).toBe(2)
    })

    it('should accept query parameters', async () => {
      mockApi.list.mockResolvedValue({ results: [], count: 0 })

      const crud = useCrud({ name: 'test', api: mockApi })
      await crud.fetchList({ page: 2, pageSize: 50 })

      expect(mockApi.list).toHaveBeenCalledWith({ page: 2, pageSize: 50 })
    })

    it('should handle API errors gracefully', async () => {
      mockApi.list.mockRejectedValue(new Error('API Error'))

      const crud = useCrud({ name: 'test', api: mockApi })
      await crud.fetchList()

      expect(crud.listData.value).toEqual([])
      expect(crud.loading.value).toBe(false)
    })

    it('should set loading to true during fetch', async () => {
      let resolveFetch: any
      const fetchPromise = new Promise(resolve => {
        resolveFetch = resolve
      })

      mockApi.list.mockReturnValue(fetchPromise)

      const crud = useCrud({ name: 'test', api: mockApi })
      const fetchListPromise = crud.fetchList()

      // Wait a tick for the async function to start
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(crud.loading.value).toBe(true)

      resolveFetch({ results: [], count: 0 })
      await fetchListPromise

      expect(crud.loading.value).toBe(false)
    })
  })

  describe('handleDelete', () => {
    it('should delete item after confirmation', async () => {
      mockApi.delete.mockResolvedValue({ success: true })

      const crud = useCrud({ name: 'test', api: mockApi })
      const result = await crud.handleDelete({ id: '1', name: 'Item 1' })

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        'Confirm to delete test "Item 1"?',
        'Confirm Delete',
        expect.objectContaining({
          type: 'warning'
        })
      )
      expect(mockApi.delete).toHaveBeenCalledWith('1')
      expect(ElMessage.success).toHaveBeenCalledWith('Delete successful')
      expect(result).toBe(true)
    })

    it('should use code when name is not available', async () => {
      mockApi.delete.mockResolvedValue({ success: true })

      const crud = useCrud({ name: 'test', api: mockApi })
      await crud.handleDelete({ id: '1', code: 'TEST001' })

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        'Confirm to delete test "TEST001"?',
        'Confirm Delete',
        expect.anything()
      )
    })

    it('should handle empty name/code', async () => {
      mockApi.delete.mockResolvedValue({ success: true })

      const crud = useCrud({ name: 'test', api: mockApi })
      await crud.handleDelete({ id: '1' })

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        'Confirm to delete test ""?',
        'Confirm Delete',
        expect.anything()
      )
    })

    it('should return false when user cancels', async () => {
      // Mock cancel behavior
      (ElMessageBox.confirm as any).mockRejectedValue('cancel')

      const crud = useCrud({ name: 'test', api: mockApi })
      const result = await crud.handleDelete({ id: '1', name: 'Item 1' })

      expect(mockApi.delete).not.toHaveBeenCalled()
      expect(ElMessage.error).not.toHaveBeenCalled()
      expect(result).toBe(false)
    })

    it('should handle API errors', async () => {
      mockApi.delete.mockRejectedValue(new Error('Delete failed'))

      const crud = useCrud({ name: 'test', api: mockApi })
      const result = await crud.handleDelete({ id: '1', name: 'Item 1' })

      expect(ElMessage.error).toHaveBeenCalledWith('Delete failed')
      expect(result).toBe(false)
    })

    it('should do nothing when delete API is not provided', async () => {
      const crud = useCrud({
        name: 'test',
        api: { list: mockApi.list }
      })
      const result = await crud.handleDelete({ id: '1', name: 'Item 1' })

      expect(result).toBeUndefined()
    })
  })

  describe('handleBatchDelete', () => {
    it('should delete multiple items after confirmation', async () => {
      mockApi.batchDelete.mockResolvedValue({ success: true })

      const rows = [
        { id: '1', name: 'Item 1' },
        { id: '2', name: 'Item 2' },
        { id: '3', name: 'Item 3' }
      ]

      const crud = useCrud({ name: 'test', api: mockApi })
      const result = await crud.handleBatchDelete(rows)

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        'Confirm to delete selected 3 items?',
        'Confirm Batch Delete',
        expect.objectContaining({
          type: 'warning'
        })
      )
      expect(mockApi.batchDelete).toHaveBeenCalledWith(['1', '2', '3'])
      expect(ElMessage.success).toHaveBeenCalledWith('Successfully deleted 3 items')
      expect(result).toBe(true)
    })

    it('should return false when user cancels', async () => {
      (ElMessageBox.confirm as any).mockRejectedValue('cancel')

      const rows = [{ id: '1', name: 'Item 1' }]

      const crud = useCrud({ name: 'test', api: mockApi })
      const result = await crud.handleBatchDelete(rows)

      expect(mockApi.batchDelete).not.toHaveBeenCalled()
      expect(result).toBe(false)
    })

    it('should handle API errors', async () => {
      mockApi.batchDelete.mockRejectedValue(new Error('Batch delete failed'))

      const rows = [{ id: '1', name: 'Item 1' }]

      const crud = useCrud({ name: 'test', api: mockApi })
      const result = await crud.handleBatchDelete(rows)

      expect(ElMessage.error).toHaveBeenCalledWith('Batch delete failed')
      expect(result).toBe(false)
    })

    it('should do nothing when no rows selected', async () => {
      const crud = useCrud({ name: 'test', api: mockApi })
      const result = await crud.handleBatchDelete([])

      expect(result).toBeUndefined()
    })

    it('should do nothing when batchDelete API is not provided', async () => {
      const crud = useCrud({
        name: 'test',
        api: { list: mockApi.list, delete: mockApi.delete }
      })
      const result = await crud.handleBatchDelete([{ id: '1', name: 'Item 1' }])

      expect(result).toBeUndefined()
    })
  })

  describe('handleExport', () => {
    beforeEach(() => {
      // Mock URL.createObjectURL and related DOM APIs
      global.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
      global.URL.revokeObjectURL = vi.fn()
      global.document.createElement = vi.fn((tag: string) => {
        if (tag === 'a') {
          return {
            href: '',
            download: '',
            click: vi.fn(),
            style: {}
          }
        }
        return document.createElement(tag)
      }) as any
    })

    it('should export data successfully', async () => {
      const mockBlob = new Blob(['test data'], { type: 'application/vnd.ms-excel' })
      mockApi.export.mockResolvedValue(mockBlob)

      const crud = useCrud({ name: 'Asset', api: mockApi })
      await crud.handleExport({ param1: 'value1' })

      expect(mockApi.export).toHaveBeenCalledWith({ param1: 'value1' })
      expect(URL.createObjectURL).toHaveBeenCalledWith(mockBlob)
      expect(ElMessage.success).toHaveBeenCalledWith('Export successful')
    })

    it('should handle export errors', async () => {
      mockApi.export.mockRejectedValue(new Error('Export failed'))

      const crud = useCrud({ name: 'test', api: mockApi })
      await crud.handleExport()

      expect(ElMessage.error).toHaveBeenCalledWith('Export failed')
    })

    it('should do nothing when export API is not provided', async () => {
      const crud = useCrud({
        name: 'test',
        api: { list: mockApi.list }
      })
      await crud.handleExport()

      expect(ElMessage.error).not.toHaveBeenCalled()
    })
  })

  describe('handleBatchExport', () => {
    beforeEach(() => {
      global.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
      global.URL.revokeObjectURL = vi.fn()
      global.document.createElement = vi.fn((tag: string) => {
        if (tag === 'a') {
          return {
            href: '',
            download: '',
            click: vi.fn(),
            style: {}
          }
        }
        return document.createElement(tag)
      }) as any
    })

    it('should export selected items', async () => {
      const mockBlob = new Blob(['test data'])
      mockApi.export.mockResolvedValue(mockBlob)

      const rows = [
        { id: '1', name: 'Item 1' },
        { id: '2', name: 'Item 2' }
      ]

      const crud = useCrud({ name: 'test', api: mockApi })
      await crud.handleBatchExport(rows)

      expect(mockApi.export).toHaveBeenCalledWith({ ids: ['1', '2'] })
    })

    it('should show warning when no rows selected', async () => {
      const crud = useCrud({ name: 'test', api: mockApi })
      await crud.handleBatchExport([])

      expect(ElMessage.warning).toHaveBeenCalledWith('Please select items to export')
      expect(mockApi.export).not.toHaveBeenCalled()
    })

    it('should show warning when export API is not provided', async () => {
      const crud = useCrud({
        name: 'test',
        api: { list: mockApi.list }
      })
      await crud.handleBatchExport([{ id: '1', name: 'Item 1' }])

      // Should show warning because export API is not provided
      expect(ElMessage.warning).toHaveBeenCalled()
      expect(ElMessage.warning.mock.calls[0][0]).toBe('Please select items to export')
    })
  })

  describe('initialization', () => {
    it('should initialize with default values', () => {
      const crud = useCrud({ name: 'test', api: mockApi })

      expect(crud.loading.value).toBe(false)
      expect(crud.listData.value).toEqual([])
      expect(crud.total.value).toBe(0)
    })
  })
})
