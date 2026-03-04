/**
 * useDynamicForm Hook
 *
 * Manages form state, loads metadata, generates validation rules,
 * and transforms layout configurations for dynamic form rendering.
 *
 * This hook is the core of the dynamic form engine, bridging the gap
 * between backend metadata and frontend form components.
 */

import { ref, computed } from 'vue'
import type { FieldDefinition, FieldType } from '@/types'
import type { RuntimeLayoutConfig } from '@/types/runtime'
import { normalizeLayoutConfig } from '@/adapters/layoutNormalizer'
import { snakeToCamel } from '@/utils/case'
import { normalizeFieldType } from '@/utils/fieldType'
import { resolveRuntimeLayout } from '@/platform/layout/runtimeLayoutResolver'
import { resolveFieldValue } from '@/utils/fieldKey'
import { isCreateRuntimeContext } from '@/platform/layout/runtimeFieldPolicy'
import type { RenderSchema } from '@/platform/layout/renderSchema'
import { projectRuntimeLayoutFromRenderSchema } from '@/platform/layout/renderSchemaProjector'
import type { RuntimeMode } from '@/contracts/runtimeContract'
import { buildAndOrderFields } from '@/platform/layout/unifiedFieldOrder'
import { compileLayoutSchema } from '@/platform/layout/layoutCompiler'

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Business object action
 */
export interface BusinessObjectAction {
  code: string
  label: string
  type: 'primary' | 'default' | 'danger' | 'warning' | 'success'
  actionType: 'submit' | 'cancel' | 'custom' | 'workflow'
  apiEndpoint?: string
  method?: 'POST' | 'GET' | 'PUT' | 'DELETE'
  confirmMessage?: string
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Composable for dynamic form management
 *
 * @param businessObject - Business object code (e.g., 'Asset', 'Consumable')
 * @param layoutCode - Layout type to load ('form', 'detail', etc.)
 * @param layoutConfig - Optional local layout config for preview mode
 * @param availableFields - Optional field list for preview mode
 * @returns Form state and methods
 */
export function useDynamicForm(
  businessObject: string,
  layoutCode: string = 'form',
  layoutConfig: Record<string, unknown> | null = null,
  availableFields: FieldDefinition[] | null = null,
  instanceId: string | null = null
) {
  // ============================================================================
  // Reactive State
  // ============================================================================

  /** Form element reference */
  const formRef = ref<{
    validate?: () => Promise<boolean> | boolean
    resetFields?: () => void
    clearValidate?: () => void
  } | null>(null)

  /** Form data object */
  const formData = ref<Record<string, unknown>>({})

  /** Field definitions from metadata */
  const fieldDefinitions = ref<FieldDefinition[]>([])

  /** Raw layout config (from API or preview) */
  const layoutConfigState = ref<Record<string, unknown> | null>(null)

  const toRuntimeMode = (value: string): RuntimeMode => {
    const raw = String(value || '').toLowerCase()
    if (raw === 'readonly' || raw === 'detail') return 'readonly'
    if (raw === 'list') return 'list'
    if (raw === 'search') return 'search'
    return 'edit'
  }

  const FIELD_TYPES: FieldType[] = [
    'text', 'textarea', 'richtext', 'number', 'currency', 'percent',
    'date', 'datetime', 'time', 'boolean', 'switch', 'select', 'multi_select',
    'radio', 'checkbox', 'reference', 'user', 'department', 'file', 'image',
    'attachment', 'qr_code', 'barcode', 'formula', 'subtable', 'location', 'organization'
  ]

  const toFieldType = (value: unknown): FieldType => {
    const normalized = normalizeFieldType(String(value || 'text'))
    return FIELD_TYPES.includes(normalized as FieldType) ? (normalized as FieldType) : 'text'
  }

  const toBoolean = (value: unknown, fallback = false): boolean => {
    if (typeof value === 'boolean') return value
    if (typeof value === 'number') return value !== 0
    if (typeof value === 'string') {
      const normalized = value.trim().toLowerCase()
      if (normalized === 'true' || normalized === '1') return true
      if (normalized === 'false' || normalized === '0') return false
    }
    return fallback
  }

  const toNumber = (value: unknown, fallback: number): number => {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : fallback
  }

  const renderSchema = computed<RenderSchema>(() => {
    return compileLayoutSchema({
      layoutConfig: layoutConfigState.value,
      fields: fieldDefinitions.value as unknown as Record<string, unknown>[],
      mode: toRuntimeMode(layoutCode)
    }).renderSchema
  })

  /** Runtime layout projected from shared RenderSchema */
  const runtimeLayout = computed<RuntimeLayoutConfig>(() => {
    return projectRuntimeLayoutFromRenderSchema(renderSchema.value)
  })

  /** Loading state */
  const loading = ref(false)

  /** Error state */
  const error = ref<string | null>(null)

  /** Business object actions */
  const businessObjectActions = ref<BusinessObjectAction[]>([])

  // ============================================================================
  // Validation Rules
  // ============================================================================

  /**
   * Generate Element Plus validation rules from field definitions
   */
  const formRules = computed(() => {
    const rules: Record<string, Array<Record<string, unknown>>> = {}

    fieldDefinitions.value.forEach((field) => {
      const fieldRules: Array<Record<string, unknown>> = []

      // Required validation
      if (field.isRequired) {
        fieldRules.push({
          required: true,
          message: `Please enter ${field.name}`,
          trigger: getValidationTrigger(field.fieldType)
        })
      }

      // Type-specific validations
      if (String(field.fieldType) === 'email') {
        fieldRules.push({
          type: 'email',
          message: 'Please enter a valid email address',
          trigger: 'blur'
        })
      }

      if (field.fieldType === 'number' || field.fieldType === 'currency') {
        fieldRules.push({
          validator: (_rule: unknown, value: unknown, callback: (error?: Error) => void) => {
            if (value === null || value === undefined || value === '') return callback()
            if (typeof value === 'number' && !Number.isNaN(value)) return callback()
            if (typeof value === 'string' && value.trim() !== '' && !Number.isNaN(Number(value))) return callback()
            callback(new Error('Please enter a valid number'))
          },
          trigger: 'blur'
        })
      }

      // Custom length validation
      if (field.componentProps?.maxLength) {
        fieldRules.push({
          max: field.componentProps.maxLength,
          message: `Maximum length is ${field.componentProps.maxLength}`,
          trigger: 'blur'
        })
      }

      if (fieldRules.length > 0) {
        rules[field.code] = fieldRules
      }
    })

    return rules
  })

  /**
   * Get validation trigger based on field type
   */
  function getValidationTrigger(fieldType: string): string {
    const selectTypes = ['select', 'radio', 'checkbox', 'multi_select', 'user', 'department', 'reference']
    return selectTypes.includes(fieldType) ? 'change' : 'blur'
  }

  // ============================================================================
  // Metadata Loading
  // ============================================================================

  /**
   * Load metadata for the business object
   */
  async function loadMetadata(): Promise<void> {
    loading.value = true
    error.value = null

    try {
      // Use local config if provided (preview mode)
      if (layoutConfig && availableFields) {
        fieldDefinitions.value = buildAndOrderFields({
          fields: availableFields as unknown as Record<string, unknown>[],
          layoutConfig,
          mode: toRuntimeMode(layoutCode)
        }) as FieldDefinition[]
        layoutConfigState.value = normalizeLayoutConfig(layoutConfig)
        initializeFormData()
        return
      }

      // Prefer the unified runtime endpoint (fields + layout in one request).
      // Fall back to legacy calls if the endpoint is unavailable or errors.
      const resolved = await resolveRuntimeLayout(businessObject, layoutCode, {
        includeRelations: true
      })
      const fieldsData: unknown[] = Array.isArray(resolved.fields) ? resolved.fields : []
      const layoutData: Record<string, unknown> | null =
        resolved.layoutConfig && typeof resolved.layoutConfig === 'object'
          ? (resolved.layoutConfig as Record<string, unknown>)
          : null

      // Process field definitions
      if (fieldsData && Array.isArray(fieldsData)) {
        const transformedFields = fieldsData
          .filter((field): field is Record<string, unknown> => !!field && typeof field === 'object')
          .map(transformFieldDefinition)
        fieldDefinitions.value = buildAndOrderFields({
          fields: transformedFields as unknown as Record<string, unknown>[],
          layoutConfig: layoutData,
          mode: toRuntimeMode(layoutCode)
        }) as FieldDefinition[]
      } else {
        fieldDefinitions.value = []
      }

      // Process layout configuration
      layoutConfigState.value = layoutData ? normalizeLayoutConfig(layoutData) : null

      // Initialize form data with default values
      initializeFormData()

    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : 'Failed to load form metadata'
      // Set empty defaults on error
      fieldDefinitions.value = []
      layoutConfigState.value = null
      formData.value = {}
    } finally {
      loading.value = false
    }
  }

  /**
   * Transform field definition from API to internal format
   * Backend returns camelCase directly via djangorestframework-camel-case
   *
   * API response structure for hardcoded models (Asset, etc.):
   *   - fieldName: The database field name (e.g., "qr_code", "images")
   *   - fieldType: The field type (e.g., "qr_code", "image", "file")
   *   - displayName: Human-readable name
   *
   * API response structure for custom objects (FieldDefinition):
   *   - code: Field code
   *   - fieldType: Field type
   *   - name: Display name
   */
  function transformFieldDefinition(apiField: Record<string, unknown>): FieldDefinition {
    const componentProps =
      (apiField.componentProps as Record<string, unknown> | undefined) ||
      (apiField.component_props as Record<string, unknown> | undefined) ||
      {}

    return {
      // Handle both fieldName (hardcoded models) and code (custom objects)
      code: String(apiField.fieldName || apiField.code || apiField.fieldCode || ''),
      // Handle displayName (hardcoded) and name/label (custom)
      name: String(apiField.displayName || apiField.name || apiField.label || ''),
      // fieldType is consistent across both
      fieldType: toFieldType(apiField.fieldType ?? apiField.type),
      // Handle camelCase and snake_case variants
      isRequired: toBoolean(apiField.isRequired ?? apiField.is_required ?? apiField.required, false),
      isReadonly: toBoolean(apiField.isReadonly ?? apiField.is_readonly ?? apiField.readOnly, false),
      isHidden: toBoolean(apiField.isHidden ?? apiField.is_hidden, false),
      isVisible: apiField.isVisible !== undefined
        ? toBoolean(apiField.isVisible, true)
        : (apiField.show_in_form !== undefined ? toBoolean(apiField.show_in_form, true) : true),
      sortOrder: toNumber(apiField.sortOrder ?? apiField.sort_order, 0),
      defaultValue: apiField.defaultValue ?? apiField.default_value,
      options: Array.isArray(apiField.options) ? (apiField.options as any[]) : [],
      componentProps,
      description: typeof apiField.description === 'string' ? apiField.description : undefined,
      placeholder: typeof apiField.placeholder === 'string' ? apiField.placeholder : undefined,
      span: toNumber(apiField.span ?? componentProps.span, 12),
      referenceObject: (() => {
        const value = apiField.referenceObject || apiField.reference_model_path || apiField.referenceModelPath
        return value ? String(value) : undefined
      })()
    }
  }

  /**
   * Initialize form data with default values
   */
  function initializeFormData(preserveExisting: boolean = true): void {
    const data: Record<string, unknown> = preserveExisting ? { ...formData.value } : {}
    const createContext = isCreateRuntimeContext(instanceId)

    fieldDefinitions.value.forEach(field => {
      // Preserve externally-provided values (e.g. detail/edit page passes modelValue)
      // If canonical exists but is empty, try to backfill from camelCase key.
      if (preserveExisting && Object.prototype.hasOwnProperty.call(data, field.code)) {
        const current = data[field.code]
        if (current !== undefined && current !== null && current !== '') return

        const camelKey = snakeToCamel(field.code || '')
        if (camelKey && Object.prototype.hasOwnProperty.call(data, camelKey)) {
          const candidate = data[camelKey]
          if (candidate !== undefined && candidate !== null && candidate !== '') {
            data[field.code] = candidate
            return
          }
        }
      }

      // Canonical key backfill from known aliases/custom bags.
      if (preserveExisting) {
        const candidate = resolveFieldValue(data, {
          fieldCode: field.code,
          dataKey: field.code.includes('_') ? snakeToCamel(field.code) : field.code,
          includeWrappedData: false,
          includeCustomBags: true,
          treatEmptyAsMissing: true,
          returnEmptyMatch: false
        })
        if (candidate !== undefined) {
          data[field.code] = candidate
          return
        }
      }

      // Default values are create-only; edit/readonly should reflect persisted data.
      if (!createContext) return

      if (field.defaultValue !== undefined && field.defaultValue !== null) {
        data[field.code] = field.defaultValue
        return
      }

      // Set type-specific defaults
      switch (field.fieldType) {
        case 'boolean':
        case 'switch':
          data[field.code] = false
          break
        case 'multi_select':
        case 'checkbox':
          data[field.code] = []
          break
        default:
          data[field.code] = null
      }
    })

    formData.value = data
  }

  // ============================================================================
  // Form Methods
  // ============================================================================

  /**
   * Validate the form
   */
  async function validate(): Promise<boolean> {
    if (!formRef.value) {
      console.warn('useDynamicForm: formRef is not available')
      return false
    }

    try {
      const result = await formRef.value.validate?.()
      return result === undefined ? true : result
    } catch (err) {
      console.warn('useDynamicForm: validation failed', err)
      return false
    }
  }

  /**
   * Reset form to initial state
   */
  function resetFields(): void {
    if (!formRef.value) {
      console.warn('useDynamicForm: formRef is not available for reset')
      return
    }

    formRef.value.resetFields?.()
    initializeFormData(false)
  }

  /**
   * Clear form validation
   */
  function clearValidation(): void {
    if (!formRef.value) return
    formRef.value.clearValidate?.()
  }

  // ============================================================================
  // Return Public Interface
  // ============================================================================

  return {
    // Form reference and data
    formRef,
    formData,
    formRules,

    // Metadata
    fieldDefinitions,
    runtimeLayout,
    renderSchema,

    // State
    loading,
    error,

    // Methods
    loadMetadata,
    validate,
    resetFields,
    clearValidation,

    // Actions
    businessObjectActions
  }
}
