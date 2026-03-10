import * as XLSX from 'xlsx'
import i18n from '@/locales'
import type { ExportColumn } from './exportService'

const t = (key: string, params?: Record<string, unknown>) => i18n.global.t(key, params || {}) as string

export interface ImportError {
  row: number
  col: string
  message: string
}

export interface ImportResult<T = any> {
  data: T[]
  errors: ImportError[]
  unknownHeaders: string[]
  missingHeaders: string[]
}

export interface ImportOptions {
  required?: string[]
  sheetIndex?: number
  maxRows?: number
}

export async function parseExcelFile<T = any>(
  file: File,
  columns: ExportColumn[],
  options: ImportOptions = {}
): Promise<ImportResult<T>> {
  const { required = [], sheetIndex = 0, maxRows = 10000 } = options

  const labelToProp = new Map<string, string>(
    columns.map(col => [col.label.trim(), col.prop])
  )

  columns.forEach(col => {
    if (!labelToProp.has(col.prop.trim())) {
      labelToProp.set(col.prop.trim(), col.prop)
    }
  })

  const buffer = await file.arrayBuffer()
  const workbook = XLSX.read(buffer, { type: 'array', cellDates: true })
  const sheetName = workbook.SheetNames[sheetIndex]

  if (!sheetName) {
    return {
      data: [],
      errors: [{ row: 0, col: '', message: t('common.import.invalidSheet') }],
      unknownHeaders: [],
      missingHeaders: []
    }
  }

  const ws = workbook.Sheets[sheetName]
  const rawRows: any[][] = XLSX.utils.sheet_to_json(ws, { header: 1, raw: false, defval: '' })

  if (rawRows.length < 2) {
    return { data: [], errors: [], unknownHeaders: [], missingHeaders: [] }
  }

  const headerRow: string[] = rawRows[0].map((h: any) => String(h ?? '').trim())
  const indexToProp: (string | null)[] = headerRow.map(h => labelToProp.get(h) ?? null)
  const unknownHeaders = headerRow.filter(h => h !== '' && !labelToProp.has(h))

  const missingHeaders = columns
    .filter(c => !headerRow.includes(c.label.trim()))
    .map(c => c.label)

  const requiredProps = new Set(required)
  const data: T[] = []
  const errors: ImportError[] = []

  const dataRows = rawRows.slice(1, 1 + maxRows)
  dataRows.forEach((rawRow, rowIdx) => {
    const rowNum = rowIdx + 1
    const record: any = {}

    indexToProp.forEach((prop, colIdx) => {
      if (!prop) return

      const rawVal = rawRow[colIdx]
      const val = rawVal === null || rawVal === undefined ? '' : String(rawVal).trim()
      record[prop] = val

      if (requiredProps.has(prop) && val === '') {
        const label = headerRow[colIdx] || prop
        errors.push({
          row: rowNum,
          col: label,
          message: t('common.import.requiredCell', { label, row: rowNum + 1 })
        })
      }
    })

    const hasData = columns.some(c => record[c.prop] !== '' && record[c.prop] !== undefined)
    if (hasData) {
      data.push(record as T)
    }
  })

  return { data, errors, unknownHeaders, missingHeaders }
}

export function downloadImportTemplate(
  filename: string,
  columns: ExportColumn[],
  exampleRow?: Record<string, any>
): void {
  const headers = columns.map(col => col.label)
  const sheetData: any[][] = [headers]

  if (exampleRow) {
    sheetData.push(columns.map(col => exampleRow[col.prop] ?? ''))
  }

  const ws = XLSX.utils.aoa_to_sheet(sheetData)
  ws['!cols'] = columns.map(col => ({ wch: Math.max(col.label.length + 4, col.width || 16) }))

  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, t('common.import.templateSheetName'))

  const safeFilename = filename.replace(/[/\\?%*:|"<>]/g, '_')
  XLSX.writeFile(wb, `${safeFilename}_${t('common.import.templateSuffix')}.xlsx`)
}

/**
 * Enhanced column definition for smart import templates
 */
export interface EnhancedColumn extends ExportColumn {
  /** Whether this field is required */
  required?: boolean
  /** Field type for hint generation */
  fieldType?: string
  /** Option labels for select/dictionary fields */
  optionLabels?: string[]
  /** Whether this is a reference field */
  isReference?: boolean
  /** Referenced object display name */
  referenceObjectName?: string
}

/**
 * Download an enhanced import template with:
 * - Required field markers (*) in headers
 * - Hints row with select options / reference prompts
 * - Example data row (optional)
 */
export function downloadEnhancedImportTemplate(
  filename: string,
  columns: EnhancedColumn[],
  exampleRow?: Record<string, any>
): void {
  // Row 1: Headers with required markers
  const headers = columns.map(col => {
    const label = col.label || col.prop
    return col.required ? `${label} *` : label
  })

  // Row 2: Hints row (options / reference prompts)
  const hints = columns.map(col => {
    if (col.optionLabels?.length) {
      return `[${col.optionLabels.join(' | ')}]`
    }
    if (col.isReference) {
      const refName = col.referenceObjectName || ''
      return refName
        ? t('common.import.referenceHint', { name: refName })
        : (i18n.global.t('common.import.referenceHintGeneric') as string || '填写名称，系统自动匹配')
    }
    return ''
  })

  const hasHints = hints.some(h => h !== '')
  const sheetData: any[][] = [headers]

  if (hasHints) {
    sheetData.push(hints)
  }

  if (exampleRow) {
    sheetData.push(columns.map(col => exampleRow[col.prop] ?? ''))
  }

  const ws = XLSX.utils.aoa_to_sheet(sheetData)

  // Auto-size columns
  ws['!cols'] = columns.map((col, idx) => {
    const headerLen = headers[idx].length
    const hintLen = hasHints ? (hints[idx]?.length || 0) : 0
    return { wch: Math.max(headerLen + 2, hintLen + 2, col.width || 16) }
  })

  // Style hints row (lighter color) — xlsx doesn't support styles natively
  // but headers with * are visually distinguished

  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, t('common.import.templateSheetName'))

  const safeFilename = filename.replace(/[/\\?%*:|"<>]/g, '_')
  XLSX.writeFile(wb, `${safeFilename}_${t('common.import.templateSuffix')}.xlsx`)
}
