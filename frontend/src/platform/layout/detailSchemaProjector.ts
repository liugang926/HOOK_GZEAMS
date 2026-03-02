import { normalizeFieldType } from '@/utils/fieldType'
import type { FieldDefinition } from '@/types'
import type { RenderSchema } from '@/platform/layout/renderSchema'

export interface ProjectedDetailField {
  prop: string
  label: string
  type?: 'text' | 'date' | 'datetime' | 'time' | 'number' | 'currency' | 'percent' | 'tag' | 'slot' | 'link' | 'image'
  options?: { label: string; value: any; color?: string }[]
  dateFormat?: string
  precision?: number
  currency?: string
  tagType?: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'>
  defaultTagType?: 'success' | 'warning' | 'danger' | 'info' | 'primary'
  span?: number
  href?: string
  hidden?: boolean
  labelClass?: string
  valueClass?: string
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
  const columns = Number(rawColumns) || 2
  const span = Number(rawSpan)

  if (!Number.isFinite(span) || span <= 0) return Math.max(1, Math.round(24 / columns))
  if (span <= columns) return Math.max(1, Math.min(24, Math.round((24 / columns) * span)))
  if (span <= 24) return Math.max(1, Math.min(24, Math.round(span)))
  return 24
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
      if (metaField) {
        if (mustSkipField?.(metaField)) continue
        if (strictVisibility && shouldSkipField?.(metaField)) continue

        const detailField = fieldToDetailField(metaField)
        detailField.label = renderField.label || detailField.label
        detailField.hidden = renderField.visible === false
        detailField.span = normalizeSpan(renderField.span ?? detailField.span ?? 1, section.columns)
        detailFields.push(detailField)
        continue
      }

      detailFields.push({
        prop: code,
        label: renderField.label || code,
        type: normalizeFieldType(renderField.fieldType || 'text') as ProjectedDetailField['type'],
        span: normalizeSpan(renderField.span ?? 1, section.columns),
        hidden: renderField.visible === false
      })
    }

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
        fields: detailFields
      })
      continue
    }

    if (detailFields.length === 0 && section.kind !== 'tab') continue

    const sectionName = String(section.id || `section_${sections.length + 1}`)
    sections.push({
      name: sectionName,
      title: section.title || (getSectionTitle?.(sectionName) || sectionName),
      type: section.kind || 'section',
      position: section.position,
      icon: getSectionIcon?.(sectionName),
      collapsible: section.collapsible === true,
      collapsed: section.collapsed === true,
      fields: detailFields
    })
  }

  return sections
}
