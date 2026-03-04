import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { columnConfigApi, type ColumnConfig as ApiColumnConfig } from '@/api/system'
import type { ColumnItem } from '@/types/common'
export type { ColumnItem } from '@/types/common'

/**
 * Column configuration types
 */

export interface ColumnConfig {
  object_code: string
  columns: ColumnItem[]
}

/**
 * Column configuration cache for performance
 */
const columnConfigCache = new Map<string, ColumnConfig>()

/**
 * useColumnConfig - Composable for managing table column configurations
 *
 * Features:
 * - Fetch column configuration from API
 * - Save column configuration
 * - Reset to default configuration
 * - Apply configuration to columns
 * - Cache configurations for performance
 */
export function useColumnConfig(objectCode: string) {
  const userStore = useUserStore()
  const config = ref<ColumnConfig | null>(null)
  const loading = ref(false)
  const error = ref<Error | null>(null)

  /**
   * Build cache key for object code
   */
  const getCacheKey = (code: string) => {
    const userId = userStore.userInfo?.id || 'anonymous'
    const orgId = userStore.currentOrganization?.id || 'default'
    return `${userId}:${orgId}:${code}`
  }

  /**
   * Fetch column configuration from API
   */
  const fetchConfig = async () => {
    const cacheKey = getCacheKey(objectCode)

    // 1. Return in-memory cache if available
    if (columnConfigCache.has(cacheKey)) {
      config.value = columnConfigCache.get(cacheKey)!
      return config.value
    }

    loading.value = true
    error.value = null

    try {
      // Use the centralized API from system.ts
      // Note: response interceptor unwraps {success, data} envelope,
      // so `response` IS the inner data directly.
      const response: any = await columnConfigApi.get(objectCode)

      // Handle both wrapped ({success, data}) and unwrapped (direct data) formats
      const result = response?.data?.columns
        ? response.data
        : (response?.columns ? response : null)

      if (result) {
        config.value = {
          object_code: objectCode,
          columns: result.columns || []
        }

        // Update in-memory cache
        columnConfigCache.set(cacheKey, config.value)
      }
    } catch (err) {
      console.warn('Failed to fetch column config', err)
      error.value = err as Error
    } finally {
      loading.value = false
    }

    return config.value
  }

  /**
   * Save column configuration to API
   */
  const saveConfig = async (columns: ColumnItem[]) => {
    const cacheKey = getCacheKey(objectCode)

    loading.value = true
    error.value = null

    try {
      // Convert columns to API format
      const columnConfig: ApiColumnConfig = {
        columns: columns.map((col) => ({
          fieldCode: (col as any).fieldCode || (col as any).field_code || col.prop,
          field_code: (col as any).field_code || (col as any).fieldCode || col.prop,
          width: col.width || col.defaultWidth || 120,
          fixed: col.fixed === true
            ? 'left'
            : (col.fixed === false ? undefined : (col.fixed || undefined)),
          visible: col.visible !== false
        })),
        columnOrder: columns.map((col) => (col as any).field_code || (col as any).fieldCode || col.prop)
      }

      // Use the centralized API
      // Note: response interceptor unwraps {success, data} envelope,
      // so a successful save means we get here without throwing.
      await columnConfigApi.save(objectCode, columnConfig)

      const newConfig: ColumnConfig = {
        object_code: objectCode,
        columns
      }
      config.value = newConfig
      columnConfigCache.set(cacheKey, newConfig)
      ElMessage.success('Column configuration saved')
    } catch (err) {
      console.error('Save API error', err)
      error.value = err as Error
      ElMessage.warning('Failed to save column configuration')
    } finally {
      loading.value = false
    }
  }

  /**
   * Reset column configuration to default
   */
  const resetConfig = async () => {
    const cacheKey = getCacheKey(objectCode)

    loading.value = true
    error.value = null

    try {
      // Use the centralized API
      // Note: response interceptor unwraps envelope; success = no throw
      await columnConfigApi.reset(objectCode)

      // Clear cache and config
      columnConfigCache.delete(cacheKey)
      config.value = null
      ElMessage.success('Column configuration reset to default')
    } catch (err) {
      console.error('Reset API error', err)
      error.value = err as Error
      ElMessage.warning('Failed to reset column configuration')
    } finally {
      loading.value = false
    }
  }

  /**
   * Apply configuration to columns
   * Merges default column definitions with saved preferences
   */
  const applyConfig = (defaultColumns: ColumnItem[]): ColumnItem[] => {
    // If no config loaded, return defaults
    if (!config.value || !config.value.columns.length) {
      return defaultColumns
    }

    const savedColumns = config.value.columns
    const result: ColumnItem[] = []

    // Create a map of saved columns for quick lookup
    const savedMap = new Map<string, ColumnItem>()
    savedColumns.forEach(col => {
      const key = (col as any).field_code || (col as any).fieldCode || col.prop
      savedMap.set(key, col)
    })

    // Apply saved configuration to default columns
    defaultColumns.forEach((defaultCol) => {
      const key = (defaultCol as any).field_code || (defaultCol as any).fieldCode || defaultCol.prop
      const saved = savedMap.get(key)

      if (saved) {
        result.push({
          ...defaultCol,
          visible: saved.visible !== false,
          width: saved.width || defaultCol.defaultWidth || defaultCol.width,
          fixed: saved.fixed === undefined ? defaultCol.fixed : saved.fixed,
          // we merge other props if needed
        })
      } else {
        result.push(defaultCol)
      }
    })

    // Sort by saved order (if columnOrder exists)
    if (config.value && (config.value as any).columnOrder) {
      const order = (config.value as any).columnOrder
      result.sort((a, b) => {
        const aKey = (a as any).field_code || (a as any).fieldCode || a.prop
        const bKey = (b as any).field_code || (b as any).fieldCode || b.prop
        const aIndex = order.indexOf(aKey)
        const bIndex = order.indexOf(bKey)

        if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex
        if (aIndex !== -1) return -1
        if (bIndex !== -1) return 1

        return 0
      })
    }

    return result
  }


  /**
   * Get visible columns only
   */
  const visibleColumns = computed(() => {
    if (!config.value) return []
    return config.value.columns.filter(col => col.visible !== false)
  })

  /**
   * Clear cached configuration for this object
   */
  const clearCache = () => {
    const cacheKey = getCacheKey(objectCode)
    columnConfigCache.delete(cacheKey)
    config.value = null
  }

  return {
    config,
    loading,
    error,
    visibleColumns,
    fetchConfig,
    saveConfig,
    resetConfig,
    applyConfig,
    clearCache
  }
}

/**
 * Clear all cached column configurations
 */
export function clearAllColumnConfigCache() {
  columnConfigCache.clear()
}
