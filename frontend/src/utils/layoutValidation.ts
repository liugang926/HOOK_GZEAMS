/**
 * Layout Schema Validation Utilities
 */

import i18n from '@/locales'

export interface LayoutValidationError {
  path: string
  message: string
}

export interface ValidationResult {
  valid: boolean
  errors: LayoutValidationError[]
}

const VALID_SECTION_TYPES = ['section', 'tab', 'divider', 'collapse', 'column'] as const
const VALID_SPANS = [1, 2, 3, 4, 6, 8, 12, 24] as const
const FIELD_MIN_HEIGHT_MIN = 44
const FIELD_MIN_HEIGHT_MAX = 720

export type LayoutType = 'form' | 'list' | 'detail' | 'search'

const lt = (key: string, params?: Record<string, unknown>) => i18n.global.t(key, params || {}) as string

const missingArrayMessage = (field: string) =>
  lt('common.layoutValidation.missingOrInvalidArray', { field })

const cannotBeEmptyMessage = (field: string) =>
  lt('common.layoutValidation.cannotBeEmpty', { field })

const missingRequiredFieldMessage = (field: string) =>
  lt('common.layoutValidation.missingRequiredField', { field })

export function validateLayoutConfig(config: unknown, layoutType: LayoutType): ValidationResult {
  const errors: LayoutValidationError[] = []

  if (!config || typeof config !== 'object') {
    return {
      valid: false,
      errors: [{ path: '', message: lt('common.layoutValidation.configurationMustBeObject') }]
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
      message: missingArrayMessage('sections')
    })
    return
  }

  if (config.sections.length === 0) {
    errors.push({
      path: 'sections',
      message: cannotBeEmptyMessage('sections')
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
      message: missingArrayMessage('columns')
    })
    return
  }

  if (config.columns.length === 0) {
    errors.push({
      path: 'columns',
      message: cannotBeEmptyMessage('columns')
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
      message: lt('common.layoutValidation.mustBeArray', { field: 'fields' })
    })
  }
}

function validateSection(section: any, path: string, errors: LayoutValidationError[]): void {
  if (!section || typeof section !== 'object') {
    errors.push({ path, message: lt('common.layoutValidation.sectionMustBeObject') })
    return
  }

  if (!section.id) {
    errors.push({ path, message: missingRequiredFieldMessage('id') })
  }

  if (!section.type) {
    errors.push({ path, message: missingRequiredFieldMessage('type') })
    return
  }

  if (!VALID_SECTION_TYPES.includes(section.type)) {
    errors.push({
      path,
      message: lt('common.layoutValidation.invalidType', {
        type: section.type,
        types: VALID_SECTION_TYPES.join(', ')
      })
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
      errors.push({ path: `${path}.fields`, message: lt('common.layoutValidation.mustBeArray', { field: 'fields' }) })
    } else {
      section.fields.forEach((field: any, index: number) => {
        validateField(field, `${path}.fields[${index}]`, errors)
      })
    }
  }
}

function validateTabSection(section: any, path: string, errors: LayoutValidationError[]): void {
  if (!Array.isArray(section.tabs)) {
    errors.push({ path: `${path}.tabs`, message: missingArrayMessage('tabs') })
    return
  }

  if (section.tabs.length === 0) {
    errors.push({ path: `${path}.tabs`, message: cannotBeEmptyMessage('tabs') })
  }

  section.tabs.forEach((tab: any, index: number) => {
    validateTab(tab, `${path}.tabs[${index}]`, errors)
  })
}

function validateTab(tab: any, path: string, errors: LayoutValidationError[]): void {
  if (!tab || typeof tab !== 'object') {
    errors.push({ path, message: lt('common.layoutValidation.tabMustBeObject') })
    return
  }

  if (!tab.id) {
    errors.push({ path, message: missingRequiredFieldMessage('id') })
  }

  if (!tab.title) {
    errors.push({ path, message: missingRequiredFieldMessage('title') })
  }

  if (tab.fields !== undefined) {
    if (!Array.isArray(tab.fields)) {
      errors.push({ path: `${path}.fields`, message: lt('common.layoutValidation.mustBeArray', { field: 'fields' }) })
    } else {
      tab.fields.forEach((field: any, index: number) => {
        validateField(field, `${path}.fields[${index}]`, errors)
      })
    }
  }
}

function validateCollapseSection(section: any, path: string, errors: LayoutValidationError[]): void {
  if (!Array.isArray(section.items)) {
    errors.push({ path: `${path}.items`, message: missingArrayMessage('items') })
    return
  }

  if (section.items.length === 0) {
    errors.push({ path: `${path}.items`, message: cannotBeEmptyMessage('items') })
  }

  section.items.forEach((item: any, index: number) => {
    validateCollapseItem(item, `${path}.items[${index}]`, errors)
  })
}

function validateCollapseItem(item: any, path: string, errors: LayoutValidationError[]): void {
  if (!item || typeof item !== 'object') {
    errors.push({ path, message: lt('common.layoutValidation.collapseItemMustBeObject') })
    return
  }

  if (!item.id) {
    errors.push({ path, message: missingRequiredFieldMessage('id') })
  }

  if (!item.title) {
    errors.push({ path, message: missingRequiredFieldMessage('title') })
  }

  if (item.fields !== undefined) {
    if (!Array.isArray(item.fields)) {
      errors.push({ path: `${path}.fields`, message: lt('common.layoutValidation.mustBeArray', { field: 'fields' }) })
    } else {
      item.fields.forEach((field: any, index: number) => {
        validateField(field, `${path}.fields[${index}]`, errors)
      })
    }
  }
}

function validateColumnSection(section: any, path: string, errors: LayoutValidationError[]): void {
  if (!Array.isArray(section.columns)) {
    errors.push({ path: `${path}.columns`, message: missingArrayMessage('columns') })
    return
  }

  if (section.columns.length === 0) {
    errors.push({ path: `${path}.columns`, message: cannotBeEmptyMessage('columns') })
  }

  section.columns.forEach((column: any, index: number) => {
    validateColumnItem(column, `${path}.columns[${index}]`, errors)
  })
}

function validateColumnItem(column: any, path: string, errors: LayoutValidationError[]): void {
  if (!column || typeof column !== 'object') {
    errors.push({ path, message: lt('common.layoutValidation.columnItemMustBeObject') })
    return
  }

  if (column.span !== undefined && !VALID_SPANS.includes(column.span)) {
    errors.push({
      path: `${path}.span`,
      message: lt('common.layoutValidation.spanMustBeOneOf', { options: VALID_SPANS.join(', ') })
    })
  }

  if (column.fields !== undefined) {
    if (!Array.isArray(column.fields)) {
      errors.push({ path: `${path}.fields`, message: lt('common.layoutValidation.mustBeArray', { field: 'fields' }) })
    } else {
      column.fields.forEach((field: any, index: number) => {
        validateField(field, `${path}.fields[${index}]`, errors)
      })
    }
  }
}

function validateListColumn(column: any, path: string, errors: LayoutValidationError[]): void {
  if (!column || typeof column !== 'object') {
    errors.push({ path, message: lt('common.layoutValidation.columnMustBeObject') })
    return
  }

  const fieldCode = column.field_code || column.fieldCode || column.prop || column.code || column.field
  const label = column.label || column.title || column.name

  if (!fieldCode) {
    errors.push({ path, message: missingRequiredFieldMessage('fieldCode') })
  }

  if (!label) {
    errors.push({ path, message: missingRequiredFieldMessage('label') })
  }

  if (column.width !== undefined) {
    const width = Number(column.width)
    if (isNaN(width) || width <= 0) {
      errors.push({ path: `${path}.width`, message: lt('common.layoutValidation.widthMustBePositiveInteger') })
    }
  }
}

function validateField(field: any, path: string, errors: LayoutValidationError[]): void {
  if (!field || typeof field !== 'object') {
    errors.push({ path, message: lt('common.layoutValidation.fieldMustBeObject') })
    return
  }

  if (!field.id) {
    errors.push({ path, message: missingRequiredFieldMessage('id') })
  }

  const fieldCode = field.field_code || field.fieldCode || field.code || field.field || field.prop || field.name
  if (!fieldCode) {
    errors.push({ path, message: missingRequiredFieldMessage('fieldCode') })
  }

  const label = field.label || field.name || field.title
  if (!label) {
    errors.push({ path, message: missingRequiredFieldMessage('label') })
  }

  if (field.span === undefined || field.span === null) {
    errors.push({ path, message: missingRequiredFieldMessage('span') })
  }

  if (field.span !== undefined && !VALID_SPANS.includes(field.span)) {
    errors.push({
      path: `${path}.span`,
      message: lt('common.layoutValidation.spanMustBeIntegerRange', { options: VALID_SPANS.join(', ') })
    })
  }

  const componentProps = {
    ...(field.component_props || {}),
    ...(field.componentProps || {})
  }
  const rawMinHeight = field.minHeight ?? field.min_height ?? componentProps.minHeight ?? componentProps.min_height
  if (rawMinHeight !== undefined && rawMinHeight !== null && rawMinHeight !== '') {
    const minHeight = Number(rawMinHeight)
    const isInteger = Number.isInteger(minHeight)
    if (!Number.isFinite(minHeight) || !isInteger || minHeight < FIELD_MIN_HEIGHT_MIN || minHeight > FIELD_MIN_HEIGHT_MAX) {
      errors.push({
        path: `${path}.minHeight`,
        message: lt('common.layoutValidation.minHeightMustBeIntegerRange', {
          min: FIELD_MIN_HEIGHT_MIN,
          max: FIELD_MIN_HEIGHT_MAX
        })
      })
    }
  }
}

export function getDefaultLayoutConfig(layoutType: LayoutType | 'edit' | 'readonly'): Record<string, unknown> {
  const normalizedType = layoutType === 'edit' ? 'form'
    : layoutType === 'readonly' ? 'detail'
      : layoutType

  if (normalizedType === 'form') {
    return {
      sections: [
        {
          id: `section-${Date.now()}`,
          type: 'section',
          title: lt('common.layoutDefaults.formSectionTitle'),
          collapsible: true,
          collapsed: false,
          columns: 2,
          border: false,
          render_as_card: false,
          fields: []
        }
      ],
      actions: [
        { code: 'submit', label: lt('common.layoutDefaults.submitActionLabel'), type: 'primary', position: 'bottom-right' },
        { code: 'cancel', label: lt('common.layoutDefaults.cancelActionLabel'), type: 'default', position: 'bottom-right' }
      ]
    }
  }

  if (normalizedType === 'list') {
    return {
      columns: [],
      actions: [
        { code: 'create', label: lt('common.layoutDefaults.createActionLabel'), type: 'primary', position: 'top-right' },
        { code: 'delete', label: lt('common.layoutDefaults.deleteActionLabel'), type: 'danger', position: 'toolbar' }
      ],
      page_size: 20,
      show_pagination: true
    }
  }

  if (normalizedType === 'detail') {
    return {
      sections: [
        {
          id: `section-detail-${Date.now()}`,
          type: 'section',
          title: lt('common.layoutDefaults.detailSectionTitle'),
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

  if (normalizedType === 'search') {
    return {
      fields: [],
      layout: 'horizontal',
      label_width: '100px'
    }
  }

  console.warn(lt('common.layoutValidation.unknownLayoutTypeFallback', { type: layoutType }))
  return {
    sections: [
      {
        id: `section-${Date.now()}`,
        type: 'section',
        title: lt('common.layoutDefaults.formSectionTitle'),
        collapsible: true,
        collapsed: false,
        columns: 2,
        border: false,
        fields: []
      }
    ]
  }
}

export function validateAndSanitizeLayoutConfig(config: unknown, layoutType: LayoutType): {
  valid: boolean
  errors: LayoutValidationError[]
  sanitized?: Record<string, unknown>
} {
  const result = validateLayoutConfig(config, layoutType)

  if (!result.valid) {
    return result
  }

  const sanitized = JSON.parse(JSON.stringify(config)) as Record<string, unknown>

  if (layoutType === 'form' && !sanitized.actions) {
    sanitized.actions = []
  }

  return {
    valid: true,
    errors: [],
    sanitized
  }
}

export function generateId(prefix: string = 'element'): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

export function cloneLayoutConfig(config: unknown): Record<string, unknown> {
  return JSON.parse(JSON.stringify(config)) as Record<string, unknown>
}

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
      } else if (section.fields && section.fields.length > 0) {
        return false
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
