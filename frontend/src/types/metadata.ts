/**
 * metadata.ts - Unified metadata type definitions
 *
 * This file consolidates all metadata-related types for the layout designer.
 * Types use camelCase to match the frontend coding standard.
 *
 * Backend Integration Note:
 * - Backend uses djangorestframework-camel-case for API serialization
 * - All API responses should be in camelCase format
 * - If backend returns snake_case, configure djangorestframework-camel-case
 */

// Re-export layout types that are shared with the layout system
export type {
  LayoutConfig,
  LayoutSection,
  LayoutField,
  LayoutColumn,
  LayoutAction,
  LayoutTab,
  SectionType,
  ActionType,
  ActionCategory
} from './layout'

// ============================================================================
// Field Metadata Types
// ============================================================================

/**
 * Field metadata from backend API
 * Represents a field definition in a business object
 */
export interface FieldMetadata {
  /** Unique field identifier */
  code: string

  /** Human-readable field name */
  name: string

  /** Field type (text, number, reference, enum, etc.) */
  fieldType: string

  /** Whether field is required */
  isRequired: boolean

  /** Whether field is read-only */
  isReadonly: boolean

  /** Display sort order */
  sortOrder: number

  /** Section this field belongs to */
  sectionName?: string

  /** Whether this is a reverse relation field */
  isReverseRelation?: boolean

  /** How reverse relation is displayed */
  relationDisplayMode?: string

  /** Related object code (for reference fields) */
  relatedObject?: string

  /** Whether field is visible in form */
  showInForm?: boolean

  /** Whether field is visible in list */
  showInList?: boolean

  /** Whether field is visible in detail view */
  showInDetail?: boolean

  /** Whether field is hidden (for computed/virtual fields) */
  isHidden?: boolean

  /** Custom CSS class */
  customClass?: string

  /** Field span (1-24, based on 24-column grid) */
  span?: number

  /** Default value */
  defaultValue?: any

  /** Help text for field */
  helpText?: string

  /** Placeholder text */
  placeholder?: string

  /** Readonly flag (alias for isReadonly for compatibility) */
  readonly?: boolean
}

/**
 * Field definition for layout designer
 * Used in designer components for field configuration
 */
export interface FieldDefinition extends FieldMetadata {
  /** Internal component ID */
  id: string

  /** Field label (can override name) */
  label: string

  /** Grid column span (1-24) */
  span: number

  /** Minimum rendered field block height (px) */
  minHeight?: number

  /** Whether field is currently visible */
  visible?: boolean

  /** Field width (CSS value) */
  width?: string

  /** Visible rules (conditional visibility) */
  visibleRules?: Array<{ field: string; value: any }>

  /** Validation rules */
  validationRules?: Array<{ logic: string; message: string }>

  /** Regex pattern for validation */
  regexPattern?: string

  /** Minimum value (for numbers) */
  minValue?: number

  /** Maximum value (for numbers) */
  maxValue?: number

  /** Reference filters (for reference fields) */
  referenceFilters?: Record<string, any>
}

// ============================================================================
// Layout Field Config (for WysiwygLayoutDesigner)
// ============================================================================

/**
 * Layout field configuration for the WYSIWYG Layout Designer
 * 
 * This type preserves complete field metadata needed for proper rendering.
 * Unlike the minimal LayoutField type, this includes options, referenceObject,
 * and other metadata required by FieldRenderer.
 * 
 * @see WysiwygLayoutDesigner.vue - uses this for field configuration
 * @see FieldRenderer.vue - requires metadata like options for proper rendering
 */
export interface LayoutFieldConfig {
  // === Basic Identification ===
  /** Internal component ID (unique within layout) */
  id: string

  /** Field code (matches FieldDefinition.code) */
  fieldCode: string

  // === Display Configuration ===
  /** Display label (can override FieldDefinition.name) */
  label: string

  /** Grid column span (1-24) */
  span: number

  /** Placeholder text */
  placeholder?: string

  /** Help text */
  helpText?: string

  // === Behavior Configuration ===
  /** Whether field is read-only */
  readonly?: boolean

  /** Whether field is visible */
  visible?: boolean

  /** Whether field is required */
  required?: boolean

  /** Default value */
  defaultValue?: any

  // === Validation Configuration ===
  /** Minimum text length */
  minLength?: number

  /** Maximum text length */
  maxLength?: number

  /** Minimum numeric value */
  minValue?: number

  /** Maximum numeric value */
  maxValue?: number

  /** Regex pattern for validation */
  regexPattern?: string

  // === Field Metadata (CRITICAL for rendering) ===
  /** Field type (text, select, reference, etc.) */
  fieldType: string

  /** Options for select/radio/checkbox fields */
  options?: Array<{ value: any; label: string }>

  /** Related object code for reference fields */
  referenceObject?: string

  /** Related object (alias for referenceObject) */
  relatedObject?: string

  /** Component-specific configuration */
  componentProps?: Record<string, any>

  /** Dictionary type code for dictionary fields */
  dictionaryType?: string

  /** Reference model path (for Django model lookups) */
  referenceModelPath?: string
}

// ============================================================================
// Layout Configuration Types
// ============================================================================

/**
 * Differential configuration for layout customization
 * Represents changes from default layout
 */
export interface DifferentialConfig {
  /** Custom field order */
  fieldOrder?: string[]

  /** Field-specific overrides */
  fieldOverrides?: Record<string, FieldOverride>

  /** Section configurations */
  sections?: SectionConfig[]

  /** Tab configurations */
  tabs?: DesignerTabConfig[]

  /** Container configurations */
  containers?: ContainerConfig[]
}

/**
 * Field override in differential config
 * Allows overriding default field properties
 */
export interface FieldOverride {
  /** Visibility override */
  visible?: boolean

  /** Read-only override */
  readonly?: boolean

  /** Required override */
  required?: boolean

  /** Column span override */
  span?: number

  /** Default value override */
  defaultValue?: any

  /** Label override */
  label?: string

  /** Placeholder override */
  placeholder?: string

  /** Help text override */
  helpText?: string
}

// ============================================================================
// Section Types
// ============================================================================

/**
 * Section configuration
 * Groups related fields together
 */
export interface SectionConfig {
  /** Section identifier */
  id: string

  /** Section title */
  title: string

  /** Field codes in this section */
  fields: string[]

  /** Section position */
  position?: 'main' | 'sidebar'

  /** Number of columns (1-4) */
  columns?: number

  /** Whether section is collapsed by default */
  collapsed?: boolean

  /** Background color */
  backgroundColor?: string

  /** Border visibility */
  border?: boolean

  /** Section icon name */
  icon?: string

  /** Custom CSS class */
  customClass?: string

  /** Whether section is visible */
  visible?: boolean
}

// ============================================================================
// Tab Types
// ============================================================================

/**
 * Tab configuration for layout designer
 * Defines a tab in tabbed layout
 * Note: Renamed from TabConfig to avoid collision with common.TabConfig
 */
export interface DesignerTabConfig {
  /** Tab identifier */
  id: string

  /** Tab title */
  title: string

  /** Field codes in this tab */
  fields?: string[]

  /** Related object codes in this tab */
  relations?: string[]

  /** Whether tab is disabled */
  disabled?: boolean

  /** Tab icon name */
  icon?: string
}

// ============================================================================
// Container Types
// ============================================================================

/**
 * Container configuration
 * Defines layout containers for organizing content
 */
export interface ContainerConfig {
  /** Container type */
  type: ContainerType

  /** Container identifier */
  id: string

  /** Container title */
  title?: string

  /** Container items */
  items?: ContainerConfig[]

  /** Additional properties */
  [key: string]: any
}

/** Container types */
export type ContainerType = 'tab' | 'column' | 'collapse' | 'divider'

// ============================================================================
// Preview Types
// ============================================================================

/**
 * Preview field (for layout preview)
 * Extends FieldDefinition with simulated values
 */
export interface PreviewField extends FieldDefinition {
  /** Simulated value for preview */
  simulatedValue?: any
}

// ============================================================================
// List Column Types
// ============================================================================

/**
 * List column (from PropertyPanel.vue)
 * Used in list layout designer
 */
export interface ListColumn {
  /** Field code */
  fieldCode: string

  /** Column label */
  label: string

  /** Column width (px) */
  width?: number

  /** Fixed position */
  fixed?: string

  /** Whether sortable */
  sortable?: boolean
}

// ============================================================================
// Validation Types
// ============================================================================

/**
 * Validation result
 */
export interface ValidationResult {
  /** Whether validation passed */
  valid: boolean

  /** Validation errors */
  errors: ValidationError[]
}

/**
 * Validation error detail
 */
export interface ValidationError {
  /** Error path (dot notation) */
  path: string

  /** Error message */
  message: string

  /** Error code */
  code: string
}

/** Standard error codes */
export const ERROR_CODES = {
  REQUIRED_FIELD: 'REQUIRED_FIELD',
  INVALID_TYPE: 'INVALID_TYPE',
  INVALID_VALUE: 'INVALID_VALUE',
  DUPLICATE_ID: 'DUPLICATE_ID',
  UNKNOWN_FIELD: 'UNKNOWN_FIELD',
  INVALID_STRUCTURE: 'INVALID_STRUCTURE'
} as const

// ============================================================================
// Context-Aware Field Metadata Types
// ============================================================================

/**
 * Field metadata response with context filtering
 * Separates editable fields from reverse relations
 */
export interface FieldMetadataResponse {
  /** Fields that can be edited in the given context */
  editableFields: FieldDefinition[]

  /** Reverse relation fields (one-to-many from other objects) */
  reverseRelations: FieldDefinition[]

  /** The context this metadata is for */
  context: 'form' | 'detail' | 'list'
}

/**
 * Display mode for reverse relation fields
 * Determines how related data is shown in the UI
 */
export type RelationDisplayMode = 'inline' | 'tab' | 'dialog'
