import { placeCanvasFields, type CanvasPlacement } from '@/platform/layout/canvasLayout'
import { cloneLayoutConfig } from '@/utils/layoutValidation'
import type {
  FieldVisibilityRule,
  DesignerAnyRecord,
  DesignerFieldDefinition,
  LayoutConfig,
  LayoutField,
  LayoutSection
} from '@/components/designer/designerTypes'

export type ApiDataEnvelope<T> = { data?: T }

export const isRecord = (value: unknown): value is DesignerAnyRecord => {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

export function unwrapData<T>(raw: T | ApiDataEnvelope<T>): T {
  if (isRecord(raw) && 'data' in raw) {
    const value = (raw as ApiDataEnvelope<T>).data
    return (value ?? raw) as T
  }
  return raw as T
}

export const readErrorMessage = (error: unknown): string | null => {
  if (!isRecord(error)) return null
  const response = error.response
  if (!isRecord(response)) return null
  const data = response.data
  if (!isRecord(data)) return null
  const message = data.message
  return typeof message === 'string' && message.trim() ? message : null
}

export const readComponentProps = (
  field: Partial<DesignerFieldDefinition & LayoutField> | null | undefined
): DesignerAnyRecord => {
  const componentProps = {
    ...((isRecord(field?.componentProps) ? field.componentProps : {}) as DesignerAnyRecord),
    ...((isRecord(field?.component_props) ? field.component_props : {}) as DesignerAnyRecord)
  }

  const relatedObjectCode = readOptionalString(
    (field as DesignerAnyRecord | undefined)?.relatedObjectCode,
    (field as DesignerAnyRecord | undefined)?.related_object_code,
    (field as DesignerAnyRecord | undefined)?.targetObjectCode,
    (field as DesignerAnyRecord | undefined)?.target_object_code
  )
  const displayMode = readOptionalString(
    (field as DesignerAnyRecord | undefined)?.displayMode,
    (field as DesignerAnyRecord | undefined)?.display_mode
  )
  const pageSize = readOptionalNumber(
    (field as DesignerAnyRecord | undefined)?.pageSize,
    (field as DesignerAnyRecord | undefined)?.page_size
  )
  const lookupColumns =
    (field as DesignerAnyRecord | undefined)?.lookupColumns ??
    (field as DesignerAnyRecord | undefined)?.lookup_columns
  const relatedFields =
    (field as DesignerAnyRecord | undefined)?.relatedFields ??
    (field as DesignerAnyRecord | undefined)?.related_fields

  if (relatedObjectCode) {
    componentProps.relatedObjectCode = relatedObjectCode
    componentProps.related_object_code = relatedObjectCode
    componentProps.targetObjectCode = relatedObjectCode
    componentProps.target_object_code = relatedObjectCode
  }
  if (displayMode) {
    componentProps.displayMode = displayMode
    componentProps.display_mode = displayMode
  }
  if (pageSize !== undefined) {
    componentProps.pageSize = pageSize
    componentProps.page_size = pageSize
  }
  if (Array.isArray(lookupColumns)) {
    componentProps.lookupColumns = lookupColumns
    componentProps.lookup_columns = lookupColumns
  }
  if (Array.isArray(relatedFields)) {
    componentProps.relatedFields = relatedFields
    componentProps.related_fields = relatedFields
  }

  return componentProps
}

const readOptionalBoolean = (...values: unknown[]): boolean | undefined => {
  for (const value of values) {
    if (value === undefined || value === null || value === '') continue
    if (typeof value === 'boolean') return value
    if (typeof value === 'number') return value !== 0
    if (typeof value === 'string') {
      const normalized = value.trim().toLowerCase()
      if (['true', '1', 'yes', 'on'].includes(normalized)) return true
      if (['false', '0', 'no', 'off'].includes(normalized)) return false
    }
  }
  return undefined
}

const readOptionalNumber = (...values: unknown[]): number | undefined => {
  for (const value of values) {
    if (value === undefined || value === null || value === '') continue
    const num = Number(value)
    if (Number.isFinite(num)) return num
  }
  return undefined
}

const readOptionalString = (...values: unknown[]): string | undefined => {
  for (const value of values) {
    if (typeof value !== 'string') continue
    const normalized = value.trim()
    if (normalized) return normalized
  }
  return undefined
}

const normalizeVisibilityOperator = (value: unknown): FieldVisibilityRule['operator'] | undefined => {
  if (value === 'eq' || value === 'neq' || value === 'in' || value === 'notIn') return value
  return undefined
}

const normalizeVisibilityRule = (...values: unknown[]): FieldVisibilityRule | undefined => {
  for (const value of values) {
    if (!isRecord(value)) continue
    const field = readOptionalString(value.field)
    const operator = normalizeVisibilityOperator(value.operator)
    if (!field || !operator) continue
    return {
      field,
      operator,
      value: value.value
    }
  }
  return undefined
}

export const normalizeLayoutFieldAliases = (field: LayoutField): LayoutField => {
  const componentProps = readComponentProps(field)
  const fieldType = String(field.fieldType || field.field_type || 'text').trim() || 'text'
  const minHeight = resolveLayoutFieldMinHeight(field)
  const minLength = readOptionalNumber(field.minLength, field.min_length)
  const maxLength = readOptionalNumber(field.maxLength, field.max_length)
  const minValue = readOptionalNumber(field.minValue, field.min_value)
  const maxValue = readOptionalNumber(field.maxValue, field.max_value)
  const regexPattern = readOptionalString(field.regexPattern, field.regex_pattern)
  const validationMessage = readOptionalString(field.validationMessage, field.validation_message)
  const required = readOptionalBoolean(field.required)
  const readonly = readOptionalBoolean(field.readonly)
  const visible = readOptionalBoolean(field.visible)
  const visibilityRule = normalizeVisibilityRule(field.visibilityRule, field.visibility_rule)

  return {
    ...field,
    fieldType,
    field_type: fieldType,
    componentProps,
    component_props: componentProps,
    minHeight,
    min_height: minHeight,
    minLength,
    min_length: minLength,
    maxLength,
    max_length: maxLength,
    minValue,
    min_value: minValue,
    maxValue,
    max_value: maxValue,
    regexPattern,
    regex_pattern: regexPattern,
    validationMessage,
    validation_message: validationMessage,
    required,
    readonly,
    visible,
    visibilityRule,
    visibility_rule: visibilityRule
  }
}

const normalizeLayoutFieldList = (fields: LayoutField[] | undefined): LayoutField[] => {
  return (fields || []).map((field) => normalizeLayoutFieldAliases(field))
}

const normalizeDetailRegionSectionAliases = (section: LayoutSection): LayoutSection => {
  const next = { ...section }
  const relationCode = readOptionalString(next.relationCode, next.relation_code)
  const fieldCode = readOptionalString(next.fieldCode, next.field_code)
  const targetObjectCode = readOptionalString(next.targetObjectCode, next.target_object_code)
  const detailEditMode = readOptionalString(next.detailEditMode, next.detail_edit_mode)
  const toolbarConfig = isRecord(next.toolbarConfig) ? next.toolbarConfig : (isRecord(next.toolbar_config) ? next.toolbar_config : undefined)
  const summaryRules = Array.isArray(next.summaryRules) ? next.summaryRules : (Array.isArray(next.summary_rules) ? next.summary_rules : undefined)
  const validationRules = Array.isArray(next.validationRules) ? next.validationRules : (Array.isArray(next.validation_rules) ? next.validation_rules : undefined)
  const titleEn = readOptionalString(next.titleEn, next.title_en)
  const translationKey = readOptionalString(next.translationKey, next.translation_key)
  const titleI18n = isRecord(next.titleI18n) ? next.titleI18n : (isRecord(next.title_i18n) ? next.title_i18n : undefined)

  return {
    ...next,
    columns: 1,
    relationCode,
    relation_code: relationCode,
    fieldCode,
    field_code: fieldCode,
    targetObjectCode,
    target_object_code: targetObjectCode,
    detailEditMode,
    detail_edit_mode: detailEditMode,
    toolbarConfig,
    toolbar_config: toolbarConfig,
    summaryRules,
    summary_rules: summaryRules,
    validationRules,
    validation_rules: validationRules,
    titleEn,
    title_en: titleEn,
    titleI18n,
    title_i18n: titleI18n,
    translationKey,
    translation_key: translationKey
  }
}

export const normalizeLayoutConfigFieldAliases = (rawConfig: LayoutConfig): LayoutConfig => {
  const next = cloneLayoutConfig(rawConfig || { sections: [] }) as LayoutConfig
  next.sections = (next.sections || []).map((rawSection) => {
    const section = { ...(rawSection || {}) }
    if (section.type === 'tab') {
      section.tabs = (section.tabs || []).map((tab) => ({
        ...(tab || {}),
        fields: normalizeLayoutFieldList(tab.fields)
      }))
      return section
    }

    if (section.type === 'collapse') {
      section.items = (section.items || []).map((item) => ({
        ...(item || {}),
        fields: normalizeLayoutFieldList(item.fields)
      }))
      return section
    }

    if (section.type === 'detail-region') {
      return normalizeDetailRegionSectionAliases(section)
    }

    section.fields = normalizeLayoutFieldList(section.fields)
    return section
  })
  return next
}

export const readLayoutPlacement = (
  field: LayoutField | null | undefined
): LayoutField['layoutPlacement'] | LayoutField['layout_placement'] | null => {
  if (!field) return null
  return field.layoutPlacement || field.layout_placement || null
}

export const FIELD_MIN_HEIGHT_MIN = 44
export const FIELD_MIN_HEIGHT_MAX = 720
export const FIELD_MIN_HEIGHT_STEP = 8

export const normalizeFieldMinHeight = (value: unknown): number | undefined => {
  const raw = Number(value)
  if (!Number.isFinite(raw) || raw <= 0) return undefined
  return Math.round(raw)
}

export const clampFieldMinHeight = (value: number): number => {
  if (!Number.isFinite(value)) return FIELD_MIN_HEIGHT_MIN
  const rounded = Math.round(value / FIELD_MIN_HEIGHT_STEP) * FIELD_MIN_HEIGHT_STEP
  return Math.max(FIELD_MIN_HEIGHT_MIN, Math.min(FIELD_MIN_HEIGHT_MAX, rounded))
}

export const resolveLayoutFieldMinHeight = (
  field: Partial<LayoutField> | null | undefined
): number | undefined => {
  if (!field) return undefined
  const componentProps = readComponentProps(field)
  const componentMinHeight = componentProps.minHeight
  const legacyComponentMinHeight = componentProps.min_height
  const raw = componentMinHeight ?? legacyComponentMinHeight ?? field.minHeight ?? field.min_height
  const normalized = normalizeFieldMinHeight(raw)
  return normalized ? clampFieldMinHeight(normalized) : undefined
}

export const setLayoutFieldMinHeight = (field: LayoutField, value: unknown) => {
  const normalized = normalizeFieldMinHeight(value)
  const next = normalized ? clampFieldMinHeight(normalized) : undefined

  const componentProps = readComponentProps(field)

  if (next === undefined) {
    delete componentProps.minHeight
    delete componentProps.min_height
  } else {
    componentProps.minHeight = next
    delete componentProps.min_height
  }

  field.componentProps = componentProps
  field.component_props = componentProps
  if (next === undefined) {
    delete field.minHeight
    delete field.min_height
  } else {
    field.minHeight = next
    field.min_height = next
  }
}

export const toCanvasField = (field: LayoutField): LayoutField => {
  return normalizeLayoutFieldAliases(field)
}

export function getColumns(section: Partial<LayoutSection> | null | undefined): number {
  if (section?.type === 'detail-region') return 1
  return Number(section?.columns || section?.columnCount || section?.column || 2) || 2
}

export function getRenderColumns(section: Partial<LayoutSection> | null | undefined): number {
  if (section?.position === 'sidebar') return 1
  return getColumns(section)
}

const writeLegacyLayoutPlacement = (
  field: LayoutField,
  placement: LayoutField['layoutPlacement'] | undefined
): void => {
  if (!placement) {
    delete field.layoutPlacement
    delete field.layout_placement
    return
  }

  field.layoutPlacement = placement
  field.layout_placement = {
    row: placement.row,
    col_start: placement.colStart,
    col_span: placement.colSpan,
    row_span: placement.rowSpan,
    columns: placement.columns,
    total_rows: placement.totalRows,
    order: placement.order
  }
}

const toPersistedLayoutPlacement = (placement: CanvasPlacement | null): LayoutField['layoutPlacement'] | undefined => {
  if (!placement) return undefined
  return {
    row: placement.row,
    colStart: placement.colStart,
    colSpan: placement.colSpan,
    rowSpan: placement.rowSpan,
    columns: placement.columns,
    totalRows: placement.totalRows,
    order: placement.order,
    canvas: {
      x: placement.canvas.x,
      y: placement.canvas.y,
      width: placement.canvas.width,
      height: placement.canvas.height
    }
  }
}

const applyPlacementSnapshotToFieldList = (
  fields: LayoutField[],
  columns: number
): LayoutField[] => {
  const placementSeed = (fields || []).map((field) => ({
    span: field?.span ?? 1,
    minHeight: resolveLayoutFieldMinHeight(field)
  }))
  const placed = placeCanvasFields(placementSeed, columns, {
    preferSavedPlacement: false
  })

  return (fields || []).map((field, index) => {
    const next = { ...field }
    setLayoutFieldMinHeight(next, resolveLayoutFieldMinHeight(next))
    const placement = (placed[index]?.placement || null) as CanvasPlacement | null
    const persisted = toPersistedLayoutPlacement(placement)
    if (persisted) {
      writeLegacyLayoutPlacement(next, persisted)
    } else {
      writeLegacyLayoutPlacement(next, undefined)
    }
    return next
  })
}

export const buildLayoutConfigWithPlacementSnapshot = (rawConfig: LayoutConfig): LayoutConfig => {
  const next = cloneLayoutConfig(rawConfig || { sections: [] }) as LayoutConfig
  next.sections = (next.sections || []).map((rawSection) => {
    const section = { ...(rawSection || {}) }
    const columns = getRenderColumns(section)
    if (section.type === 'tab') {
      section.tabs = (section.tabs || []).map((tab) => ({
        ...(tab || {}),
        fields: applyPlacementSnapshotToFieldList(tab.fields || [], columns)
      }))
      return section
    }

    if (section.type === 'collapse') {
      section.items = (section.items || []).map((item) => ({
        ...(item || {}),
        fields: applyPlacementSnapshotToFieldList(item.fields || [], columns)
      }))
      return section
    }

    if (section.type === 'detail-region') {
      return normalizeDetailRegionSectionAliases(section)
    }

    section.fields = applyPlacementSnapshotToFieldList(section.fields || [], columns)
    return section
  })
  return next
}
