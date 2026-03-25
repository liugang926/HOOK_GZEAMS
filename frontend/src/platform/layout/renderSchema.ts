import { normalizeFieldType } from '@/utils/fieldType'
import { normalizeSpan } from '@/adapters/layoutNormalizer'
import { sortFieldsByRuntimeOrder } from '@/platform/layout/runtimeFieldPolicy'
import type { RuntimeMode } from '@/contracts/runtimeContract'
import type { CanvasPlacement } from '@/platform/layout/canvasLayout'

type AnyRecord = Record<string, any>

export interface RenderField {
  code: string
  label: string
  fieldType: string
  span: number
  minHeight?: number
  fullWidth?: boolean
  labelPosition?: 'left' | 'top'
  labelWidth?: string | number
  layoutPlacement?: Partial<CanvasPlacement>
  componentProps?: AnyRecord
  required: boolean
  readonly: boolean
  visible: boolean
  metadata?: AnyRecord
}

export interface RenderSection {
  id: string
  title: any
  columns: number
  position?: 'main' | 'sidebar'
  kind: 'section' | 'tab' | 'collapse'
  containerId?: string
  containerTitle?: any
  itemId?: string
  itemTitle?: any
  collapsible: boolean
  collapsed: boolean
  labelPosition?: 'left' | 'top'
  labelWidth?: string | number
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

const preserveTitlePayload = (value: unknown, fallback = ''): any => {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value
  if (value && typeof value === 'object') return value
  if (value === undefined || value === null) return fallback
  const normalized = String(value).trim()
  return normalized || fallback
}

const buildLocalizedTitlePayload = (source: AnyRecord, fallback = ''): any => {
  const titleI18n = source?.titleI18n || source?.title_i18n
  if (titleI18n && typeof titleI18n === 'object' && !Array.isArray(titleI18n)) {
    return titleI18n
  }
  const title = source?.title
  const titleEn = source?.titleEn || source?.title_en
  if (titleEn) {
    return {
      'zh-CN': preserveTitlePayload(title, fallback),
      'en-US': preserveTitlePayload(titleEn, fallback)
    }
  }
  return preserveTitlePayload(title, fallback)
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
  const mergedComponentProps = {
    ...(meta?.component_props || {}),
    ...(meta?.componentProps || {}),
    ...(layoutField?.component_props || {}),
    ...(layoutField?.componentProps || {})
  }
  const rawType = layoutField?.fieldType || layoutField?.field_type || meta?.fieldType || meta?.field_type || 'text'
  const label = String(layoutField?.label || layoutField?.name || meta?.label || meta?.name || code)
  const span = normalizeSpan(layoutField?.span ?? meta?.span ?? 1, columns)
  const rawMinHeight = layoutField?.minHeight ??
    layoutField?.min_height ??
    mergedComponentProps?.minHeight ??
    mergedComponentProps?.min_height ??
    meta?.minHeight ??
    meta?.min_height
  const minHeight = Number.isFinite(Number(rawMinHeight)) && Number(rawMinHeight) > 0 ? Math.round(Number(rawMinHeight)) : undefined
  const layoutPlacement = (
    layoutField?.layoutPlacement ||
    layoutField?.layout_placement ||
    layoutField?.placement ||
    layoutField?.canvasPlacement ||
    null
  ) as Partial<CanvasPlacement> | null

  return {
    code,
    label,
    fieldType: normalizeFieldType(rawType),
    span,
    minHeight,
    fullWidth: layoutField?.fullWidth === true,
    labelPosition: layoutField?.labelPosition || undefined,
    labelWidth: layoutField?.labelWidth || undefined,
    layoutPlacement: layoutPlacement || undefined,
    componentProps: Object.keys(mergedComponentProps).length > 0 ? mergedComponentProps : undefined,
    required: Boolean(layoutField?.required ?? meta?.required ?? meta?.isRequired ?? meta?.is_required ?? false),
    readonly: normalizeReadonly(layoutField, meta, mode),
    visible: layoutField?.visible !== false && meta?.isHidden !== true && meta?.is_hidden !== true,
    metadata: meta
  }
}

const buildSectionFromFields = (
  id: string,
  title: any,
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
    containerTitle?: any
    itemId?: string
    itemTitle?: any
    labelPosition?: 'left' | 'top'
    labelWidth?: string | number
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
    labelPosition: options.labelPosition,
    labelWidth: options.labelWidth,
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

const buildDetailRegionLayoutField = (section: AnyRecord): AnyRecord | null => {
  const fieldCode = String(section?.fieldCode || section?.field_code || '').trim()
  if (!fieldCode) return null
  const relationCode = String(section?.relationCode || section?.relation_code || '').trim()
  const targetObjectCode = String(section?.targetObjectCode || section?.target_object_code || '').trim()
  const detailEditMode = String(section?.detailEditMode || section?.detail_edit_mode || '').trim()
  const displayMode = detailEditMode === 'readonly_table' ? 'inline_readonly' : 'inline_editable'
  const lookupColumns = Array.isArray(section?.lookupColumns)
    ? section.lookupColumns
    : (Array.isArray(section?.lookup_columns) ? section.lookup_columns : undefined)
  const relatedFields = Array.isArray(section?.relatedFields)
    ? section.relatedFields
    : (Array.isArray(section?.related_fields) ? section.related_fields : undefined)
  const componentProps = {
    ...(section?.toolbarConfig || section?.toolbar_config || {}),
    relationCode,
    targetObjectCode,
    relatedObjectCode: targetObjectCode,
    displayMode
  } as AnyRecord

  if (Array.isArray(lookupColumns)) {
    componentProps.lookupColumns = lookupColumns
    componentProps.lookup_columns = lookupColumns
  }
  if (Array.isArray(relatedFields)) {
    componentProps.relatedFields = relatedFields
    componentProps.related_fields = relatedFields
    componentProps.columns = relatedFields.map((field: AnyRecord) => ({
      key: String(field?.code || field?.fieldCode || '').trim(),
      label: String(field?.label || field?.name || field?.code || field?.fieldCode || '').trim(),
      width: Number.isFinite(Number(field?.width)) && Number(field?.width) > 0 ? Math.round(Number(field?.width)) : undefined,
      minWidth:
        Number.isFinite(Number(field?.minWidth ?? field?.min_width)) && Number(field?.minWidth ?? field?.min_width) > 0
          ? Math.round(Number(field?.minWidth ?? field?.min_width))
          : undefined,
      align: ['left', 'center', 'right'].includes(String(field?.align || '').trim().toLowerCase())
        ? String(field?.align).trim().toLowerCase()
        : undefined,
      fixed: ['left', 'right'].includes(String(field?.fixed || '').trim().toLowerCase())
        ? String(field?.fixed).trim().toLowerCase()
        : undefined,
      formatter: String(field?.formatter || field?.displayFormatter || '').trim() || undefined,
      emptyText: String(field?.emptyText ?? field?.empty_text ?? '').trim() || undefined,
      tooltipTemplate: String(field?.tooltipTemplate ?? field?.tooltip_template ?? '').trim() || undefined,
      showOverflowTooltip:
        field?.ellipsis === true ||
        field?.showOverflowTooltip === true ||
        field?.show_overflow_tooltip === true
    })).filter((field: AnyRecord) => field.key)
  }

  return {
    fieldCode,
    label: buildLocalizedTitlePayload(section, fieldCode),
    span: 1,
    componentProps
  }
}

const buildWorkflowProgressLayoutField = (section: AnyRecord): AnyRecord => {
  const sectionId = String(section?.id || section?.name || 'workflow_progress').trim() || 'workflow_progress'
  const statusFieldCode = String(section?.statusFieldCode || section?.status_field_code || 'status').trim() || 'status'
  const componentProps: AnyRecord = {
    ...(section?.componentProps || {}),
    ...(section?.component_props || {}),
    statusFieldCode,
    status_field_code: statusFieldCode
  }

  if (Array.isArray(section?.steps)) {
    componentProps.steps = section.steps
  }

  return {
    fieldCode: `__workflow_progress__${sectionId}`,
    label: buildLocalizedTitlePayload(section, ''),
    fieldType: 'workflow_progress',
    span: 1,
    fullWidth: true,
    componentProps
  }
}

export function buildRenderSchema(input: {
  layoutConfig: AnyRecord | null | undefined
  fields: AnyRecord[]
  mode: RuntimeMode
  reverseRelations?: AnyRecord[]
}): RenderSchema {
  const { layoutConfig, fields, mode, reverseRelations } = input
  const fieldMap = buildFieldMap(fields)
  const sections: RenderSection[] = []
  const rawSections = Array.isArray(layoutConfig?.sections) ? layoutConfig.sections : []

  if (rawSections.length === 0) {
    // Phase 3: Detailed Fallback Architecture
    const fallbackSections: RenderSection[] = []

    // 1. Sort standard fields
    const fallbackFields = sortFieldsByRuntimeOrder(fields).map((field) => ({
      fieldCode: toFieldCode(field),
      label: field?.label || field?.name
    }))

    // 2. Separate Reverse Relations
    const standardRelations: AnyRecord[] = []
    const sidebarRelations: AnyRecord[] = []

    if (Array.isArray(reverseRelations)) {
      for (const rel of reverseRelations) {
        if (rel.position === 'sidebar') sidebarRelations.push(rel)
        else standardRelations.push(rel)
      }
    }

    if (standardRelations.length === 0 && sidebarRelations.length === 0) {
      // Degrade to old behavior if no relations are present at all
      const fallback = buildFallbackSections(fields, fieldMap, mode)
      return {
        mode,
        sections: fallback,
        fieldOrder: flattenFieldOrder(fallback)
      }
    }

    // 3. Build Main Tabs (Details & Related)
    const containerId = 'default_fallback_container'
    const detailTabFields = fallbackFields

    const relatedTabFields = standardRelations.map((rel) => ({
      fieldCode: rel.code || rel.relationCode || rel.relation_code,
      label: rel.label || rel.name,
      fieldType: 'related_object',
      span: 2,
      componentProps: {
        relationCode: rel.code || rel.relationCode || rel.relation_code,
        relatedObjectCode: rel.targetObjectCode || rel.target_object_code || rel.relatedObjectCode,
        displayMode: rel.relationDisplayMode || rel.relation_display_mode || rel.displayMode || 'inline_readonly'
      }
    }))

    const detailSection = buildSectionFromFields(
      `${containerId}::tab::details`,
      'Details',
      'tab',
      2,
      detailTabFields,
      fieldMap,
      mode,
      {
        containerId,
        containerTitle: 'Record Details',
        itemId: 'details',
        itemTitle: 'Details'
      }
    )
    if (detailSection) fallbackSections.push(detailSection)

    if (relatedTabFields.length > 0) {
      const relatedSection = buildSectionFromFields(
        `${containerId}::tab::related`,
        'Related',
        'tab',
        1, // Single column for tables is better
        relatedTabFields as AnyRecord[],
        fieldMap,
        mode,
        {
          containerId,
          containerTitle: 'Record Details',
          itemId: 'related',
          itemTitle: 'Related'
        }
      )
      if (relatedSection) fallbackSections.push(relatedSection)
    }

    // 4. Build Sidebar Sections
    for (const rel of sidebarRelations) {
      const sidebarField = {
        fieldCode: rel.code || rel.relationCode || rel.relation_code,
        label: rel.label || rel.name,
        fieldType: 'related_object',
        span: 1,
        componentProps: {
          relationCode: rel.code || rel.relationCode || rel.relation_code,
          relatedObjectCode: rel.targetObjectCode || rel.target_object_code || rel.relatedObjectCode,
          displayMode: rel.relationDisplayMode || rel.relation_display_mode || rel.displayMode || 'inline_readonly'
        }
      }

      const relSection = buildSectionFromFields(
        `${containerId}::sidebar::${String(sidebarField.fieldCode || 'related').trim() || 'related'}`,
        sidebarField.label,
        'section',
        1,
        [sidebarField] as AnyRecord[],
        fieldMap,
        mode,
        {
          position: 'sidebar'
        }
      )
      if (relSection) fallbackSections.push(relSection)
    }

    return {
      mode,
      sections: fallbackSections,
      fieldOrder: flattenFieldOrder(fallbackSections)
    }
  }

  for (const rawSection of rawSections) {
    const sectionId = String(rawSection?.id || rawSection?.name || `section_${sections.length + 1}`)
    const sectionTitle = buildLocalizedTitlePayload(rawSection, '')
    const columns = resolveColumns(rawSection)
    const sectionType = String(rawSection?.type || 'section')

    if (sectionType === 'tab') {
      const tabs = Array.isArray(rawSection?.tabs) ? rawSection.tabs : []
      for (const tab of tabs) {
        const tabId = String(tab?.id || tab?.name || `tab_${sections.length + 1}`)
        const tabTitle = preserveTitlePayload(tab?.title ?? tab?.name, 'Tab')
        const section = buildSectionFromFields(
          `${sectionId}::tab::${tabId}`,
          tabTitle,
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
            itemTitle: tabTitle,
            labelPosition: rawSection?.labelPosition || undefined,
            labelWidth: rawSection?.labelWidth || undefined
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
        const itemTitle = preserveTitlePayload(item?.title ?? item?.name, 'Group')
        const section = buildSectionFromFields(
          `${sectionId}::collapse::${itemId}`,
          itemTitle,
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
            itemTitle: itemTitle,
            labelPosition: rawSection?.labelPosition || undefined,
            labelWidth: rawSection?.labelWidth || undefined
          }
        )
        if (section) sections.push(section)
      }
      continue
    }

    if (sectionType === 'detail-region') {
      const detailField = buildDetailRegionLayoutField(rawSection)
      const section = buildSectionFromFields(
        sectionId,
        sectionTitle,
        'section',
        1,
        detailField ? [detailField] : [],
        fieldMap,
        mode,
        {
          position: rawSection?.position as 'main' | 'sidebar' | undefined,
          collapsible: rawSection?.collapsible === true,
          collapsed: rawSection?.collapsed === true,
          labelPosition: rawSection?.labelPosition || undefined,
          labelWidth: rawSection?.labelWidth || undefined
        }
      )
      if (section) sections.push(section)
      continue
    }

    if (sectionType === 'workflow-progress') {
      const workflowField = buildWorkflowProgressLayoutField(rawSection)
      const section = buildSectionFromFields(
        sectionId,
        sectionTitle,
        'section',
        1,
        [workflowField],
        fieldMap,
        mode,
        {
          position: rawSection?.position as 'main' | 'sidebar' | undefined,
          collapsible: rawSection?.collapsible === true,
          collapsed: rawSection?.collapsed === true,
          labelPosition: rawSection?.labelPosition || undefined,
          labelWidth: rawSection?.labelWidth || undefined
        }
      )
      if (section) sections.push(section)
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
        collapsed: rawSection?.collapsed === true,
        labelPosition: rawSection?.labelPosition || undefined,
        labelWidth: rawSection?.labelWidth || undefined
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
