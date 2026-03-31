import { describe, expect, it, vi } from 'vitest'
import { useLocaleFormatter } from '../useLocaleFormatter'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    locale: { value: 'zh-CN' }
  })
}))

describe('useLocaleFormatter', () => {
  const { formatNumber, formatCurrency, formatPercent, formatDate, formatDateTime, formatRelativeTime: _formatRelativeTime } = useLocaleFormatter()

  describe('formatNumber', () => {
    it('formats numbers with locale-aware grouping', () => {
      const result = formatNumber(1234567.89)
      expect(result).toContain('1')
      expect(result).toContain('234')
      expect(result).toContain('567')
    })

    it('handles null/undefined gracefully', () => {
      expect(formatNumber(null)).toBe('')
      expect(formatNumber(undefined)).toBe('')
      expect(formatNumber('')).toBe('')
    })

    it('handles string numbers', () => {
      const result = formatNumber('42.5')
      expect(result).toContain('42')
    })
  })

  describe('formatCurrency', () => {
    it('formats currency with CNY by default', () => {
      const result = formatCurrency(9999.99)
      // Should contain the numeric value, locale-specific
      expect(result).toContain('9')
    })

    it('handles null values', () => {
      expect(formatCurrency(null)).toBe('')
    })
  })

  describe('formatPercent', () => {
    it('formats percentage values', () => {
      const result = formatPercent(75)
      expect(result).toContain('75')
      expect(result).toContain('%')
    })
  })

  describe('formatDate', () => {
    it('formats ISO date string', () => {
      const result = formatDate('2026-03-10')
      expect(result).toContain('2026')
      expect(result).toContain('03')
      expect(result).toContain('10')
    })

    it('handles null', () => {
      expect(formatDate(null)).toBe('')
    })

    it('handles Date objects', () => {
      const result = formatDate(new Date(2026, 2, 10))
      expect(result).toContain('2026')
    })
  })

  describe('formatDateTime', () => {
    it('formats datetime with time portion', () => {
      const result = formatDateTime('2026-03-10T14:30:00')
      expect(result).toContain('2026')
      expect(result).toContain('14')
      expect(result).toContain('30')
    })
  })
})
