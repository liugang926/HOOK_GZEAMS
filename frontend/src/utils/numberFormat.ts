/**
 * Number Formatting Utilities
 *
 * Centralized number formatting for currency, percentages, and file sizes.
 * Reference: docs/plans/2025-01-22-frontend-implementation.md
 */

/**
 * Format number as money/currency with Chinese locale
 *
 * @param amount - The number to format
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted currency string
 *
 * @example
 * formatMoney(1234.56) // '1,234.56'
 * formatMoney(1234.56, 0) // '1,235'
 * formatMoney(0) // '0.00'
 */
export function formatMoney(amount: number, decimals = 2): string {
  if (isNaN(amount)) return '0.00'
  return Number(amount).toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

/**
 * Format number with thousands separator
 *
 * @param num - The number to format
 * @param decimals - Number of decimal places (default: 0)
 * @returns Formatted number string
 *
 * @example
 * formatNumber(1234567) // '1,234,567'
 * formatNumber(1234.56, 2) // '1,234.56'
 */
export function formatNumber(num: number, decimals = 0): string {
  if (isNaN(num)) return '0'
  return Number(num).toLocaleString('zh-CN', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

/**
 * Format decimal as percentage
 *
 * @param value - The decimal value (e.g., 0.123 for 12.3%)
 * @param decimals - Number of decimal places (default: 2)
 * @returns Percentage string
 *
 * @example
 * formatPercent(0.1234) // '12.34%'
 * formatPercent(0.5) // '50.00%'
 * formatPercent(1) // '100.00%'
 */
export function formatPercent(value: number, decimals = 2): string {
  if (isNaN(value)) return '0.00%'
  return (value * 100).toFixed(decimals) + '%'
}

/**
 * Format bytes as file size
 *
 * @param bytes - The number of bytes
 * @returns Formatted file size string
 *
 * @example
 * formatFileSize(100) // '100 B'
 * formatFileSize(1024) // '1.0 KB'
 * formatFileSize(1048576) // '1.0 MB'
 * formatFileSize(1073741824) // '1024.0 MB'
 */
export function formatFileSize(bytes: number): string {
  if (isNaN(bytes) || bytes < 0) return '0 B'

  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

/**
 * Format number with unit (万, 亿)
 *
 * @param num - The number to format
 * @param decimals - Number of decimal places (default: 2)
 * @returns Formatted number with Chinese unit
 *
 * @example
 * formatWithUnit(12345) // '1.23万'
 * formatWithUnit(123456789) // '1.23亿'
 */
export function formatWithUnit(num: number, decimals = 2): string {
  if (isNaN(num)) return '0'

  if (Math.abs(num) >= 100000000) {
    return `${(num / 100000000).toFixed(decimals)}亿`
  }
  if (Math.abs(num) >= 10000) {
    return `${(num / 10000).toFixed(decimals)}万`
  }
  return formatNumber(num, decimals)
}

/**
 * Parse money string to number
 *
 * @param str - The money string to parse
 * @returns Parsed number
 *
 * @example
 * parseMoney('1,234.56') // 1234.56
 * parseMoney('¥1,234.56') // 1234.56
 */
export function parseMoney(str: string): number {
  if (!str) return 0
  // Remove currency symbol and commas, then parse
  const cleaned = str.replace(/[¥$,\s]/g, '')
  const parsed = parseFloat(cleaned)
  return isNaN(parsed) ? 0 : parsed
}

/**
 * Round number to specified decimals
 *
 * @param num - The number to round
 * @param decimals - Number of decimal places
 * @returns Rounded number
 *
 * @example
 * roundTo(1.236, 2) // 1.24
 * roundTo(1.234, 2) // 1.23
 */
export function roundTo(num: number, decimals = 2): number {
  const multiplier = Math.pow(10, decimals)
  return Math.round(num * multiplier) / multiplier
}
