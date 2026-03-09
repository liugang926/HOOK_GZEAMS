type TranslateFn = (key: string, params?: Record<string, unknown>) => string
type TranslateExistsFn = (key: string) => boolean

export interface ReferenceCardMetaItem {
  key: string
  label: string
  value: string
}

interface BuildReferenceCardMetaItemsOptions {
  label?: string
  secondary?: string
  fieldKeys?: string[]
  maxItems?: number
  t: TranslateFn
  te: TranslateExistsFn
}

type AnyRecord = Record<string, any>

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

const DEFAULT_PRIORITY_KEYS = [
  'status',
  'category',
  'type',
  'department',
  'location',
  'parent',
  'owner',
  'user',
  'custodian',
  'manager',
  'brand',
  'model',
  'specification',
  'serialNumber',
  'serial_number',
  'phone',
  'mobile',
  'email',
  'depreciationMethodDisplay',
  'depreciationMethod',
  'defaultUsefulLife',
  'residualRate',
  'isActive',
  'updatedAt',
  'createdAt'
]

const HIDDEN_KEYS = new Set([
  'id',
  '_id',
  'pk',
  'name',
  'label',
  'fullName',
  'full_name',
  'code',
  'organization',
  'customFields',
  'custom_fields',
  'isDeleted',
  'is_deleted',
  'deletedAt',
  'deleted_at',
  'deletedBy',
  'deleted_by'
])

const FIELD_LABEL_KEY_MAP: Record<string, string> = {
  status: 'common.referenceCard.fields.status',
  category: 'common.referenceCard.fields.category',
  type: 'common.referenceCard.fields.type',
  department: 'common.referenceCard.fields.department',
  location: 'common.referenceCard.fields.location',
  parent: 'common.referenceCard.fields.parent',
  owner: 'common.referenceCard.fields.owner',
  user: 'common.referenceCard.fields.user',
  custodian: 'common.referenceCard.fields.custodian',
  manager: 'common.referenceCard.fields.manager',
  brand: 'common.referenceCard.fields.brand',
  model: 'common.referenceCard.fields.model',
  specification: 'common.referenceCard.fields.specification',
  serial_number: 'common.referenceCard.fields.serialNumber',
  phone: 'common.referenceCard.fields.phone',
  mobile: 'common.referenceCard.fields.mobile',
  email: 'common.referenceCard.fields.email',
  depreciation_method_display: 'common.referenceCard.fields.depreciationMethod',
  depreciation_method: 'common.referenceCard.fields.depreciationMethod',
  default_useful_life: 'common.referenceCard.fields.defaultUsefulLife',
  residual_rate: 'common.referenceCard.fields.residualRate',
  is_active: 'common.referenceCard.fields.isActive',
  updated_at: 'common.referenceCard.fields.updatedAt',
  created_at: 'common.referenceCard.fields.createdAt'
}

const normalizeKey = (key: string): string => {
  return String(key || '')
    .trim()
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .replace(/[\s-]+/g, '_')
    .toLowerCase()
}

const humanizeKey = (key: string): string => {
  return String(key || '')
    .trim()
    .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

const isUuidLike = (value: unknown): boolean => {
  return typeof value === 'string' && UUID_PATTERN.test(value.trim())
}

const resolveNestedDisplay = (value: AnyRecord): string => {
  const candidates = [
    value.name,
    value.label,
    value.fullName,
    value.full_name,
    value.code,
    value.username,
    value.email,
    value.phone,
    value.mobile
  ]
  for (const candidate of candidates) {
    const normalized = normalizeMetaValue(candidate)
    if (normalized) return normalized
  }
  return ''
}

export const normalizeMetaValue = (
  value: unknown,
  options: { t?: TranslateFn } = {}
): string => {
  if (value === null || value === undefined) return ''

  if (Array.isArray(value)) {
    const joined = value
      .map((item) => normalizeMetaValue(item, options))
      .filter(Boolean)
      .slice(0, 3)
    return joined.join(', ')
  }

  if (typeof value === 'boolean') {
    if (options.t) {
      const key = value ? 'common.yes' : 'common.no'
      const translated = options.t(key)
      return translated === key ? String(value) : translated
    }
    return String(value)
  }

  if (typeof value === 'number') return String(value)

  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed || isUuidLike(trimmed)) return ''
    return trimmed
  }

  if (typeof value === 'object') {
    return resolveNestedDisplay(value as AnyRecord)
  }

  return String(value)
}

const buildKeyOrder = (record: AnyRecord, preferredKeys: string[]): string[] => {
  const seen = new Set<string>()
  const ordered: string[] = []

  ;[...preferredKeys, ...Object.keys(record || {})].forEach((key) => {
    const normalized = normalizeKey(key)
    if (!normalized || seen.has(normalized)) return
    seen.add(normalized)
    ordered.push(String(key))
  })

  return ordered
}

const localizeFieldLabel = (key: string, t: TranslateFn, te: TranslateExistsFn): string => {
  const normalized = normalizeKey(key)
  const translationKey = FIELD_LABEL_KEY_MAP[normalized]
  if (translationKey && te(translationKey)) {
    const translated = t(translationKey)
    if (translated !== translationKey) return translated
  }
  return humanizeKey(key)
}

const shouldSkipMetaKey = (key: string): boolean => {
  const normalized = normalizeKey(key)
  if (!normalized) return true
  if (HIDDEN_KEYS.has(normalized)) return true
  if (normalized.endsWith('_id') || normalized === 'userid' || normalized === 'departmentid') return true
  return false
}

export const buildReferenceCardMetaItems = (
  record: unknown,
  options: BuildReferenceCardMetaItemsOptions
): ReferenceCardMetaItem[] => {
  if (!record || typeof record !== 'object') return []

  const source = record as AnyRecord
  const label = String(options.label || '').trim()
  const secondary = String(options.secondary || '').trim()
  const maxItems = Number(options.maxItems || 4) > 0 ? Number(options.maxItems || 4) : 4
  const orderedKeys = buildKeyOrder(source, [...(options.fieldKeys || []), ...DEFAULT_PRIORITY_KEYS])

  const items: ReferenceCardMetaItem[] = []
  const valueSet = new Set<string>(
    [label, secondary]
      .map((item) => item.trim().toLowerCase())
      .filter(Boolean)
  )

  for (const key of orderedKeys) {
    if (items.length >= maxItems) break
    if (shouldSkipMetaKey(key)) continue

    const normalizedValue = normalizeMetaValue(source[key], { t: options.t })
    if (!normalizedValue) continue

    const comparableValue = normalizedValue.trim().toLowerCase()
    if (valueSet.has(comparableValue)) continue

    items.push({
      key,
      label: localizeFieldLabel(key, options.t, options.te),
      value: normalizedValue
    })
    valueSet.add(comparableValue)
  }

  return items
}
