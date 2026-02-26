/**
 * Common Model Type Definitions
 *
 * Shared interfaces and types used across the application.
 * Reference: docs/plans/common_base_features/00_core/frontend_api_standardization_design.md
 */

/**
 * Base model interface - all models inherit these fields
 * Matches backend BaseModel with camelCase transformation
 */
export interface BaseModel {
  id: string
  organizationId: string
  isDeleted: boolean
  deletedAt: string | null
  createdAt: string
  updatedAt: string
  createdBy: string
  customFields?: Record<string, any>
}

/**
 * User model
 */
export interface User {
  id: string
  username: string
  email?: string
  firstName?: string
  lastName?: string
  fullName: string
  avatar?: string
  isActive: boolean
  roles?: string[]
  permissions?: string[]
}

/**
 * Organization model
 */
export interface Organization {
  id: string
  name: string
  code: string
  parentId?: string
  level: number
  path: string
}

/**
 * Tree node interface for hierarchical data
 */
export interface TreeNode<T = any> {
  id: string
  label: string
  children?: TreeNode<T>[]
  data?: T
}

/**
 * Select option interface for dropdown components
 */
export interface SelectOption {
  label: string
  value: any
  disabled?: boolean
  [key: string]: any
}

/**
 * Table column configuration
 */
export interface TableColumn {
  fieldCode?: string
  prop: string
  label: string
  type?: string // Legacy field type (text, user, status, etc.)
  fieldType?: string // Preferred field type for rendering
  options?: SelectOption[]
  width?: number
  defaultWidth?: number
  minWidth?: number
  align?: 'left' | 'center' | 'right'
  fixed?: boolean | 'left' | 'right'
  slot?: string
  visible?: boolean
  sortable?: boolean | 'custom'
  // Custom render helpers
  tagType?: (row: any) => string
  dateFormatter?: string
  format?: (value: any, row: any) => string
}

/**
 * Search field configuration
 */
export interface SearchField {
  prop?: string
  field?: string
  label: string
  type?: 'text' | 'input' | 'select' | 'date' | 'dateRange' | 'daterange' | 'month' | 'year' | 'numberRange' | 'boolean' | 'slot'
  placeholder?: string
  options?: SelectOption[]
  multiple?: boolean
  defaultValue?: any
}

/**
 * Field configuration for dynamic forms
 */
export interface FieldConfig {
  field: string
  label: string
  type: 'input' | 'textarea' | 'number' | 'select' | 'date' | 'daterange' |
  'treeselect' | 'user' | 'dept' | 'asset' | 'switch' | 'radio' | 'checkbox'
  placeholder?: string
  disabled?: boolean
  required?: boolean
  options?: SelectOption[]
  multiple?: boolean
  min?: number
  max?: number
  precision?: number
  rows?: number
}

/**
 * Tab item for DynamicTabs component
 * Reference: docs/plans/common_base_features/tab_configuration.md
 */
export interface TabItem {
  id?: string
  name?: string
  title: string
  icon?: string
  closable?: boolean
  disabled?: boolean
  badge?: string | number
  permission?: string
  visible?: boolean
  lazy?: boolean
  content?: any
  component?: any
  props?: Record<string, any>
  slots?: Record<string, any>
}

/**
 * Tab configuration for DynamicTabs component
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface TabConfig {
  id?: string
  businessObject?: string
  businessObjectCode?: string
  businessObjectName?: string
  name: string
  position?: 'top' | 'left' | 'right' | 'bottom'
  positionDisplay?: string
  typeStyle?: '' | 'card' | 'border-card'
  typeStyleDisplay?: string
  stretch?: boolean
  lazy?: boolean
  animated?: boolean
  addable?: boolean
  draggable?: boolean
  tabsConfig: TabItem[]
  isActive?: boolean
}

/**
 * Column item for list table configuration
 * Reference: docs/plans/common_base_features/list_column_configuration.md
 * Note: Backend returns camelCase directly via djangorestframework-camel-case
 */
export interface ColumnItem {
  fieldCode: string
  prop?: string  // Legacy support
  label: string
  labelOverride?: string
  width?: number
  defaultWidth?: number
  fixed?: 'left' | 'right' | '' | null
  sortable?: boolean
  visible?: boolean
  defaultVisible?: boolean
  requiredInList?: boolean
  fieldType?: string
}

/**
 * Column configuration storage
 */
export interface ColumnConfig {
  columns: ColumnItem[]
  columnOrder?: string[]
  source?: 'user' | 'default'
}
