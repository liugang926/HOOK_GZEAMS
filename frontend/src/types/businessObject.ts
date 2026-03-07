/**
 * Business Object Type Definitions
 *
 * Unified business object types for the low-code metadata platform.
 * All properties use camelCase to match backend djangorestframework-camel-case output.
 *
 * Reference: docs/plans/frontend/TYPE_UNIFICATION_EXECUTION_PLAN.md
 */

import type { FieldDefinition } from './field'
import type { PageLayout } from './layout'

/**
 * Business object definition
 * Represents a configurable entity in the low-code platform
 */
export interface BusinessObject {
  /** Unique identifier */
  id: string

  /** Object code - unique identifier */
  code: string

  /** Object display name */
  name: string

  /** English name */
  nameEn?: string

  /** Object description */
  description?: string

  /** Object icon */
  icon?: string

  /** Module category */
  module?: string

  /** Whether the object is active */
  isActive?: boolean

  /** Whether this is a hardcoded model (vs custom object) */
  isHardcoded?: boolean

  /** Menu category for automated routing */
  menuCategory?: string

  /** Whether the object should be hidden from the sidebar menu */
  isMenuHidden?: boolean

  /** Django model path for hardcoded models */
  djangoModelPath?: string

  // ========================================
  // Workflow Configuration
  // ========================================

  /** Whether workflow is enabled */
  enableWorkflow?: boolean

  /** Whether versioning is enabled */
  enableVersion?: boolean

  /** Whether soft delete is enabled */
  enableSoftDelete?: boolean

  // ========================================
  // Layout Configuration
  // ========================================

  /** Default form layout code */
  defaultFormLayout?: string

  /** Default list layout code */
  defaultListLayout?: string

  /** Default detail layout code */
  defaultDetailLayout?: string

  /** Default search layout code */
  defaultSearchLayout?: string

  /** Database table name */
  tableName?: string

  // ========================================
  // Metadata
  // ========================================

  /** Number of fields */
  fieldCount?: number

  /** Number of layouts */
  layoutCount?: number

  // ========================================
  // Nested Data (when populated)
  // ========================================

  /** Field definitions for this object */
  fields?: FieldDefinition[]

  /** Page layouts for this object */
  pageLayouts?: PageLayout[]

  /** Created timestamp */
  createdAt?: string

  /** Updated timestamp */
  updatedAt?: string
}

/**
 * Complete object metadata
 * Returned by the metadata endpoint with all related data
 */
export interface ObjectMetadata {
  /** Object code */
  code: string

  /** Object name */
  name: string

  /** English name */
  nameEn?: string

  /** Menu category */
  menuCategory?: string

  /** Whether the object is hidden from menus */
  isMenuHidden?: boolean

  /** Whether this is a hardcoded model */
  isHardcoded: boolean

  /** Django model path */
  djangoModelPath?: string

  /** Whether workflow is enabled */
  enableWorkflow: boolean

  /** Whether versioning is enabled */
  enableVersion: boolean

  /** Whether soft delete is enabled */
  enableSoftDelete: boolean

  /** Field definitions */
  fields: FieldDefinition[]

  /** Layout configurations by type */
  layouts: ObjectLayouts

  /** User permissions */
  permissions: ObjectPermissions

  /** Object description */
  description?: string

  /** Object icon */
  icon?: string

  /** Module */
  module?: string
}

/**
 * Layout configurations for different page types
 */
export interface ObjectLayouts {
  /** Form layout */
  form?: PageLayout

  /** List layout */
  list?: PageLayout

  /** Detail layout */
  detail?: PageLayout

  /** Search layout */
  search?: PageLayout
}

/**
 * User permissions for an object
 */
export interface ObjectPermissions {
  /** Can view records */
  view: boolean

  /** Can create records */
  add: boolean

  /** Can update records */
  change: boolean

  /** Can delete records */
  delete: boolean

  /** Can export records */
  export?: boolean

  /** Can import records */
  import?: boolean
}

/**
 * Business object list item
 * Lightweight version for list displays
 */
export interface BusinessObjectListItem {
  /** Object code */
  code: string

  /** Object name */
  name: string

  /** English name */
  nameEn?: string

  /** Object icon */
  icon?: string

  /** Module */
  module?: string

  /** Menu category */
  menuCategory?: string

  /** Whether hidden from menu */
  isMenuHidden?: boolean

  /** Whether active */
  isActive?: boolean

  /** Field count */
  fieldCount?: number

  /** Layout count */
  layoutCount?: number

  /** Description */
  description?: string
}

/**
 * Business object filter criteria
 */
export interface BusinessObjectFilter {
  /** Filter by module */
  module?: string

  /** Filter by active status */
  isActive?: boolean

  /** Filter by hardcoded status */
  isHardcoded?: boolean

  /** Search in name/code */
  search?: string

  /** Sort field */
  sortBy?: 'code' | 'name' | 'createdAt' | 'fieldCount'

  /** Sort direction */
  sortOrder?: 'asc' | 'desc'
}

/**
 * Business object configuration options
 */
export interface BusinessObjectConfig {
  /** Enable workflow */
  enableWorkflow?: boolean

  /** Enable versioning */
  enableVersion?: boolean

  /** Enable soft delete */
  enableSoftDelete?: boolean

  /** Default form layout */
  defaultFormLayout?: string

  /** Default list layout */
  defaultListLayout?: string

  /** Table name */
  tableName?: string
}
