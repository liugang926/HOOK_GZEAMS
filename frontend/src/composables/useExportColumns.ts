/**
 * useExportColumns — Generates type-aware ExportColumn[] from field metadata.
 *
 * Each column gets a `format` callback that resolves values to human-readable text:
 *   - Reference fields → display name (not raw ID)
 *   - Dictionary/Select → option label (not code)
 *   - Date/DateTime    → locale-formatted string
 *   - Currency         → locale-formatted with symbol
 *   - Boolean          → localized Yes/No
 *   - Multi-select     → comma-joined labels
 *
 * Usage:
 *   const { buildExportColumns, buildExportableFields } = useExportColumns(fieldSource)
 */

import { computed, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { ExportColumn } from '@/utils/exportService'
import { normalizeFieldType, resolveFieldType } from '@/utils/fieldType'
import { filterSystemFields } from '@/utils/transform'
import {
  isReferenceLikeFieldType,
  resolveReferenceLabel,
  resolveReferenceDisplayField,
} from '@/platform/reference/referenceFieldMeta'
import { resolveListFieldValue } from '@/utils/listFieldValue'

// ── Types ──────────────────────────────────────────────────────────────────────

interface FieldMeta {
  code: string
  name?: string
  label?: string
  fieldCode?: string
  field_code?: string
  fieldType?: string
  field_type?: string
  type?: string
  options?: Array<{ label: string; value: any; color?: string }>
  choices?: Array<{ label: string; value: any }>
  isRequired?: boolean
  is_required?: boolean
  referenceObject?: string
  reference_object?: string
  targetObjectCode?: string
  target_object_code?: string
  referenceDisplayField?: string
  reference_display_field?: string
  referenceSecondaryField?: string
  reference_secondary_field?: string
  [key: string]: any
}

export interface ExportableField {
  code: string
  label: string
  fieldType: string
  isRequired: boolean
}

// ── Formatters ─────────────────────────────────────────────────────────────────

function buildOptionsLookup(field: FieldMeta): Map<any, string> | null {
  const options = field?.options || field?.choices || []
  if (!options.length) return null
  const map = new Map<any, string>()
  for (const opt of options) {
    if (opt.value !== undefined && opt.value !== null) {
      map.set(opt.value, opt.label || String(opt.value))
      // Also handle string coercion (API may return "1" vs 1)
      map.set(String(opt.value), opt.label || String(opt.value))
    }
  }
  return map.size > 0 ? map : null
}

function createReferenceFormatter(field: FieldMeta): ExportColumn['format'] {
  const displayField = resolveReferenceDisplayField(field)
  const fieldCode = String(field.code || field.fieldCode || field.field_code || '').trim()
  const fieldType = resolveFieldType(field)

  return (_value: any, row: any) => {
    // Use the full list field value resolver (handles display aliases)
    const resolved = resolveListFieldValue(row, {
      fieldCode,
      fieldType,
      referenceObject: field.referenceObject || field.reference_object || field.targetObjectCode || field.target_object_code,
      referenceDisplayField: field.referenceDisplayField || field.reference_display_field,
    })
    // Extract label from the resolved reference
    return resolveReferenceLabel(resolved, displayField) || ''
  }
}

function createSelectFormatter(field: FieldMeta): ExportColumn['format'] {
  const lookup = buildOptionsLookup(field)
  if (!lookup) return undefined

  return (value: any) => {
    if (value === null || value === undefined || value === '') return ''
    // Multi-select arrays
    if (Array.isArray(value)) {
      return value
        .map(v => lookup.get(v) ?? lookup.get(String(v)) ?? String(v))
        .join(', ')
    }
    return lookup.get(value) ?? lookup.get(String(value)) ?? String(value)
  }
}

function createDateFormatter(locale: string): ExportColumn['format'] {
  return (value: any) => {
    if (!value) return ''
    const date = value instanceof Date ? value : new Date(value)
    if (isNaN(date.getTime())) return String(value)
    return new Intl.DateTimeFormat(locale, {
      year: 'numeric', month: '2-digit', day: '2-digit'
    }).format(date)
  }
}

function createDateTimeFormatter(locale: string): ExportColumn['format'] {
  return (value: any) => {
    if (!value) return ''
    const date = value instanceof Date ? value : new Date(value)
    if (isNaN(date.getTime())) return String(value)
    return new Intl.DateTimeFormat(locale, {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false
    }).format(date)
  }
}

function createCurrencyFormatter(locale: string, currency = 'CNY'): ExportColumn['format'] {
  return (value: any) => {
    if (value === null || value === undefined || value === '') return ''
    const num = typeof value === 'string' ? parseFloat(value) : value
    if (typeof num !== 'number' || isNaN(num)) return String(value)
    return new Intl.NumberFormat(locale, {
      style: 'currency', currency,
      minimumFractionDigits: 2, maximumFractionDigits: 2
    }).format(num)
  }
}

function createBooleanFormatter(tYes: string, tNo: string): ExportColumn['format'] {
  return (value: any) => {
    if (value === null || value === undefined || value === '') return ''
    return value ? tYes : tNo
  }
}

// ── Composable ─────────────────────────────────────────────────────────────────

export function useExportColumns(fieldSource: Ref<any[]>) {
  const { locale, t } = useI18n()

  const effectiveLocale = computed(() => locale.value || 'zh-CN')

  /** All exportable (non-system) fields with metadata */
  const exportableFields = computed<ExportableField[]>(() => {
    return filterSystemFields(fieldSource.value || [])
      .map((field: any) => ({
        code: String(field?.code || field?.fieldCode || field?.field_code || '').trim(),
        label: String(field?.name || field?.label || field?.code || ''),
        fieldType: resolveFieldType(field),
        isRequired: !!(field?.isRequired || field?.is_required)
      }))
      .filter(f => f.code && f.label)
  })

  /** Build smart ExportColumn[] from all or selected field codes */
  function buildExportColumns(fieldCodes?: string[]): ExportColumn[] {
    const fields = filterSystemFields(fieldSource.value || []) as FieldMeta[]
    const codeSet = fieldCodes ? new Set(fieldCodes) : null

    const loc = effectiveLocale.value
    const tYes = t('common.units.yes', '是')
    const tNo = t('common.units.no', '否')

    return fields
      .filter(f => {
        const code = String(f?.code || f?.fieldCode || f?.field_code || '').trim()
        return code && (!codeSet || codeSet.has(code))
      })
      .map(field => {
        const code = String(field.code || field.fieldCode || field.field_code || '').trim()
        const label = String(field.name || field.label || code)
        const fieldType = normalizeFieldType(resolveFieldType(field))

        let format: ExportColumn['format'] = undefined

        // Reference fields → resolve display name
        if (isReferenceLikeFieldType(fieldType) ||
            field.referenceObject || field.reference_object ||
            field.targetObjectCode || field.target_object_code) {
          format = createReferenceFormatter(field)
        }
        // Select / dictionary → option label
        else if (['select', 'dictionary', 'tag', 'radio'].includes(fieldType)) {
          format = createSelectFormatter(field)
        }
        // Multi-select → comma-joined labels
        else if (fieldType === 'multi_select') {
          format = createSelectFormatter(field) // handles arrays
        }
        // Date fields
        else if (fieldType === 'date' || fieldType === 'daterange') {
          format = createDateFormatter(loc)
        }
        // DateTime fields
        else if (fieldType === 'datetime') {
          format = createDateTimeFormatter(loc)
        }
        // Currency fields
        else if (fieldType === 'currency') {
          format = createCurrencyFormatter(loc)
        }
        // Boolean fields
        else if (fieldType === 'boolean' || fieldType === 'switch') {
          format = createBooleanFormatter(tYes, tNo)
        }

        return { label, prop: code, width: 20, format }
      })
  }

  /** Default columns: all business fields with smart formatting */
  const defaultExportColumns = computed<ExportColumn[]>(() => buildExportColumns())

  /** Required field codes (for import validation) */
  const requiredFieldCodes = computed<string[]>(() => {
    return exportableFields.value
      .filter(f => f.isRequired)
      .map(f => f.code)
  })

  return {
    exportableFields,
    defaultExportColumns,
    requiredFieldCodes,
    buildExportColumns
  }
}
