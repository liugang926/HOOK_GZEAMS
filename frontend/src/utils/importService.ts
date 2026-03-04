/**
 * importService.ts
 *
 * Generic, label-aware Excel import parser.
 *
 * Key design:
 *  - Reads the first row of the Excel sheet as column headers
 *  - Maps header text → prop key using the same ExportColumn[] definition
 *    (the same column config shared with the export)
 *  - Returns typed rows and a list of validation errors
 *
 * Usage:
 *   const { data, errors } = await parseExcelFile(file, columns, { required: ['assetName'] })
 *   // data[0].assetName is the value, not "资产名称"
 */

import * as XLSX from 'xlsx'
import type { ExportColumn } from './exportService'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ImportError {
    row: number       // 1-indexed data row (row 1 = first data row, after header)
    col: string       // column label
    message: string
}

export interface ImportResult<T = any> {
    data: T[]
    errors: ImportError[]
    /** Columns that were present in the file but not in the column config */
    unknownHeaders: string[]
    /** Columns defined in config but missing from the file */
    missingHeaders: string[]
}

export interface ImportOptions {
    /** Column props that must have a non-empty value */
    required?: string[]
    /** Sheet index to read (default: 0, first sheet) */
    sheetIndex?: number
    /** Maximum number of rows to parse (safety guard) */
    maxRows?: number
}

// ─── Core parser ─────────────────────────────────────────────────────────────

/**
 * Parse an Excel (.xlsx / .xls) or CSV file.
 *
 * Column headers in the file should match ExportColumn.label values
 * (i.e. the same human-readable labels shown in the export).
 *
 * Returns { data, errors, unknownHeaders, missingHeaders }.
 */
export async function parseExcelFile<T = any>(
    file: File,
    columns: ExportColumn[],
    options: ImportOptions = {}
): Promise<ImportResult<T>> {
    const { required = [], sheetIndex = 0, maxRows = 10000 } = options

    // Build label → prop lookup map
    const labelToProp = new Map<string, string>(
        columns.map(col => [col.label.trim(), col.prop])
    )
    // Also allow prop as fallback (in case a file uses prop keys directly)
    columns.forEach(col => {
        if (!labelToProp.has(col.prop.trim())) {
            labelToProp.set(col.prop.trim(), col.prop)
        }
    })

    // Read file as ArrayBuffer
    const buffer = await file.arrayBuffer()
    const workbook = XLSX.read(buffer, { type: 'array', cellDates: true })
    const sheetName = workbook.SheetNames[sheetIndex]
    if (!sheetName) {
        return { data: [], errors: [{ row: 0, col: '', message: '文件不包含有效工作表' }], unknownHeaders: [], missingHeaders: [] }
    }

    const ws = workbook.Sheets[sheetName]
    // Parse as rows: first row is header
    const rawRows: any[][] = XLSX.utils.sheet_to_json(ws, { header: 1, raw: false, defval: '' })

    if (rawRows.length < 2) {
        return { data: [], errors: [], unknownHeaders: [], missingHeaders: [] }
    }

    const headerRow: string[] = rawRows[0].map((h: any) => String(h ?? '').trim())

    // Map header index → prop key
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
        const rowNum = rowIdx + 1 // 1-indexed data row
        const record: any = {}

        indexToProp.forEach((prop, colIdx) => {
            if (!prop) return
            const rawVal = rawRow[colIdx]
            const val = rawVal === null || rawVal === undefined ? '' : String(rawVal).trim()
            record[prop] = val

            // Required validation
            if (requiredProps.has(prop) && val === '') {
                const label = headerRow[colIdx] || prop
                errors.push({ row: rowNum, col: label, message: `"${label}" 不能为空（第 ${rowNum + 1} 行）` })
            }
        })

        // Only include row if it has at least one non-empty configured field
        const hasData = columns.some(c => record[c.prop] !== '' && record[c.prop] !== undefined)
        if (hasData) {
            data.push(record as T)
        }
    })

    return { data, errors, unknownHeaders, missingHeaders }
}

// ─── Template generator ───────────────────────────────────────────────────────

/**
 * Generate and download an empty import template Excel file.
 * The template has the correct column headers (i18n labels) and
 * optional example data in row 2.
 */
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
    XLSX.utils.book_append_sheet(wb, ws, '导入模板')

    const safeFilename = filename.replace(/[/\\?%*:|"<>]/g, '_')
    XLSX.writeFile(wb, `${safeFilename}_导入模板.xlsx`)
}
