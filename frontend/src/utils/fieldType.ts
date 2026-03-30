/**
 * Field type normalization utilities.
 *
 * Keeps field type aliases consistent across:
 * - runtime form renderer (engine)
 * - list/detail display (common)
 * - metadata adapters
 */

const TYPE_ALIASES: Record<string, string> = {
  // text
  string: 'text',
  char: 'text',
  varchar: 'text',
  richtext: 'rich_text',

  // numbers
  int: 'number',
  integer: 'number',
  float: 'number',
  decimal: 'number',
  money: 'currency',

  // boolean
  bool: 'boolean',
  toggle: 'switch',

  // date/time
  datetime: 'datetime',
  date_time: 'datetime',
  dateTime: 'datetime',
  daterange: 'daterange',
  date_range: 'daterange',
  dateRange: 'daterange',

  // selection
  multiselect: 'multi_select',
  multiSelect: 'multi_select',

  // complex
  subtable: 'sub_table',
  subTable: 'sub_table',

  // codes
  qrcode: 'qr_code',
  qrCode: 'qr_code'
}

const normalizeKey = (raw: string): string => {
  const trimmed = String(raw || '').trim()
  if (!trimmed) return ''
  // Convert camelCase to snake_case-like, normalize separators, lower-case.
  const camelToSnake = trimmed.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`)
  return camelToSnake
    .replace(/\s+/g, '_')
    .replace(/-/g, '_')
    .replace(/__+/g, '_')
    .replace(/^_+/, '')
    .toLowerCase()
}

export const normalizeFieldType = (raw?: string): string => {
  if (!raw) return 'text'
  const normalized = normalizeKey(raw)
  return TYPE_ALIASES[raw] || TYPE_ALIASES[normalized] || normalized || 'text'
}

export const resolveFieldType = (field: any, fallback = 'text'): string => {
  if (!field) return fallback
  const raw =
    field.fieldType ??
    field.field_type ??
    field.editorType ??
    field.editor_type ??
    field.type ??
    field.dataType ??
    field.data_type ??
    fallback
  return normalizeFieldType(raw) || fallback
}
