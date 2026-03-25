import type { RuntimeField } from '@/types/runtime'
import { isPlainObject, resolveFieldValue, toDataKey } from '@/utils/fieldKey'

type AnyRecord = Record<string, any>

export function getFieldDataKey(field: RuntimeField): string {
  return field.dataKey || toDataKey(field.code)
}

export function getFieldValue(field: RuntimeField, record: AnyRecord): any {
  if (!field || !record) return undefined

  return resolveFieldValue(record, {
    fieldCode: field.code,
    dataKey: getFieldDataKey(field),
    includeWrappedData: false,
    includeCustomBags: true,
    treatEmptyAsMissing: true,
    returnEmptyMatch: false
  })
}

export function setFieldValue(field: RuntimeField, record: AnyRecord, value: any): AnyRecord {
  const next: AnyRecord = { ...(record || {}) }

  const codeKey = field.code
  const dataKey = getFieldDataKey(field)

  // Canonical: always write to codeKey so Element Plus rules/props stay stable.
  next[codeKey] = value

  // If the incoming record already uses dataKey, keep it updated for compatibility.
  if (dataKey && Object.prototype.hasOwnProperty.call(next, dataKey)) {
    next[dataKey] = value
  }

  // If value was stored in customFields, keep it updated there too.
  if (isPlainObject(next.customFields) && Object.prototype.hasOwnProperty.call(next.customFields, codeKey)) {
    next.customFields = { ...next.customFields, [codeKey]: value }
  }

  return next
}

export function toSubmitValue(field: RuntimeField, value: any): any {
  const fieldType = field.fieldType || 'text'
  const relationshipTypes = new Set(['reference', 'user', 'department', 'location', 'asset', 'organization'])
  const fileLikeTypes = new Set(['file', 'image', 'attachment'])
  const objectPayloadTypes = new Set(['sub_table', 'subtable'])

  const normalizeId = (val: any) => {
    if (val === null || val === undefined) return val
    if (isPlainObject(val)) return val.id ?? val.value ?? val.code ?? val
    return val
  }

  // If the value is an expanded entity object, submit its id by default.
  // This matches backend serializers which typically expect IDs for relation fields.
  if (!objectPayloadTypes.has(fieldType)) {
    if (Array.isArray(value) && value.some((v) => isPlainObject(v) && 'id' in v)) {
      return value.map(normalizeId)
    }
    if (isPlainObject(value) && 'id' in value) {
      return normalizeId(value)
    }
  }

  // Robust relationship detection: type OR presence of referenceObject.
  if (relationshipTypes.has(fieldType) || !!field.referenceObject) {
    if (Array.isArray(value)) return value.map(normalizeId)
    return normalizeId(value)
  }

  if (fileLikeTypes.has(fieldType)) {
    if (Array.isArray(value)) return value.map(normalizeId)
    return normalizeId(value)
  }

  return value
}

export function buildSubmitPayload(layoutFields: RuntimeField[], record: AnyRecord): AnyRecord {
  const payload: AnyRecord = {}
  const customFieldsOut: AnyRecord = {}

  const custom = isPlainObject(record?.customFields) ? (record.customFields as AnyRecord) : null

  for (const field of layoutFields) {
    if (!field?.code) continue

    const rawValue = getFieldValue(field, record)
    const submitValue = toSubmitValue(field, rawValue)

    // If this field is currently stored in customFields, submit it there.
    if (custom && Object.prototype.hasOwnProperty.call(custom, field.code)) {
      customFieldsOut[field.code] = submitValue
      continue
    }

    const key = getFieldDataKey(field)
    payload[key] = submitValue
  }

  if (Object.keys(customFieldsOut).length > 0) {
    payload.customFields = customFieldsOut
  }

  return payload
}
