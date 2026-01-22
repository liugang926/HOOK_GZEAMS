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
