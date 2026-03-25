import type { ObjectRuntimeResponse } from '@/api/dynamic'
import { filterSystemFields } from '@/utils/transform'
import { resolveTranslatableText } from '@/utils/localeText'
import { normalizeFieldType } from '@/utils/fieldType'

type AnyRecord = Record<string, any>

export interface DetailRegionFieldOption {
  code: string
  label: string
  fieldType: string
  width?: number
  minWidth?: number
  align?: 'left' | 'center' | 'right'
  fixed?: 'left' | 'right'
  ellipsis?: boolean
  formatter?: string
  emptyText?: string
  tooltipTemplate?: string
  options?: Array<Record<string, unknown>>
  referenceObject?: string
  targetObjectCode?: string
  referenceDisplayField?: string
  referenceSecondaryField?: string
  componentProps?: Record<string, unknown>
  readonly?: boolean
  required?: boolean
}

const toFieldCode = (field: AnyRecord): string => {
  return String(field?.code || field?.fieldCode || field?.field_code || '').trim()
}

const resolveMultilingualLabel = (value: unknown): string => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return ''
  const record = value as AnyRecord
  const candidateKeys = [
    'zh-CN',
    'zh-cn',
    'zh_CN',
    'zh_cn',
    'zhCN',
    'zhcn',
    'zh',
    'en-US',
    'en-us',
    'en_US',
    'en_us',
    'enUS',
    'enus',
    'en'
  ]

  for (const key of candidateKeys) {
    const text = String(record[key] || '').trim()
    if (text) return text
  }

  return ''
}

const toDisplayLabel = (field: AnyRecord, fallback: string): string => {
  return (
    resolveTranslatableText(field?.label) ||
    resolveMultilingualLabel(field?.label) ||
    resolveTranslatableText(field?.name) ||
    resolveMultilingualLabel(field?.name) ||
    String(field?.label || field?.name || fallback).trim() ||
    fallback
  )
}

const extractEditableFields = (runtime: ObjectRuntimeResponse): AnyRecord[] => {
  const raw = (runtime?.fields || {}) as AnyRecord
  const editableFields = Array.isArray(raw.editableFields)
    ? raw.editableFields
    : Array.isArray(raw.editable_fields)
      ? raw.editable_fields
      : Array.isArray(raw.fields)
        ? raw.fields
        : []

  return editableFields.filter((field: AnyRecord) => {
    const isReverse = field?.isReverseRelation ?? field?.is_reverse_relation
    const isHidden = field?.isHidden ?? field?.is_hidden
    return isReverse !== true && isHidden !== true
  })
}

export const extractDetailRegionFieldOptions = (
  runtime: ObjectRuntimeResponse
): DetailRegionFieldOption[] => {
  const businessFields = filterSystemFields(extractEditableFields(runtime))
  return businessFields
    .map((field: AnyRecord) => {
      const code = toFieldCode(field)
      if (!code) return null

      const componentProps = {
        ...(field?.component_props || {}),
        ...(field?.componentProps || {})
      }
      const width = Number(field?.width ?? field?.columnWidth ?? field?.column_width)
      const minWidth = Number(field?.minWidth ?? field?.min_width ?? field?.minColumnWidth ?? field?.min_column_width)
      const align = String(field?.align || field?.columnAlign || field?.column_align || '').trim().toLowerCase()
      const fixed = String(field?.fixed || field?.columnFixed || field?.column_fixed || '').trim().toLowerCase()
      const ellipsis =
        field?.ellipsis === true ||
        field?.showOverflowTooltip === true ||
        field?.show_overflow_tooltip === true
      const formatter = String(
        field?.formatter ||
        field?.displayFormatter ||
        componentProps?.formatter ||
        ''
      ).trim()
      const emptyText = String(
        field?.emptyText ??
        field?.empty_text ??
        componentProps?.emptyText ??
        componentProps?.empty_text ??
        ''
      ).trim()
      const tooltipTemplate = String(
        field?.tooltipTemplate ??
        field?.tooltip_template ??
        componentProps?.tooltipTemplate ??
        componentProps?.tooltip_template ??
        ''
      ).trim()
      const option: DetailRegionFieldOption = {
        code,
        label: toDisplayLabel(field, code),
        fieldType: normalizeFieldType(field?.fieldType || field?.field_type || field?.type || 'text'),
        options: Array.isArray(field?.options) ? field.options : (Array.isArray(field?.choices) ? field.choices : undefined),
        referenceObject:
          field?.referenceObject ||
          field?.reference_object ||
          field?.targetObjectCode ||
          field?.target_object_code,
        targetObjectCode:
          field?.targetObjectCode ||
          field?.target_object_code ||
          field?.referenceObject ||
          field?.reference_object,
        referenceDisplayField:
          field?.referenceDisplayField ||
          field?.reference_display_field ||
          field?.displayField ||
          field?.display_field,
        referenceSecondaryField:
          field?.referenceSecondaryField ||
          field?.reference_secondary_field,
        readonly: field?.readonly === true || field?.isReadonly === true || field?.is_readonly === true,
        required: field?.required === true || field?.isRequired === true || field?.is_required === true
      }

      if (Number.isFinite(width) && width > 0) option.width = width
      if (Number.isFinite(minWidth) && minWidth > 0) option.minWidth = minWidth
      if (align === 'left' || align === 'center' || align === 'right') option.align = align
      if (fixed === 'left' || fixed === 'right') option.fixed = fixed
      if (ellipsis) option.ellipsis = true
      if (formatter) option.formatter = formatter
      if (emptyText) option.emptyText = emptyText
      if (tooltipTemplate) option.tooltipTemplate = tooltipTemplate
      if (Object.keys(componentProps).length > 0) option.componentProps = componentProps

      return option
    })
    .filter((item): item is DetailRegionFieldOption => !!item)
}

const toStringArray = (value: unknown, keyResolver: (item: unknown) => string): string[] => {
  if (!Array.isArray(value)) return []
  const seen = new Set<string>()
  const output: string[] = []

  for (const item of value) {
    const key = keyResolver(item)
    if (!key || seen.has(key)) continue
    seen.add(key)
    output.push(key)
  }

  return output
}

export const extractRelatedFieldCodes = (value: unknown): string[] => {
  return toStringArray(value, (item) => {
    if (!item || typeof item !== 'object') return ''
    return String((item as AnyRecord).code || (item as AnyRecord).fieldCode || '').trim()
  })
}

export const extractLookupColumnKeys = (value: unknown): string[] => {
  return toStringArray(value, (item) => {
    if (typeof item === 'string') return String(item).trim()
    if (!item || typeof item !== 'object') return ''
    return String((item as AnyRecord).key || '').trim()
  })
}

export const buildRelatedFieldConfigs = (
  selectedCodes: string[],
  availableFields: DetailRegionFieldOption[],
  existingValue?: unknown
): Array<Record<string, unknown>> => {
  const selectedSet = new Set(selectedCodes.map((code) => String(code || '').trim()).filter(Boolean))
  const availableMap = new Map(availableFields.map((field) => [field.code, field]))
  const existingMap = new Map(
    (Array.isArray(existingValue) ? existingValue : [])
      .map((item) => {
        const raw = item as AnyRecord
        const code = String(raw?.code || raw?.fieldCode || '').trim()
        return code ? [code, raw] as const : null
      })
      .filter((item): item is readonly [string, AnyRecord] => !!item)
  )

  return selectedCodes
    .map((code) => {
      const normalized = String(code || '').trim()
      if (!normalized || !selectedSet.has(normalized)) return null
      const option = availableMap.get(normalized)
      const existing = existingMap.get(normalized) || {}
      if (!option && !existing) return null

      const componentProps = {
        ...((existing.component_props || {}) as Record<string, unknown>),
        ...((existing.componentProps || {}) as Record<string, unknown>),
        ...(option?.componentProps || {})
      }

      const result: Record<string, unknown> = {
        ...existing,
        code: normalized,
        fieldCode: normalized,
        label: option?.label || String(existing.label || existing.name || normalized),
        name: option?.label || String(existing.name || existing.label || normalized),
        fieldType: option?.fieldType || String(existing.fieldType || existing.field_type || existing.type || 'text'),
        field_type: option?.fieldType || String(existing.field_type || existing.fieldType || existing.type || 'text')
      }

      if (option?.width ?? existing.width) {
        result.width = option?.width ?? existing.width
      }
      if (option?.minWidth ?? existing.minWidth ?? existing.min_width) {
        result.minWidth = option?.minWidth ?? existing.minWidth ?? existing.min_width
      }
      if (option?.align || existing.align) {
        result.align = option?.align || existing.align
      }
      if (option?.fixed || existing.fixed) {
        result.fixed = option?.fixed || existing.fixed
      }
      if (
        option?.ellipsis === true ||
        existing.ellipsis === true ||
        existing.showOverflowTooltip === true ||
        existing.show_overflow_tooltip === true
      ) {
        result.ellipsis = true
        result.showOverflowTooltip = true
        result.show_overflow_tooltip = true
      }
      if (option?.formatter || existing.formatter || existing.displayFormatter) {
        result.formatter = option?.formatter || existing.formatter || existing.displayFormatter
      }
      if (option?.emptyText || existing.emptyText || existing.empty_text) {
        result.emptyText = option?.emptyText || existing.emptyText || existing.empty_text
      }
      if (option?.tooltipTemplate || existing.tooltipTemplate || existing.tooltip_template) {
        result.tooltipTemplate = option?.tooltipTemplate || existing.tooltipTemplate || existing.tooltip_template
      }
      if (option?.readonly ?? existing.readonly ?? existing.isReadonly ?? existing.is_readonly) {
        result.readonly = option?.readonly ?? existing.readonly ?? existing.isReadonly ?? existing.is_readonly
      }
      if (option?.required ?? existing.required ?? existing.isRequired ?? existing.is_required) {
        result.required = option?.required ?? existing.required ?? existing.isRequired ?? existing.is_required
      }
      if (option?.options || existing.options || existing.choices) {
        result.options = option?.options || existing.options || existing.choices
      }
      if (option?.referenceObject || existing.referenceObject || existing.reference_object) {
        result.referenceObject = option?.referenceObject || existing.referenceObject || existing.reference_object
      }
      if (option?.targetObjectCode || existing.targetObjectCode || existing.target_object_code) {
        result.targetObjectCode = option?.targetObjectCode || existing.targetObjectCode || existing.target_object_code
      }
      if (option?.referenceDisplayField || existing.referenceDisplayField || existing.reference_display_field) {
        result.referenceDisplayField =
          option?.referenceDisplayField || existing.referenceDisplayField || existing.reference_display_field
      }
      if (option?.referenceSecondaryField || existing.referenceSecondaryField || existing.reference_secondary_field) {
        result.referenceSecondaryField =
          option?.referenceSecondaryField || existing.referenceSecondaryField || existing.reference_secondary_field
      }
      if (Object.keys(componentProps).length > 0) {
        result.componentProps = componentProps
        result.component_props = componentProps
      }

      return result
    })
    .filter((item): item is Record<string, unknown> => !!item)
}

export const buildLookupColumnConfigs = (
  selectedCodes: string[],
  availableFields: DetailRegionFieldOption[],
  existingValue?: unknown
): Array<Record<string, unknown>> => {
  const availableMap = new Map(availableFields.map((field) => [field.code, field]))
  const existingMap = new Map(
    (Array.isArray(existingValue) ? existingValue : [])
      .map((item) => {
        if (typeof item === 'string') {
          const code = String(item).trim()
          return code ? [code, { key: code }] as const : null
        }
        const raw = item as AnyRecord
        const key = String(raw?.key || '').trim()
        return key ? [key, raw] as const : null
      })
      .filter((item): item is readonly [string, AnyRecord] => !!item)
  )

  return selectedCodes
    .map((code) => {
      const normalized = String(code || '').trim()
      if (!normalized) return null
      const option = availableMap.get(normalized)
      const existing = existingMap.get(normalized) || {}
      const result: Record<string, unknown> = {
        ...existing,
        key: normalized,
        label: option?.label || String(existing.label || normalized),
        width: existing.width || option?.width,
        minWidth: existing.minWidth || existing.min_width || option?.minWidth,
        align: existing.align || option?.align
      }

      if (existing.fixed || option?.fixed) {
        result.fixed = existing.fixed || option?.fixed
      }
      if (
        existing.ellipsis === true ||
        existing.showOverflowTooltip === true ||
        existing.show_overflow_tooltip === true ||
        option?.ellipsis === true
      ) {
        result.ellipsis = true
        result.showOverflowTooltip = true
        result.show_overflow_tooltip = true
      }
      if (existing.formatter || existing.displayFormatter || option?.formatter) {
        result.formatter = existing.formatter || existing.displayFormatter || option?.formatter
      }
      if (existing.emptyText || existing.empty_text || option?.emptyText) {
        result.emptyText = existing.emptyText || existing.empty_text || option?.emptyText
      }
      if (existing.tooltipTemplate || existing.tooltip_template || option?.tooltipTemplate) {
        result.tooltipTemplate = existing.tooltipTemplate || existing.tooltip_template || option?.tooltipTemplate
      }

      return result
    })
    .filter((item): item is Record<string, unknown> => !!item)
}
