/**
 * Unified Type Exports
 *
 * Single source of truth for all low-code platform types.
 * All types use camelCase to match backend djangorestframework-camel-case output.
 *
 * Reference: docs/plans/frontend/TYPE_UNIFICATION_EXECUTION_PLAN.md
 */

// ========================================
// Field Types
// ========================================
export * from './field'

// ========================================
// Layout Types
// ========================================
export * from './layout'

// ========================================
// Business Object Types
// ========================================
export * from './businessObject'

// ========================================
// Metadata Types (NEW)
// ========================================
export * from './metadata'

// ========================================
// Runtime Rendering Types
// ========================================
export * from './runtime'

// ========================================
// Common Types (existing)
// ========================================
export * from './common'

// ========================================
// Other Existing Types
// ========================================
export * from './api'
export * from './assets'
export * from './auth'
export * from './error'
export * from './finance'
export * from './inventory'
export * from './softwareLicenses'
export * from './workflow'
export * from './depreciation'
export * from './models'
