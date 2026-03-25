/**
 * exportService.ts
 *
 * Generic, label-aware Excel / CSV export engine.
 *
 * Key design:
 *  - ExportColumn.label  → written as the Excel header (human-readable, typically from i18n)
 *  - ExportColumn.prop   → used to read the value from each data row
 *  - ExportColumn.format → optional value formatter (e.g. status codes → translated labels)
 *
 * Usage:
 *   exportToExcel('资产列表', columns, rows)
 *   exportToCSV('资产列表', columns, rows)
 *   // For large datasets, supply a fetchAll to avoid manual pagination:
 *   await exportAllPages('资产列表', columns, myApi, { status: 'active' })
 */

import i18n from '@/locales'
import { loadXlsx } from '@/utils/xlsxLoader'

// ─── Types ────────────────────────────────────────────────────────────────────

export interface ExportColumn {
    /** Human-readable column header written to the Excel/CSV file */
    label: string
    /** Property key read from each data row */
    prop: string
    /** Optional value transformer (receive raw value and full row) */
    format?: (value: any, row: any) => string | number
    /** Column width in characters (Excel only) */
    width?: number
}

export interface ExportOptions {
    /** Sheet name shown in Excel (default: 'Sheet1') */
    sheetName?: string
    /** Whether to auto-fit column widths based on content (default: true) */
    autoFit?: boolean
}

// ─── Core helpers ─────────────────────────────────────────────────────────────

/**
 * Resolve a (possibly nested) prop from a row object.
 * Supports dot notation: "asset.name"
 */
function resolveProp(row: any, prop: string): any {
    if (!row || !prop) return undefined
    const parts = prop.split('.')
    return parts.reduce((acc: any, key: string) => (acc != null ? acc[key] : undefined), row)
}

/**
 * Format a single cell value using the column definition.
 * Falls back to empty string for null/undefined.
 */
function formatCell(value: any, row: any, col: ExportColumn): string | number {
    if (col.format) return col.format(value, row)
    if (value === null || value === undefined) return ''
    if (typeof value === 'boolean') {
        return value
            ? (i18n.global.t('common.units.yes') as string)
            : (i18n.global.t('common.units.no') as string)
    }
    if (Array.isArray(value)) return value.join(', ')
    if (typeof value === 'object') {
        // Try common display fields
        return value.name || value.label || value.title || value.display_name || JSON.stringify(value)
    }
    return value
}

/**
 * Build a 2D array (header + rows) from column definitions and data.
 * This is the core transformation where label → header, prop → data.
 */
export function buildSheetData(columns: ExportColumn[], data: any[]): (string | number)[][] {
    // Row 0: headers (human-readable labels)
    const headers = columns.map(col => col.label)

    // Rows 1+: data
    const rows = data.map(row =>
        columns.map(col => formatCell(resolveProp(row, col.prop), row, col))
    )

    return [headers, ...rows]
}

// ─── Excel export ─────────────────────────────────────────────────────────────

/**
 * Export data to an .xlsx file and trigger browser download.
 *
 * Column headers are taken from ExportColumn.label (i18n text, not raw prop keys).
 */
export async function exportToExcel(
    filename: string,
    columns: ExportColumn[],
    data: any[],
    options: ExportOptions = {}
): Promise<void> {
    const { sheetName = 'Sheet1', autoFit = true } = options

    const XLSX = await loadXlsx()
    const sheetData = buildSheetData(columns, data)
    const ws = XLSX.utils.aoa_to_sheet(sheetData)

    // Style the header row (bold) — sheetjs-style / ExcelJS would be richer; xlsx CE supports basic cell props
    // Set column widths
    if (autoFit) {
        ws['!cols'] = columns.map((col, _colIdx) => {
            const headerLen = col.label.length
            const maxDataLen = data.reduce((max, row) => {
                const val = formatCell(resolveProp(row, col.prop), row, col)
                const len = String(val).length
                return Math.max(max, len)
            }, 0)
            const wch = Math.min(Math.max(headerLen, maxDataLen) + 2, col.width || 40)
            return { wch }
        })
    }

    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, sheetName)

    // Trigger download
    const safeFilename = filename.replace(/[/\\?%*:|"<>]/g, '_')
    XLSX.writeFile(wb, `${safeFilename}.xlsx`)
}

// ─── CSV export ───────────────────────────────────────────────────────────────

/**
 * Export data to a .csv file and trigger browser download.
 * Useful when the user only has Excel-lite environments.
 */
export async function exportToCSV(
    filename: string,
    columns: ExportColumn[],
    data: any[]
): Promise<void> {
    const XLSX = await loadXlsx()
    const sheetData = buildSheetData(columns, data)
    const ws = XLSX.utils.aoa_to_sheet(sheetData)
    const csv = XLSX.utils.sheet_to_csv(ws)

    // Add UTF-8 BOM so Excel opens Chinese text correctly
    const bom = '\uFEFF'
    const blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${filename}.csv`
    link.click()
    URL.revokeObjectURL(url)
}

// ─── Paginated fetch + export ─────────────────────────────────────────────────

/**
 * Fetch ALL pages from an API function and export to Excel.
 * This handles the common pattern where one page ≠ all records.
 *
 * @param api       Function matching (params) => Promise<{ results, count }>
 * @param baseParams Any additional filter params (status, date range, etc.)
 */
export async function exportAllPages(
    filename: string,
    columns: ExportColumn[],
    api: (params: any) => Promise<any>,
    baseParams: any = {},
    options: ExportOptions = {}
): Promise<void> {
    const PAGE_SIZE = 200
    const page = 1
    let allData: any[] = []

    // First page to get total count
    const first = await api({ ...baseParams, page, page_size: PAGE_SIZE, pageSize: PAGE_SIZE })
    const results0: any[] = first?.results ?? first?.data?.results ?? (Array.isArray(first) ? first : [])
    const total: number = first?.count ?? first?.data?.count ?? results0.length
    allData = [...results0]

    // Fetch remaining pages
    const totalPages = Math.ceil(total / PAGE_SIZE)
    const pagePromises = []
    for (let p = 2; p <= totalPages; p++) {
        pagePromises.push(
            api({ ...baseParams, page: p, page_size: PAGE_SIZE, pageSize: PAGE_SIZE })
                .then((res: any) => res?.results ?? res?.data?.results ?? [])
        )
    }
    const rest = await Promise.all(pagePromises)
    allData = [...allData, ...rest.flat()]

    await exportToExcel(filename, columns, allData, options)
}
