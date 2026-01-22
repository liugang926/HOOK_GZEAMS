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
  prop: string
  label: string
  width?: number
  minWidth?: number
  align?: 'left' | 'center' | 'right'
  fixed?: boolean | 'left' | 'right'
  slot?: boolean
  format?: (value: any, row: any) => string
}

/**
 * Search field configuration
 */
export interface SearchField {
  field: string
  label: string
  type: 'input' | 'select' | 'daterange' | 'treeselect' | 'cascader'
  placeholder?: string
  options?: SelectOption[]
  multiple?: boolean
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
