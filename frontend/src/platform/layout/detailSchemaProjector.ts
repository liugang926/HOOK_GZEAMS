import { normalizeFieldType } from '@/utils/fieldType'
import type { FieldDefinition } from '@/types'
import type { RenderSchema } from '@/platform/layout/renderSchema'
import { normalizeGridSpan24 } from '@/platform/layout/semanticGrid'
import { placeCanvasFields } from '@/platform/layout/canvasLayout'

export interface ProjectedDetailField {
  prop: string
  label: string
  editorType?: string
  type?:
    | 'text'
    | 'date'
    | 'datetime'
    | 'time'
    | 'daterange'
    | 'year'
    | 'month'
    | 'number'
    | 'currency'
    | 'percent'
    | 'boolean'
    | 'switch'
    | 'checkbox'
    | 'tag'
    | 'slot'
    | 'link'
    | 'image'
    | 'qr_code'
    | 'barcode'
    | 'color'
    | 'rate'
    | 'file'
    | 'attachment'
    | 'rich_text'
    | 'sub_table'
    | 'json'
    | 'object'
  options?: { label: string; value: any; color?: string }[]
  dateFormat?: string
  precision?: number
  currency?: string
  tagType?: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'>
  defaultTagType?: 'success' | 'warning' | 'danger' | 'info' | 'primary'
  span?: number
  minHeight?: number
  href?: string
  hidden?: boolean
  readonly?: boolean
  labelClass?: string
  valueClass?: string
  layoutPlacement?: {
    row?: number
    colStart?: number
    colSpan?: number
    rowSpan?: number
    columns?: number
    totalRows?: number
    order?: number
    canvas?: {
      x?: number
      y?: number
      width?: number
      height?: number
    }
  }
  placement?: {
    row: number
    colStart: number
    colSpan: number
    rowSpan: number
    columns: number
    totalRows: number
    order: number
    canvas: {
      x: number
      y: number
      width: number
      height: number
    }
  }
}

export interface ProjectedDetailTab {
  id: string
  title: string
  fields: ProjectedDetailField[]
}

export interface ProjectedDetailSection {
  name: string
  title: string
  type?: string
  position?: 'main' | 'sidebar'
  fields: ProjectedDetailField[]
  tabs?: ProjectedDetailTab[]
  icon?: string
  collapsible?: boolean
  collapsed?: boolean
}

export interface DetailSchemaProjectorOptions {
  strictVisibility?: boolean
  mustSkipField?: (field: FieldDefinition) => boolean
  shouldSkipField?: (field: FieldDefinition) => boolean
  isAuditFieldCode?: (code: string) => boolean
  fieldToDetailField: (field: FieldDefinition) => ProjectedDetailField
  getSectionTitle?: (sectionName: string) => string
  getSectionIcon?: (sectionName: string) => string
  normalizeSpan?: (rawSpan: unknown, rawColumns: unknown) => number
}

const defaultNormalizeDetailSpan = (rawSpan: unknown, rawColumns: unknown): number => {
  return normalizeGridSpan24(rawSpan, rawColumns)
}

export function projectDetailSectionsFromRenderSchema(
  renderSchema: RenderSchema,
  fields: FieldDefinition[],
  options: DetailSchemaProjectorOptions
): ProjectedDetailSection[] {
  const {
    strictVisibility = true,
    mustSkipField,
    shouldSkipField,
    isAuditFieldCode,
    fieldToDetailField,
    getSectionTitle,
    getSectionIcon,
    normalizeSpan = defaultNormalizeDetailSpan
  } = options

  const fieldMap = new Map<string, FieldDefinition>()
  for (const field of fields || []) fieldMap.set(field.code, field)

  const sections: ProjectedDetailSection[] = []

  // Track reconstructed container tabs (containerId -> ProjectedDetailSection)
  const tabContainers = new Map<string, ProjectedDetailSection>()

  for (const section of renderSchema.sections || []) {
    const detailFields: ProjectedDetailField[] = []

    for (const renderField of section.fields || []) {
      const code = String(renderField.code || '').trim()
      if (!code) continue

      if (isAuditFieldCode?.(code)) continue

      const metaField = (renderField.metadata as FieldDefinition | undefined) || fieldMap.get(code)
      const policyField = {
        ...(metaField || ({} as FieldDefinition)),
        code,
        name: String(renderField.label || (metaField as any)?.name || code),
        label: String(renderField.label || (metaField as any)?.label || code),
        fieldType: normalizeFieldType(renderField.fieldType || (metaField as any)?.fieldType || 'text'),
        isHidden:
          renderField.visible === false ||
          (metaField as any)?.isHidden === true ||
          (metaField as any)?.is_hidden === true
      } as FieldDefinition

      if (mustSkipField?.(policyField)) continue
      if (strictVisibility && shouldSkipField?.(policyField)) continue

      if (metaField) {
        const detailField = fieldToDetailField(metaField)
        detailField.editorType = detailField.editorType || normalizeFieldType(renderField.fieldType || metaField.fieldType || 'text')
        detailField.label = renderField.label || detailField.label
        detailField.hidden = renderField.visible === false
        detailField.readonly = renderField.readonly === true
        detailField.span = normalizeSpan(renderField.span ?? detailField.span ?? 1, section.columns)
        detailField.minHeight = Number.isFinite(Number(renderField.minHeight)) && Number(renderField.minHeight) > 0
          ? Math.round(Number(renderField.minHeight))
          : (
              Number.isFinite(Number((detailField as any).minHeight)) && Number((detailField as any).minHeight) > 0
                ? Math.round(Number((detailField as any).minHeight))
                : undefined
            )
        ;(detailField as any).layoutPlacement = (renderField as any).layoutPlacement || undefined
        detailFields.push(detailField)
        continue
      }

      detailFields.push({
        prop: code,
        label: renderField.label || code,
        editorType: normalizeFieldType(renderField.fieldType || 'text'),
        type: normalizeFieldType(renderField.fieldType || 'text') as ProjectedDetailField['type'],
        span: normalizeSpan(renderField.span ?? 1, section.columns),
        minHeight: Number.isFinite(Number(renderField.minHeight)) && Number(renderField.minHeight) > 0
          ? Math.round(Number(renderField.minHeight))
          : undefined,
        layoutPlacement: (renderField as any).layoutPlacement || undefined,
        hidden: renderField.visible === false,
        readonly: renderField.readonly === true
      } as ProjectedDetailField)
    }

    const placedDetailFields = placeCanvasFields(detailFields, section.columns, {
      preferSavedPlacement: true
    })

    if (section.kind === 'tab' && section.containerId) {
      let container = tabContainers.get(section.containerId)
      if (!container) {
        container = {
          name: section.containerId,
          title: section.containerTitle || getSectionTitle?.(section.containerId) || section.containerId,
          type: 'tab',
          position: section.position,
          fields: [], // Tab containers don't have top-level fields
          tabs: []
        }
        tabContainers.set(section.containerId, container)
        sections.push(container)
      }

      const tabId = section.itemId || section.id
      container.tabs?.push({
        id: tabId,
        title: section.itemTitle || section.title,
        fields: placedDetailFields
      })
      continue
    }

    if (placedDetailFields.length === 0 && section.kind !== 'tab') continue

    const sectionName = String(section.id || `section_${sections.length + 1}`)
    sections.push({
      name: sectionName,
      title: section.title || (getSectionTitle?.(sectionName) || sectionName),
      type: section.kind || 'section',
      position: section.position,
      icon: getSectionIcon?.(sectionName),
      collapsible: section.collapsible === true,
      collapsed: section.collapsed === true,
      fields: placedDetailFields
    })
  }

  return sections
}

