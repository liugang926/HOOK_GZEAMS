import type { TableColumn, SearchField } from '@/types/common'
import type { RuntimeField, RuntimeLayoutConfig, RuntimeSection } from '@/types/runtime'
import { buildSearchFields } from '@/platform/layout/searchFieldBuilder'
import { filterSystemFields } from '@/utils/transform'
import type { RenderSchema, RenderSection } from '@/platform/layout/renderSchema'
import { snakeToCamel } from '@/utils/case'
import { normalizeFieldType } from '@/utils/fieldType'
import { placeCanvasFields, type CanvasPlacement } from '@/platform/layout/canvasLayout'

type AnyRecord = Record<string, any>

const getFieldCode = (field: AnyRecord): string =>
  String(field?.code || field?.fieldCode || field?.field_code || field?.fieldName || '').trim()

const toFieldMap = (fields: AnyRecord[]): Map<string, AnyRecord> => {
  const map = new Map<string, AnyRecord>()
  for (const field of fields || []) {
    const code = getFieldCode(field)
    if (!code) continue
    if (!map.has(code)) map.set(code, field)
  }
  return map
}

const projectRuntimeField = (field: AnyRecord): RuntimeField => {
  const metadata = (field.metadata || {}) as AnyRecord
  const code = String(field.code || metadata.code || '').trim()
  const dataKey = String(
    metadata.dataKey || metadata.data_key || (code.includes('_') ? snakeToCamel(code) : code)
  ).trim()
  const fieldType = normalizeFieldType(
    String(field.fieldType || metadata.fieldType || metadata.field_type || 'text')
  )
  const componentProps = {
    ...(metadata.component_props || {}),
    ...(metadata.componentProps || {}),
    ...(field.component_props || {}),
    ...(field.componentProps || {})
  }
  const rawMinHeight = field.minHeight ?? componentProps.minHeight ?? componentProps.min_height ?? metadata.minHeight ?? metadata.min_height
  const minHeight = Number.isFinite(Number(rawMinHeight)) && Number(rawMinHeight) > 0
    ? Math.round(Number(rawMinHeight))
    : undefined
  const layoutPlacement = (
    field.layoutPlacement ||
    field.layout_placement ||
    field.placement ||
    metadata.layoutPlacement ||
    metadata.layout_placement ||
    null
  ) as Partial<CanvasPlacement> | null

  return {
    code,
    dataKey,
    label: String(field.label || metadata.label || metadata.name || code),
    fieldType,
    span: Number(field.span || metadata.span || 1),
    minHeight,
    required: field.required === true || metadata.required === true || metadata.isRequired === true || metadata.is_required === true,
    readonly: field.readonly === true || metadata.readonly === true || metadata.isReadonly === true || metadata.is_readonly === true,
    hidden: metadata.hidden === true || metadata.isHidden === true || metadata.is_hidden === true,
    visible: field.visible !== false && metadata.visible !== false,
    options: (metadata.options || undefined) as RuntimeField['options'],
    referenceObject: String(
      metadata.referenceObject || metadata.reference_model_path || metadata.relatedObject || ''
    ) || undefined,
    referenceDisplayField: String(
      field.referenceDisplayField ||
      field.reference_display_field ||
      metadata.referenceDisplayField ||
      metadata.reference_display_field ||
      metadata.displayField ||
      metadata.display_field ||
      ''
    ) || undefined,
    referenceSecondaryField: String(
      field.referenceSecondaryField ||
      field.reference_secondary_field ||
      metadata.referenceSecondaryField ||
      metadata.reference_secondary_field ||
      ''
    ) || undefined,
    objectCode: metadata.objectCode || metadata.object_code,
    instanceId: metadata.instanceId || metadata.instance_id,
    componentProps,
    placement: layoutPlacement ? (layoutPlacement as RuntimeField['placement']) : undefined,
    layoutPlacement: layoutPlacement || undefined,
    metadata
  }
}

const projectRuntimeFieldsWithCanvas = (
  fields: AnyRecord[],
  columns: number
): RuntimeField[] => {
  const runtimeFields = (fields || []).map(projectRuntimeField)
  const placed = placeCanvasFields(
    runtimeFields as Array<RuntimeField & { span?: number; minHeight?: number }>,
    columns,
    { preferSavedPlacement: true }
  )
  return placed.map((field) => ({
    ...field,
    placement: field.placement
  }))
}

const projectRuntimeSection = (section: RenderSection): RuntimeSection => ({
  id: section.id,
  name: section.id,
  title: section.title,
  type: 'section',
  position: section.position,
  columns: section.columns,
  visible: true,
  collapsible: section.collapsible === true,
  collapsed: section.collapsed === true,
  showTitle: !!section.title,
  fields: projectRuntimeFieldsWithCanvas(section.fields, Number(section.columns || 2) || 2)
})

const projectTabSection = (group: RenderSection[]): RuntimeSection => {
  const seed = group[0]
  const sectionId = String(seed.containerId || seed.id || 'tab_section')
  const sectionTitle = seed.containerTitle ?? seed.title ?? ''

  return {
    id: sectionId,
    name: sectionId,
    title: sectionTitle,
    type: 'tab',
    position: seed.position,
    columns: Number(seed.columns || 2) || 2,
    visible: true,
    collapsible: seed.collapsible === true,
    collapsed: seed.collapsed === true,
    showTitle: !!sectionTitle,
    tabs: group.map((item, index) => {
      const tabId = String(item.itemId || item.id || `tab_${index + 1}`)
      return {
        id: tabId,
        name: tabId,
        title: item.itemTitle ?? item.title ?? tabId,
        fields: projectRuntimeFieldsWithCanvas(item.fields, Number(seed.columns || 2) || 2)
      }
    })
  }
}

const projectCollapseSection = (group: RenderSection[]): RuntimeSection => {
  const seed = group[0]
  const sectionId = String(seed.containerId || seed.id || 'collapse_section')
  const sectionTitle = seed.containerTitle ?? seed.title ?? ''

  return {
    id: sectionId,
    name: sectionId,
    title: sectionTitle,
    type: 'collapse',
    position: seed.position,
    columns: Number(seed.columns || 2) || 2,
    visible: true,
    collapsible: seed.collapsible === true,
    collapsed: seed.collapsed === true,
    showTitle: !!sectionTitle,
    items: group.map((item, index) => {
      const itemId = String(item.itemId || item.id || `collapse_${index + 1}`)
      return {
        id: itemId,
        name: itemId,
        title: item.itemTitle ?? item.title ?? itemId,
        collapsed: item.collapsed === true,
        fields: projectRuntimeFieldsWithCanvas(item.fields, Number(seed.columns || 2) || 2)
      }
    })
  }
}

const groupRenderSections = (sections: RenderSection[], kind: RenderSection['kind']): RenderSection[][] => {
  const groups = new Map<string, RenderSection[]>()
  for (const section of sections) {
    if (section.kind !== kind) continue
    const groupKey = String(section.containerId || section.id || `${kind}_${groups.size + 1}`)
    const bucket = groups.get(groupKey) || []
    bucket.push(section)
    groups.set(groupKey, bucket)
  }
  return Array.from(groups.values())
}

const resolveFieldCode = (entry: AnyRecord): string => {
  return String(entry?.fieldCode || entry?.field_code || entry?.code || entry?.prop || entry?.field || '').trim()
}

/**
 * List runtime payloads may still provide `columns` instead of `sections`.
 * Build a lightweight section layout so RenderSchema can remain the single source.
 */
export const projectListLayoutConfigForRenderSchema = (
  layoutConfig: AnyRecord | null | undefined,
  fallbackColumns: AnyRecord[] = []
): AnyRecord | null => {
  if (!layoutConfig && fallbackColumns.length === 0) return null

  if (Array.isArray(layoutConfig?.sections) && layoutConfig.sections.length > 0) {
    return layoutConfig as AnyRecord
  }

  const layoutColumns = Array.isArray(layoutConfig?.columns) ? layoutConfig.columns : []
  const columns = fallbackColumns.length > 0 ? fallbackColumns : layoutColumns
  if (!columns.length) return layoutConfig || null

  return {
    sections: [
      {
        id: 'list_default',
        title: '',
        type: 'section',
        columns: 1,
        fields: columns
          .map((column) => {
            const code = resolveFieldCode(column)
            if (!code) return null
            return {
              fieldCode: code,
              label: column?.label || column?.title || code,
              visible: column?.visible !== false
            }
          })
          .filter((item): item is { fieldCode: string; label: any; visible: boolean } => !!item)
      }
    ]
  }
}

export const projectRuntimeLayoutFromRenderSchema = (schema: RenderSchema | null | undefined): RuntimeLayoutConfig => {
  if (!schema) return { sections: [] }

  const runtimeSections: RuntimeSection[] = []
  const processed = new Set<string>()

  for (const section of schema.sections) {
    if (section.kind === 'section') {
      runtimeSections.push(projectRuntimeSection(section))
      continue
    }

    const groupKey = String(section.containerId || section.id || section.kind)
    if (processed.has(groupKey)) continue
    processed.add(groupKey)

    const groups = groupRenderSections(schema.sections, section.kind)
    const target = groups.find((group) => String(group[0]?.containerId || group[0]?.id || section.kind) === groupKey)
    if (!target || target.length === 0) continue

    if (section.kind === 'tab') {
      runtimeSections.push(projectTabSection(target))
      continue
    }
    runtimeSections.push(projectCollapseSection(target))
  }

  return {
    sections: runtimeSections
  }
}

export const orderFieldsByRenderSchema = (fields: AnyRecord[], schema: RenderSchema | null | undefined): AnyRecord[] => {
  if (!schema?.fieldOrder?.length) return [...fields]

  const order = schema.fieldOrder
  const fieldMap = toFieldMap(fields)
  const ordered: AnyRecord[] = []

  for (const code of order) {
    const hit = fieldMap.get(code)
    if (hit) ordered.push(hit)
  }

  for (const field of fields || []) {
    const code = getFieldCode(field)
    if (!code) continue
    if (!order.includes(code)) ordered.push(field)
  }

  return ordered
}

export const projectListColumnsFromRenderSchema = (
  schema: RenderSchema | null | undefined,
  fields: AnyRecord[]
): TableColumn[] => {
  if (!schema?.sections?.length) return []
  const fieldMap = toFieldMap(fields)
  const columns: TableColumn[] = []
  const seen = new Set<string>()

  for (const section of schema.sections) {
    for (const field of section.fields) {
      const code = String(field.code || '').trim()
      if (!code || seen.has(code)) continue
      seen.add(code)

      const meta = fieldMap.get(code) || {}
      const type = String(field.fieldType || meta.fieldType || 'text')
      columns.push({
        fieldCode: code,
        prop: code,
        label: String(field.label || meta.name || meta.label || code),
        fieldType: type,
        type,
        options: meta.options,
        width: Number(meta.columnWidth || meta.column_width || 0) || undefined,
        minWidth: Number(meta.minColumnWidth || meta.min_column_width || 0) || undefined,
        sortable: meta.sortable !== false,
        visible: field.visible !== false
      })
    }
  }

  return columns
}

export const projectSearchFieldsFromRenderSchema = (
  schema: RenderSchema | null | undefined,
  fields: AnyRecord[]
): SearchField[] => {
  if (!schema?.fieldOrder?.length) {
    return buildSearchFields(filterSystemFields(fields as AnyRecord[])) as SearchField[]
  }
  const ordered = orderFieldsByRenderSchema(fields, schema)
  return buildSearchFields(filterSystemFields(ordered as AnyRecord[])) as SearchField[]
}
