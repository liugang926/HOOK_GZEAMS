import { camelToSnake, snakeToCamel } from '@/utils/case'
import { resolveFieldValue } from '@/utils/fieldKey'
import { normalizeFieldType } from '@/utils/fieldType'
import {
  isReferenceLikeFieldType,
  resolveReferenceDisplayField,
} from '@/platform/reference/referenceFieldMeta'

type AnyRecord = Record<string, any>

export interface ListFieldValueOptions {
  fieldCode?: string
  prop?: string
  dataKey?: string
  fieldType?: string
  type?: string
  referenceObject?: string
  reference_object?: string
  targetObjectCode?: string
  target_object_code?: string
  referenceDisplayField?: string
  reference_display_field?: string
}

const EXTRA_REFERENCE_SUFFIXES: Record<string, string[]> = {
  reference: ['display', 'name', 'label', 'code', 'path', 'fullPath', 'full_path'],
  user: ['username', 'fullName', 'full_name', 'name', 'display'],
  department: ['name', 'display', 'code', 'path', 'fullPath', 'full_path', 'fullPathName', 'full_path_name'],
  location: ['name', 'display', 'path', 'fullPath', 'full_path', 'code', 'label', 'fullPathName', 'full_path_name'],
  organization: ['name', 'display', 'code', 'path', 'fullPath', 'full_path', 'fullPathName', 'full_path_name'],
  asset: ['name', 'display', 'code'],
}

const isPresent = (value: unknown): boolean => value !== undefined && value !== null && value !== ''

const toPascalCase = (value: string): string => {
  const camel = snakeToCamel(camelToSnake(String(value || '').trim()))
  return camel ? camel.charAt(0).toUpperCase() + camel.slice(1) : ''
}

const uniqueNonEmpty = (values: Array<unknown>): string[] => {
  return Array.from(
    new Set(
      values
        .map((value) => String(value || '').trim())
        .filter(Boolean)
    )
  )
}

const getRecordSources = (record: any): AnyRecord[] => {
  if (!record || typeof record !== 'object') return []
  const sources: AnyRecord[] = [record as AnyRecord]
  if (record.data && typeof record.data === 'object' && !Array.isArray(record.data)) {
    sources.push(record.data as AnyRecord)
  }
  return sources
}

const readDirectValue = (record: any, key: string): unknown => {
  for (const source of getRecordSources(record)) {
    if (Object.prototype.hasOwnProperty.call(source, key)) {
      const value = source[key]
      if (isPresent(value)) return value
    }
  }
  return undefined
}

const assignValueByPath = (target: AnyRecord, path: string, value: unknown) => {
  const segments = String(path || '')
    .split('.')
    .map((segment) => segment.trim())
    .filter(Boolean)

  if (segments.length === 0) return

  let current: AnyRecord = target
  segments.forEach((segment, index) => {
    if (index === segments.length - 1) {
      current[segment] = value
      return
    }

    const next = current[segment]
    if (!next || typeof next !== 'object' || Array.isArray(next)) {
      current[segment] = {}
    }
    current = current[segment] as AnyRecord
  })
}

const buildDisplayAliasKeys = (
  fieldCode: string,
  dataKey: string,
  displayField: string,
  fieldType: string
): string[] => {
  const baseKeys = uniqueNonEmpty([
    fieldCode,
    dataKey,
    camelToSnake(fieldCode),
    snakeToCamel(fieldCode),
    dataKey ? camelToSnake(dataKey) : '',
    dataKey ? snakeToCamel(dataKey) : '',
  ])

  const displaySuffixes = uniqueNonEmpty([
    displayField,
    camelToSnake(displayField),
    snakeToCamel(displayField),
    ...EXTRA_REFERENCE_SUFFIXES[fieldType] || [],
  ])

  const keys: string[] = []
  for (const baseKey of baseKeys) {
    const camelBase = snakeToCamel(camelToSnake(baseKey))
    const snakeBase = camelToSnake(baseKey)
    for (const suffix of displaySuffixes) {
      const camelSuffix = snakeToCamel(camelToSnake(suffix))
      const snakeSuffix = camelToSnake(suffix)
      const pascalSuffix = toPascalCase(camelSuffix)
      keys.push(`${camelBase}${pascalSuffix}`)
      keys.push(`${snakeBase}_${snakeSuffix}`)
    }
  }

  return uniqueNonEmpty(keys)
}

const buildReferenceDisplayValue = (
  directValue: unknown,
  aliasValue: unknown,
  displayField: string
): unknown => {
  if (!isPresent(aliasValue)) return directValue
  if (aliasValue && typeof aliasValue === 'object') return aliasValue
  if (directValue && typeof directValue === 'object') return directValue
  if (!isPresent(directValue) || Array.isArray(directValue)) return aliasValue
  if (String(directValue) === String(aliasValue)) return aliasValue

  const referenceValue: AnyRecord = {
    id: directValue
  }
  assignValueByPath(referenceValue, displayField || 'name', aliasValue)
  return referenceValue
}

export function resolveListFieldValue(record: any, options: ListFieldValueOptions): unknown {
  const fieldCode = String(options.fieldCode || options.prop || '').trim()
  if (!fieldCode) return undefined

  const dataKey = String(options.dataKey || options.prop || fieldCode).trim()
  const fieldType = normalizeFieldType(String(options.fieldType || options.type || 'text'))
  const referenceObject = String(
    options.referenceObject ||
    options.reference_object ||
    options.targetObjectCode ||
    options.target_object_code ||
    ''
  ).trim()
  const referenceDisplayField = resolveReferenceDisplayField(options, 'name')

  const directValue = resolveFieldValue(record, {
    fieldCode,
    dataKey,
    includeWrappedData: true,
    includeCustomBags: true,
    treatEmptyAsMissing: false,
    returnEmptyMatch: true
  })

  if (isReferenceLikeFieldType(fieldType) || !!referenceObject) {
    if (directValue && typeof directValue === 'object') {
      return directValue
    }

    const aliasKeys = buildDisplayAliasKeys(fieldCode, dataKey, referenceDisplayField, fieldType)
    for (const key of aliasKeys) {
      const aliasValue = readDirectValue(record, key)
      if (isPresent(aliasValue)) {
        return buildReferenceDisplayValue(directValue, aliasValue, referenceDisplayField)
      }
    }
  }

  return directValue
}
