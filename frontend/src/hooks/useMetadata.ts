import { ref, computed, watch } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

/**
 * Metadata types for low-code platform
 */

export interface FieldDefinition {
  id: string
  name: string
  code: string
  field_type: 'text' | 'number' | 'date' | 'datetime' | 'boolean' | 'select' |
           'multiselect' | 'reference' | 'file' | 'richtext' | 'formula' |
           'subtable' | 'user' | 'department' | 'location'
  label: string
  description?: string
  is_required: boolean
  default_value?: any
  options?: { label: string; value: any }[]
  reference_object?: string
  formula_expression?: string
  subtable_fields?: FieldDefinition[]
  validation_rules?: ValidationRule[]
  placeholder?: string
  help_text?: string
}

export interface ValidationRule {
  type: 'required' | 'pattern' | 'min' | 'max' | 'minLength' | 'maxLength' | 'custom'
  value?: any
  message: string
}

export interface BusinessObject {
  id: string
  name: string
  code: string
  description?: string
  icon?: string
  module: string
  is_active: boolean
  fields?: FieldDefinition[]
}

export interface PageLayout {
  id: string
  name: string
  code: string
  layout_type: 'form' | 'list' | 'detail'
  business_object: string
  layout_config: LayoutConfig
}

export interface LayoutConfig {
  sections: LayoutSection[]
  actions?: LayoutAction[]
}

export interface LayoutSection {
  id: string
  title?: string
  type: 'default' | 'card' | 'fieldset' | 'tab' | 'collapse'
  collapsible?: boolean
  collapsed?: boolean
  column_count?: number
  fields: LayoutField[]
  order: number
}

export interface LayoutField {
  field_code: string
  span?: number
  readonly?: boolean
  visible?: boolean
  order: number
}

export interface LayoutAction {
  code: string
  label: string
  type: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  action_type: 'submit' | 'cancel' | 'custom' | 'workflow'
  api_endpoint?: string
  confirm_message?: string
  order: number
}

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

  const apiBaseUrl = '/api/system'

  /**
   * Generic fetch helper with error handling
   */
  const fetchFromApi = async (url: string, options: RequestInit = {}): Promise<any> => {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Authorization': `Bearer ${userStore.token}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    })

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`)
    }

    const data = await response.json()
    // Handle both direct data and wrapped response formats
    return data.data || data
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

      const results = data.results || data || []
      metadataCache.set(cacheKey, results)

      return results
    } catch (err) {
      error.value = err as Error
      ElMessage.error('Failed to load business objects')
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
      const fields = await fetchFieldDefinitions(objectCode)
      data.fields = fields

      metadataCache.set(cacheKey, data)

      return data
    } catch (err) {
      error.value = err as Error
      ElMessage.error(`Failed to load business object: ${objectCode}`)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch field definitions for a business object
   */
  const fetchFieldDefinitions = async (objectCode: string) => {
    const cacheKey = getCacheKey('field_definitions', objectCode)
    if (metadataCache.has(cacheKey)) {
      return metadataCache.get(cacheKey)
    }

    loading.value = true
    error.value = null

    try {
      const data = await fetchFromApi(
        `${apiBaseUrl}/field-definitions/?business_object=${objectCode}`
      )

      const results = data.results || data || []
      metadataCache.set(cacheKey, results)

      return results
    } catch (err) {
      error.value = err as Error
      ElMessage.error(`Failed to load field definitions for: ${objectCode}`)
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
      ElMessage.error(`Failed to load field definition: ${fieldCode}`)
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

      const results = data.results || data || []
      metadataCache.set(cacheKey, results)

      return results
    } catch (err) {
      error.value = err as Error
      ElMessage.error(`Failed to load page layouts for: ${objectCode}`)
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
      const data = await fetchFromApi(
        `${apiBaseUrl}/page-layouts/by-code/${layoutCode}/`
      )

      metadataCache.set(cacheKey, data)
      return data
    } catch (err) {
      error.value = err as Error
      ElMessage.error(`Failed to load page layout: ${layoutCode}`)
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
    if (!field.formula_expression) return undefined

    try {
      const expression = field.formula_expression
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
    // Required validation
    if (field.is_required && (value === null || value === undefined || value === '')) {
      return { valid: false, error: `${field.label} is required` }
    }

    // Custom validation rules
    if (field.validation_rules) {
      for (const rule of field.validation_rules) {
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

      // Separate layouts by type
      layouts.forEach((layout: PageLayout) => {
        if (layout.layout_type === 'form') {
          formLayout.value = layout
        } else if (layout.layout_type === 'list') {
          listLayout.value = layout
        }
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
