/**
 * Context-Aware Field Metadata Composable
 *
 * Provides field metadata with context filtering for the unified field display architecture.
 * Separates editable fields from reverse relations based on rendering context.
 *
 * Uses businessObjectApi instead of native fetch for proper authentication.
 *
 * Reference: docs/plans/2025-02-03-unified-field-display-design.md
 * Reference: docs/plans/2025-02-04-composables-api-layer-prd.md
 */
import { ref, type Ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { businessObjectApi } from '@/api/system'
import i18n from '@/locales'
import type { FieldMetadataResponse, RelationDisplayMode } from '@/types'
import { sortFieldsByRuntimeOrder } from '@/platform/layout/runtimeFieldPolicy'
import { localizeMultilingualObject } from '@/utils/localeText'

// Use the metadata FieldDefinition which has all needed properties
import type { FieldDefinition } from '@/types/metadata'

/**
 * Fetch options for field metadata
 */
export interface FetchFieldMetadataOptions {
  /** Whether to include reverse relations */
  includeRelations?: boolean
  /** Force refresh from API */
  force?: boolean
}

/**
 * Field metadata composable return type
 */
export interface UseFieldMetadataReturn {
  /** All fields (editable + reverse relations) */
  fields: Ref<any[]>

  /** Editable fields only (non-reverse relations) */
  editableFields: Ref<any[]>

  /** Reverse relation fields only */
  reverseRelations: Ref<any[]>

  /** Loading state */
  loading: Ref<boolean>

  /** Error state */
  error: Ref<Error | null>

  /** Current context */
  context: Ref<'form' | 'detail' | 'list'>

  /**
   * Fetch field metadata for the given context
   * @param context Rendering context (form/detail/list)
   * @param options Fetch options
   */
  fetchFields: (
    context: 'form' | 'detail' | 'list',
    options?: FetchFieldMetadataOptions
  ) => Promise<FieldMetadataResponse | null>

  /**
   * Clear cached metadata for this object
   */
  clearCache: () => void

  /**
   * Get reverse relations by display mode
   * @param mode Display mode to filter by
   */
  getRelationsByMode: (mode: RelationDisplayMode) => any[]

  /**
   * Check if a field should be visible in current context
   * @param fieldCode Field code to check
   */
  isFieldVisible: (fieldCode: string) => boolean
}

/**
 * Metadata cache for field metadata responses
 * Key format: orgId:objectCode:context
 *
 * Note: Using any type for cache to avoid FieldDefinition type conflicts
 * between @/types/metadata and @/types/field
 */
const fieldMetadataCache = new Map<string, any>()

/**
 * Context-aware field metadata composable
 *
 * Provides unified field metadata access with context filtering,
 * separating editable fields from reverse relations.
 *
 * @param objectCode Business object code (e.g., 'Asset', 'Maintenance')
 * @returns Field metadata composable API
 *
 * @example
 * ```ts
 * const { editableFields, reverseRelations, fetchFields, loading } = useFieldMetadata('Asset')
 *
 * onMounted(async () => {
 *   await fetchFields('detail')
 * })
 *
 * // In template:
 * // - editableFields: form fields for editing
 * // - reverseRelations: related objects (e.g., maintenance_records)
 * ```
 */
export function useFieldMetadata(
  objectCode: string
): UseFieldMetadataReturn {
  const userStore = useUserStore()

  const loading = ref(false)
  const error = ref<Error | null>(null)
  const context = ref<'form' | 'detail' | 'list'>('form')

  const fields = ref<any[]>([])
  const editableFields = ref<any[]>([])
  const reverseRelations = ref<any[]>([])

  /**
   * Get cache key for field metadata requests
   */
  const getCacheKey = (ctx: 'form' | 'detail' | 'list'): string => {
    const orgId = userStore.currentOrganization?.id || 'default'
    return `${orgId}:${objectCode}:${ctx}`
  }

  /**
   * Fetch field metadata with context filtering
   */
  const fetchFields = async (
    ctx: 'form' | 'detail' | 'list' = 'form',
    options: FetchFieldMetadataOptions = {}
  ): Promise<FieldMetadataResponse | null> => {
    context.value = ctx
    loading.value = true
    error.value = null

    const cacheKey = getCacheKey(ctx)

    // Return cached data if available and not forcing refresh
    if (!options.force && fieldMetadataCache.has(cacheKey)) {
      const cached = fieldMetadataCache.get(cacheKey)!
      fields.value = [...cached.editableFields, ...cached.reverseRelations]
      editableFields.value = cached.editableFields
      reverseRelations.value = cached.reverseRelations
      return cached
    }

    try {
      // Use businessObjectApi instead of native fetch for proper authentication
      const response = await businessObjectApi.getFieldsWithContext(
        objectCode,
        ctx,
        { includeRelations: options.includeRelations !== false }
      )

      // The API returns data directly (not wrapped in {success, data})
      // Handle both formats for compatibility:
      // Format 1: {success: true, data: {editableFields, reverseRelations, context}}
      // Format 2: {editableFields, reverseRelations, context} (direct)
      const rawResponse = response.data || response

      // Check if it's wrapped format or direct format
      let responseData: {
        editable_fields?: any[]
        editableFields?: any[]
        reverse_relations?: any[]
        reverseRelations?: any[]
        context: 'form' | 'detail' | 'list'
      }

      if (rawResponse.success && rawResponse.data) {
        // Wrapped format: {success: true, data: {...}}
        responseData = rawResponse.data
      } else if (rawResponse.editableFields !== undefined || rawResponse.editable_fields !== undefined) {
        // Direct format: {editableFields, reverseRelations, context}
        responseData = rawResponse
      } else {
        throw new Error('Invalid response format from field metadata API')
      }

      // Handle both snake_case (backend) and camelCase (for backwards compatibility)
      const rawEditableFields = responseData.editable_fields || responseData.editableFields || []
      const rawReverseRelations = responseData.reverse_relations || responseData.reverseRelations || []

      // Convert API fields to FieldDefinition format
      const editableFieldsConverted: FieldDefinition[] = sortFieldsByRuntimeOrder(
        rawEditableFields.map((f) => {
          const localized = localizeMultilingualObject(f)
          return {
            ...localized,
            id: f.id || f.code,
            label: localized.label || localized.name || f.label || f.name,
            span: f.span || 12
          }
        })
      ) as FieldDefinition[]

      const reverseRelationsConverted: FieldDefinition[] = rawReverseRelations.map((f) => {
        const localized = localizeMultilingualObject(f)
        return {
          ...localized,
        id: f.id || f.code,
        label: localized.label || localized.name || f.label || f.name,
        span: f.span || 12
        }
      })

      // Use type assertion to avoid FieldDefinition type conflicts
      const data: FieldMetadataResponse = {
        editableFields: editableFieldsConverted as any,
        reverseRelations: reverseRelationsConverted as any,
        context: responseData.context
      }

      // Update state
      fields.value = [...data.editableFields, ...data.reverseRelations]
      editableFields.value = data.editableFields
      reverseRelations.value = data.reverseRelations

      // Cache the response
      fieldMetadataCache.set(cacheKey, data)

      return data
    } catch (err) {
      error.value = err as Error
      ElMessage.error(i18n.global.t('common.messages.loadFailed'))
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear cached metadata for this object
   */
  const clearCache = () => {
    const orgId = userStore.currentOrganization?.id || 'default'
    const contexts: Array<'form' | 'detail' | 'list'> = ['form', 'detail', 'list']

    contexts.forEach(ctx => {
      fieldMetadataCache.delete(`${orgId}:${objectCode}:${ctx}`)
    })

    fields.value = []
    editableFields.value = []
    reverseRelations.value = []
  }

  /**
   * Get reverse relations filtered by display mode
   */
  const getRelationsByMode = (mode: RelationDisplayMode): any[] => {
    return reverseRelations.value.filter(
      rel => rel.relationDisplayMode === mode || rel.relation_display_mode === mode
    )
  }

  /**
   * Check if a field should be visible in current context
   */
  const isFieldVisible = (fieldCode: string): boolean => {
    const field = fields.value.find(f => f.code === fieldCode)
    if (!field) return false

    // Check context-specific visibility
    if (context.value === 'form') {
      return field.showInForm !== false && !field.isHidden
    } else if (context.value === 'detail') {
      return field.showInDetail !== false && !field.isHidden
    } else if (context.value === 'list') {
      return field.showInList !== false && !field.isHidden
    }

    return true
  }

  return {
    fields,
    editableFields,
    reverseRelations,
    loading,
    error,
    context,
    fetchFields,
    clearCache,
    getRelationsByMode,
    isFieldVisible
  }
}

/**
 * Clear all field metadata cache (useful for logout/org switch)
 */
export function clearAllFieldMetadataCache(): void {
  fieldMetadataCache.clear()
}
