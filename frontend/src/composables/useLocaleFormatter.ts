/**
 * useLocaleFormatter — Locale-aware formatting for numbers, currency, and dates.
 *
 * Uses Intl.NumberFormat / Intl.DateTimeFormat per the user's browser locale
 * or an explicitly provided locale override.
 *
 * Usage:
 *   const { formatCurrency, formatNumber, formatDate, formatDateTime } = useLocaleFormatter()
 *   formatCurrency(9999.99)          // "$9,999.99" or "¥9,999.99" depending on locale
 *   formatDate('2026-03-10')         // "2026/3/10" in zh-CN, "Mar 10, 2026" in en-US
 */

import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

interface FormatterOptions {
  /** Override locale instead of using vue-i18n locale. */
  locale?: string
  /** ISO 4217 currency code. Default: 'CNY'. */
  currency?: string
}

export function useLocaleFormatter(options: FormatterOptions = {}) {
  const { locale: i18nLocale } = useI18n()

  const effectiveLocale = computed(() => {
    return options.locale || i18nLocale.value || navigator.language || 'zh-CN'
  })

  const currencyCode = computed(() => options.currency || 'CNY')

  // ── Number ────────────────────────────────────────────────────────────

  function formatNumber(value: number | string | null | undefined, decimals?: number): string {
    if (value == null || value === '') return ''
    const num = typeof value === 'string' ? parseFloat(value) : value
    if (isNaN(num)) return String(value)

    return new Intl.NumberFormat(effectiveLocale.value, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals ?? 2
    }).format(num)
  }

  // ── Currency ──────────────────────────────────────────────────────────

  function formatCurrency(value: number | string | null | undefined, overrideCurrency?: string): string {
    if (value == null || value === '') return ''
    const num = typeof value === 'string' ? parseFloat(value) : value
    if (isNaN(num)) return String(value)

    return new Intl.NumberFormat(effectiveLocale.value, {
      style: 'currency',
      currency: overrideCurrency || currencyCode.value,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(num)
  }

  // ── Percentage ────────────────────────────────────────────────────────

  function formatPercent(value: number | string | null | undefined, decimals = 1): string {
    if (value == null || value === '') return ''
    const num = typeof value === 'string' ? parseFloat(value) : value
    if (isNaN(num)) return String(value)

    return new Intl.NumberFormat(effectiveLocale.value, {
      style: 'percent',
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    }).format(num / 100)
  }

  // ── Date ──────────────────────────────────────────────────────────────

  function formatDate(value: string | Date | null | undefined): string {
    if (!value) return ''
    const date = value instanceof Date ? value : new Date(value)
    if (isNaN(date.getTime())) return String(value)

    return new Intl.DateTimeFormat(effectiveLocale.value, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).format(date)
  }

  function formatDateTime(value: string | Date | null | undefined): string {
    if (!value) return ''
    const date = value instanceof Date ? value : new Date(value)
    if (isNaN(date.getTime())) return String(value)

    return new Intl.DateTimeFormat(effectiveLocale.value, {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).format(date)
  }

  function formatRelativeTime(value: string | Date | null | undefined): string {
    if (!value) return ''
    const date = value instanceof Date ? value : new Date(value)
    if (isNaN(date.getTime())) return String(value)

    const diff = Date.now() - date.getTime()
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    const rtf = new Intl.RelativeTimeFormat(effectiveLocale.value, { numeric: 'auto' })

    if (days > 0) return rtf.format(-days, 'day')
    if (hours > 0) return rtf.format(-hours, 'hour')
    if (minutes > 0) return rtf.format(-minutes, 'minute')
    return rtf.format(-seconds, 'second')
  }

  return {
    locale: effectiveLocale,
    formatNumber,
    formatCurrency,
    formatPercent,
    formatDate,
    formatDateTime,
    formatRelativeTime
  }
}
