/**
 * Layout Designer Services Index
 *
 * Exports all utility services for the layout designer.
 *
 * Reference: docs/plans/2025-02-03-metadata-layout-implementation-plan.md
 */

// Layout Merge Service
export {
  mergeLayoutWithDiff,
  calculateDifferentialConfig,
  getFieldByCode,
  getSectionById,
  getTabById,
  isFieldVisible
} from './layoutMerge'

export type {
  MergedLayout
} from './layoutMerge'

// Re-export types from @/types/metadata for convenience
export type {
  FieldOverride,
  SectionConfig,
  DesignerTabConfig,
  DifferentialConfig
} from '@/types/metadata'

// Export TabConfig as alias for DesignerTabConfig for backward compatibility
export type { DesignerTabConfig as TabConfig } from '@/types/metadata'

// Layout Schema Validation Service
export {
  validateDifferentialConfig,
  validateSection,
  validateTab,
  formatValidationErrors,
  getFirstErrorMessage
} from './layoutSchema'

export { ERROR_CODES } from './layoutSchema'
