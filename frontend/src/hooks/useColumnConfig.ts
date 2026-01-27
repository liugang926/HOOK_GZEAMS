import { ref, computed, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

/**
 * Column configuration types
 */

export interface ColumnItem {
  prop: string
  label: string
  width?: number
  minWidth?: number
  fixed?: boolean | 'left' | 'right' // Updated to allow boolean
  visible?: boolean
  sortable?: boolean | 'custom'
  defaultVisible?: boolean
  defaultWidth?: number
  defaultOrder?: number
}

export interface ColumnConfig {
  object_code: string
  columns: ColumnItem[]
}

export interface UserColumnPreference {
  id?: string
  object_code: string
  column_key: string
  config: {
    visible: boolean
    width: number
    order: number
    fixed?: 'left' | 'right' | false
  }
  scope: 'user' | 'role' | 'organization'
  scope_id?: string
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

  const apiBaseUrl = '/api/system/column-config'

  /**
   * Build cache key for object code
   */
  const getCacheKey = (code: string) => {
    const userId = userStore.userInfo?.id || 'anonymous'
    const orgId = userStore.currentOrganization?.id || 'default'
    return `${userId}:${orgId}:${code}`
  }

  /**
   * Fetch column configuration from API or LocalStorage
   */
  const fetchConfig = async () => {
    const cacheKey = getCacheKey(objectCode)
    const localKey = `column-config:${cacheKey}`

    // 1. Return in-memory cache if available
    if (columnConfigCache.has(cacheKey)) {
      config.value = columnConfigCache.get(cacheKey)!
      return config.value
    }

    loading.value = true
    error.value = null

    try {
      // 2. Try API (Persistent Storage)
      // Note: If objectCode is missing or auth is missing, we might skip this
      const response = await fetch(
        `${apiBaseUrl}/${objectCode}/`,
        {
          headers: {
            'Authorization': `Bearer ${userStore.token}`,
            'Content-Type': 'application/json'
          }
        }
      )

      if (!response.ok) {
        throw new Error(`Failed to fetch column config: ${response.statusText}`)
      }

      const data = await response.json()
      const result = data.data || data

      config.value = {
        object_code: objectCode,
        columns: result.columns || []
      }

      // Sync to LocalStorage
      localStorage.setItem(localKey, JSON.stringify(config.value))

    } catch (err) {
      // 3. Fallback to LocalStorage (Temporary Preservation)
      console.warn('API fetch failed, checking localStorage', err)
      const localData = localStorage.getItem(localKey)
      if (localData) {
        try {
          config.value = JSON.parse(localData)
        } catch (e) {
          console.error('Failed to parse local config', e)
        }
      }

      // If still no config, we will just return null (using defaults)
    } finally {
      // Update in-memory cache
      if (config.value) {
        columnConfigCache.set(cacheKey, config.value)
      }
      loading.value = false
    }
  }

  /**
   * Save column configuration to API and LocalStorage
   */
  const saveConfig = async (columns: ColumnItem[]) => {
    const cacheKey = getCacheKey(objectCode)
    const localKey = `column-config:${cacheKey}`

    loading.value = true
    error.value = null

    // Optimistic Update: Save to LocalStorage immediately
    const newConfig: ColumnConfig = {
      object_code: objectCode,
      columns
    }
    config.value = newConfig
    columnConfigCache.set(cacheKey, newConfig)
    localStorage.setItem(localKey, JSON.stringify(newConfig))

    try {
      const preferences: UserColumnPreference[] = columns.map((col, index) => ({
        object_code: objectCode,
        column_key: col.prop,
        config: {
          visible: col.visible !== false,
          width: col.width || col.defaultWidth || 120,
          order: index,
          fixed: col.fixed || false
        },
        scope: 'user'
      }))

      // Try API Save
      const response = await fetch(
        `${apiBaseUrl}/${objectCode}/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${userStore.token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ preferences })
        }
      )

      if (!response.ok) {
        // We do not throw here to allow "Temporary" save even if "Persistent" fails
        console.warn('Failed to sync to backend', response.statusText)
        ElMessage.warning('Saved locally (Offline Mode)')
      } else {
        ElMessage.success('Column configuration saved')
      }

    } catch (err) {
      console.error('Save API error', err)
      ElMessage.warning('Issue saving to server, kept locally')
    } finally {
      loading.value = false
    }
  }

  /**
   * Reset column configuration to default
   */
  const resetConfig = async () => {
    loading.value = true
    const cacheKey = getCacheKey(objectCode)
    const localKey = `column-config:${cacheKey}`

    try {
      // API Reset
      await fetch(
        `${apiBaseUrl}/${objectCode}/reset/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${userStore.token}`,
            'Content-Type': 'application/json'
          }
        }
      ).catch(e => console.warn('API reset failed', e))

      // Clear Local
      localStorage.removeItem(localKey)
      columnConfigCache.delete(cacheKey)
      config.value = null

      ElMessage.success('Column configuration reset to default')
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
    savedColumns.forEach(col => savedMap.set(col.prop, col))

    // Apply saved configuration to default columns
    defaultColumns.forEach((defaultCol, index) => {
      const saved = savedMap.get(defaultCol.prop)

      if (saved) {
        result.push({
          ...defaultCol,
          visible: saved.visible !== false,
          width: saved.width || defaultCol.defaultWidth || defaultCol.width,
          fixed: saved.fixed === undefined ? defaultCol.fixed : saved.fixed, // Use saved fixed if present
          // we merge other props if needed
        })
      } else {
        result.push(defaultCol)
      }
    })

    // Sort by saved order
    const sortedResult = result.sort((a, b) => {
      const aSaved = savedMap.get(a.prop)
      const bSaved = savedMap.get(b.prop)

      const aOrder = aSaved?.defaultOrder ?? (a.defaultOrder || 999)
      const bOrder = bSaved?.defaultOrder ?? (b.defaultOrder || 999)

      // If both have saved order, compare them
      if (aSaved && bSaved) {
        return (aSaved.defaultOrder || 0) - (bSaved.defaultOrder || 0)
      }

      // If one is saved (shouldn't happen often if we iterate defaults), prioritize it? 
      // Actually we just rely on the array order of savedColumns usually, 
      // but here we are iterating defaults. 

      // Better strategy: Use the order from savedColumns if it exists in the config list
      const aIndex = savedColumns.findIndex(c => c.prop === a.prop)
      const bIndex = savedColumns.findIndex(c => c.prop === b.prop)

      if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex
      if (aIndex !== -1) return -1
      if (bIndex !== -1) return 1

      return 0
    })

    return sortedResult
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
