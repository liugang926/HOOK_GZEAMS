import { normalizeFieldType } from '@/utils/fieldType'

type AnyRecord = Record<string, any>
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
const INTEGER_ID_PATTERN = /^\d+$/

const REFERENCE_TYPE_OBJECT_CODE_MAP: Record<string, string> = {
  user: 'User',
  department: 'Department',
  location: 'Location',
  organization: 'Organization',
  asset: 'Asset'
}

const CANONICAL_REFERENCE_OBJECT_CODE_MAP: Record<string, string> = {
  user: 'User',
  department: 'Department',
  location: 'Location',
  organization: 'Organization',
  asset: 'Asset'
}

const LABEL_FALLBACK_FIELDS = [
  'name',
  'label',
  'title',
  'displayName',
  'display_name',
  'fullName',
  'full_name',
  'username',
  'code',
  'id'
]

export const normalizeReferenceObjectCode = (raw: unknown): string => {
  const value = String(raw || '').trim()
  if (!value) return ''
  const noQuery = value.split('?')[0].replace(/\/+$/, '')
  if (!noQuery) return ''
  const lastDot = noQuery.split('.').pop() || noQuery
  const lastPath = lastDot.split('/').filter(Boolean).pop() || lastDot
  const normalized = String(lastPath || '').trim()
  if (!normalized) return ''
  return CANONICAL_REFERENCE_OBJECT_CODE_MAP[normalized.toLowerCase()] || normalized
}

export const resolveReferenceObjectCode = (field: AnyRecord | null | undefined): string => {
  if (!field) return ''
  const componentProps = field.componentProps || field.component_props || {}
  const explicitCode =
    field.referenceObject ||
    field.reference_object ||
    field.targetObjectCode ||
    field.target_object_code ||
    field.reference_model_path ||
    field.referenceModelPath ||
    field.relatedObject ||
    field.related_object ||
    componentProps.referenceObject ||
    componentProps.reference_object ||
    componentProps.targetObjectCode ||
    componentProps.target_object_code ||
    componentProps.relatedObject ||
    componentProps.related_object ||
    ''

  const normalizedExplicit = normalizeReferenceObjectCode(explicitCode)
  if (normalizedExplicit) return normalizedExplicit

  const fieldType = normalizeFieldType(
    String(field.editorType || field.fieldType || field.field_type || field.type || '')
  )
  return REFERENCE_TYPE_OBJECT_CODE_MAP[fieldType] || ''
}

export const resolveReferenceDisplayField = (
  field: AnyRecord | null | undefined,
  fallback = 'name'
): string => {
  if (!field) return fallback
  const componentProps = field.componentProps || field.component_props || {}
  const value =
    field.referenceDisplayField ||
    field.reference_display_field ||
    field.displayField ||
    field.display_field ||
    componentProps.referenceDisplayField ||
    componentProps.reference_display_field ||
    componentProps.displayField ||
    componentProps.display_field ||
    fallback
  return String(value || fallback).trim() || fallback
}

export const resolveReferenceSecondaryField = (
  field: AnyRecord | null | undefined,
  fallback = 'code'
): string => {
  if (!field) return fallback
  const componentProps = field.componentProps || field.component_props || {}
  const value =
    field.referenceSecondaryField ||
    field.reference_secondary_field ||
    componentProps.referenceSecondaryField ||
    componentProps.reference_secondary_field ||
    componentProps.secondaryField ||
    componentProps.secondary_field ||
    fallback
  return String(value || fallback).trim() || fallback
}

export const isReferenceLikeFieldType = (rawType: unknown): boolean => {
  const normalized = normalizeFieldType(String(rawType || ''))
  return ['reference', 'user', 'department', 'location', 'organization', 'asset'].includes(normalized)
}

export const isReferenceLikeField = (field: AnyRecord | null | undefined): boolean => {
  if (!field) return false
  if (resolveReferenceObjectCode(field)) return true
  return isReferenceLikeFieldType(field.editorType || field.fieldType || field.field_type || field.type)
}

const toIdString = (value: unknown): string => {
  if (value === undefined || value === null) return ''
  if (typeof value === 'number' && Number.isFinite(value)) return String(value)
  const id = String(value).trim()
  if (!id) return ''
  if (UUID_PATTERN.test(id) || INTEGER_ID_PATTERN.test(id)) return id
  return ''
}

export const extractReferenceIds = (value: unknown): string[] => {
  if (value === undefined || value === null || value === '') return []

  const out = new Set<string>()
  const walk = (input: unknown) => {
    if (input === undefined || input === null || input === '') return
    if (Array.isArray(input)) {
      input.forEach((item) => walk(item))
      return
    }
    if (typeof input === 'object') {
      const record = input as AnyRecord
      const candidate = record.id ?? record.value ?? record.pk ?? record.uuid
      const id = toIdString(candidate)
      if (id) out.add(id)
      return
    }
    const id = toIdString(input)
    if (id) out.add(id)
  }

  walk(value)
  return Array.from(out)
}

const resolveByPath = (value: AnyRecord, path: string): unknown => {
  if (!path || !value || typeof value !== 'object') return undefined
  const parts = String(path).split('.').filter(Boolean)
  let current: unknown = value
  for (const part of parts) {
    if (!current || typeof current !== 'object' || Array.isArray(current)) return undefined
    current = (current as AnyRecord)[part]
  }
  return current
}

export const resolveReferenceLabel = (value: unknown, displayField = 'name'): string => {
  if (value === undefined || value === null || value === '') return ''
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
    return String(value)
  }
  if (Array.isArray(value)) {
    return value.map((item) => resolveReferenceLabel(item, displayField)).filter(Boolean).join(', ')
  }
  if (typeof value !== 'object') return String(value)

  const record = value as AnyRecord
  const explicit = resolveByPath(record, displayField)
  if (explicit !== undefined && explicit !== null && explicit !== '') {
    return String(explicit)
  }

  for (const key of LABEL_FALLBACK_FIELDS) {
    const candidate = resolveByPath(record, key)
    if (candidate !== undefined && candidate !== null && candidate !== '') {
      return String(candidate)
    }
  }

  return ''
}

export const resolveReferenceSecondaryText = (
  value: unknown,
  secondaryField = 'code',
  displayField = 'name'
): string => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return ''
  const record = value as AnyRecord
  const secondary = resolveByPath(record, secondaryField)
  if (secondary === undefined || secondary === null || secondary === '') return ''

  const secondaryText = String(secondary)
  const labelText = resolveReferenceLabel(record, displayField)
  if (labelText && secondaryText === labelText) return ''
  return secondaryText
}
