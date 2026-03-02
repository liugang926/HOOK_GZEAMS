import { ref, computed, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import request from '@/utils/request'
import { toRuntimeMode } from '@/utils/layoutMode'
import type {
  FieldDefinition,
  BusinessObject,
  PageLayout,
  LayoutConfig,
  LayoutSection,
  LayoutField,
  LayoutAction,
  ValidationRule
} from '@/types'

/**
 * Metadata cache for performance
 */
const metadataCache = new Map<string, any>()

/**
 * useMetadata - Composable for metadata-driven features
 *
 * Features:
 * - Fetch business object metadata
 * - Fetch field definitions
 * - Fetch page layouts
 * - Resolve field values with formulas
 * - Cache metadata for performance
 */
export function useMetadata() {
  const userStore = useUserStore()
  const loading = ref(false)
  const error = ref<Error | null>(null)

  const apiBaseUrl = '/system'

  const showMessageOnce = (message: string, err: any) => {
    // Axios errors are already handled in `handleApiError`; avoid duplicate toasts.
    if (err?.isHandled) return
    ElMessage.error(message)
  }

  /**
   * Generic request helper with error handling
   */
  const fetchFromApi = async (
    url: string,
    options: { method?: 'get' | 'post' | 'put' | 'patch' | 'delete'; params?: any; data?: any; silent?: boolean } = {}
  ): Promise<any> => {
    const method = options.method || 'get'
    return request({
      url,
      method,
      params: options.params,
      data: options.data,
      silent: options.silent
    })
  }

  /**
   * Get cache key for metadata requests
   */
  const getCacheKey = (type: string, identifier: string) => {
    const orgId = userStore.currentOrganization?.id || 'default'
    return `${orgId}:${type}:${identifier}`
  }

  /**
   * Fetch all business objects
   */
  const fetchBusinessObjects = async (params: any = {}) => {
    const cacheKey = getCacheKey('business_objects', 'all')
    if (metadataCache.has(cacheKey)) {
      return metadataCache.get(cacheKey)
    }

    loading.value = true
    error.value = null

    try {
      const queryParams = new URLSearchParams({
        is_active: 'true',
        ...params
      })

      const data = await fetchFromApi(
        `${apiBaseUrl}/business-objects/?${queryParams}`
      )

      // Response structure: { success: true, data: { objectCode, fields: [...] } }
      const results = data.data?.fields || data.fields || data.results || []
      metadataCache.set(cacheKey, results)

      return results
    } catch (err) {
      error.value = err as Error
      showMessageOnce('Failed to load business objects', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch a single business object by code
   */
  const fetchBusinessObject = async (objectCode: string) => {
    const cacheKey = getCacheKey('business_object', objectCode)
    if (metadataCache.has(cacheKey)) {
      return metadataCache.get(cacheKey)
    }

    loading.value = true
    error.value = null

    try {
      const data = await fetchFromApi(
        `${apiBaseUrl}/business-objects/by-code/${objectCode}/`
      )

      // Also fetch field definitions
      const fields = await fetchFieldDefinitions(objectCode, 'form')
      data.fields = fields

      metadataCache.set(cacheKey, data)

      return data
    } catch (err) {
      error.value = err as Error
      showMessageOnce(`Failed to load business object: ${objectCode}`, err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch field definitions for a business object
   * Uses the unified business-objects/fields endpoint that handles both
   * hardcoded models (ModelFieldDefinition) and custom objects (FieldDefinition)
   */
  const fetchFieldDefinitions = async (objectCode: string, context: 'form' | 'detail' | 'list' = 'form') => {
    const cacheKey = getCacheKey('field_definitions', `${objectCode}:${context}`)
    if (metadataCache.has(cacheKey)) {
      return metadataCache.get(cacheKey)
    }

    loading.value = true
    error.value = null

    try {
      // Prefer context-aware endpoint to align with designer preview
      try {
        const ctxData = await fetchFromApi(
          `${apiBaseUrl}/objects/${objectCode}/fields/?context=${context}&include_relations=true`
        )

        const payload = ctxData.data || ctxData
        const editable = payload.editableFields || payload.fields || []
        const reverse = payload.reverseRelations || []
        const combined = [...editable, ...reverse]
        metadataCache.set(cacheKey, combined)
        return combined
      } catch (ctxError) {
        // Fall back to legacy endpoint
        const data = await fetchFromApi(
          `${apiBaseUrl}/business-objects/fields/?object_code=${objectCode}`
        )

        // Response structure: { success: true, data: { objectCode, fields: [...] } }
        const results = data.data?.fields || data.fields || data.results || []
        metadataCache.set(cacheKey, results)
        return results
      }
    } catch (err) {
      error.value = err as Error
      showMessageOnce(`Failed to load field definitions for: ${objectCode}`, err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch a single field definition
   */
  const fetchFieldDefinition = async (fieldCode: string) => {
    const cacheKey = getCacheKey('field_definition', fieldCode)
    if (metadataCache.has(cacheKey)) {
      return metadataCache.get(cacheKey)
    }

    loading.value = true
    error.value = null

    try {
      const data = await fetchFromApi(
        `${apiBaseUrl}/field-definitions/by-code/${fieldCode}/`
      )

      metadataCache.set(cacheKey, data)
      return data
    } catch (err) {
      error.value = err as Error
      showMessageOnce(`Failed to load field definition: ${fieldCode}`, err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch page layouts for a business object
   */
  const fetchPageLayouts = async (objectCode: string, layoutType?: string) => {
    const cacheKey = getCacheKey('page_layouts', `${objectCode}:${layoutType || 'all'}`)
    if (metadataCache.has(cacheKey)) {
      return metadataCache.get(cacheKey)
    }

    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams({
        business_object: objectCode
      })

      if (layoutType) {
        params.append('layout_type', layoutType)
      }

      const data = await fetchFromApi(
        `${apiBaseUrl}/page-layouts/?${params}`
      )

      // Response structure: { success: true, data: { objectCode, fields: [...] } }
      const results = data.data?.fields || data.fields || data.results || []
      metadataCache.set(cacheKey, results)

      return results
    } catch (err) {
      error.value = err as Error
      showMessageOnce(`Failed to load page layouts for: ${objectCode}`, err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch a single page layout by code
   */
  const fetchPageLayout = async (layoutCode: string) => {
    const cacheKey = getCacheKey('page_layout', layoutCode)
    if (metadataCache.has(cacheKey)) {
      return metadataCache.get(cacheKey)
    }

    loading.value = true
    error.value = null

    try {
      let data: any = null

      if (layoutCode.includes(':')) {
        const [objectCode, rawMode] = layoutCode.split(':')
        const mode = toRuntimeMode(rawMode)
        data = await fetchFromApi(
          `${apiBaseUrl}/page-layouts/get_active_layout/?object_code=${objectCode}&mode=${mode}`
        )
      } else {
        data = await fetchFromApi(
          `${apiBaseUrl}/page-layouts/by-code/${layoutCode}/`
        )
      }

      metadataCache.set(cacheKey, data)
      return data
    } catch (err) {
      error.value = err as Error
      showMessageOnce(`Failed to load page layout: ${layoutCode}`, err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Resolve formula field value
   * This is a client-side basic implementation
   * Complex formulas should be evaluated on the backend
   */
  const resolveFormula = (
    field: FieldDefinition,
    formData: Record<string, any>
  ): any => {
    // Use camelCase property name
    if (!field.formula) return undefined

    try {
      const expression = field.formula
      let result = expression

      // Replace field references with actual values
      Object.keys(formData).forEach(key => {
        const regex = new RegExp(`\\{${key}\\}`, 'g')
        result = result.replace(regex, formData[key] || 0)
      })

      // Safe evaluation - only allow basic math operations
      // For production, use a proper expression parser library
      if (/^[\d\s+\-*/().]+$/.test(result)) {
        // eslint-disable-next-line no-new-func
        return new Function('return ' + result)()
      }

      return expression
    } catch (err) {
      console.warn('Formula evaluation failed:', err)
      return undefined
    }
  }

  /**
   * Get field options (for select/multiselect types)
   */
  const getFieldOptions = (field: FieldDefinition): { label: string; value: any }[] => {
    return field.options || []
  }

  /**
   * Validate field value against rules
   */
  const validateField = (
    field: FieldDefinition,
    value: any
  ): { valid: boolean; error?: string } => {
    // Required validation - use camelCase property name
    if (field.isRequired && (value === null || value === undefined || value === '')) {
      return { valid: false, error: `${field.label || field.name} is required` }
    }

    // Custom validation rules - use camelCase property name
    if (field.validationRules) {
      for (const rule of field.validationRules) {
        switch (rule.type) {
          case 'required':
            if (!value) {
              return { valid: false, error: rule.message }
            }
            break
          case 'pattern':
            if (value && !new RegExp(rule.value).test(value)) {
              return { valid: false, error: rule.message }
            }
            break
          case 'min':
            if (value !== null && value < rule.value) {
              return { valid: false, error: rule.message }
            }
            break
          case 'max':
            if (value !== null && value > rule.value) {
              return { valid: false, error: rule.message }
            }
            break
          case 'minLength':
            if (value && value.length < rule.value) {
              return { valid: false, error: rule.message }
            }
            break
          case 'maxLength':
            if (value && value.length > rule.value) {
              return { valid: false, error: rule.message }
            }
            break
        }
      }
    }

    return { valid: true }
  }

  /**
   * Clear all metadata cache
   */
  const clearCache = () => {
    metadataCache.clear()
  }

  /**
   * Clear specific cache entry
   */
  const clearCacheEntry = (type: string, identifier: string) => {
    const cacheKey = getCacheKey(type, identifier)
    metadataCache.delete(cacheKey)
  }

  return {
    loading,
    error,
    fetchBusinessObjects,
    fetchBusinessObject,
    fetchFieldDefinitions,
    fetchFieldDefinition,
    fetchPageLayouts,
    fetchPageLayout,
    resolveFormula,
    getFieldOptions,
    validateField,
    clearCache,
    clearCacheEntry
  }
}

/**
 * Helper to create a typed metadata hook for a specific business object
 */
export function createObjectMetadataHook(objectCode: string) {
  const {
    loading,
    error,
    fetchBusinessObject,
    fetchFieldDefinitions,
    fetchPageLayouts,
    resolveFormula,
    getFieldOptions,
    validateField,
    clearCacheEntry
  } = useMetadata()

  const businessObject = ref<BusinessObject | null>(null)
  const fieldDefinitions = ref<FieldDefinition[]>([])
  const formLayout = ref<PageLayout | null>(null)
  const listLayout = ref<PageLayout | null>(null)

  const loadMetadata = async () => {
    try {
      const [bo, fields, layouts] = await Promise.all([
        fetchBusinessObject(objectCode),
        fetchFieldDefinitions(objectCode),
        fetchPageLayouts(objectCode)
      ])

      businessObject.value = bo
      fieldDefinitions.value = fields

      // Separate layouts by mode - use camelCase property name
      layouts.forEach((layout: PageLayout) => {
        if (layout.mode === 'edit' || layout.layoutType === 'form') {
          formLayout.value = layout
        } else if (layout.mode === 'search' || layout.layoutType === 'search') {
          // Search layouts are handled separately
        }
        // List layouts are auto-generated from FieldDefinition.show_in_list
      })

      return { bo, fields, layouts }
    } catch (err) {
      console.error('Failed to load metadata:', err)
      throw err
    }
  }

  const clearObjectCache = () => {
    clearCacheEntry('business_object', objectCode)
    clearCacheEntry('field_definitions', objectCode)
    clearCacheEntry('page_layouts', `${objectCode}:form`)
    clearCacheEntry('page_layouts', `${objectCode}:list`)
    businessObject.value = null
    fieldDefinitions.value = []
    formLayout.value = null
    listLayout.value = null
  }

  return {
    loading,
    error,
    businessObject,
    fieldDefinitions,
    formLayout,
    listLayout,
    loadMetadata,
    resolveFormula,
    getFieldOptions,
    validateField,
    clearCache: clearObjectCache
  }
}
