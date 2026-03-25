/**
 * Layout Schema Validation Service
 */

import i18n from '@/locales'
import type {
  DifferentialConfig,
  SectionConfig,
  DesignerTabConfig,
  ContainerConfig,
  FieldOverride,
  ValidationResult,
  ValidationError
} from '@/types/metadata'
import { ERROR_CODES } from '@/types/metadata'

// Local type alias for backward compatibility
// eslint-disable-next-line @typescript-eslint/no-unused-vars
type TabConfig = DesignerTabConfig

const lt = (key: string, params?: Record<string, unknown>) =>
  (params ? i18n.global.t(key, params) : i18n.global.t(key)) as string

// Re-export ERROR_CODES for convenience
export { ERROR_CODES }

export function validateDifferentialConfig(
  config: DifferentialConfig,
  availableFields?: string[]
): ValidationResult {
  const errors: ValidationError[] = []

  if (config.fieldOrder !== undefined) {
    errors.push(...validateFieldOrder(config.fieldOrder, availableFields))
  }

  if (config.fieldOverrides !== undefined) {
    errors.push(...validateFieldOverrides(config.fieldOverrides, availableFields))
  }

  if (config.sections !== undefined) {
    errors.push(...validateSections(config.sections, availableFields))
  }

  if (config.tabs !== undefined) {
    errors.push(...validateTabs(config.tabs))
  }

  if (config.containers !== undefined) {
    errors.push(...validateContainers(config.containers))
  }

  return {
    valid: errors.length === 0,
    errors
  }
}

export function validateSection(section: SectionConfig, availableFields?: string[]): ValidationError[] {
  const errors: ValidationError[] = []

  if (!section.id) {
    errors.push({
      path: 'section.id',
      message: lt('common.layoutSchema.sectionIdRequired'),
      code: ERROR_CODES.REQUIRED_FIELD
    })
  }

  if (!section.title) {
    errors.push({
      path: 'section.title',
      message: lt('common.layoutSchema.sectionTitleRequired'),
      code: ERROR_CODES.REQUIRED_FIELD
    })
  }

  if (section.fields !== undefined) {
    if (!Array.isArray(section.fields)) {
      errors.push({
        path: 'section.fields',
        message: lt('common.layoutSchema.sectionFieldsArray'),
        code: ERROR_CODES.INVALID_TYPE
      })
    } else if (availableFields) {
      const unknownFields = section.fields.filter(f => !availableFields.includes(f))
      unknownFields.forEach(field => {
        errors.push({
          path: `section.fields.${field}`,
          message: lt('common.layoutSchema.unknownFieldCode', { code: field }),
          code: ERROR_CODES.UNKNOWN_FIELD
        })
      })
    }
  }

  if (section.columns !== undefined) {
    if (typeof section.columns !== 'number' || section.columns < 1 || section.columns > 4) {
      errors.push({
        path: 'section.columns',
        message: lt('common.layoutSchema.sectionColumnsRange'),
        code: ERROR_CODES.INVALID_VALUE
      })
    }
  }

  return errors
}

export function validateTab(tab: TabConfig): ValidationError[] {
  const errors: ValidationError[] = []

  if (!tab.id) {
    errors.push({
      path: 'tab.id',
      message: lt('common.layoutSchema.tabIdRequired'),
      code: ERROR_CODES.REQUIRED_FIELD
    })
  }

  if (!tab.title) {
    errors.push({
      path: 'tab.title',
      message: lt('common.layoutSchema.tabTitleRequired'),
      code: ERROR_CODES.REQUIRED_FIELD
    })
  }

  if (tab.fields !== undefined && !Array.isArray(tab.fields)) {
    errors.push({
      path: 'tab.fields',
      message: lt('common.layoutSchema.tabFieldsArray'),
      code: ERROR_CODES.INVALID_TYPE
    })
  }

  if (tab.relations !== undefined && !Array.isArray(tab.relations)) {
    errors.push({
      path: 'tab.relations',
      message: lt('common.layoutSchema.tabRelationsArray'),
      code: ERROR_CODES.INVALID_TYPE
    })
  }

  return errors
}

function validateFieldOrder(fieldOrder: string[], availableFields?: string[]): ValidationError[] {
  const errors: ValidationError[] = []

  if (!Array.isArray(fieldOrder)) {
    errors.push({
      path: 'fieldOrder',
      message: lt('common.layoutSchema.fieldOrderArray'),
      code: ERROR_CODES.INVALID_TYPE
    })
    return errors
  }

  const seen = new Set<string>()
  fieldOrder.forEach((code, idx) => {
    if (seen.has(code)) {
      errors.push({
        path: `fieldOrder[${idx}]`,
        message: lt('common.layoutSchema.duplicateFieldCode', { code }),
        code: ERROR_CODES.DUPLICATE_ID
      })
    }
    seen.add(code)
  })

  if (availableFields) {
    fieldOrder.forEach((code, idx) => {
      if (!availableFields.includes(code)) {
        errors.push({
          path: `fieldOrder[${idx}]`,
          message: lt('common.layoutSchema.unknownFieldCode', { code }),
          code: ERROR_CODES.UNKNOWN_FIELD
        })
      }
    })
  }

  return errors
}

function validateFieldOverrides(
  fieldOverrides: Record<string, FieldOverride>,
  availableFields?: string[]
): ValidationError[] {
  const errors: ValidationError[] = []

  if (typeof fieldOverrides !== 'object' || fieldOverrides === null) {
    errors.push({
      path: 'fieldOverrides',
      message: lt('common.layoutSchema.fieldOverridesObject'),
      code: ERROR_CODES.INVALID_TYPE
    })
    return errors
  }

  for (const [fieldCode, overrides] of Object.entries(fieldOverrides)) {
    if (availableFields && !availableFields.includes(fieldCode)) {
      errors.push({
        path: `fieldOverrides.${fieldCode}`,
        message: lt('common.layoutSchema.unknownFieldCode', { code: fieldCode }),
        code: ERROR_CODES.UNKNOWN_FIELD
      })
      continue
    }

    if (typeof overrides !== 'object' || overrides === null) {
      errors.push({
        path: `fieldOverrides.${fieldCode}`,
        message: lt('common.layoutSchema.fieldOverrideMustBeObject', { code: fieldCode }),
        code: ERROR_CODES.INVALID_TYPE
      })
      continue
    }

    if (overrides.span !== undefined) {
      if (typeof overrides.span !== 'number' || overrides.span < 1 || overrides.span > 24) {
        errors.push({
          path: `fieldOverrides.${fieldCode}.span`,
          message: lt('common.layoutSchema.spanRange', { code: fieldCode }),
          code: ERROR_CODES.INVALID_VALUE
        })
      }
    }
  }

  return errors
}

function validateSections(sections: SectionConfig[], availableFields?: string[]): ValidationError[] {
  const errors: ValidationError[] = []

  if (!Array.isArray(sections)) {
    errors.push({
      path: 'sections',
      message: lt('common.layoutSchema.sectionsArray'),
      code: ERROR_CODES.INVALID_TYPE
    })
    return errors
  }

  const sectionIds = new Set<string>()
  sections.forEach((section, idx) => {
    if (section.id) {
      if (sectionIds.has(section.id)) {
        errors.push({
          path: `sections[${idx}].id`,
          message: lt('common.layoutSchema.duplicateSectionId', { id: section.id }),
          code: ERROR_CODES.DUPLICATE_ID
        })
      }
      sectionIds.add(section.id)
    }

    const sectionErrors = validateSection(section, availableFields)
    sectionErrors.forEach(err => {
      err.path = `sections[${idx}].${err.path}`
    })
    errors.push(...sectionErrors)
  })

  return errors
}

function validateTabs(tabs: TabConfig[]): ValidationError[] {
  const errors: ValidationError[] = []

  if (!Array.isArray(tabs)) {
    errors.push({
      path: 'tabs',
      message: lt('common.layoutSchema.tabsArray'),
      code: ERROR_CODES.INVALID_TYPE
    })
    return errors
  }

  const tabIds = new Set<string>()
  tabs.forEach((tab, idx) => {
    if (tab.id) {
      if (tabIds.has(tab.id)) {
        errors.push({
          path: `tabs[${idx}].id`,
          message: lt('common.layoutSchema.duplicateTabId', { id: tab.id }),
          code: ERROR_CODES.DUPLICATE_ID
        })
      }
      tabIds.add(tab.id)
    }

    const tabErrors = validateTab(tab)
    tabErrors.forEach(err => {
      err.path = `tabs[${idx}].${err.path}`
    })
    errors.push(...tabErrors)
  })

  return errors
}

function validateContainers(containers: ContainerConfig[]): ValidationError[] {
  const errors: ValidationError[] = []

  if (!Array.isArray(containers)) {
    errors.push({
      path: 'containers',
      message: lt('common.layoutSchema.containersArray'),
      code: ERROR_CODES.INVALID_TYPE
    })
    return errors
  }

  const validTypes = ['tab', 'column', 'collapse', 'divider']

  containers.forEach((container, idx) => {
    if (!container.type) {
      errors.push({
        path: `containers[${idx}].type`,
        message: lt('common.layoutSchema.containerTypeRequired'),
        code: ERROR_CODES.REQUIRED_FIELD
      })
    } else if (!validTypes.includes(container.type)) {
      errors.push({
        path: `containers[${idx}].type`,
        message: lt('common.layoutSchema.invalidContainerType', {
          type: container.type,
          types: validTypes.join(', ')
        }),
        code: ERROR_CODES.INVALID_VALUE
      })
    }

    if (!container.id) {
      errors.push({
        path: `containers[${idx}].id`,
        message: lt('common.layoutSchema.containerIdRequired'),
        code: ERROR_CODES.REQUIRED_FIELD
      })
    }
  })

  const containerIds = new Set<string>()
  containers.forEach((container, idx) => {
    if (container.id) {
      if (containerIds.has(container.id)) {
        errors.push({
          path: `containers[${idx}].id`,
          message: lt('common.layoutSchema.duplicateContainerId', { id: container.id }),
          code: ERROR_CODES.DUPLICATE_ID
        })
      }
      containerIds.add(container.id)
    }
  })

  return errors
}

export function formatValidationErrors(result: ValidationResult): string {
  if (result.valid) {
    return lt('common.layoutSchema.validationPassed')
  }

  return result.errors
    .map(err => `[${err.code}] ${err.path}: ${err.message}`)
    .join('\n')
}

export function getFirstErrorMessage(result: ValidationResult): string | null {
  if (result.valid || result.errors.length === 0) {
    return null
  }
  return result.errors[0].message
}
