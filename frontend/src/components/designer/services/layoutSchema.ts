/**
 * Layout Schema Validation Service
 *
 * Validates layout configuration structures for correctness.
 * Provides detailed error messages for invalid configurations.
 *
 * Reference: docs/plans/2025-02-03-metadata-layout-implementation-plan.md
 */

import type {
  DifferentialConfig,
  SectionConfig,
  DesignerTabConfig,
  ContainerConfig,
  FieldOverride,
  ValidationResult,
  ValidationError
} from '@/types/metadata'

// Local type alias for backward compatibility
type TabConfig = DesignerTabConfig

import { ERROR_CODES } from '@/types/metadata'

// Re-export ERROR_CODES for convenience
export { ERROR_CODES }

// ============================================================================
// Public Validation Functions
// ============================================================================

/**
 * Validate differential configuration
 *
 * @param config - Differential configuration to validate
 * @param availableFields - List of valid field codes (optional)
 * @returns Validation result
 */
export function validateDifferentialConfig(
  config: DifferentialConfig,
  availableFields?: string[]
): ValidationResult {
  const errors: ValidationError[] = []

  // Validate fieldOrder
  if (config.fieldOrder !== undefined) {
    const fieldOrderErrors = validateFieldOrder(config.fieldOrder, availableFields)
    errors.push(...fieldOrderErrors)
  }

  // Validate fieldOverrides
  if (config.fieldOverrides !== undefined) {
    const fieldOverridesErrors = validateFieldOverrides(config.fieldOverrides, availableFields)
    errors.push(...fieldOverridesErrors)
  }

  // Validate sections
  if (config.sections !== undefined) {
    const sectionsErrors = validateSections(config.sections, availableFields)
    errors.push(...sectionsErrors)
  }

  // Validate tabs
  if (config.tabs !== undefined) {
    const tabsErrors = validateTabs(config.tabs)
    errors.push(...tabsErrors)
  }

  // Validate containers
  if (config.containers !== undefined) {
    const containersErrors = validateContainers(config.containers)
    errors.push(...containersErrors)
  }

  return {
    valid: errors.length === 0,
    errors
  }
}

/**
 * Validate section configuration
 */
export function validateSection(section: SectionConfig, availableFields?: string[]): ValidationError[] {
  const errors: ValidationError[] = []

  // Check required fields
  if (!section.id) {
    errors.push({
      path: 'section.id',
      message: 'Section id is required',
      code: ERROR_CODES.REQUIRED_FIELD
    })
  }

  if (!section.title) {
    errors.push({
      path: 'section.title',
      message: 'Section title is required',
      code: ERROR_CODES.REQUIRED_FIELD
    })
  }

  // Validate fields array
  if (section.fields !== undefined) {
    if (!Array.isArray(section.fields)) {
      errors.push({
        path: 'section.fields',
        message: 'Section fields must be an array',
        code: ERROR_CODES.INVALID_TYPE
      })
    } else if (availableFields) {
      // Check for unknown fields
      const unknownFields = section.fields.filter(f => !availableFields.includes(f))
      unknownFields.forEach(field => {
        errors.push({
          path: `section.fields.${field}`,
          message: `Unknown field code: ${field}`,
          code: ERROR_CODES.UNKNOWN_FIELD
        })
      })
    }
  }

  // Validate columns
  if (section.columns !== undefined) {
    if (typeof section.columns !== 'number' || section.columns < 1 || section.columns > 4) {
      errors.push({
        path: 'section.columns',
        message: 'Section columns must be a number between 1 and 4',
        code: ERROR_CODES.INVALID_VALUE
      })
    }
  }

  return errors
}

/**
 * Validate tab configuration
 */
export function validateTab(tab: TabConfig): ValidationError[] {
  const errors: ValidationError[] = []

  // Check required fields
  if (!tab.id) {
    errors.push({
      path: 'tab.id',
      message: 'Tab id is required',
      code: ERROR_CODES.REQUIRED_FIELD
    })
  }

  if (!tab.title) {
    errors.push({
      path: 'tab.title',
      message: 'Tab title is required',
      code: ERROR_CODES.REQUIRED_FIELD
    })
  }

  // Validate fields array
  if (tab.fields !== undefined && !Array.isArray(tab.fields)) {
    errors.push({
      path: 'tab.fields',
      message: 'Tab fields must be an array',
      code: ERROR_CODES.INVALID_TYPE
    })
  }

  // Validate relations array
  if (tab.relations !== undefined && !Array.isArray(tab.relations)) {
    errors.push({
      path: 'tab.relations',
      message: 'Tab relations must be an array',
      code: ERROR_CODES.INVALID_TYPE
    })
  }

  return errors
}

// ============================================================================
// Internal Validation Functions
// ============================================================================

/**
 * Validate fieldOrder array
 */
function validateFieldOrder(fieldOrder: string[], availableFields?: string[]): ValidationError[] {
  const errors: ValidationError[] = []

  if (!Array.isArray(fieldOrder)) {
    errors.push({
      path: 'fieldOrder',
      message: 'fieldOrder must be an array',
      code: ERROR_CODES.INVALID_TYPE
    })
    return errors
  }

  // Check for duplicates
  const seen = new Set<string>()
  fieldOrder.forEach((code, idx) => {
    if (seen.has(code)) {
      errors.push({
        path: `fieldOrder[${idx}]`,
        message: `Duplicate field code: ${code}`,
        code: ERROR_CODES.DUPLICATE_ID
      })
    }
    seen.add(code)
  })

  // Check for unknown fields if availableFields provided
  if (availableFields) {
    fieldOrder.forEach((code, idx) => {
      if (!availableFields.includes(code)) {
        errors.push({
          path: `fieldOrder[${idx}]`,
          message: `Unknown field code: ${code}`,
          code: ERROR_CODES.UNKNOWN_FIELD
        })
      }
    })
  }

  return errors
}

/**
 * Validate fieldOverrides object
 */
function validateFieldOverrides(
  fieldOverrides: Record<string, FieldOverride>,
  availableFields?: string[]
): ValidationError[] {
  const errors: ValidationError[] = []

  if (typeof fieldOverrides !== 'object' || fieldOverrides === null) {
    errors.push({
      path: 'fieldOverrides',
      message: 'fieldOverrides must be an object',
      code: ERROR_CODES.INVALID_TYPE
    })
    return errors
  }

  for (const [fieldCode, overrides] of Object.entries(fieldOverrides)) {
    // Check if field exists
    if (availableFields && !availableFields.includes(fieldCode)) {
      errors.push({
        path: `fieldOverrides.${fieldCode}`,
        message: `Unknown field code: ${fieldCode}`,
        code: ERROR_CODES.UNKNOWN_FIELD
      })
      continue
    }

    // Validate override structure
    if (typeof overrides !== 'object' || overrides === null) {
      errors.push({
        path: `fieldOverrides.${fieldCode}`,
        message: `Field override for ${fieldCode} must be an object`,
        code: ERROR_CODES.INVALID_TYPE
      })
      continue
    }

    // Validate span if provided
    if (overrides.span !== undefined) {
      if (typeof overrides.span !== 'number' || overrides.span < 1 || overrides.span > 24) {
        errors.push({
          path: `fieldOverrides.${fieldCode}.span`,
          message: `Span for ${fieldCode} must be a number between 1 and 24`,
          code: ERROR_CODES.INVALID_VALUE
        })
      }
    }
  }

  return errors
}

/**
 * Validate sections array
 */
function validateSections(sections: SectionConfig[], availableFields?: string[]): ValidationError[] {
  const errors: ValidationError[] = []

  if (!Array.isArray(sections)) {
    errors.push({
      path: 'sections',
      message: 'sections must be an array',
      code: ERROR_CODES.INVALID_TYPE
    })
    return errors
  }

  // Check for duplicate section IDs
  const sectionIds = new Set<string>()
  sections.forEach((section, idx) => {
    if (section.id) {
      if (sectionIds.has(section.id)) {
        errors.push({
          path: `sections[${idx}].id`,
          message: `Duplicate section id: ${section.id}`,
          code: ERROR_CODES.DUPLICATE_ID
        })
      }
      sectionIds.add(section.id)
    }

    // Validate individual section
    const sectionErrors = validateSection(section, availableFields)
    sectionErrors.forEach(err => {
      err.path = `sections[${idx}].${err.path}`
    })
    errors.push(...sectionErrors)
  })

  return errors
}

/**
 * Validate tabs array
 */
function validateTabs(tabs: TabConfig[]): ValidationError[] {
  const errors: ValidationError[] = []

  if (!Array.isArray(tabs)) {
    errors.push({
      path: 'tabs',
      message: 'tabs must be an array',
      code: ERROR_CODES.INVALID_TYPE
    })
    return errors
  }

  // Check for duplicate tab IDs
  const tabIds = new Set<string>()
  tabs.forEach((tab, idx) => {
    if (tab.id) {
      if (tabIds.has(tab.id)) {
        errors.push({
          path: `tabs[${idx}].id`,
          message: `Duplicate tab id: ${tab.id}`,
          code: ERROR_CODES.DUPLICATE_ID
        })
      }
      tabIds.add(tab.id)
    }

    // Validate individual tab
    const tabErrors = validateTab(tab)
    tabErrors.forEach(err => {
      err.path = `tabs[${idx}].${err.path}`
    })
    errors.push(...tabErrors)
  })

  return errors
}

/**
 * Validate containers array
 */
function validateContainers(containers: ContainerConfig[]): ValidationError[] {
  const errors: ValidationError[] = []

  if (!Array.isArray(containers)) {
    errors.push({
      path: 'containers',
      message: 'containers must be an array',
      code: ERROR_CODES.INVALID_TYPE
    })
    return errors
  }

  const validTypes = ['tab', 'column', 'collapse', 'divider']

  containers.forEach((container, idx) => {
    if (!container.type) {
      errors.push({
        path: `containers[${idx}].type`,
        message: 'Container type is required',
        code: ERROR_CODES.REQUIRED_FIELD
      })
    } else if (!validTypes.includes(container.type)) {
      errors.push({
        path: `containers[${idx}].type`,
        message: `Invalid container type: ${container.type}. Must be one of: ${validTypes.join(', ')}`,
        code: ERROR_CODES.INVALID_VALUE
      })
    }

    if (!container.id) {
      errors.push({
        path: `containers[${idx}].id`,
        message: 'Container id is required',
        code: ERROR_CODES.REQUIRED_FIELD
      })
    }
  })

  // Check for duplicate container IDs
  const containerIds = new Set<string>()
  containers.forEach((container, idx) => {
    if (container.id) {
      if (containerIds.has(container.id)) {
        errors.push({
          path: `containers[${idx}].id`,
          message: `Duplicate container id: ${container.id}`,
          code: ERROR_CODES.DUPLICATE_ID
        })
      }
      containerIds.add(container.id)
    }
  })

  return errors
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Format validation errors as a human-readable string
 */
export function formatValidationErrors(result: ValidationResult): string {
  if (result.valid) {
    return 'Validation passed'
  }

  return result.errors
    .map(err => `[${err.code}] ${err.path}: ${err.message}`)
    .join('\n')
}

/**
 * Get the first error message from a validation result
 */
export function getFirstErrorMessage(result: ValidationResult): string | null {
  if (result.valid || result.errors.length === 0) {
    return null
  }
  return result.errors[0].message
}
