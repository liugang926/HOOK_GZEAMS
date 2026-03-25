import { snakeToCamel } from '@/utils/case'
import type {
  AggregateDocumentResponse,
  RuntimeAggregate,
  RuntimeAggregateDetailRegion,
} from '@/types/runtime'
import type { AggregateDocumentPayload } from '@/api/dynamic'

const AGGREGATE_DOCUMENT_OBJECT_CODES = new Set([
  'AssetPickup',
  'AssetTransfer',
  'AssetReturn',
  'AssetLoan',
  'PurchaseRequest',
  'AssetReceipt',
  'DisposalRequest',
])

const toRecordKey = (value: string | undefined): string => String(value || '').trim()

export const resolveAggregateDetailFieldCode = (region: RuntimeAggregateDetailRegion) => {
  return toRecordKey(region.fieldCode) || toRecordKey(region.relationCode)
}

const extractRows = (value: unknown): Array<Record<string, any>> => {
  if (Array.isArray(value)) {
    return value.filter((row): row is Record<string, any> => !!row && typeof row === 'object' && !Array.isArray(row))
  }

  if (value && typeof value === 'object') {
    const candidate = value as Record<string, unknown>
    for (const key of ['rows', 'items', 'data', 'list']) {
      if (Array.isArray(candidate[key])) {
        return extractRows(candidate[key])
      }
    }
  }

  return []
}

const readRecordCandidate = (record: Record<string, any>, keys: string[]): unknown => {
  for (const rawKey of keys) {
    const key = toRecordKey(rawKey)
    if (!key) continue
    if (Object.prototype.hasOwnProperty.call(record, key)) {
      return record[key]
    }
    const camelKey = snakeToCamel(key)
    if (camelKey && Object.prototype.hasOwnProperty.call(record, camelKey)) {
      return record[camelKey]
    }
  }
  return undefined
}

export const supportsAggregateDocument = (
  objectCode: string,
  aggregate: RuntimeAggregate | null | undefined,
) => {
  if (!AGGREGATE_DOCUMENT_OBJECT_CODES.has(String(objectCode || '').trim())) {
    return false
  }

  if (!aggregate?.isAggregateRoot) {
    return false
  }

  return Array.isArray(aggregate.detailRegions) && aggregate.detailRegions.length > 0
}

export const buildAggregateDocumentFormData = (
  document: AggregateDocumentResponse,
): Record<string, any> => {
  const formData: Record<string, any> = {
    ...(document.master || {}),
    id: document.context?.recordId,
  }

  const detailRegions = Array.isArray(document.aggregate?.detailRegions)
    ? document.aggregate.detailRegions
    : []

  for (const region of detailRegions) {
    const relationCode = toRecordKey(region.relationCode)
    const fieldCode = resolveAggregateDetailFieldCode(region)
    const rows = extractRows(document.details?.[relationCode]?.rows || [])
    if (!fieldCode) continue
    formData[fieldCode] = rows
    if (relationCode) {
      formData[relationCode] = { rows }
    }
  }

  return formData
}

export const buildAggregateDocumentPayload = (
  submitData: Record<string, any>,
  aggregate: RuntimeAggregate | null | undefined,
): AggregateDocumentPayload => {
  const detailRegions = Array.isArray(aggregate?.detailRegions) ? aggregate.detailRegions : []
  const detailFieldKeys = new Set<string>()
  const detailRelationKeys = new Set<string>()
  const details: Record<string, { rows: Array<Record<string, any>> }> = {}

  for (const region of detailRegions) {
    const relationCode = toRecordKey(region.relationCode)
    const fieldCode = resolveAggregateDetailFieldCode(region)
    if (!relationCode) continue

    if (fieldCode) {
      detailFieldKeys.add(fieldCode)
      detailFieldKeys.add(snakeToCamel(fieldCode))
    }
    detailRelationKeys.add(relationCode)
    detailRelationKeys.add(snakeToCamel(relationCode))

    const rows = extractRows(readRecordCandidate(submitData, [fieldCode, relationCode]))
    details[relationCode] = { rows }
  }

  const master = Object.entries(submitData || {}).reduce<Record<string, any>>((accumulator, [key, value]) => {
    if (detailFieldKeys.has(key) || detailRelationKeys.has(key)) {
      return accumulator
    }
    accumulator[key] = value
    return accumulator
  }, {})

  return {
    master,
    details,
  }
}

export const resolveAggregateDocumentDetailPath = (
  objectCode: string,
  document: AggregateDocumentResponse | null | undefined,
): string | null => {
  const normalizedObjectCode = toRecordKey(objectCode)
  const normalizedRecordId = toRecordKey(document?.context?.recordId)

  if (!normalizedObjectCode || !normalizedRecordId) {
    return null
  }

  return `/objects/${encodeURIComponent(normalizedObjectCode)}/${encodeURIComponent(normalizedRecordId)}`
}

const resolveDetailRegion = (
  aggregate: RuntimeAggregate | null | undefined,
  relationCode?: string,
) => {
  const detailRegions = Array.isArray(aggregate?.detailRegions) ? aggregate.detailRegions : []
  const normalizedRelationCode = toRecordKey(relationCode)

  if (normalizedRelationCode) {
    const matched = detailRegions.find((region) => toRecordKey(region.relationCode) === normalizedRelationCode)
    if (matched) return matched
  }

  return detailRegions[0] || null
}

export const readAggregateDocumentDetailRows = (
  modelValue: Record<string, any> | null | undefined,
  aggregate: RuntimeAggregate | null | undefined,
  relationCode?: string,
): Array<Record<string, any>> => {
  const region = resolveDetailRegion(aggregate, relationCode)
  if (!region) return []

  const fieldCode = resolveAggregateDetailFieldCode(region)
  const normalizedRelationCode = toRecordKey(region.relationCode)

  return extractRows(
    readRecordCandidate(modelValue || {}, [fieldCode, normalizedRelationCode]),
  )
}

export const writeAggregateDocumentDetailRows = (
  modelValue: Record<string, any> | null | undefined,
  aggregate: RuntimeAggregate | null | undefined,
  rows: Array<Record<string, any>>,
  relationCode?: string,
): Record<string, any> => {
  const region = resolveDetailRegion(aggregate, relationCode)
  const nextModel = { ...(modelValue || {}) }

  if (!region) {
    return nextModel
  }

  const normalizedRows = extractRows(rows)
  const fieldCode = resolveAggregateDetailFieldCode(region)
  const normalizedRelationCode = toRecordKey(region.relationCode)

  if (fieldCode) {
    nextModel[fieldCode] = normalizedRows
  }

  if (normalizedRelationCode) {
    const existingRelationPayload = nextModel[normalizedRelationCode]
    if (existingRelationPayload && typeof existingRelationPayload === 'object' && !Array.isArray(existingRelationPayload)) {
      nextModel[normalizedRelationCode] = {
        ...existingRelationPayload,
        rows: normalizedRows,
      }
    } else {
      nextModel[normalizedRelationCode] = { rows: normalizedRows }
    }
  }

  return nextModel
}
