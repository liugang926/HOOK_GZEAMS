/**
 * useFieldPermissions Hook
 *
 * Manages field-level permissions for dynamic forms.
 * Supports readonly, visible, and hidden states based on:
 * 1. Field metadata properties (is_readonly, is_hidden, is_visible)
 * 2. Runtime field permissions (passed via props)
 * 3. Workflow node permissions (future extension)
 */

import { Ref, computed } from 'vue'
import type { FieldDefinition } from '@/types'

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Permission level for a field
 */
export type PermissionLevel = 'editable' | 'readonly' | 'hidden'

/**
 * Field permission configuration
 */
export interface FieldPermission {
  readonly?: boolean
  visible?: boolean
  hidden?: boolean
}

/**
 * Field permissions mapping (field code -> permission config)
 */
export type FieldPermissionsMap = Record<string, FieldPermission>

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Composable for field permission management
 *
 * @param fieldPermissions - Reactive field permissions map from props
 * @param fieldDefinitions - Field definitions from metadata
 * @returns Permission checking methods
 */
export function useFieldPermissions(
  fieldPermissions: Ref<FieldPermissionsMap>,
  fieldDefinitions: Ref<FieldDefinition[]>
) {
  // ============================================================================
  // Permission Lookup
  // ============================================================================

  /**
   * Get the permission configuration for a specific field
   * Combines metadata permissions with runtime permissions
   *
   * @param fieldCode - Field code to look up
   * @returns Permission level for the field
   */
  function getFieldPermission(fieldCode: string): PermissionLevel {
    // Find field definition
    const field = fieldDefinitions.value.find(f => f.code === fieldCode)
    if (!field) {
      return 'editable' // Default to editable if field not found
    }

    // Check runtime permissions first (highest priority)
    const runtimePerm = fieldPermissions.value[fieldCode]
    if (runtimePerm) {
      if (runtimePerm.hidden === true) return 'hidden'
      if (runtimePerm.visible === false) return 'hidden'
      if (runtimePerm.readonly === true) return 'readonly'
    }

    // Check metadata permissions
    if (field.isHidden === true || field.isVisible === false) {
      return 'hidden'
    }
    if (field.isReadonly === true) {
      return 'readonly'
    }

    return 'editable'
  }

  /**
   * Get permission configuration object for a field
   */
  function getFieldPermissionConfig(fieldCode: string): FieldPermission {
    const level = getFieldPermission(fieldCode)
    return {
      readonly: level === 'readonly',
      visible: level !== 'hidden',
      hidden: level === 'hidden'
    }
  }

  // ============================================================================
  // Permission Checkers
  // ============================================================================

  /**
   * Check if a field should be rendered as readonly
   * A field is readonly if:
   * 1. Metadata has is_readonly: true
   * 2. Runtime permissions have readonly: true
   *
   * @param field - Field definition to check
   * @returns true if field should be readonly
   */
  function isFieldReadonly(field: FieldDefinition | string): boolean {
    const fieldCode = typeof field === 'string' ? field : field.code
    return getFieldPermission(fieldCode) === 'readonly'
  }

  /**
   * Check if a field should be visible
   * A field is visible if:
   * 1. Not hidden (is_hidden !== true, is_visible !== false)
   * 2. Runtime permissions don't mark it as hidden
   *
   * @param field - Field definition to check
   * @returns true if field should be visible
   */
  function isFieldVisible(field: FieldDefinition | string): boolean {
    const fieldCode = typeof field === 'string' ? field : field.code
    return getFieldPermission(fieldCode) !== 'hidden'
  }

  /**
   * Check if a field is editable (not readonly and not hidden)
   *
   * @param field - Field definition to check
   * @returns true if field can be edited
   */
  function isFieldEditable(field: FieldDefinition | string): boolean {
    const fieldCode = typeof field === 'string' ? field : field.code
    return getFieldPermission(fieldCode) === 'editable'
  }

  /**
   * Check if a field is hidden
   *
   * @param field - Field definition to check
   * @returns true if field should be hidden
   */
  function isFieldHidden(field: FieldDefinition | string): boolean {
    const fieldCode = typeof field === 'string' ? field : field.code
    return getFieldPermission(fieldCode) === 'hidden'
  }

  // ============================================================================
  // Computed Helpers
  // ============================================================================

  /**
   * Get all visible field definitions
   */
  const visibleFields = computed(() => {
    return fieldDefinitions.value.filter(field => isFieldVisible(field))
  })

  /**
   * Get all editable field definitions
   */
  const editableFields = computed(() => {
    return fieldDefinitions.value.filter(field => isFieldEditable(field))
  })

  /**
   * Get all readonly field definitions
   */
  const readonlyFields = computed(() => {
    return fieldDefinitions.value.filter(field => isFieldReadonly(field))
  })

  /**
   * Get field codes for all visible fields
   */
  const visibleFieldCodes = computed(() => {
    return visibleFields.value.map(f => f.code)
  })

  // ============================================================================
  // Return Public Interface
  // ============================================================================

  return {
    // Permission lookup
    getFieldPermission,
    getFieldPermissionConfig,

    // Permission checkers
    isFieldReadonly,
    isFieldVisible,
    isFieldEditable,
    isFieldHidden,

    // Computed helpers
    visibleFields,
    editableFields,
    readonlyFields,
    visibleFieldCodes
  }
}
