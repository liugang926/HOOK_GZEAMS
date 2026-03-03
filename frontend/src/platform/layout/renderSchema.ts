import { normalizeFieldType } from '@/utils/fieldType'
import { normalizeSpan } from '@/adapters/layoutNormalizer'
import { sortFieldsByRuntimeOrder } from '@/platform/layout/runtimeFieldPolicy'
import type { RuntimeMode } from '@/contracts/runtimeContract'

type AnyRecord = Record<string, any>

export interface RenderField {
  code: string
  label: string
  fieldType: string
  span: number
  required: boolean
  readonly: boolean
  visible: boolean
  metadata?: AnyRecord
}

export interface RenderSection {
  id: string
  title: string
  columns: number
  position?: 'main' | 'sidebar'
  kind: 'section' | 'tab' | 'collapse'
  containerId?: string
  containerTitle?: string
  itemId?: string
  itemTitle?: string
  collapsible: boolean
  collapsed: boolean
  fields: RenderField[]
}

export interface RenderSchema {
  mode: RuntimeMode
  sections: RenderSection[]
  fieldOrder: string[]
}

const toFieldCode = (field: AnyRecord): string =>
  String(field?.code || field?.fieldCode || field?.field_code || '').trim()

const buildFieldMap = (fields: AnyRecord[]): Map<string, AnyRecord> => {
  const map = new Map<string, AnyRecord>()
  for (const field of fields) {
    const code = toFieldCode(field)
    if (!code) continue
    if (!map.has(code)) {
      map.set(code, field)
    }
  }
  return map
}

const resolveColumns = (section: AnyRecord): number => {
  return Number(section?.columns || section?.columnCount || section?.column || 2) || 2
}

const coerceBoolean = (value: unknown): boolean | undefined => {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') {
    if (value === 1) return true
    if (value === 0) return false
    return undefined
  }
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    if (['true', '1', 'yes', 'y'].includes(normalized)) return true
    if (['false', '0', 'no', 'n'].includes(normalized)) return false
  }
  return undefined
}

const pickBooleanByKeys = (source: AnyRecord | undefined, keys: string[]): boolean | undefined => {
  if (!source) return undefined
  for (const key of keys) {
    const value = coerceBoolean(source[key])
    if (value !== undefined) return value
  }
  return undefined
}

const normalizeReadonly = (
  layoutField: AnyRecord | undefined,
  meta: AnyRecord | undefined,
  mode: RuntimeMode
): boolean => {
  if (mode === 'readonly') return true

  const layoutReadonly = pickBooleanByKeys(layoutField, ['readonly', 'isReadonly', 'is_readonly'])
  if (layoutReadonly !== undefined) return layoutReadonly

  const layoutEditable = pickBooleanByKeys(layoutField, ['editable', 'isEditable', 'is_editable', 'allowEdit', 'allow_edit'])
  if (layoutEditable !== undefined) return !layoutEditable

  const metaReadonly = pickBooleanByKeys(meta, ['readonly', 'isReadonly', 'is_readonly'])
  if (metaReadonly !== undefined) return metaReadonly

  const metaEditable = pickBooleanByKeys(meta, ['editable', 'isEditable', 'is_editable'])
  if (metaEditable !== undefined) return !metaEditable

  return false
}

const buildRenderField = (
  layoutField: AnyRecord,
  fieldMap: Map<string, AnyRecord>,
  columns: number,
  mode: RuntimeMode
): RenderField | null => {
  const code = toFieldCode(layoutField)
  if (!code) return null

  const meta = fieldMap.get(code)
  const rawType = layoutField?.fieldType || layoutField?.field_type || meta?.fieldType || meta?.field_type || 'text'
  const label = String(layoutField?.label || layoutField?.name || meta?.label || meta?.name || code)
  const span = normalizeSpan(layoutField?.span ?? meta?.span ?? 1, columns)

  return {
    code,
    label,
    fieldType: normalizeFieldType(rawType),
    span,
    required: Boolean(layoutField?.required ?? meta?.required ?? meta?.isRequired ?? meta?.is_required ?? false),
    readonly: normalizeReadonly(layoutField, meta, mode),
    visible: layoutField?.visible !== false && meta?.isHidden !== true && meta?.is_hidden !== true,
    metadata: meta
  }
}

const buildSectionFromFields = (
  id: string,
  title: string,
  kind: 'section' | 'tab' | 'collapse',
  columns: number,
  fields: AnyRecord[],
  fieldMap: Map<string, AnyRecord>,
  mode: RuntimeMode,
  options: {
    position?: 'main' | 'sidebar'
    collapsible?: boolean
    collapsed?: boolean
    containerId?: string
    containerTitle?: string
    itemId?: string
    itemTitle?: string
  } = {}
): RenderSection | null => {
  const renderFields = (fields || [])
    .map((item) => buildRenderField(item, fieldMap, columns, mode))
    .filter((item): item is RenderField => !!item)

  if (renderFields.length === 0) return null
  return {
    id,
    title,
    columns,
    position: options.position || 'main',
    kind,
    collapsible: options.collapsible === true,
    collapsed: options.collapsed === true,
    containerId: options.containerId,
    containerTitle: options.containerTitle,
    itemId: options.itemId,
    itemTitle: options.itemTitle,
    fields: renderFields
  }
}

const flattenFieldOrder = (sections: RenderSection[]): string[] => {
  const order: string[] = []
  for (const section of sections) {
    for (const field of section.fields) {
      if (!order.includes(field.code)) {
        order.push(field.code)
      }
    }
  }
  return order
}

const buildFallbackSections = (
  fields: AnyRecord[],
  fieldMap: Map<string, AnyRecord>,
  mode: RuntimeMode
): RenderSection[] => {
  const fallbackFields = sortFieldsByRuntimeOrder(fields).map((field) => ({
    fieldCode: toFieldCode(field),
    label: field?.label || field?.name
  }))

  const section = buildSectionFromFields(
    'default',
    '',
    'section',
    2,
    fallbackFields,
    fieldMap,
    mode,
    { collapsible: false, collapsed: false }
  )
  return section ? [section] : []
}

export function buildRenderSchema(input: {
  layoutConfig: AnyRecord | null | undefined
  fields: AnyRecord[]
  mode: RuntimeMode
}): RenderSchema {
  const { layoutConfig, fields, mode } = input
  const fieldMap = buildFieldMap(fields)
  const sections: RenderSection[] = []
  const rawSections = Array.isArray(layoutConfig?.sections) ? layoutConfig.sections : []

  if (rawSections.length === 0) {
    const fallback = buildFallbackSections(fields, fieldMap, mode)
    return {
      mode,
      sections: fallback,
      fieldOrder: flattenFieldOrder(fallback)
    }
  }

  for (const rawSection of rawSections) {
    const sectionId = String(rawSection?.id || rawSection?.name || `section_${sections.length + 1}`)
    const sectionTitle = String(rawSection?.title || '')
    const columns = resolveColumns(rawSection)
    const sectionType = String(rawSection?.type || 'section')

    if (sectionType === 'tab') {
      const tabs = Array.isArray(rawSection?.tabs) ? rawSection.tabs : []
      for (const tab of tabs) {
        const tabId = String(tab?.id || tab?.name || `tab_${sections.length + 1}`)
        const tabTitle = String(tab?.title || tab?.name || 'Tab')
        const section = buildSectionFromFields(
          `${sectionId}::tab::${tabId}`,
          sectionTitle ? `${sectionTitle} / ${tabTitle}` : tabTitle,
          'tab',
          columns,
          Array.isArray(tab?.fields) ? tab.fields : [],
          fieldMap,
          mode,
          {
            position: rawSection?.position as 'main' | 'sidebar' | undefined,
            collapsible: rawSection?.collapsible === true,
            collapsed: rawSection?.collapsed === true,
            containerId: sectionId,
            containerTitle: sectionTitle || tabTitle,
            itemId: tabId,
            itemTitle: tabTitle
          }
        )
        if (section) sections.push(section)
      }
      continue
    }

    if (sectionType === 'collapse') {
      const items = Array.isArray(rawSection?.items) ? rawSection.items : []
      for (const item of items) {
        const itemId = String(item?.id || item?.name || `item_${sections.length + 1}`)
        const itemTitle = String(item?.title || item?.name || 'Group')
        const section = buildSectionFromFields(
          `${sectionId}::collapse::${itemId}`,
          sectionTitle ? `${sectionTitle} / ${itemTitle}` : itemTitle,
          'collapse',
          columns,
          Array.isArray(item?.fields) ? item.fields : [],
          fieldMap,
          mode,
          {
            position: rawSection?.position as 'main' | 'sidebar' | undefined,
            collapsible: rawSection?.collapsible === true,
            collapsed: item?.collapsed === true || rawSection?.collapsed === true,
            containerId: sectionId,
            containerTitle: sectionTitle || itemTitle,
            itemId: itemId,
            itemTitle: itemTitle
          }
        )
        if (section) sections.push(section)
      }
      continue
    }

    const section = buildSectionFromFields(
      sectionId,
      sectionTitle,
      'section',
      columns,
      Array.isArray(rawSection?.fields) ? rawSection.fields : [],
      fieldMap,
      mode,
      {
        position: rawSection?.position as 'main' | 'sidebar' | undefined,
        collapsible: rawSection?.collapsible === true,
        collapsed: rawSection?.collapsed === true
      }
    )
    if (section) sections.push(section)
  }

  if (sections.length === 0) {
    const fallback = buildFallbackSections(fields, fieldMap, mode)
    return {
      mode,
      sections: fallback,
      fieldOrder: flattenFieldOrder(fallback)
    }
  }

  return {
    mode,
    sections,
    fieldOrder: flattenFieldOrder(sections)
  }
}
