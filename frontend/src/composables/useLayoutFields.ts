/**
 * Layout Fields Composable
 *
 * Provides field metadata access for the layout designer.
 * Uses the unified request utility for authentication and error handling.
 *
 * Features:
 * - Fetches fields by object code using businessObjectApi
 * - Caches field data to avoid redundant API calls
 * - Groups fields by type for better UI organization
 * - Provides search functionality for field filtering
 *
 * @reference docs/plans/2025-02-04-composables-api-layer-prd.md
 */
import { ref, computed, type Ref } from 'vue'
import { businessObjectApi } from '@/api/system'
import type { AvailableField, FieldGroup } from '@/api/system'
import { normalizeFieldType } from '@/utils/fieldType'

// Re-export types from system.ts for convenience
export type { AvailableField, FieldGroup }

/**
 * Field fetch options for layout fields
 */
export interface LayoutFieldsFetchOptions {
  /** Force refresh from API, bypassing cache */
  force?: boolean
  /** Include reverse relation fields */
  includeRelations?: boolean
}

/**
 * Composable return type
 */
export interface UseLayoutFieldsReturn {
  /** All available fields (editable only, no reverse relations by default) */
  availableFields: Ref<AvailableField[]>
  /** Fields grouped by type for UI organization */
  fieldGroups: Ref<FieldGroup[]>
  /** Loading state */
  loading: Ref<boolean>
  /** Error state */
  error: Ref<Error | null>
  /** Fetch fields for the given object code */
  fetchFields: (options?: LayoutFieldsFetchOptions) => Promise<void>
  /** Search fields by name or code */
  searchFields: (query: string) => AvailableField[]
  /** Clear cached data */
  clearCache: () => void
}

/**
 * Field metadata cache
 * Key format: objectCode
 */
const fieldsCache = new Map<string, AvailableField[]>()

/**
 * Field type group definitions
 */
const FIELD_TYPE_GROUPS: Record<string, { label: string; icon: string }> = {
  basic: { label: 'Basic Fields', icon: 'Document' },
  text: { label: 'Text Fields', icon: 'Edit' },
  number: { label: 'Number Fields', icon: 'Calculator' },
  date: { label: 'Date Fields', icon: 'Calendar' },
  selection: { label: 'Selection Fields', icon: 'Selector' },
  reference: { label: 'Reference Fields', icon: 'Link' },
  media: { label: 'Media Fields', icon: 'Picture' },
  system: { label: 'System Fields', icon: 'Setting' }
}

/**
 * Get field type group for a given field type
 */
function getFieldTypeGroup(fieldType: string): string {
  const type = normalizeFieldType(fieldType || 'text')

  if (['text', 'textarea', 'rich_text', 'email', 'url', 'phone', 'password', 'code', 'color'].includes(type)) return 'text'
  if (['number', 'percent', 'currency', 'slider', 'rate'].includes(type)) return 'number'
  if (['date', 'datetime', 'time', 'daterange', 'year', 'month'].includes(type)) return 'date'
  if (['select', 'radio', 'checkbox', 'multi_select', 'boolean', 'switch', 'dictionary'].includes(type)) return 'selection'
  if (['reference', 'user', 'department', 'location', 'asset', 'sub_table'].includes(type)) return 'reference'
  if (['image', 'file', 'attachment'].includes(type)) return 'media'
  if (['id', 'created_at', 'updated_at', 'created_by', 'organization'].includes(type)) return 'system'

  return 'basic'
}

/**
 * Get display name for field type
 */
function getFieldTypeDisplay(fieldType: string): string {
  const type = normalizeFieldType(fieldType || 'text')
  const displayNames: Record<string, string> = {
    text: 'Text',
    textarea: 'Long Text',
    rich_text: 'Rich Text',
    email: 'Email',
    url: 'URL',
    phone: 'Phone',
    number: 'Number',
    percent: 'Percentage',
    currency: 'Currency',
    slider: 'Slider',
    rate: 'Rate',
    date: 'Date',
    datetime: 'Date Time',
    time: 'Time',
    daterange: 'Date Range',
    year: 'Year',
    month: 'Month',
    boolean: 'Boolean',
    switch: 'Switch',
    select: 'Dropdown',
    multi_select: 'Multi Select',
    radio: 'Radio',
    checkbox: 'Checkbox',
    dictionary: 'Dictionary',
    reference: 'Reference',
    user: 'User',
    department: 'Department',
    location: 'Location',
    asset: 'Asset',
    sub_table: 'Sub Table',
    image: 'Image',
    file: 'File',
    attachment: 'Attachment',
    formula: 'Formula'
  }

  return displayNames[type] || type
}

/**
 * Layout fields composable
 *
 * Fetches and manages field metadata for layout designer.
 *
 * @param objectCode - Business object code (e.g., 'Asset', 'Maintenance')
 * @returns Layout fields composable API
 *
 * @example
 * ```ts
 * const { availableFields, fieldGroups, fetchFields, loading } = useLayoutFields('Asset')
 *
 * onMounted(async () => {
 *   await fetchFields()
 * })
 * ```
 */
export function useLayoutFields(objectCode: string): UseLayoutFieldsReturn {
  const loading = ref(false)
  const error = ref<Error | null>(null)
  const availableFields = ref<AvailableField[]>([])

  /**
   * Group fields by type for organized display
   */
  const fieldGroups = computed<FieldGroup[]>(() => {
    const groups: Record<string, AvailableField[]> = {}

    // Group fields by type category
    for (const field of availableFields.value) {
      const groupKey = getFieldTypeGroup(field.fieldType)
      if (!groups[groupKey]) {
        groups[groupKey] = []
      }
      groups[groupKey].push(field)
    }

    // Convert to array format
    return Object.entries(groups)
      .filter(([_, fields]) => fields.length > 0)
      .map(([type, fields]) => ({
        type,
        label: FIELD_TYPE_GROUPS[type]?.label || type,
        icon: FIELD_TYPE_GROUPS[type]?.icon || 'Document',
        fields
      }))
      .sort((a, b) => a.label.localeCompare(b.label))
  })

  /**
   * Fetch field definitions for the business object
   */
  const fetchFields = async (options: LayoutFieldsFetchOptions = {}): Promise<void> => {
    loading.value = true
    error.value = null

    // Return cached data if available and not forcing refresh
    if (!options.force && fieldsCache.has(objectCode)) {
      availableFields.value = fieldsCache.get(objectCode)!
      loading.value = false
      return
    }

    try {
      // Use businessObjectApi instead of fetch for proper authentication
      const response = await businessObjectApi.getFieldsWithContext(
        objectCode,
        'form',
        { includeRelations: options.includeRelations !== false }
      )

      // request.ts unwraps { success, data }, so support both unwrapped and legacy shapes
      const apiResponse = (response as any)?.data ?? response
      const data = (apiResponse as any)?.data ?? apiResponse
      const rawFields: any[] = data?.editableFields || data?.fields || []

      if (rawFields.length > 0) {
        // Transform editable fields to available fields
        const fields: AvailableField[] = rawFields.map((field: any) => {
          const normalizedType = normalizeFieldType(field.fieldType || field.type || 'text')
          return {
            ...field,
            fieldType: normalizedType,
            fieldTypeDisplay: getFieldTypeDisplay(normalizedType),
            showInForm: (field as any).showInForm !== false,
            showInList: (field as any).showInList !== false,
            showInDetail: (field as any).showInDetail !== false,
            isHidden: (field as any).isHidden || false
          }
        })

        availableFields.value = fields
        fieldsCache.set(objectCode, fields)
      }
    } catch (err) {
      error.value = err as Error
      availableFields.value = []
    } finally {
      loading.value = false
    }
  }

  /**
   * Search fields by name or code
   */
  const searchFields = (query: string): AvailableField[] => {
    if (!query.trim()) {
      return availableFields.value
    }

    const lowerQuery = query.toLowerCase()
    return availableFields.value.filter(field =>
      String(field.name || '').toLowerCase().includes(lowerQuery) ||
      String(field.code || '').toLowerCase().includes(lowerQuery)
    )
  }

  /**
   * Clear cached field data
   */
  const clearCache = (): void => {
    fieldsCache.delete(objectCode)
    availableFields.value = []
  }

  return {
    availableFields,
    fieldGroups,
    loading,
    error,
    fetchFields,
    searchFields,
    clearCache
  }
}

/**
 * Clear all field cache (useful for logout/org switch)
 */
export function clearAllLayoutFieldsCache(): void {
  fieldsCache.clear()
}
