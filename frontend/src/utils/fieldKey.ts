import { camelToSnake, snakeToCamel } from '@/utils/case'

type AnyRecord = Record<string, any>

export interface ResolveFieldValueOptions {
  fieldCode: string
  dataKey?: string
  includeWrappedData?: boolean
  includeCustomBags?: boolean
  treatEmptyAsMissing?: boolean
  returnEmptyMatch?: boolean
}

export function isPlainObject(value: any): value is Record<string, any> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

export function isEmptyValue(value: any): boolean {
  return value === undefined || value === null || value === ''
}

export function toDataKey(fieldCode: string): string {
  if (!fieldCode) return fieldCode
  return fieldCode.includes('_') ? snakeToCamel(fieldCode) : fieldCode
}

export function buildFieldKeyCandidates(fieldCode: string, dataKey?: string): string[] {
  if (!fieldCode) return []

  const normalizedCode = String(fieldCode).trim()
  const normalizedDataKey = dataKey ? String(dataKey).trim() : toDataKey(normalizedCode)

  const candidates = [
    normalizedCode,
    normalizedDataKey,
    camelToSnake(normalizedCode),
    snakeToCamel(normalizedCode),
    normalizedDataKey ? camelToSnake(normalizedDataKey) : '',
    normalizedDataKey ? snakeToCamel(normalizedDataKey) : ''
  ]

  return Array.from(new Set(candidates.filter(Boolean)))
}

function tryReadByCandidates(
  source: AnyRecord,
  keys: string[],
  treatEmptyAsMissing: boolean
): { matched: boolean; value: any; preferred: boolean } {
  let matched = false
  let fallback: any = undefined

  for (const key of keys) {
    if (!Object.prototype.hasOwnProperty.call(source, key)) continue

    const value = source[key]
    matched = true
    if (fallback === undefined) fallback = value

    if (!treatEmptyAsMissing || !isEmptyValue(value)) {
      return { matched: true, value, preferred: true }
    }
  }

  return { matched, value: fallback, preferred: false }
}

export function resolveFieldValue(record: any, options: ResolveFieldValueOptions): any {
  if (!record || !options?.fieldCode) return undefined

  const {
    fieldCode,
    dataKey,
    includeWrappedData = true,
    includeCustomBags = true,
    treatEmptyAsMissing = true,
    returnEmptyMatch = false
  } = options

  const keys = buildFieldKeyCandidates(fieldCode, dataKey)
  if (keys.length === 0) return undefined

  const sources: AnyRecord[] = []
  if (isPlainObject(record)) {
    sources.push(record)
    if (includeWrappedData && isPlainObject(record.data)) {
      sources.push(record.data)
    }
  }

  let emptyMatch: any = undefined
  let hasEmptyMatch = false

  for (const source of sources) {
    const hit = tryReadByCandidates(source, keys, treatEmptyAsMissing)
    if (hit.preferred) return hit.value
    if (hit.matched && !hasEmptyMatch) {
      hasEmptyMatch = true
      emptyMatch = hit.value
    }

    if (!includeCustomBags) continue

    const customBags = [source.customFields, source.custom_fields]
    for (const bag of customBags) {
      if (!isPlainObject(bag)) continue
      const bagHit = tryReadByCandidates(bag, keys, treatEmptyAsMissing)
      if (bagHit.preferred) return bagHit.value
      if (bagHit.matched && !hasEmptyMatch) {
        hasEmptyMatch = true
        emptyMatch = bagHit.value
      }
    }
  }

  if (returnEmptyMatch && hasEmptyMatch) {
    return emptyMatch
  }
  return undefined
}

