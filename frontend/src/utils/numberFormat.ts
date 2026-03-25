/**
 * Number Formatting Utilities
 *
 * Centralized number formatting for currency, percentages, and file sizes.
 * Reference: docs/plans/2025-01-22-frontend-implementation.md
 */

import i18n from '@/locales'

const DEFAULT_LOCALE = 'en-US'

function getCurrentLocale(): string {
  const locale = i18n.global.locale as unknown
  if (typeof locale === 'string' && locale) return locale
  if (locale && typeof locale === 'object' && 'value' in (locale as Record<string, unknown>)) {
    const value = (locale as { value?: string }).value
    if (value) return value
  }
  return DEFAULT_LOCALE
}

/**
 * Format number as money/currency with current locale
 */
export function formatMoney(amount: number, decimals = 2): string {
  if (isNaN(amount)) return '0.00'
  return Number(amount).toLocaleString(getCurrentLocale(), {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

/**
 * Format number with thousands separator
 */
export function formatNumber(num: number, decimals = 0): string {
  if (isNaN(num)) return '0'
  return Number(num).toLocaleString(getCurrentLocale(), {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })
}

/**
 * Format decimal as percentage
 */
export function formatPercent(value: number, decimals = 2): string {
  if (isNaN(value)) return '0.00%'
  return (value * 100).toFixed(decimals) + '%'
}

/**
 * Format bytes as file size
 */
export function formatFileSize(bytes: number): string {
  if (isNaN(bytes) || bytes < 0) return '0 B'

  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

/**
 * Format number with locale compact notation (e.g. 1.2K / 1.2万)
 */
export function formatWithUnit(num: number, decimals = 2): string {
  if (isNaN(num)) return '0'

  return new Intl.NumberFormat(getCurrentLocale(), {
    notation: 'compact',
    compactDisplay: 'short',
    maximumFractionDigits: decimals
  }).format(num)
}

/**
 * Parse money string to number
 */
export function parseMoney(str: string): number {
  if (!str) return 0
  const cleaned = str.replace(/[^\d.-]/g, '')
  const parsed = parseFloat(cleaned)
  return isNaN(parsed) ? 0 : parsed
}

/**
 * Round number to specified decimals
 */
export function roundTo(num: number, decimals = 2): number {
  const multiplier = Math.pow(10, decimals)
  return Math.round(num * multiplier) / multiplier
}
