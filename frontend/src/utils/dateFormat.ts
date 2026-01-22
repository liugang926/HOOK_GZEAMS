/**
 * Date Formatting Utilities
 *
 * Centralized date formatting using dayjs.
 * Reference: docs/plans/2025-01-22-frontend-implementation.md
 */

import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'
import quarterOfYear from 'dayjs/plugin/quarterOfYear'

// Configure dayjs
dayjs.locale('zh-cn')
dayjs.extend(relativeTime)
dayjs.extend(quarterOfYear)

/**
 * Format date to specified format string
 *
 * @param date - The date to format (string, Date, or dayjs object)
 * @param format - The format string (default: YYYY-MM-DD)
 * @returns Formatted date string
 *
 * @example
 * formatDate('2023-01-15') // '2023-01-15'
 * formatDate(new Date(), 'YYYY/MM/DD') // '2023/01/15'
 */
export function formatDate(date: string | Date, format = 'YYYY-MM-DD'): string {
  return dayjs(date).format(format)
}

/**
 * Format date with time
 *
 * @param date - The date to format
 * @returns Formatted datetime string (YYYY-MM-DD HH:mm:ss)
 *
 * @example
 * formatDateTime('2023-01-15T10:30:00') // '2023-01-15 10:30:00'
 */
export function formatDateTime(date: string | Date): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

/**
 * Format date as relative time from now
 *
 * @param date - The date to format
 * @returns Relative time string in Chinese
 *
 * @example
 * formatRelativeTime(dayjs().subtract(5, 'minute')) // '5分钟前'
 * formatRelativeTime(dayjs().subtract(2, 'day')) // '2天前'
 */
export function formatRelativeTime(date: string | Date): string {
  return dayjs(date).fromNow()
}

/**
 * Format date as month (YYYY-MM)
 *
 * @param date - The date to format
 * @returns Month string
 *
 * @example
 * formatMonth('2023-01-15') // '2023-01'
 */
export function formatMonth(date: string | Date): string {
  return dayjs(date).format('YYYY-MM')
}

/**
 * Get current month string
 *
 * @returns Current month in YYYY-MM format
 */
export function getCurrentMonth(): string {
  return dayjs().format('YYYY-MM')
}

/**
 * Get current date string
 *
 * @returns Current date in YYYY-MM-DD format
 */
export function getCurrentDate(): string {
  return dayjs().format('YYYY-MM-DD')
}

/**
 * Get current datetime string
 *
 * @returns Current datetime in YYYY-MM-DD HH:mm:ss format
 */
export function getCurrentDateTime(): string {
  return dayjs().format('YYYY-MM-DD HH:mm:ss')
}

/**
 * Format date as quarter
 *
 * @param date - The date to format
 * @returns Quarter string (e.g., 2023-Q1)
 */
export function formatQuarter(date: string | Date): string {
  const d = dayjs(date)
  const quarter = d.quarter()
  return `${d.year()}-Q${quarter}`
}

/**
 * Get start of month
 *
 * @param date - The reference date
 * @returns Start of month date string
 */
export function startOfMonth(date: string | Date): string {
  return dayjs(date).startOf('month').format('YYYY-MM-DD')
}

/**
 * Get end of month
 *
 * @param date - The reference date
 * @returns End of month date string
 */
export function endOfMonth(date: string | Date): string {
  return dayjs(date).endOf('month').format('YYYY-MM-DD')
}

/**
 * Calculate date difference in days
 *
 * @param date1 - First date
 * @param date2 - Second date
 * @returns Difference in days
 */
export function diffDays(date1: string | Date, date2: string | Date): number {
  return dayjs(date1).diff(dayjs(date2), 'day')
}

/**
 * Add days to date
 *
 * @param date - The base date
 * @param days - Number of days to add (can be negative)
 * @returns New date string
 */
export function addDays(date: string | Date, days: number): string {
  return dayjs(date).add(days, 'day').format('YYYY-MM-DD')
}

/**
 * Check if date is valid
 *
 * @param date - The date to check
 * @returns True if valid, false otherwise
 */
export function isValidDate(date: string | Date): boolean {
  return dayjs(date).isValid()
}
