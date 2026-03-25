import { computed, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { isPlainObject, isEmptyValue, resolveFieldValue } from '@/utils/fieldKey'
import { resolveTranslatableText } from '@/utils/localeText'
import { normalizeColumnSpan } from '@/platform/layout/semanticGrid'
import { getCanvasPlacementAttrs, toCanvasGridStyle, type CanvasPlacement } from '@/platform/layout/canvasLayout'

interface DetailFieldLike {
  prop: string
  label: string
  hidden?: boolean
  visible?: boolean
  readonly?: boolean
  type?: string
  editorType?: string
  options?: { label: string; value: any; color?: string }[]
  span?: number
  minHeight?: number
  labelClass?: string
  valueClass?: string
  referenceObject?: string
  referenceDisplayField?: string
  referenceSecondaryField?: string
  componentProps?: Record<string, any>
  required?: boolean
  minLength?: number
  maxLength?: number
  minValue?: number
  maxValue?: number
  regexPattern?: string
  validationMessage?: string
  visibilityRule?: {
    field: string
    operator: 'eq' | 'neq' | 'in' | 'notIn'
    value: unknown
  }
  visibility_rule?: {
    field: string
    operator: 'eq' | 'neq' | 'in' | 'notIn'
    value: unknown
  }
  min_length?: number
  max_length?: number
  min_value?: number
  max_value?: number
  regex_pattern?: string
  validation_message?: string
  placement?: {
    row: number
    colStart: number
    colSpan: number
    rowSpan: number
    columns: number
    totalRows: number
    order: number
    canvas?: {
      x: number
      y: number
      width: number
      height: number
    }
  }
}

interface DetailTabLike {
  id: string
  fields: DetailFieldLike[]
}

interface DetailSectionLike {
  name: string
  type?: string
  position?: 'main' | 'sidebar'
  fields: DetailFieldLike[]
  tabs?: DetailTabLike[]
}

interface UseBaseDetailPageFieldsOptions {
  props: {
    sections: DetailSectionLike[]
    data: Record<string, any>
    formData: Record<string, any>
    fieldSpan: number
    formRules: Record<string, any>
  }
  activeTabs: Ref<Record<string, string>>
}

type FormRuleLike = Record<string, any>
type VisibilityOperator = 'eq' | 'neq' | 'in' | 'notIn'

const isEmptyFieldValue = (value: unknown): boolean => {
  if (value === null || value === undefined) return true
  if (typeof value === 'string') return value.trim().length === 0
  if (Array.isArray(value)) return value.length === 0
  return false
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

const isFieldExplicitlyHidden = (field: DetailFieldLike): boolean => {
  return field.hidden === true || field.visible === false
}

const normalizeVisibilityOperator = (value: unknown): VisibilityOperator | undefined => {
  if (value === 'eq' || value === 'neq' || value === 'in' || value === 'notIn') return value
  return undefined
}

const normalizeVisibilityRule = (
  field: DetailFieldLike
): { field: string; operator: VisibilityOperator; value: unknown } | undefined => {
  const raw = field.visibilityRule || field.visibility_rule
  if (!raw || !isPlainObject(raw)) return undefined
  const dependentField = String(raw.field || '').trim()
  const operator = normalizeVisibilityOperator(raw.operator)
  if (!dependentField || !operator) return undefined
  return {
    field: dependentField,
    operator,
    value: raw.value
  }
}

const resolveRuleTrigger = (fieldType: string): 'blur' | 'change' => {
  if (['select', 'multi_select', 'radio', 'checkbox', 'boolean', 'switch', 'date', 'datetime', 'time', 'daterange', 'year', 'month', 'reference'].includes(fieldType)) {
    return 'change'
  }
  return 'blur'
}

const buildPatternValidator = (field: DetailFieldLike, pattern: string) => {
  let regex: RegExp | null = null
  try {
    regex = new RegExp(pattern)
  } catch {
    regex = null
  }

  return (_rule: FormRuleLike, value: unknown, callback: (error?: Error) => void) => {
    if (!regex || isEmptyFieldValue(value)) {
      callback()
      return
    }

    const text = String(value)
    if (!regex.test(text)) {
      callback(new Error(field.validationMessage || `${field.label} format is invalid`))
      return
    }
    callback()
  }
}

const buildMinLengthValidator = (field: DetailFieldLike, minLength: number) => {
  return (_rule: FormRuleLike, value: unknown, callback: (error?: Error) => void) => {
    if (isEmptyFieldValue(value)) {
      callback()
      return
    }
    const length = Array.isArray(value) ? value.length : String(value).length
    if (length < minLength) {
      callback(new Error(field.validationMessage || `${field.label} must be at least ${minLength} characters`))
      return
    }
    callback()
  }
}

const buildMaxLengthValidator = (field: DetailFieldLike, maxLength: number) => {
  return (_rule: FormRuleLike, value: unknown, callback: (error?: Error) => void) => {
    if (isEmptyFieldValue(value)) {
      callback()
      return
    }
    const length = Array.isArray(value) ? value.length : String(value).length
    if (length > maxLength) {
      callback(new Error(field.validationMessage || `${field.label} must be at most ${maxLength} characters`))
      return
    }
    callback()
  }
}

const buildMinValueValidator = (field: DetailFieldLike, minValue: number) => {
  return (_rule: FormRuleLike, value: unknown, callback: (error?: Error) => void) => {
    if (isEmptyFieldValue(value)) {
      callback()
      return
    }
    const num = Number(value)
    if (Number.isFinite(num) && num < minValue) {
      callback(new Error(field.validationMessage || `${field.label} must be greater than or equal to ${minValue}`))
      return
    }
    callback()
  }
}

const buildMaxValueValidator = (field: DetailFieldLike, maxValue: number) => {
  return (_rule: FormRuleLike, value: unknown, callback: (error?: Error) => void) => {
    if (isEmptyFieldValue(value)) {
      callback()
      return
    }
    const num = Number(value)
    if (Number.isFinite(num) && num > maxValue) {
      callback(new Error(field.validationMessage || `${field.label} must be less than or equal to ${maxValue}`))
      return
    }
    callback()
  }
}

export const buildDetailFieldRules = (field: DetailFieldLike): FormRuleLike[] => {
  if (!field?.prop || isFieldExplicitlyHidden(field) || field.readonly === true) return []

  const fieldType = String(field.editorType || field.type || 'text').trim() || 'text'
  const trigger = resolveRuleTrigger(fieldType)
  const rules: FormRuleLike[] = []
  const minLength = readOptionalNumber(field.minLength, field.min_length)
  const maxLength = readOptionalNumber(field.maxLength, field.max_length)
  const minValue = readOptionalNumber(field.minValue, field.min_value)
  const maxValue = readOptionalNumber(field.maxValue, field.max_value)
  const regexPattern = readOptionalString(field.regexPattern, field.regex_pattern)
  const customMessage = readOptionalString(field.validationMessage, field.validation_message)

  if (field.required) {
    rules.push({
      required: true,
      trigger,
      validator: (_rule: FormRuleLike, value: unknown, callback: (error?: Error) => void) => {
        if (isEmptyFieldValue(value)) {
          callback(new Error(customMessage || `${field.label} is required`))
          return
        }
        callback()
      }
    })
  }

  if (minLength !== undefined) {
    rules.push({ trigger, validator: buildMinLengthValidator(field, minLength) })
  }

  if (maxLength !== undefined) {
    rules.push({ trigger, validator: buildMaxLengthValidator(field, maxLength) })
  }

  if (minValue !== undefined) {
    rules.push({ trigger: 'change', validator: buildMinValueValidator(field, minValue) })
  }

  if (maxValue !== undefined) {
    rules.push({ trigger: 'change', validator: buildMaxValueValidator(field, maxValue) })
  }

  if (regexPattern) {
    rules.push({ trigger, validator: buildPatternValidator(field, regexPattern) })
  }

  return rules
}

export function useBaseDetailPageFields(options: UseBaseDetailPageFieldsOptions) {
  const { locale } = useI18n()

  const getDisplayText = (value: any): string => {
    return resolveTranslatableText(value, locale.value as 'zh-CN' | 'en-US')
  }

  const normalizeListValue = (value: unknown): unknown[] => {
    if (Array.isArray(value)) return value
    if (typeof value === 'string') {
      return value
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean)
    }
    if (value === null || value === undefined || value === '') return []
    return [value]
  }

  const samePrimitiveValue = (left: unknown, right: unknown): boolean => {
    if (left === right) return true
    if (left === null || left === undefined || right === null || right === undefined) return false

    const leftText = String(left).trim()
    const rightText = String(right).trim()
    if (leftText === rightText) return true

    const leftNumber = Number(left)
    const rightNumber = Number(right)
    if (Number.isFinite(leftNumber) && Number.isFinite(rightNumber)) {
      return leftNumber === rightNumber
    }

    return leftText.toLowerCase() === rightText.toLowerCase()
  }

  const evaluateVisibilityMatch = (
    actualValue: unknown,
    operator: VisibilityOperator,
    expectedValue: unknown
  ): boolean => {
    const actualValues = Array.isArray(actualValue) ? actualValue : [actualValue]
    const expectedValues = normalizeListValue(expectedValue)

    if (operator === 'eq') {
      return actualValues.some((candidate) => samePrimitiveValue(candidate, expectedValue))
    }

    if (operator === 'neq') {
      return actualValues.every((candidate) => !samePrimitiveValue(candidate, expectedValue))
    }

    if (operator === 'in') {
      return actualValues.some((candidate) =>
        expectedValues.some((expected) => samePrimitiveValue(candidate, expected))
      )
    }

    return actualValues.every((candidate) =>
      expectedValues.every((expected) => !samePrimitiveValue(candidate, expected))
    )
  }

  const resolveFromObjectPath = (obj: any, prop: string): any => {
    const parts = prop.split('.')
    let current = obj

    for (const part of parts) {
      if (!isPlainObject(current)) return undefined

      if (part in current) {
        current = current[part]
        continue
      }

      const camelKey = part.replace(/_([a-z])/g, (_, char: string) => char.toUpperCase())
      if (camelKey in current) {
        current = current[camelKey]
        continue
      }

      const snakeKey = part.replace(/[A-Z]/g, (char: string) => `_${char.toLowerCase()}`)
      if (snakeKey in current) {
        current = current[snakeKey]
        continue
      }

      return undefined
    }

    return current
  }

  const resolveValue = (data: any, prop?: string, allowWrapped = true): any => {
    if (!data || !prop) return undefined

    if (!prop.includes('.')) {
      return resolveFieldValue(data, {
        fieldCode: prop,
        includeWrappedData: allowWrapped,
        includeCustomBags: true,
        treatEmptyAsMissing: true,
        returnEmptyMatch: true
      })
    }

    const directValue = resolveFromObjectPath(data, prop)
    if (!isEmptyValue(directValue)) return directValue

    if (allowWrapped && isPlainObject((data as any).data)) {
      const wrappedValue = resolveFromObjectPath((data as any).data, prop)
      if (!isEmptyValue(wrappedValue)) return wrappedValue
    }

    return directValue
  }

  const evaluateFieldVisibility = (field: DetailFieldLike): boolean => {
    if (field.hidden === true || field.visible === false) return false

    const rule = normalizeVisibilityRule(field)
    if (!rule) return true

    const currentValue = resolveValue(options.props.formData, rule.field, false)
    const sourceValue = currentValue === undefined
      ? resolveValue(options.props.data, rule.field, true)
      : currentValue

    return evaluateVisibilityMatch(sourceValue, rule.operator, rule.value)
  }

  const resolvedSections = computed<DetailSectionLike[]>(() => {
    return (options.props.sections || []).reduce<DetailSectionLike[]>((sections, section) => {
      if (section.type === 'tab' && Array.isArray(section.tabs) && section.tabs.length > 0) {
        const tabs = (section.tabs || [])
          .map((tab) => ({
            ...tab,
            fields: (tab.fields || []).map((field) => ({
              ...field,
              visible: evaluateFieldVisibility(field)
            }))
          }))
          .filter((tab) => tab.fields.some((field) => !isFieldExplicitlyHidden(field)))

        if (tabs.length > 0) {
          sections.push({
            ...section,
            tabs
          })
        }
        return sections
      }

      const fields = (section.fields || []).map((field) => ({
        ...field,
        visible: evaluateFieldVisibility(field)
      }))

      if (fields.some((field) => !isFieldExplicitlyHidden(field))) {
        sections.push({
          ...section,
          fields
        })
      }

      return sections
    }, [])
  })

  const editDrawerProxyFields = computed<DetailFieldLike[]>(() => {
    const out: DetailFieldLike[] = []

    for (const section of resolvedSections.value) {
      if (section.type === 'tab' && Array.isArray(section.tabs) && section.tabs.length > 0) {
        const activeId = options.activeTabs.value[section.name] || section.tabs[0].id
        const activeTab = section.tabs.find((tab) => tab.id === activeId) || section.tabs[0]
        for (const field of activeTab.fields || []) {
          if (!isFieldExplicitlyHidden(field)) out.push(field)
        }
        continue
      }

      for (const field of section.fields || []) {
        if (!isFieldExplicitlyHidden(field)) out.push(field)
      }
    }

    return out
  })

  const getFieldValue = (field: DetailFieldLike) => {
    const value = resolveValue(options.props.data, field.prop)
    return value !== undefined && value !== null ? value : '-'
  }

  const getEditFieldValue = (field: DetailFieldLike) => {
    const value = resolveValue(options.props.formData, field.prop, false)
    return value !== undefined ? value : null
  }

  const resolveEditFieldType = (field: DetailFieldLike): string => {
    const explicitType = String(field.editorType || '').trim()
    if (explicitType) return explicitType

    const fallbackType = String(field.type || 'text').trim()
    if (fallbackType === 'tag') return 'select'
    if (fallbackType === 'link') return 'text'
    return fallbackType || 'text'
  }

  const toInlineEditRuntimeField = (field: DetailFieldLike): Record<string, any> => {
    return {
      code: field.prop,
      name: field.label,
      label: field.label,
      fieldType: resolveEditFieldType(field),
      options: field.options,
      referenceObject: field.referenceObject,
      referenceDisplayField: field.referenceDisplayField,
      referenceSecondaryField: field.referenceSecondaryField,
      componentProps: field.componentProps || {}
    }
  }

  const getDetailSectionColumns = (section: DetailSectionLike): number => {
    if (section.position === 'sidebar') return 1

    const candidates: DetailFieldLike[] = []
    candidates.push(...(section.fields || []))
    for (const tab of section.tabs || []) candidates.push(...(tab.fields || []))

    for (const field of candidates) {
      const placement = field?.placement
      const columns = Number(placement?.columns)
      if (Number.isFinite(columns) && columns > 0) {
        return Math.round(columns)
      }
    }
    return 2
  }

  const getSectionCanvasStyle = (section: DetailSectionLike): Record<string, string> => {
    const styles: Record<string, string> = {
      '--detail-section-columns': String(getDetailSectionColumns(section))
    }
    if ((section as any).labelPosition === 'top') {
      styles['--section-label-position'] = 'top'
    }
    if ((section as any).labelWidth) {
      const width = (section as any).labelWidth
      styles['--section-label-width'] = typeof width === 'number' ? `${width}px` : width
    }
    return styles
  }

  const getFieldColStyle = (
    field: DetailFieldLike,
    section: DetailSectionLike
  ): Record<string, string> => {
    if (field && (field as any).fullWidth) {
      return { gridColumn: '1 / -1' }
    }

    const placement = field?.placement as CanvasPlacement | undefined
    if (placement) {
      return toCanvasGridStyle(placement)
    }

    const columns = getDetailSectionColumns(section)
    const colSpan =
      section?.position === 'sidebar'
        ? 1
        : normalizeColumnSpan(field?.span ?? options.props.fieldSpan, columns)
    return {
      gridColumn: `span ${colSpan}`
    }
  }

  const getFieldItemStyle = (field: DetailFieldLike): Record<string, string> => {
    const styles: Record<string, string> = {}
    const minHeight = Number(field?.minHeight)
    if (Number.isFinite(minHeight) && minHeight > 0) {
      styles.minHeight = `${Math.round(minHeight)}px`
    }
    
    if (field && (field as any).labelWidth) {
      const width = (field as any).labelWidth
      styles['--field-label-width'] = typeof width === 'number' ? `${width}px` : width
    } else {
      styles['--field-label-width'] = 'var(--section-label-width, var(--detail-label-width))'
    }
    return styles
  }

  const getFieldItemClass = (field: DetailFieldLike, section?: DetailSectionLike): string[] => {
    const classes: string[] = []
    const fieldPos = field ? (field as any).labelPosition : undefined
    const sectionPos = section ? (section as any).labelPosition : undefined
    
    if (fieldPos === 'top' || (!fieldPos && sectionPos === 'top')) {
      classes.push('label-position-top')
    }
    return classes
  }

  const getFieldPlacementAttrs = (field: DetailFieldLike): Record<string, string> => {
    return getCanvasPlacementAttrs(field?.placement as CanvasPlacement | undefined)
  }

  const generatedFormRules = computed<Record<string, FormRuleLike[]>>(() => {
    const merged: Record<string, FormRuleLike[]> = {}
    for (const [prop, rules] of Object.entries(options.props.formRules || {})) {
      merged[prop] = Array.isArray(rules) ? [...rules] : [rules]
    }

    for (const field of editDrawerProxyFields.value) {
      const rules = buildDetailFieldRules(field)
      if (rules.length > 0) {
        merged[field.prop] = [...(merged[field.prop] || []), ...rules]
      }
    }
    return merged
  })

  return {
    getDisplayText,
    resolvedSections,
    editDrawerProxyFields,
    getFieldValue,
    getEditFieldValue,
    toInlineEditRuntimeField,
    getFieldItemStyle,
    getFieldItemClass,
    getSectionCanvasStyle,
    getFieldColStyle,
    getFieldPlacementAttrs,
    generatedFormRules
  }
}
