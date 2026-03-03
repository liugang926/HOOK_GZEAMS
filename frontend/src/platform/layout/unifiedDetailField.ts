import { normalizeFieldType } from '@/utils/fieldType'
import i18n from '@/locales'

export type UnifiedDetailField = {
  prop: string
  label: string
  editorType?: string
  type?:
    | 'text'
    | 'date'
    | 'datetime'
    | 'time'
    | 'daterange'
    | 'year'
    | 'month'
    | 'number'
    | 'currency'
    | 'percent'
    | 'boolean'
    | 'switch'
    | 'checkbox'
    | 'tag'
    | 'slot'
    | 'link'
    | 'image'
    | 'qr_code'
    | 'barcode'
    | 'color'
    | 'rate'
    | 'file'
    | 'attachment'
    | 'rich_text'
    | 'sub_table'
    | 'json'
    | 'object'
  options?: { label: string; value: any; color?: string }[]
  dateFormat?: string
  precision?: number
  currency?: string
  tagType?: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'>
  defaultTagType?: 'success' | 'warning' | 'danger' | 'info' | 'primary'
  span?: number
  href?: string
  hidden?: boolean
  labelClass?: string
  valueClass?: string
}

const AUDIT_FIELD_CODES = new Set([
  'created_at',
  'created_by',
  'updated_at',
  'updated_by',
  'createdAt',
  'createdBy',
  'updatedAt',
  'updatedBy'
])

export function isAuditFieldCode(code: string): boolean {
  return AUDIT_FIELD_CODES.has(String(code || '').trim())
}

export function normalizeDetailSpan(rawSpan: any, rawColumns: any): number {
  const columns = Number(rawColumns) || 2
  const span = Number(rawSpan)

  if (!Number.isFinite(span) || span <= 0) return Math.max(1, Math.round(24 / columns))
  if (span <= columns) return Math.max(1, Math.min(24, Math.round((24 / columns) * span)))
  if (span <= 24) return Math.max(1, Math.min(24, Math.round(span)))
  return 24
}

export function toUnifiedDetailField(field: Record<string, any>): UnifiedDetailField {
  const code = String(field.code || field.fieldCode || '').trim()
  const rawType = field.fieldType || field.field_type || field.type || 'text'
  const normalizedType = normalizeFieldType(rawType)
  const options = field.options || []

  const detailField: UnifiedDetailField = {
    prop: code,
    label: field.label || field.name || code,
    editorType: normalizedType,
    span: field.span || 12,
    options
  }

  if (
    normalizedType === 'date' ||
    normalizedType === 'datetime' ||
    normalizedType === 'time' ||
    normalizedType === 'year' ||
    normalizedType === 'month'
  ) {
    detailField.type = normalizedType as UnifiedDetailField['type']
    if (normalizedType === 'date') detailField.dateFormat = field.dateFormat || 'YYYY-MM-DD'
    if (normalizedType === 'datetime') detailField.dateFormat = field.dateFormat || 'YYYY-MM-DD HH:mm:ss'
    if (normalizedType === 'time') detailField.dateFormat = field.dateFormat || 'HH:mm:ss'
    if (normalizedType === 'year') detailField.dateFormat = field.dateFormat || 'YYYY'
    if (normalizedType === 'month') detailField.dateFormat = field.dateFormat || 'YYYY-MM'
  } else if (normalizedType === 'daterange') {
    detailField.type = 'daterange'
    detailField.dateFormat = field.dateFormat || 'YYYY-MM-DD'
  } else if (normalizedType === 'number' || normalizedType === 'currency') {
    detailField.type = normalizedType === 'currency' ? 'currency' : 'number'
    detailField.precision = field.precision ?? field.decimalPlaces ?? field.decimal_places ?? 2
    detailField.currency = field.currencySymbol || field.currency || undefined
  } else if (normalizedType === 'percent') {
    detailField.type = 'percent'
    detailField.precision = field.precision ?? field.decimalPlaces ?? field.decimal_places ?? 2
  } else if (normalizedType === 'boolean' || normalizedType === 'switch' || normalizedType === 'checkbox') {
    detailField.type = normalizedType as UnifiedDetailField['type']
  } else if (normalizedType === 'color' || normalizedType === 'rate') {
    detailField.type = normalizedType as UnifiedDetailField['type']
  } else if (normalizedType === 'url') {
    detailField.type = 'link'
    detailField.href = '{value}'
  } else if (normalizedType === 'email') {
    detailField.type = 'link'
    detailField.href = 'mailto:{value}'
  } else if (normalizedType === 'phone') {
    detailField.type = 'link'
    detailField.href = 'tel:{value}'
  } else if (normalizedType === 'rich_text') {
    detailField.type = 'rich_text'
    detailField.span = 24
  } else if (normalizedType === 'sub_table') {
    detailField.type = 'sub_table'
    detailField.span = 24
  } else if (normalizedType === 'json' || normalizedType === 'object') {
    detailField.type = normalizedType as UnifiedDetailField['type']
    detailField.span = 24
  } else if (normalizedType === 'image') {
    detailField.type = 'image'
    detailField.span = 24
  } else if (normalizedType === 'qr_code' || normalizedType === 'barcode') {
    detailField.type = normalizedType as UnifiedDetailField['type']
  } else if (normalizedType === 'file' || normalizedType === 'attachment') {
    detailField.type = normalizedType as UnifiedDetailField['type']
    detailField.span = 24
  } else {
    detailField.type = 'text'
  }

  const shouldTag =
    normalizedType === 'status' ||
    normalizedType === 'enum' ||
    code === 'status' ||
    !!field.tagTypeMapping ||
    options.some((opt: any) => opt?.color)

  if (shouldTag) {
    detailField.type = 'tag'
    detailField.tagType = field.tagTypeMapping as Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'>
    detailField.defaultTagType = (field.defaultTagType as any) || 'info'
  }

  return detailField
}

export function buildRequiredFormRules(fields: Array<Record<string, any>>): Record<string, any> {
  const rules: Record<string, any> = {}
  for (const field of fields || []) {
    const required = field.is_required || field.isRequired || field.required
    if (!required) continue
    const code = String(field.code || field.fieldCode || '').trim()
    if (!code) continue
    const label = field.label || field.name || code
    rules[code] = [
      {
        required: true,
        message: i18n.global.t('common.validation.requiredWithField', { field: label }),
        trigger: ['blur', 'change']
      }
    ]
  }
  return rules
}
