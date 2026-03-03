import type { SearchField } from '@/types/common'
import i18n from '@/locales'
import { resolveFieldType } from '@/utils/fieldType'
import { isFieldSupportedInMode } from '@/platform/layout/fieldCapabilityMatrix'

type AnyRecord = Record<string, unknown>

const SEARCH_SELECT_TYPES = new Set(['select', 'multi_select', 'radio'])
const SEARCH_BOOLEAN_TYPES = new Set(['boolean', 'checkbox', 'switch'])
const SEARCH_DATE_TYPES = new Set(['date', 'datetime', 'time', 'month', 'year'])

function toSearchType(rawType: string): SearchField['type'] {
  if (SEARCH_SELECT_TYPES.has(rawType)) return 'select'
  if (SEARCH_BOOLEAN_TYPES.has(rawType)) return 'boolean'
  if (SEARCH_DATE_TYPES.has(rawType)) return 'date'
  return 'text'
}

export function buildSearchFields(fields: AnyRecord[]): SearchField[] {
  if (!Array.isArray(fields) || fields.length === 0) return []

  return fields
    .filter((field) => Boolean(field?.isSearchable || field?.is_searchable))
    .filter((field) => {
      const fieldType = resolveFieldType(field, 'text')
      return isFieldSupportedInMode(fieldType, 'search')
    })
    .map((field) => {
      const fieldType = resolveFieldType(field, 'text')
      const name = String(field?.name || field?.label || field?.code || '')
      return {
        prop: String(field?.code || ''),
        label: name,
        type: toSearchType(fieldType),
        placeholder: String(field?.placeholder || i18n.global.t('common.placeholders.search', { field: name })),
        options: (field?.options || undefined) as SearchField['options'],
        ...(fieldType === 'multi_select' ? { multiple: true } : {}),
      } as SearchField
    })
}

