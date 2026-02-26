/**
 * Field Transformation Utilities
 *
 * Handles snake_case <-> camelCase conversion between backend and frontend.
 * Reference: docs/plans/common_base_features/00_core/frontend_api_standardization_design.md
 *
 * Examples:
 * - parent_id -> parentId
 * - userId -> user_id
 */

/**
 * Convert snake_case to camelCase
 * @example parent_id -> parentId
 * @example user_profile -> userProfile
 */
export function toCamelCase<T = any>(obj: any): T {
  if (obj === null || obj === undefined) return obj

  // Handle arrays recursively
  if (Array.isArray(obj)) {
    return obj.map(item => toCamelCase(item)) as any
  }

  // Preserve Date objects
  if (obj instanceof Date) return obj as any

  // Return primitives as-is
  if (typeof obj !== 'object') return obj

  // Convert object keys
  return Object.keys(obj).reduce((acc, key) => {
    // Convert snake_case to camelCase
    const camelKey = key.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
    acc[camelKey] = toCamelCase(obj[key])
    return acc
  }, {} as any)
}

/**
 * Convert camelCase to snake_case
 * @example parentId -> parent_id
 * @example userProfile -> user_profile
 */
export function toSnakeCase<T = any>(obj: any): T {
  if (obj === null || obj === undefined) return obj

  // Handle arrays recursively
  if (Array.isArray(obj)) {
    return obj.map(item => toSnakeCase(item)) as any
  }

  // Preserve Date objects
  if (obj instanceof Date) return obj as any

  // Return primitives as-is
  if (typeof obj !== 'object') return obj

  // Convert object keys
  return Object.keys(obj).reduce((acc, key) => {
    // Convert camelCase to snake_case
    const snakeKey = key.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)
    acc[snakeKey] = toSnakeCase(obj[key])
    return acc
  }, {} as any)
}

/**
 * Field mapping for special cases where auto-conversion fails
 * Add custom mappings here as needed
 */
export const FieldMapping: Record<string, string> = {
  // 'backend_field': 'frontendField'
  // Example: 'some_api_field': 'someApiField'
}

/**
 * System field codes that should be hidden from list/detail forms.
 * These are framework-managed fields that users shouldn't edit directly.
 */
export const SYSTEM_FIELD_CODES = [
  'id',              // Primary key
  'created_at',      // Audit timestamp
  'updated_at',      // Audit timestamp
  'created_by',      // Audit user
  'updated_by',      // Audit user
  'deleted_at',      // Soft delete timestamp
  'deleted_by',      // Soft delete user
  'is_deleted',      // Soft delete flag
  'organization',    // Org foreign key
  'organization_id', // Org ID
  'custom_fields',   // JSONB dynamic fields container
  'org',             // Org relation shorthand
]

/**
 * Check if a field is a system field (framework-managed).
 * Supports both camelCase and snake_case field codes.
 *
 * @param field - Field object with code field
 * @returns true if the field is a system field
 */
export function isSystemField(field: any): boolean {
  if (!field) return false

  // Check explicit is_system flag (from backend metadata)
  if (field.isSystem || field.is_system) {
    return true
  }

  // Check against known system field codes
  const fieldCode = field.code || field.fieldCode || field.field_code
  if (!fieldCode) return false

  // Convert to snake_case for comparison
  const snakeCode = typeof fieldCode === 'string'
    ? fieldCode.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`)
    : fieldCode

  return SYSTEM_FIELD_CODES.includes(snakeCode)
}

/**
 * Filter out system fields from an array of fields.
 *
 * @param fields - Array of field objects
 * @returns Filtered array without system fields
 */
export function filterSystemFields(fields: any[]): any[] {
  if (!Array.isArray(fields)) return []
  return fields.filter(field => !isSystemField(field))
}
