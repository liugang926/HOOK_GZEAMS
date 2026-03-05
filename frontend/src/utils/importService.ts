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
