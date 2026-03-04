import { ensureLayoutConfigIds, resolveRawLayoutConfig } from '@/platform/layout/layoutPersistGuard'
import { buildRenderSchema, type RenderSchema } from '@/platform/layout/renderSchema'
import type { RuntimeMode } from '@/contracts/runtimeContract'
import { isSystemField } from '@/utils/transform'
import { normalizeLayoutConfig } from '@/adapters/layoutNormalizer'

type AnyRecord = Record<string, any>

const toFieldCode = (field: AnyRecord | null | undefined): string => {
  if (!field || typeof field !== 'object') return ''
  return String(field.code || field.fieldCode || field.field_code || field.fieldName || '').trim()
}

const toKnownFieldCodes = (fields: AnyRecord[]): Set<string> => {
  const out = new Set<string>()
  for (const field of fields || []) {
    const code = toFieldCode(field)
    if (!code) continue
    out.add(code)
  }
  return out
}

const shouldDropUnknownField = (code: string, knownFieldCodes: Set<string>): boolean => {
  if (knownFieldCodes.size === 0) return false
  return !knownFieldCodes.has(code)
}

export interface LayoutFieldDropperOptions {
  knownFieldCodes?: Set<string> | string[]
  keepUnknownFields?: boolean
  keepSystemFields?: boolean
}

export const buildLayoutFieldDropper = (
  options: LayoutFieldDropperOptions = {}
): ((code: string) => boolean) => {
  const knownFieldCodes = Array.isArray(options.knownFieldCodes)
    ? new Set((options.knownFieldCodes || []).map((code) => String(code || '').trim()).filter(Boolean))
    : (options.knownFieldCodes || new Set<string>())
  const keepUnknownFields = options.keepUnknownFields === true
  const keepSystemFields = options.keepSystemFields === true

  return (rawCode: string): boolean => {
    const code = String(rawCode || '').trim()
    if (!code) return true

    if (!keepSystemFields && isSystemField({ code })) {
      return true
    }

    if (!keepUnknownFields && shouldDropUnknownField(code, knownFieldCodes)) {
      return true
    }

    return false
  }
}

export interface CompileLayoutSchemaInput {
  layoutConfig: AnyRecord | null | undefined
  fields: AnyRecord[]
  mode: RuntimeMode
  keepUnknownFields?: boolean
  keepSystemFields?: boolean
  ensureIds?: boolean
}

export interface CompileLayoutSchemaResult {
  layoutConfig: AnyRecord
  renderSchema: RenderSchema
  knownFieldCodes: Set<string>
}

const cloneDeep = <T>(value: T): T => JSON.parse(JSON.stringify(value))

const normalizeFieldEntry = (entry: AnyRecord): AnyRecord => {
  const fieldCode = String(
    entry?.fieldCode || entry?.field_code || entry?.code || entry?.prop || entry?.field || ''
  ).trim()
  if (!fieldCode) return {}
  return {
    ...entry,
    fieldCode
  }
}

const sanitizeLayoutConfigWithoutIdGeneration = (
  rawLayout: AnyRecord,
  dropFieldCode: (code: string) => boolean
): AnyRecord => {
  const normalized = normalizeLayoutConfig(cloneDeep(rawLayout || { sections: [] })) as AnyRecord
  const sections = Array.isArray(normalized?.sections) ? normalized.sections : []

  const sanitizeFieldList = (fields: AnyRecord[]): AnyRecord[] => {
    return (fields || [])
      .map((field) => normalizeFieldEntry(field || {}))
      .filter((field) => {
        const code = String(field?.fieldCode || '').trim()
        return !!code && !dropFieldCode(code)
      })
  }

  const nextSections = sections.map((rawSection: AnyRecord, sectionIndex: number) => {
    const section = { ...(rawSection || {}) }
    const sectionType = String(section?.type || 'section')
    const sectionId = String(section?.id || `section_${sectionIndex + 1}`)

    if (sectionType === 'tab') {
      const tabs = (Array.isArray(section?.tabs) ? section.tabs : []).map((rawTab: AnyRecord, tabIndex: number) => ({
        ...(rawTab || {}),
        id: String(rawTab?.id || `tab_${tabIndex + 1}`),
        fields: sanitizeFieldList(Array.isArray(rawTab?.fields) ? rawTab.fields : [])
      }))
      return {
        ...section,
        id: sectionId,
        type: sectionType,
        tabs
      }
    }

    if (sectionType === 'collapse') {
      const items = (Array.isArray(section?.items) ? section.items : []).map((rawItem: AnyRecord, itemIndex: number) => ({
        ...(rawItem || {}),
        id: String(rawItem?.id || `item_${itemIndex + 1}`),
        fields: sanitizeFieldList(Array.isArray(rawItem?.fields) ? rawItem.fields : [])
      }))
      return {
        ...section,
        id: sectionId,
        type: sectionType,
        items
      }
    }

    return {
      ...section,
      id: sectionId,
      type: sectionType,
      fields: sanitizeFieldList(Array.isArray(section?.fields) ? section.fields : [])
    }
  })

  return {
    ...normalized,
    sections: nextSections
  }
}

export const compileLayoutSchema = (input: CompileLayoutSchemaInput): CompileLayoutSchemaResult => {
  const knownFieldCodes = toKnownFieldCodes(input.fields || [])
  const dropFieldCode = buildLayoutFieldDropper({
    knownFieldCodes,
    keepUnknownFields: input.keepUnknownFields,
    keepSystemFields: input.keepSystemFields
  })

  const rawLayout = resolveRawLayoutConfig(input.layoutConfig || { sections: [] })
  const sanitizedLayoutConfig = input.ensureIds === true
    ? ensureLayoutConfigIds(rawLayout, { dropFieldCode })
    : sanitizeLayoutConfigWithoutIdGeneration(rawLayout, dropFieldCode)
  const renderSchema = buildRenderSchema({
    layoutConfig: sanitizedLayoutConfig,
    fields: input.fields || [],
    mode: input.mode
  })

  return {
    layoutConfig: sanitizedLayoutConfig,
    renderSchema,
    knownFieldCodes
  }
}
