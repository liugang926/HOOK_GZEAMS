/**
 * Field Type Definitions
 *
 * Unified field definition types for the low-code metadata platform.
 * All properties use camelCase to match backend djangorestframework-camel-case output.
 *
 * Reference: docs/plans/frontend/TYPE_UNIFICATION_EXECUTION_PLAN.md
 */

/**
 * Unified field definition using camelCase (matches backend)
 * Consolidates duplicate definitions from:
 * - api/dynamic.ts
 * - hooks/useMetadata.ts
 * - components/engine/hooks/useDynamicForm.ts
 */
export interface FieldDefinition {
  /** Unique identifier (optional for new fields) */
  id?: string

  /** Field code - unique identifier for the field */
  code: string

  /** Field display name */
  name: string

  /** Alternative label for display */
  label?: string

  /** Field type */
  fieldType: FieldType

  /** Display name for field type */
  fieldTypeDisplay?: string

  // ========================================
  // Validation
  // ========================================

  /** Whether the field is required */
  isRequired?: boolean

  /** Whether the field is read-only */
  isReadonly?: boolean

  /** Whether this is a system field (non-deletable) */
  isSystem?: boolean

  /** Whether the field is searchable */
  isSearchable?: boolean

  /** Whether the field value must be unique */
  isUnique?: boolean

  /** Whether the field is hidden */
  isHidden?: boolean

  /** Whether the field is visible */
  isVisible?: boolean

  /** Whether the field is sortable */
  sortable?: boolean

  // ========================================
  // Display Configuration
  // ========================================

  /** Whether to show in list view */
  showInList?: boolean

  /** Whether to show in detail view */
  showInDetail?: boolean

  /** Whether to show in filter panel */
  showInFilter?: boolean

  /** Whether to show in form */
  showInForm?: boolean

  // ========================================
  // Reverse Relation Configuration
  // ========================================

  /** Whether this field represents a reverse relation (related_name) */
  isReverseRelation?: boolean

  /** Path to model that owns this relation (e.g., apps.lifecycle.models.Maintenance) */
  reverseRelationModel?: string

  /** FK field name on related model (e.g., asset) */
  reverseRelationField?: string

  /** How to display reverse relations */
  relationDisplayMode?: RelationDisplayMode

  /** Display name for relation display mode */
  relationDisplayModeDisplay?: string

  // ========================================
  // Layout Configuration
  // ========================================

  /** Display order */
  sortOrder?: number

  /** Column width in pixels */
  columnWidth?: number

  /** Minimum column width */
  minColumnWidth?: number

  /** Maximum column width */
  maxColumnWidth?: number

  /** Fixed column position */
  fixed?: 'left' | 'right'

  /** Grid span (24-column grid) */
  span?: number

  /** Minimum rendered field block height (px) */
  minHeight?: number

  // ========================================
  // Validation Rules
  // ========================================

  /** Minimum value for numeric fields */
  minValue?: number

  /** Maximum value for numeric fields */
  maxValue?: number

  /** Maximum length for text fields */
  maxLength?: number

  /** Minimum length for text fields */
  minLength?: number

  /** Regular expression pattern */
  regexPattern?: string

  // ========================================
  // Options & Reference
  // ========================================

  /** Options for select/radio/checkbox fields */
  options?: FieldOption[]

  /** Default value */
  defaultValue?: any

  /** Referenced business object code */
  referenceObject?: string

  /** Display field for reference */
  referenceDisplayField?: string

  // ========================================
  // Special Fields
  // ========================================

  /** Formula expression for calculated fields */
  formula?: string

  /** Sub-table field definitions */
  subTableFields?: FieldDefinition[]
  relatedFields?: FieldDefinition[]
  related_fields?: FieldDefinition[]
  displayTier?: string

  /** Additional validation rules */
  validationRules?: ValidationRule[]

  /** Component-specific props */
  componentProps?: Record<string, any>

  // ========================================
  // UI Helpers
  // ========================================

  /** Placeholder text */
  placeholder?: string

  /** Field description */
  description?: string

  /** Help text for the field */
  helpText?: string

  /** Decimal places for currency/number fields */
  decimalPlaces?: number
}

/**
 * All available field types in the low-code platform
 */
export type FieldType =
  | 'text'           // Single-line text input
  | 'textarea'       // Multi-line text input
  | 'richtext'       // Rich text editor
  | 'number'         // Numeric input
  | 'currency'       // Currency/money input
  | 'percent'        // Percentage input
  | 'date'           // Date picker
  | 'datetime'       // Date and time picker
  | 'time'           // Time picker
  | 'boolean'        // Boolean checkbox
  | 'switch'         // Toggle switch
  | 'select'         // Single select dropdown
  | 'multi_select'   // Multiple select dropdown
  | 'radio'          // Radio button group
  | 'checkbox'       // Checkbox group
  | 'reference'      // Reference to another business object
  | 'user'           // User picker
  | 'department'     // Department/organization picker
  | 'asset'          // Asset picker
  | 'file'           // File upload
  | 'image'          // Image upload
  | 'attachment'     // Generic attachment
  | 'qr_code'        // QR code display
  | 'barcode'        // Barcode display
  | 'formula'        // Calculated field
  | 'subtable'       // Sub-table/master-detail
  | 'sub_table'      // Sub-table/master-detail
  | 'location'       // Location picker
  | 'organization'   // Organization picker
  | 'related_object' // Embedded related table

/**
 * Field option for select/radio/checkbox fields
 */
export interface FieldOption {
  /** Display label */
  label: string

  /** Option value */
  value: any

  /** Whether the option is disabled */
  disabled?: boolean

  /** Icon for the option */
  icon?: string

  /** Additional data */
  [key: string]: any
}

/**
 * Validation rule for field
 */
export interface ValidationRule {
  /** Rule type */
  type: 'required' | 'pattern' | 'min' | 'max' | 'minLength' | 'maxLength' | 'custom'

  /** Rule value (for min/max/pattern) */
  value?: any

  /** Error message */
  message: string

  /** When to trigger validation */
  trigger?: 'blur' | 'change'
}

/**
 * Field display configuration
 */
export interface FieldDisplayConfig {
  /** Field code */
  fieldCode: string

  /** Whether to show in list */
  showInList?: boolean

  /** Whether to show in detail */
  showInDetail?: boolean

  /** Whether to show in form */
  showInForm?: boolean

  /** Display order */
  order?: number

  /** Column width */
  width?: number
}

/**
 * Field group for organizing related fields
 */
export interface FieldGroup {
  /** Group identifier */
  id: string

  /** Group name */
  name: string

  /** Group display label */
  label?: string

  /** Fields in this group */
  fields: string[]

  /** Display order */
  order?: number

  /** Whether group is collapsed */
  collapsed?: boolean

  /** Whether group is collapsible */
  collapsible?: boolean
}

/**
 * Reverse relation display modes
 */
export type RelationDisplayMode =
  | 'inline_editable'   // Inline editable table
  | 'inline_readonly'  // Inline read-only table
  | 'tab_readonly'      // Tab read-only table
  | 'hidden'           // Hidden from display
  | 'timeline'         // Timeline display mode

/**
 * Context type for layouts
 */
export type ContextType =
  | 'form_create'   // Create form context
  | 'form_edit'     // Edit form context
  | 'detail'        // Detail view context
  | 'list'          // List view context
  | 'search'        // Search form context

/**
 * Layout priority levels
 */
export type LayoutPriority =
  | 'user'     // User level (highest)
  | 'role'     // Role level
  | 'org'      // Organization level
  | 'global'   // Global level
  | 'default'  // Default layout (lowest)

/**
 * Field metadata response with context filtering
 */
export interface FieldMetadataResponse {
  /** Editable fields (non-reverse relations) */
  editableFields: FieldDefinition[]

  /** Reverse relation fields */
  reverseRelations: FieldDefinition[]

  /** Context used for filtering */
  context: 'form' | 'detail' | 'list'
}

/**
 * Differential configuration for layouts
 */
export interface DifferentialConfig {
  /** Custom field order */
  fieldOrder?: string[]

  /** Section configurations with overrides */
  sections?: DiffSectionConfig[]
}

/**
 * Differential section configuration
 */
export interface DiffSectionConfig {
  /** Section identifier */
  id: string

  /** Fields in this section with overrides */
  fields?: DiffFieldConfig[]
}

/**
 * Differential field configuration
 */
export interface DiffFieldConfig {
  /** Field code */
  fieldCode?: string
  code?: string  // Alternative property name

  /** Column span override */
  span?: number

  /** Readonly override */
  readonly?: boolean

  /** Visibility override */
  visible?: boolean

  /** Required override */
  required?: boolean

  /** Other property overrides */
  [key: string]: any
}
