/**
 * useFieldPermissions Composable
 *
 * Reactive utilities for applying field-level permissions in approval forms.
 * Integrates with NodeFormPermissions from the workflow API to determine
 * which fields are editable, read-only, or hidden.
 */
import { computed, type Ref } from 'vue'
import type { FieldPermissionLevel, NodeFormPermissions } from '@/types/workflow'

/**
 * Default permission when a field is not explicitly configured.
 * read_only is the safe default — prevents accidental edits.
 */
const DEFAULT_PERMISSION: FieldPermissionLevel = 'read_only'

export function useFieldPermissions(permissions: Ref<NodeFormPermissions>) {
  /**
   * Get permission level for a specific field.
   */
  const getPermission = (fieldCode: string): FieldPermissionLevel => {
    return permissions.value?.[fieldCode] ?? DEFAULT_PERMISSION
  }

  /**
   * Check if field is editable (approver can modify it).
   */
  const isEditable = (fieldCode: string): boolean => {
    return getPermission(fieldCode) === 'editable'
  }

  /**
   * Check if field is read-only (visible but not modifiable).
   */
  const isReadOnly = (fieldCode: string): boolean => {
    return getPermission(fieldCode) === 'read_only'
  }

  /**
   * Check if field is hidden (not rendered at all).
   */
  const isHidden = (fieldCode: string): boolean => {
    return getPermission(fieldCode) === 'hidden'
  }

  /**
   * Check if field should be visible (editable or read_only).
   */
  const isVisible = (fieldCode: string): boolean => {
    return !isHidden(fieldCode)
  }

  /**
   * List of field codes that are visible (not hidden).
   */
  const visibleFields = computed<string[]>(() => {
    if (!permissions.value) return []
    return Object.keys(permissions.value).filter(
      (code) => permissions.value[code] !== 'hidden'
    )
  })

  /**
   * List of field codes that are editable.
   */
  const editableFields = computed<string[]>(() => {
    if (!permissions.value) return []
    return Object.keys(permissions.value).filter(
      (code) => permissions.value[code] === 'editable'
    )
  })

  /**
   * Whether any fields are configured at all.
   */
  const hasPermissions = computed<boolean>(() => {
    return !!permissions.value && Object.keys(permissions.value).length > 0
  })

  return {
    getPermission,
    isEditable,
    isReadOnly,
    isHidden,
    isVisible,
    visibleFields,
    editableFields,
    hasPermissions,
  }
}
