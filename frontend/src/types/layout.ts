/**
 * Layout Type Definitions
 *
 * Unified layout types for the low-code metadata platform.
 * All properties use camelCase to match backend djangorestframework-camel-case output.
 *
 * Reference: docs/plans/frontend/TYPE_UNIFICATION_EXECUTION_PLAN.md
 */

/**
 * Page layout configuration
 * Defines how fields and actions are arranged on different page types
 */
export interface PageLayout {
  /** Unique identifier */
  id: string

  /** Layout display name */
  name: string

  /** Layout code (unique per business object) */
  code: string

  /** @deprecated Use mode instead */
  layoutType?: LayoutType

  /** Layout display mode - determines how fields are rendered */
  mode?: LayoutMode

  /** Associated business object code */
  businessObject: string

  /** Layout configuration */
  layoutConfig: LayoutConfig

  /** Whether the layout is active */
  isActive?: boolean

  /** Whether this is the default layout */
  isDefault?: boolean

  /** Layout description */
  description?: string

  /** Display order */
  order?: number
}

/**
 * Layout display mode
 * Determines how fields are rendered based on context
 * - edit: Form layout for creating/editing records (default)
 * - readonly: Detail layout for viewing records (all fields read-only)
 * - search: Search form with horizontal layout
 */
export type LayoutMode = 'edit' | 'readonly' | 'search'

/**
 * @deprecated Use LayoutMode instead. Layout types have been unified.
 * This type is kept for backward compatibility during migration.
 */
export type LayoutType = LayoutMode

/**
 * Layout configuration container
 */
export interface LayoutConfig {
  /** Layout sections */
  sections?: LayoutSection[]

  /** Column configuration (for list layouts) */
  columns?: LayoutColumn[]

  /** Action buttons */
  actions?: LayoutAction[]

  /** Page title */
  title?: string

  /** Page icon */
  icon?: string

  /** Additional metadata */
  [key: string]: any
}

/**
 * Layout section definition
 * Groups related fields together
 */
export interface LayoutSection {
  /** Section identifier */
  id: string

  /** Section name */
  name: string

  /** Section display title */
  title?: string

  /** Section type */
  type?: SectionType

  /** Section position */
  position?: 'main' | 'sidebar'

  /** Whether section is collapsible */
  collapsible?: boolean

  /** Whether section is collapsed by default */
  collapsed?: boolean

  /** Number of columns in the section */
  columnCount?: number

  /** Fields in this section (field codes or field objects) */
  fields: (string | LayoutField)[]

  /** Display order */
  order?: number

  /** Whether section is visible */
  visible?: boolean

  /** Whether to show border */
  border?: boolean

  /** Section icon */
  icon?: string

  /** Whether to show title */
  showTitle?: boolean

  /** Shadow effect */
  shadow?: string

  /** Section span (grid columns) */
  span?: number
}

/**
 * Section types
 */
export type SectionType = 'default' | 'card' | 'fieldset' | 'tab' | 'collapse'

/**
 * Layout column definition
 * Used for list view columns
 */
export interface LayoutColumn {
  /** Field code */
  fieldCode: string

  /** Column span */
  span?: number

  /** Whether column is read-only */
  readonly?: boolean

  /** Whether column is visible */
  visible?: boolean

  /** Display order */
  order?: number

  /** Column width */
  width?: number

  /** Whether column is sortable */
  sortable?: boolean

  /** Fixed position */
  fixed?: 'left' | 'right'
}

/**
 * Layout field definition
 * Used within sections to configure individual field display
 */
export interface LayoutField {
  /** Field code */
  fieldCode: string

  /** Grid span */
  span?: number

  /** Whether field is read-only */
  readonly?: boolean

  /** Whether field is visible */
  visible?: boolean

  /** Display order */
  order?: number

  /** Field-specific props */
  props?: Record<string, any>

  /** Optional persisted canvas placement snapshot */
  layoutPlacement?: {
    row?: number
    colStart?: number
    colSpan?: number
    rowSpan?: number
    columns?: number
    totalRows?: number
    order?: number
    canvas?: {
      x?: number
      y?: number
      width?: number
      height?: number
    }
  }
}

/**
 * Layout action definition
 * Defines action buttons on the page
 */
export interface LayoutAction {
  /** Action code */
  code: string

  /** Action label */
  label: string

  /** Button type */
  type: ActionType

  /** Action type */
  actionType: ActionCategory

  /** API endpoint for custom actions */
  apiEndpoint?: string

  /** HTTP method */
  method?: 'POST' | 'GET' | 'PUT' | 'DELETE' | 'PATCH'

  /** Confirmation message */
  confirmMessage?: string

  /** Display order */
  order: number

  /** Whether action is visible */
  visible?: boolean

  /** Whether action is disabled */
  disabled?: boolean

  /** Button icon */
  icon?: string

  /** Additional props */
  props?: Record<string, any>
}

/**
 * Action button types
 */
export type ActionType = 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'

/**
 * Action categories
 */
export type ActionCategory = 'submit' | 'cancel' | 'custom' | 'workflow'

/**
 * Layout tab definition
 * Used for tab-based layouts
 */
export interface LayoutTab {
  /** Tab identifier */
  id: string

  /** Tab name */
  name: string

  /** Tab title */
  title: string

  /** Tab icon */
  icon?: string

  /** Sections in this tab */
  sections: LayoutSection[]

  /** Whether tab is disabled */
  disabled?: boolean

  /** Display order */
  order?: number
}

/**
 * Layout group definition
 * Groups related sections together
 */
export interface LayoutGroup {
  /** Group identifier */
  id: string

  /** Group name */
  name: string

  /** Group display title */
  title?: string

  /** Sections in this group */
  sections: LayoutSection[]

  /** Display order */
  order?: number

  /** Whether group is visible */
  visible?: boolean

  /** Whether group is collapsible */
  collapsible?: boolean

  /** Whether group is collapsed */
  collapsed?: boolean
}
