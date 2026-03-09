/**
 * useColumnConfig composable tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useColumnConfig, clearAllColumnConfigCache } from '@/composables/useColumnConfig'
import { ElMessage } from 'element-plus'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    warning: vi.fn()
  }
}))

// Mock system API
vi.mock('@/api/system', () => ({
  columnConfigApi: {
    get: vi.fn(),
    save: vi.fn(),
    reset: vi.fn()
  }
}))

describe('useColumnConfig', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    clearAllColumnConfigCache()
  })

  describe('initialization', () => {
    it('should initialize with default values', () => {
      const config = useColumnConfig('asset')

      expect(config.config.value).toBe(null)
      expect(config.loading.value).toBe(false)
      expect(config.error.value).toBe(null)
    })
  })

  describe('fetchConfig', () => {
    it('should fetch configuration successfully', async () => {
      const { columnConfigApi } = await import('@/api/system')

      const mockResponse = {
        columns: [
          { prop: 'name', label: 'Name', width: 150, visible: true },
          { prop: 'code', label: 'Code', width: 120, visible: true }
        ],
        columnOrder: ['code', 'name'],
        source: 'user'
      }

      vi.mocked(columnConfigApi.get).mockResolvedValue(mockResponse)

      const config = useColumnConfig('asset')
      const result = await config.fetchConfig()

      expect(config.loading.value).toBe(false)
      expect(config.config.value).not.toBeNull()
      expect(config.config.value?.columns).toHaveLength(2)
      expect(config.config.value?.columnOrder).toEqual(['code', 'name'])
      expect(config.config.value?.source).toBe('user')
      expect(result?.columns[0].label).toBe('Name')
    })

    it('should normalize legacy snake_case order from backend', async () => {
      const { columnConfigApi } = await import('@/api/system')

      vi.mocked(columnConfigApi.get).mockResolvedValue({
        columns: [
          { field_code: 'name', label: 'Name', width: 150, visible: true },
          { fieldCode: 'code', label: 'Code', width: 120, visible: true }
        ],
        column_order: ['name', 'code'],
        source: 'user'
      } as any)

      const config = useColumnConfig('asset')
      const result = await config.fetchConfig()

      expect(result?.columnOrder).toEqual(['name', 'code'])
      expect(result?.columns[0]).toMatchObject({ fieldCode: 'name', field_code: 'name' })
      expect(result?.columns[1]).toMatchObject({ fieldCode: 'code', field_code: 'code' })
    })

    it('should cache configuration', async () => {
      const { columnConfigApi } = await import('@/api/system')

      const mockResponse = {
        columns: [{ prop: 'name', label: 'Name' }]
      }

      vi.mocked(columnConfigApi.get).mockResolvedValue(mockResponse)

      const config = useColumnConfig('asset')

      // First call
      await config.fetchConfig()
      // Second call should use cache
      await config.fetchConfig()

      expect(columnConfigApi.get).toHaveBeenCalledTimes(1)
    })

    it('should handle API errors gracefully', async () => {
      const { columnConfigApi } = await import('@/api/system')

      vi.mocked(columnConfigApi.get).mockRejectedValue(new Error('API Error'))

      const config = useColumnConfig('asset')
      await config.fetchConfig()

      expect(config.error.value).toBeInstanceOf(Error)
      expect(config.config.value).toBe(null)
    })

    it('should return null on error', async () => {
      const { columnConfigApi } = await import('@/api/system')

      vi.mocked(columnConfigApi.get).mockRejectedValue(new Error('API Error'))

      const config = useColumnConfig('asset')
      const result = await config.fetchConfig()

      expect(result).toBe(null)
    })
  })

  describe('saveConfig', () => {
    it('should save configuration successfully', async () => {
      const { columnConfigApi } = await import('@/api/system')

      const mockResponse = {
        data: { success: true }
      }

      vi.mocked(columnConfigApi.save).mockResolvedValue(mockResponse)

      const config = useColumnConfig('asset')

      const columns = [
        { prop: 'name', label: 'Name', width: 150, defaultWidth: 120, visible: true, defaultVisible: true, sortable: true },
        { prop: 'code', label: 'Code', width: 120, defaultWidth: 120, visible: true, defaultVisible: true, sortable: true }
      ] as any

      await config.saveConfig(columns)

      expect(columnConfigApi.save).toHaveBeenCalledWith('asset', {
        columns: expect.any(Array),
        columnOrder: ['name', 'code']
      })

      expect(ElMessage.success).toHaveBeenCalled()
      expect(config.loading.value).toBe(false)
    })

    it('should handle field_code property', async () => {
      const { columnConfigApi } = await import('@/api/system')

      vi.mocked(columnConfigApi.save).mockResolvedValue({ data: { success: true } })

      const config = useColumnConfig('asset')

      const columns = [
        { field_code: 'asset_name', prop: 'name', label: 'Name', width: 150, visible: true }
      ] as any

      await config.saveConfig(columns)

      expect(columnConfigApi.save).toHaveBeenCalledWith('asset', {
        columns: [
          expect.objectContaining({ field_code: 'asset_name' })
        ],
        columnOrder: ['asset_name']
      })
    })

    it('should handle save errors', async () => {
      const { columnConfigApi } = await import('@/api/system')

      vi.mocked(columnConfigApi.save).mockRejectedValue(new Error('Save failed'))

      const config = useColumnConfig('asset')

      const columns = [{ prop: 'name', label: 'Name' }] as any

      await config.saveConfig(columns)

      expect(ElMessage.warning).toHaveBeenCalled()
      expect(config.error.value).toBeInstanceOf(Error)
    })

    it('should update config after successful save', async () => {
      const { columnConfigApi } = await import('@/api/system')

      vi.mocked(columnConfigApi.save).mockResolvedValue({ data: { success: true } })

      const config = useColumnConfig('asset')

      const columns = [{ prop: 'name', label: 'Name' }] as any

      await config.saveConfig(columns)

      expect(config.config.value?.columns).toEqual([
        expect.objectContaining({ prop: 'name', label: 'Name', fieldCode: 'name', field_code: 'name' })
      ])
      expect(config.config.value?.columnOrder).toEqual(['name'])
      expect(config.config.value?.source).toBe('user')
    })
  })

  describe('resetConfig', () => {
    it('should reset configuration successfully', async () => {
      const { columnConfigApi } = await import('@/api/system')

      vi.mocked(columnConfigApi.reset).mockResolvedValue({ data: { success: true } })

      const config = useColumnConfig('asset')

      // First set some config
      config.config.value = {
        object_code: 'asset',
        columns: [{ prop: 'name', label: 'Name' }]
      }

      await config.resetConfig()

      expect(columnConfigApi.reset).toHaveBeenCalledWith('asset')
      expect(config.config.value).toBe(null)
      expect(ElMessage.success).toHaveBeenCalled()
    })

    it('should handle reset errors', async () => {
      const { columnConfigApi } = await import('@/api/system')

      vi.mocked(columnConfigApi.reset).mockRejectedValue(new Error('Reset failed'))

      const config = useColumnConfig('asset')

      await config.resetConfig()

      expect(ElMessage.warning).toHaveBeenCalled()
      expect(config.error.value).toBeInstanceOf(Error)
    })

    it('should clear cache on reset', async () => {
      const { columnConfigApi } = await import('@/api/system')

      vi.mocked(columnConfigApi.reset).mockResolvedValue({ data: { success: true } })

      const config = useColumnConfig('asset')

      // Set some config
      config.config.value = {
        object_code: 'asset',
        columns: [{ prop: 'name', label: 'Name' }]
      }

      await config.resetConfig()

      // Cache should be cleared
      expect(config.config.value).toBe(null)
    })
  })

  describe('applyConfig', () => {
    it('should return default columns when no config', () => {
      const config = useColumnConfig('asset')

      const defaultColumns = [
        { prop: 'name', label: 'Name', defaultWidth: 150 },
        { prop: 'code', label: 'Code', defaultWidth: 120 }
      ] as any

      const result = config.applyConfig(defaultColumns)

      expect(result).toEqual(defaultColumns)
    })

    it('should apply saved configuration to defaults', () => {
      const config = useColumnConfig('asset')

      // Set saved config
      config.config.value = {
        object_code: 'asset',
        columns: [
          { prop: 'name', width: 200, visible: false },
          { prop: 'code', width: 150, visible: true }
        ]
      }

      const defaultColumns = [
        { prop: 'name', label: 'Name', defaultWidth: 150 },
        { prop: 'code', label: 'Code', defaultWidth: 120 }
      ] as any

      const result = config.applyConfig(defaultColumns)

      expect(result[0].width).toBe(200) // Applied saved width
      expect(result[0].visible).toBe(false) // Applied saved visibility
      expect(result[0].label).toBe('Name') // Kept default label
      expect(result[1].width).toBe(150)
    })

    it('should handle fixed column property', () => {
      const config = useColumnConfig('asset')

      config.config.value = {
        object_code: 'asset',
        columns: [
          { prop: 'name', fixed: 'left' }
        ]
      }

      const defaultColumns = [
        { prop: 'name', label: 'Name', defaultWidth: 150, fixed: undefined }
      ] as any

      const result = config.applyConfig(defaultColumns)

      expect(result[0].fixed).toBe('left')
    })

    it('should preserve default fixed when not in saved config', () => {
      const config = useColumnConfig('asset')

      config.config.value = {
        object_code: 'asset',
        columns: [
          { prop: 'name', width: 200 }
        ]
      }

      const defaultColumns = [
        { prop: 'name', label: 'Name', defaultWidth: 150, fixed: 'right' }
      ] as any

      const result = config.applyConfig(defaultColumns)

      expect(result[0].fixed).toBe('right')
    })

    it('should sort columns by saved order', () => {
      const config = useColumnConfig('asset')

      config.config.value = {
        object_code: 'asset',
        columns: [
          { prop: 'code', width: 120 },
          { prop: 'name', width: 150 }
        ],
        columnOrder: ['code', 'name']
      }

      const defaultColumns = [
        { prop: 'name', label: 'Name', defaultWidth: 150 },
        { prop: 'code', label: 'Code', defaultWidth: 120 }
      ] as any

      const result = config.applyConfig(defaultColumns)

      expect(result[0].prop).toBe('code')
      expect(result[1].prop).toBe('name')
    })

    it('should sort columns by normalized legacy field keys', () => {
      const config = useColumnConfig('asset')

      config.config.value = {
        object_code: 'asset',
        columns: [
          { field_code: 'name', width: 150 } as any,
          { fieldCode: 'code', width: 120 } as any
        ],
        columnOrder: ['name', 'code']
      }

      const defaultColumns = [
        { prop: 'code', label: 'Code', defaultWidth: 120 },
        { prop: 'name', label: 'Name', defaultWidth: 150 }
      ] as any

      const result = config.applyConfig(defaultColumns)

      expect(result[0].prop).toBe('name')
      expect(result[1].prop).toBe('code')
    })
  })

  describe('visibleColumns', () => {
    it('should return only visible columns', () => {
      const config = useColumnConfig('asset')

      config.config.value = {
        object_code: 'asset',
        columns: [
          { prop: 'name', visible: true },
          { prop: 'code', visible: true },
          { prop: 'hidden', visible: false }
        ]
      }

      const visible = config.visibleColumns.value

      expect(visible).toHaveLength(2)
      expect(visible.every(col => col.visible !== false)).toBe(true)
    })

    it('should return empty array when no config', () => {
      const config = useColumnConfig('asset')

      const visible = config.visibleColumns.value

      expect(visible).toEqual([])
    })

    it('should treat missing visible as true', () => {
      const config = useColumnConfig('asset')

      config.config.value = {
        object_code: 'asset',
        columns: [
          { prop: 'name' },
          { prop: 'code', visible: false }
        ]
      }

      const visible = config.visibleColumns.value

      expect(visible).toHaveLength(1)
      expect(visible[0].prop).toBe('name')
    })
  })

  describe('clearCache', () => {
    it('should clear cached configuration', async () => {
      const { columnConfigApi } = await import('@/api/system')

      const mockResponse = {
        columns: [{ prop: 'name', label: 'Name' }]
      }

      vi.mocked(columnConfigApi.get).mockResolvedValue(mockResponse)

      const config = useColumnConfig('asset')

      // Load config
      await config.fetchConfig()
      expect(config.config.value).not.toBeNull()

      // Clear cache
      config.clearCache()
      expect(config.config.value).toBe(null)
    })
  })

  describe('clearAllColumnConfigCache', () => {
    it('should clear all cached configurations', async () => {
      const { columnConfigApi } = await import('@/api/system')

      const mockResponse = {
        columns: []
      }

      vi.mocked(columnConfigApi.get).mockResolvedValue(mockResponse)

      const config1 = useColumnConfig('asset')
      const config2 = useColumnConfig('inventory')

      // Load configs
      await config1.fetchConfig()
      await config2.fetchConfig()

      // Clear all cache
      clearAllColumnConfigCache()

      // Create new instances to verify cache is cleared
      const newConfig1 = useColumnConfig('asset')
      const newConfig2 = useColumnConfig('inventory')

      // These should not have cached values
      expect(newConfig1.config.value).toBe(null)
      expect(newConfig2.config.value).toBe(null)
    })
  })
})
