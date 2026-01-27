/**
 * Layout Schema Validation Utilities
 *
 * Provides validation functions for layout configurations.
 * Mirrors the backend validators in backend/apps/system/validators.py
 */

export interface LayoutValidationError {
  path: string
  message: string
}

export interface ValidationResult {
  valid: boolean
  errors: LayoutValidationError[]
}

// Valid section types
const VALID_SECTION_TYPES = ['section', 'tab', 'divider', 'collapse', 'column'] as const
type SectionType = typeof VALID_SECTION_TYPES[number]

// Valid span values (1-24, divisible by common grid systems)
const VALID_SPANS = [1, 2, 3, 4, 6, 8, 12, 24] as const
type SpanValue = typeof VALID_SPANS[number]

// Layout types
export type LayoutType = 'form' | 'list' | 'detail' | 'search'

/**
 * Validate layout configuration structure
 */
export function validateLayoutConfig(config: unknown, layoutType: LayoutType): ValidationResult {
  const errors: LayoutValidationError[] = []

  if (!config || typeof config !== 'object') {
    return {
      valid: false,
      errors: [{ path: '', message: 'Configuration must be a JSON object' }]
    }
  }

  if (layoutType === 'form' || layoutType === 'detail') {
    validateFormLayout(config, errors)
  } else if (layoutType === 'list') {
    validateListLayout(config, errors)
  } else if (layoutType === 'search') {
    validateSearchLayout(config, errors)
  }

  return {
    valid: errors.length === 0,
    errors
  }
}

function validateFormLayout(config: any, errors: LayoutValidationError[]): void {
  if (!Array.isArray(config.sections)) {
    errors.push({
      path: 'sections',
      message: 'Missing or invalid required field: sections (must be an array)'
    })
    return
  }

  if (config.sections.length === 0) {
    errors.push({
      path: 'sections',
      message: 'sections cannot be empty'
    })
  }

  config.sections.forEach((section: any, index: number) => {
    validateSection(section, `sections[${index}]`, errors)
  })
}

function validateListLayout(config: any, errors: LayoutValidationError[]): void {
  if (!Array.isArray(config.columns)) {
    errors.push({
      path: 'columns',
      message: 'Missing or invalid required field: columns (must be an array)'
    })
    return
  }

  if (config.columns.length === 0) {
    errors.push({
      path: 'columns',
      message: 'columns cannot be empty'
    })
  }

  config.columns.forEach((column: any, index: number) => {
    validateListColumn(column, `columns[${index}]`, errors)
  })
}

function validateSearchLayout(config: any, errors: LayoutValidationError[]): void {
  if (config.fields !== undefined && !Array.isArray(config.fields)) {
    errors.push({
      path: 'fields',
      message: 'fields must be an array'
    })
  }
}

function validateSection(section: any, path: string, errors: LayoutValidationError[]): void {
  if (!section || typeof section !== 'object') {
    errors.push({ path, message: 'Section must be an object' })
    return
  }

  if (!section.id) {
    errors.push({ path, message: 'Missing required field: id' })
  }

  if (!section.type) {
    errors.push({ path, message: 'Missing required field: type' })
    return
  }

  if (!VALID_SECTION_TYPES.includes(section.type)) {
    errors.push({
      path,
      message: `Invalid type: ${section.type}. Valid types: ${VALID_SECTION_TYPES.join(', ')}`
    })
  }

  switch (section.type) {
    case 'section':
      validateBasicSection(section, path, errors)
      break
    case 'tab':
      validateTabSection(section, path, errors)
      break
    case 'divider':
      // Divider only needs id and type, already validated
      break
    case 'collapse':
      validateCollapseSection(section, path, errors)
      break
    case 'column':
      validateColumnSection(section, path, errors)
      break
  }
}

function validateBasicSection(section: any, path: string, errors: LayoutValidationError[]): void {
  if (section.fields !== undefined) {
    if (!Array.isArray(section.fields)) {
      errors.push({ path: `${path}.fields`, message: 'fields must be an array' })
    } else {
      section.fields.forEach((field: any, index: number) => {
        validateField(field, `${path}.fields[${index}]`, errors)
      })
    }
  }
}

function validateTabSection(section: any, path: string, errors: LayoutValidationError[]): void {
  if (!Array.isArray(section.tabs)) {
    errors.push({ path: `${path}.tabs`, message: 'Missing required field: tabs (must be an array)' })
    return
  }

  if (section.tabs.length === 0) {
    errors.push({ path: `${path}.tabs`, message: 'tabs cannot be empty' })
  }

  section.tabs.forEach((tab: any, index: number) => {
    validateTab(tab, `${path}.tabs[${index}]`, errors)
  })
}

function validateTab(tab: any, path: string, errors: LayoutValidationError[]): void {
  if (!tab || typeof tab !== 'object') {
    errors.push({ path, message: 'Tab must be an object' })
    return
  }

  if (!tab.id) {
    errors.push({ path, message: 'Missing required field: id' })
  }

  if (!tab.title) {
    errors.push({ path, message: 'Missing required field: title' })
  }

  if (tab.fields !== undefined) {
    if (!Array.isArray(tab.fields)) {
      errors.push({ path: `${path}.fields`, message: 'fields must be an array' })
    } else {
      tab.fields.forEach((field: any, index: number) => {
        validateField(field, `${path}.fields[${index}]`, errors)
      })
    }
  }
}

function validateCollapseSection(section: any, path: string, errors: LayoutValidationError[]): void {
  if (!Array.isArray(section.items)) {
    errors.push({ path: `${path}.items`, message: 'Missing required field: items (must be an array)' })
    return
  }

  if (section.items.length === 0) {
    errors.push({ path: `${path}.items`, message: 'items cannot be empty' })
  }

  section.items.forEach((item: any, index: number) => {
    validateCollapseItem(item, `${path}.items[${index}]`, errors)
  })
}

function validateCollapseItem(item: any, path: string, errors: LayoutValidationError[]): void {
  if (!item || typeof item !== 'object') {
    errors.push({ path, message: 'Collapse item must be an object' })
    return
  }

  if (!item.id) {
    errors.push({ path, message: 'Missing required field: id' })
  }

  if (!item.title) {
    errors.push({ path, message: 'Missing required field: title' })
  }

  if (item.fields !== undefined) {
    if (!Array.isArray(item.fields)) {
      errors.push({ path: `${path}.fields`, message: 'fields must be an array' })
    } else {
      item.fields.forEach((field: any, index: number) => {
        validateField(field, `${path}.fields[${index}]`, errors)
      })
    }
  }
}

function validateColumnSection(section: any, path: string, errors: LayoutValidationError[]): void {
  if (!Array.isArray(section.columns)) {
    errors.push({ path: `${path}.columns`, message: 'Missing required field: columns (must be an array)' })
    return
  }

  if (section.columns.length === 0) {
    errors.push({ path: `${path}.columns`, message: 'columns cannot be empty' })
  }

  section.columns.forEach((column: any, index: number) => {
    validateColumnItem(column, `${path}.columns[${index}]`, errors)
  })
}

function validateColumnItem(column: any, path: string, errors: LayoutValidationError[]): void {
  if (!column || typeof column !== 'object') {
    errors.push({ path, message: 'Column item must be an object' })
    return
  }

  if (column.span !== undefined) {
    if (!VALID_SPANS.includes(column.span)) {
      errors.push({
        path: `${path}.span`,
        message: `span must be one of ${VALID_SPANS.join(', ')}`
      })
    }
  }

  if (column.fields !== undefined) {
    if (!Array.isArray(column.fields)) {
      errors.push({ path: `${path}.fields`, message: 'fields must be an array' })
    } else {
      column.fields.forEach((field: any, index: number) => {
        validateField(field, `${path}.fields[${index}]`, errors)
      })
    }
  }
}

function validateListColumn(column: any, path: string, errors: LayoutValidationError[]): void {
  if (!column || typeof column !== 'object') {
    errors.push({ path, message: 'Column must be an object' })
    return
  }

  const requiredFields = ['field_code', 'label']
  requiredFields.forEach(field => {
    if (!column[field]) {
      errors.push({ path, message: `Missing required field: ${field}` })
    }
  })

  if (column.width !== undefined) {
    const width = Number(column.width)
    if (isNaN(width) || width <= 0) {
      errors.push({ path: `${path}.width`, message: 'width must be a positive integer' })
    }
  }
}

function validateField(field: any, path: string, errors: LayoutValidationError[]): void {
  if (!field || typeof field !== 'object') {
    errors.push({ path, message: 'Field must be an object' })
    return
  }

  const requiredFields = ['id', 'field_code', 'label', 'span']
  requiredFields.forEach(requiredField => {
    if (!field[requiredField]) {
      errors.push({ path, message: `Missing required field: ${requiredField}` })
    }
  })

  // Validate span
  if (field.span !== undefined) {
    if (!VALID_SPANS.includes(field.span)) {
      errors.push({
        path: `${path}.span`,
        message: `span must be an integer between 1-24, preferably one of ${VALID_SPANS.join(', ')}`
      })
    }
  }
}

/**
 * Get default layout configuration for a given layout type
 */
export function getDefaultLayoutConfig(layoutType: LayoutType): Record<string, unknown> {
  if (layoutType === 'form') {
    return {
      sections: [
        {
          id: `section-${Date.now()}`,
          type: 'section',
          title: '基本信息',
          collapsible: true,
          collapsed: false,
          columns: 2,
          border: false,
          render_as_card: false,
          fields: []
        }
      ],
      actions: [
        { code: 'submit', label: '提交', type: 'primary', position: 'bottom-right' },
        { code: 'cancel', label: '取消', type: 'default', position: 'bottom-right' }
      ]
    }
  }

  if (layoutType === 'list') {
    return {
      columns: [],
      actions: [
        { code: 'create', label: '新建', type: 'primary', position: 'top-right' },
        { code: 'delete', label: '删除', type: 'danger', position: 'toolbar' }
      ],
      page_size: 20,
      show_pagination: true
    }
  }

  if (layoutType === 'detail') {
    return {
      sections: [
        {
          id: `section-detail-${Date.now()}`,
          type: 'section',
          title: '详细信息',
          collapsible: true,
          collapsed: false,
          columns: 2,
          border: false,
          render_as_card: false,
          fields: []
        }
      ]
    }
  }

  if (layoutType === 'search') {
    return {
      fields: [],
      layout: 'horizontal',
      label_width: '100px'
    }
  }

  return {}
}

/**
 * Validate and sanitize layout configuration
 */
export function validateAndSanitizeLayoutConfig(config: unknown, layoutType: LayoutType): {
  valid: boolean
  errors: LayoutValidationError[]
  sanitized?: Record<string, unknown>
} {
  const result = validateLayoutConfig(config, layoutType)

  if (!result.valid) {
    return result
  }

  // Add defaults for optional fields
  const sanitized = JSON.parse(JSON.stringify(config)) as Record<string, unknown>

  if (layoutType === 'form') {
    if (!sanitized.actions) {
      sanitized.actions = []
    }
  }

  return {
    valid: true,
    errors: [],
    sanitized
  }
}

/**
 * Generate unique ID for layout elements
 */
export function generateId(prefix: string = 'element'): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * Deep clone a layout configuration
 */
export function cloneLayoutConfig(config: unknown): Record<string, unknown> {
  return JSON.parse(JSON.stringify(config)) as Record<string, unknown>
}

/**
 * Check if a layout config is empty (no fields configured)
 */
export function isLayoutConfigEmpty(config: Record<string, unknown>, layoutType: LayoutType): boolean {
  if (layoutType === 'form' || layoutType === 'detail') {
    const sections = (config.sections as any[]) || []
    for (const section of sections) {
      if (section.type === 'tab') {
        const tabs = section.tabs || []
        for (const tab of tabs) {
          if (tab.fields && tab.fields.length > 0) return false
        }
      } else if (section.type === 'collapse') {
        const items = section.items || []
        for (const item of items) {
          if (item.fields && item.fields.length > 0) return false
        }
      } else if (section.type === 'column') {
        const columns = section.columns || []
        for (const column of columns) {
          if (column.fields && column.fields.length > 0) return false
        }
      } else {
        if (section.fields && section.fields.length > 0) return false
      }
    }
    return true
  }

  if (layoutType === 'list') {
    const columns = (config.columns as any[]) || []
    return columns.length === 0
  }

  if (layoutType === 'search') {
    const fields = (config.fields as any[]) || []
    return fields.length === 0
  }

  return true
}
