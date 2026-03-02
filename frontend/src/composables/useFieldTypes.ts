/**
 * useFieldTypes.ts - Composable for managing field types with caching
 *
 * Provides a centralized way to fetch and cache field type definitions
 * from the backend API. Implements localStorage caching with version
 * control to reduce API calls and provide offline fallback.
 *
 * @category Composables
 */

import { ref, computed } from 'vue'
import { businessObjectApi, type FieldTypeGroup, type FieldTypeOption, type FieldTypeConfig } from '@/api/system'

// Cache configuration
const CACHE_KEY = 'gzeams_field_types_v1'
const CACHE_DURATION = 24 * 60 * 60 * 1000 // 24 hours in milliseconds

// Static fallback field types (used when API fails)
// We use a function to get these so they can be reactive to language changes if needed,
// but typically they are just fallback. To support i18n, we should use keys.
import i18n from '@/locales'

const { t } = i18n.global

const getStaticFieldTypes = (): FieldTypeGroup[] => [
  {
    label: t('system.fieldDefinition.groups.basic'),
    icon: 'Document',
    types: [
      { value: 'text', label: t('system.fieldDefinition.types.text') },
      { value: 'textarea', label: t('system.fieldDefinition.types.textarea') },
      { value: 'number', label: t('system.fieldDefinition.types.number') },
      { value: 'currency', label: t('system.fieldDefinition.types.currency') },
      { value: 'percent', label: t('system.fieldDefinition.types.percent') }
    ]
  },
  {
    label: t('system.fieldDefinition.groups.datetime'),
    icon: 'Timer',
    types: [
      { value: 'date', label: t('system.fieldDefinition.types.date') },
      { value: 'datetime', label: t('system.fieldDefinition.types.datetime') },
      { value: 'time', label: t('system.fieldDefinition.types.time') }
    ]
  },
  {
    label: t('system.fieldDefinition.groups.selection'),
    icon: 'Checked',
    types: [
      { value: 'select', label: t('system.fieldDefinition.types.select') },
      { value: 'multi_select', label: t('system.fieldDefinition.types.multi_select') },
      { value: 'radio', label: t('system.fieldDefinition.types.radio') },
      { value: 'checkbox', label: t('system.fieldDefinition.types.checkbox') },
      { value: 'boolean', label: t('system.fieldDefinition.types.boolean') }
    ]
  },
  {
    label: t('system.fieldDefinition.groups.reference'),
    icon: 'Link',
    types: [
      { value: 'user', label: t('system.fieldDefinition.types.user') },
      { value: 'department', label: t('system.fieldDefinition.types.department') },
      { value: 'reference', label: t('system.fieldDefinition.types.reference') },
      { value: 'asset', label: t('system.fieldDefinition.types.asset') },
      { value: 'location', label: t('system.fieldDefinition.types.location') }
    ]
  },
  {
    label: t('system.fieldDefinition.groups.media'),
    icon: 'Picture',
    types: [
      { value: 'file', label: t('system.fieldDefinition.types.file') },
      { value: 'image', label: t('system.fieldDefinition.types.image') },
      { value: 'qr_code', label: t('system.fieldDefinition.types.qr_code') },
      { value: 'barcode', label: t('system.fieldDefinition.types.barcode') }
    ]
  },
  {
    label: t('system.fieldDefinition.groups.advanced'),
    icon: 'Tools',
    types: [
      { value: 'formula', label: t('system.fieldDefinition.types.formula') },
      { value: 'sub_table', label: t('system.fieldDefinition.types.sub_table') },
      { value: 'rich_text', label: t('system.fieldDefinition.types.rich_text') }
    ]
  }
]

// Cache data structure
interface FieldTypesCache {
  data: {
    groups: FieldTypeGroup[]
    allTypes: string[]
    typeConfig: Record<string, FieldTypeConfig>
  }
  timestamp: number
}

// Module state (shared across all instances)
const isLoading = ref(false)
const error = ref<string | null>(null)
const cache = ref<FieldTypesCache | null>(null)

/**
 * Load field types from localStorage cache
 */
function loadFromCache(): FieldTypesCache | null {
  try {
    const cached = localStorage.getItem(CACHE_KEY)
    if (!cached) return null

    const parsed: FieldTypesCache = JSON.parse(cached)
    const now = Date.now()

    // Check if cache is still valid
    if (now - parsed.timestamp < CACHE_DURATION) {
      return parsed
    }

    // Cache expired, remove it
    localStorage.removeItem(CACHE_KEY)
    return null
  } catch {
    return null
  }
}

/**
 * Save field types to localStorage cache
 */
function saveToCache(data: FieldTypesCache['data']): void {
  try {
    const cacheData: FieldTypesCache = {
      data,
      timestamp: Date.now()
    }
    localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData))
  } catch (e) {
    // Silent fail - caching is optional
    console.warn('Failed to cache field types:', e)
  }
}

/**
 * Flatten field type groups into a single array of options
 */
function flattenGroups(groups: FieldTypeGroup[]): FieldTypeOption[] {
  const options: FieldTypeOption[] = []
  for (const group of groups) {
    options.push(...group.types)
  }
  return options
}

/**
 * Get all field types as a flat array
 */
export function useFieldTypes() {
  const data = computed(() => cache.value?.data)
  /* const groups = computed(() => data.value?.groups || STATIC_FIELD_TYPES)
  const allTypes = computed(() => data.value?.allTypes || flattenGroups(STATIC_FIELD_TYPES).map(t => t.value)) */

  // Use function to get static types to allow i18n
  const staticTypes = computed(() => getStaticFieldTypes())

  const groups = computed(() => data.value?.groups || staticTypes.value)
  const allTypes = computed(() => data.value?.allTypes || flattenGroups(staticTypes.value).map(t => t.value))
  const flatOptions = computed(() => flattenGroups(groups.value))
  const typeConfig = computed(() => data.value?.typeConfig || {})

  /**
   * Fetch field types from API
   * Uses cache if available and valid
   */
  async function fetch(forceRefresh = false): Promise<void> {
    // Return cached data if available and not forcing refresh
    if (!forceRefresh && cache.value) {
      return
    }

    // Try to load from localStorage
    if (!forceRefresh) {
      const cached = loadFromCache()
      if (cached) {
        cache.value = cached
        return
      }
    }

    isLoading.value = true
    error.value = null

    try {
      const response = await businessObjectApi.getFieldTypes()
      if (response.success && response.data) {
        cache.value = {
          data: response.data,
          timestamp: Date.now()
        }
        // Save to localStorage for future use
        saveToCache(response.data)
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : t('system.fieldDefinition.messages.loadFailed')
      // Use static fallback on error
      cache.value = {
        data: {
          groups: getStaticFieldTypes(),
          allTypes: flattenGroups(getStaticFieldTypes()).map(t => t.value),
          typeConfig: {}
        },
        timestamp: 0
      }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Get label for a field type value
   */
  function getLabel(typeValue: string): string {
    for (const group of groups.value) {
      const found = group.types.find(t => t.value === typeValue)
      if (found) return found.label
    }
    return typeValue
  }

  /**
   * Get group for a field type value
   */
  function getGroup(typeValue: string): FieldTypeGroup | undefined {
    return groups.value.find(g => g.types.some(t => t.value === typeValue))
  }

  /**
   * Check if a field type requires reference object selection
   */
  function requiresReference(typeValue: string): boolean {
    return ['reference', 'sub_table'].includes(typeValue)
  }

  /**
   * Check if a field type supports options configuration
   */
  function supportsOptions(typeValue: string): boolean {
    return ['select', 'multi_select', 'radio', 'checkbox'].includes(typeValue)
  }

  /**
   * Check if a field type supports formula
   */
  function supportsFormula(typeValue: string): boolean {
    return typeValue === 'formula'
  }

  /**
   * Clear cached field types (useful for testing or after updates)
   */
  function clearCache(): void {
    localStorage.removeItem(CACHE_KEY)
    cache.value = null
  }

  return {
    // State
    isLoading,
    error,
    data,
    groups,
    allTypes,
    flatOptions,
    typeConfig,

    // Methods
    fetch,
    getLabel,
    getGroup,
    requiresReference,
    supportsOptions,
    supportsFormula,
    clearCache
  }
}

// Export static types for use in tests
export { }
