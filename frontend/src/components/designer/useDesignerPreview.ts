import { computed, type Ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { normalizeFieldType } from '@/utils/fieldType'
import { toUnifiedDetailField } from '@/platform/layout/unifiedDetailField'
import { toRuntimeFieldFromLayout } from '@/platform/layout/unifiedRuntimeField'
import { normalizeGridSpan24 } from '@/platform/layout/semanticGrid'
import { getCanvasPlacementAttrs, placeCanvasFields, type CanvasPlacement } from '@/platform/layout/canvasLayout'
import { buildDesignerRelationGroupScopeId } from '@/platform/reference/relationGroupScope'
import { resolveTranslatableText } from '@/utils/localeText'
import type {
  DesignerAnyRecord,
  DesignerFieldDefinition,
  DesignerFieldPlacement,
  DesignerRenderField,
  DesignerRenderSection,
  LayoutConfig,
  LayoutField,
  LayoutSection
} from '@/components/designer/designerTypes'
import type { AuditInfo, DetailField, DetailSection } from '@/components/common/BaseDetailPage.vue'
import type { FieldDefinition as RuntimeFieldDefinition } from '@/types'

interface UseDesignerPreviewOptions {
  props: {
    objectCode?: string
    layoutName?: string
    layoutId?: string
    mode?: string
  }
  availableFields: Ref<DesignerFieldDefinition[]>
  layoutConfig: Ref<LayoutConfig>
  sampleData: Ref<Record<string, unknown>>
  readComponentProps: (field: Partial<DesignerFieldDefinition & LayoutField> | null | undefined) => DesignerAnyRecord
  readLayoutPlacement: (
    field: LayoutField | null | undefined
  ) => LayoutField['layoutPlacement'] | LayoutField['layout_placement'] | null
  resolveLayoutFieldMinHeight: (field: Partial<LayoutField> | null | undefined) => number | undefined
  getRenderColumns: (section: Partial<LayoutSection> | null | undefined) => number
}

const iterateLayoutFields = (config: LayoutConfig): LayoutField[] => {
  const out: LayoutField[] = []
  for (const section of config.sections || []) {
    if (section.type === 'tab') {
      for (const tab of section.tabs || []) out.push(...(tab.fields || []))
      continue
    }
    if (section.type === 'collapse') {
      for (const item of section.items || []) out.push(...(item.fields || []))
      continue
    }
    if (section.type === 'detail-region') {
      const fieldCode = String(section.fieldCode || section.field_code || '').trim()
      if (fieldCode) {
        out.push({
          id: `${section.id}__detail_region`,
          fieldCode,
          label: String(section.title || fieldCode),
          fieldType: 'sub_table',
          span: 1,
          readonly: false,
          visible: true
        })
      }
      continue
    }
    out.push(...(section.fields || []))
  }
  return out.filter((field) => !!field?.fieldCode)
}

const buildSectionTitlePayload = (section: LayoutSection): any => {
  const titleI18n = section.titleI18n || section.title_i18n
  if (titleI18n && typeof titleI18n === 'object') return titleI18n
  if (section.titleEn || section.title_en) {
    return {
      'zh-CN': section.title || '',
      'en-US': section.titleEn || section.title_en || section.title || ''
    }
  }
  return section.title
}

export function useDesignerPreview(options: UseDesignerPreviewOptions) {
  const { t, locale } = useI18n()

  const buildSectionSlotField = (sectionId: string): DetailField => ({
    prop: `__designer_section_slot__${sectionId}`,
    label: '',
    type: 'slot',
    visible: true
  })

  function getDesignerPlacementAttrs(placement: DesignerFieldPlacement | null): Record<string, string> {
    return getCanvasPlacementAttrs(placement as CanvasPlacement | null)
  }

  function buildDesignerRenderFields(fields: LayoutField[], columns: number): DesignerRenderField[] {
    const placementSeed = (fields || []).map((field) => ({
      span: field?.span ?? 1,
      minHeight: options.resolveLayoutFieldMinHeight(field),
      layoutPlacement: options.readLayoutPlacement(field)
    }))
    const placed = placeCanvasFields(placementSeed, columns, {
      preferSavedPlacement: true
    })
    return (fields || []).map((field, index) => {
      const placement = (placed[index]?.placement || null) as DesignerFieldPlacement | null
      const semanticSpan = placement?.colSpan || 1
      const span24 = normalizeGridSpan24(semanticSpan, placement?.columns || columns)
      return {
        field,
        span24,
        semanticSpan,
        placement,
        placementAttrs: getDesignerPlacementAttrs(placement)
      }
    })
  }

  function fieldToDesignDisplayField(field: LayoutField): DetailField {
    const runtimeField = toRuntimeFieldFromLayout(
      field as unknown as Record<string, unknown>,
      options.availableFields.value as unknown as Array<Record<string, unknown>>
    )
    const detailField = toUnifiedDetailField(runtimeField as unknown as Record<string, unknown>) as DetailField
    detailField.prop = field.fieldCode
    detailField.label = field.label || detailField.label || field.fieldCode
    return detailField
  }

  function getSampleValue(field: LayoutField): unknown {
    const type = normalizeFieldType(field.fieldType || 'text')
    const label = field.label || ''
    const code = field.fieldCode || ''

    if (field.defaultValue !== undefined) return field.defaultValue

    const labelLower = label.toLowerCase()
    const codeLower = code.toLowerCase()

    if (codeLower.includes('name') || labelLower.includes('name')) return 'Sample Name'
    if (codeLower.includes('code') || labelLower.includes('code')) return 'CODE001'

    const sampleValues: Record<string, unknown> = {
      text: label || 'Sample Text',
      textarea: `${label || 'Sample'} details`,
      rich_text: `<p>${label || 'Sample rich text'}</p>`,
      number: 100,
      percent: 15.5,
      currency: 9999.99,
      boolean: true,
      date: '2024-01-15',
      datetime: '2024-01-15 14:30:00',
      time: '14:30:00',
      year: '2024',
      month: '2024-01',
      select: 'option-1',
      multi_select: ['option-1', 'option-2'],
      radio: 'option-1',
      checkbox: true,
      reference: null,
      user: null,
      department: null,
      location: null,
      asset: null,
      image: null,
      file: null,
      attachment: null,
      formula: 0,
      sub_table: []
    }

    return sampleValues[type] !== undefined ? sampleValues[type] : label || ''
  }

  const previewFieldDefinitions = computed<RuntimeFieldDefinition[]>(() => {
    const map = new Map<string, RuntimeFieldDefinition>()

    const register = (code: string, seed: Partial<RuntimeFieldDefinition>) => {
      const normalizedCode = String(code || '').trim()
      if (!normalizedCode) return
      const current = map.get(normalizedCode)
      const next: RuntimeFieldDefinition = {
        code: normalizedCode,
        name: seed.name || seed.label || normalizedCode,
        label: seed.label || seed.name || normalizedCode,
        fieldType: normalizeFieldType((seed.fieldType as string) || 'text') as RuntimeFieldDefinition['fieldType'],
        isRequired: seed.isRequired ?? false,
        isReadonly: seed.isReadonly ?? false,
        isHidden: seed.isHidden ?? false,
        showInForm: seed.showInForm ?? true,
        showInDetail: seed.showInDetail ?? true,
        options: seed.options || [],
        span: seed.span,
        defaultValue: seed.defaultValue,
        placeholder: seed.placeholder,
        helpText: seed.helpText,
        referenceObject: seed.referenceObject,
        componentProps: seed.componentProps || {},
        ...(current || {})
      }
      map.set(normalizedCode, { ...next, ...(seed as RuntimeFieldDefinition) })
    }

    for (const field of options.availableFields.value) {
      register(field.code, {
        name: field.name,
        label: field.name,
        fieldType: field.fieldType as RuntimeFieldDefinition['fieldType'],
        isRequired: field.isRequired,
        isReadonly: field.isReadonly,
        showInForm: field.showInForm ?? true,
        showInDetail: field.showInDetail ?? true,
        options: field.options as RuntimeFieldDefinition['options'],
        defaultValue: field.defaultValue,
        placeholder: field.placeholder,
        helpText: field.helpText,
        referenceObject: field.referenceObject || field.relatedObject,
        componentProps: field.componentProps || {}
      })
    }

    for (const field of iterateLayoutFields(options.layoutConfig.value)) {
      register(field.fieldCode, {
        name: field.label || field.fieldCode,
        label: field.label || field.fieldCode,
        fieldType: normalizeFieldType(field.fieldType || 'text') as RuntimeFieldDefinition['fieldType'],
        isRequired: !!field.required,
        isReadonly: !!field.readonly,
        isHidden: field.visible === false,
        showInForm: field.visible !== false,
        showInDetail: field.visible !== false,
        options: (field.options || []) as RuntimeFieldDefinition['options'],
        span: field.span,
        defaultValue: field.defaultValue,
        placeholder: field.placeholder,
        helpText: field.helpText,
        referenceObject: field.referenceObject || field.relatedObject,
        componentProps: options.readComponentProps(field)
      })
    }

    return Array.from(map.values())
  })

  const designerRenderSections = computed<DesignerRenderSection[]>(() => {
    return (options.layoutConfig.value.sections || []).map((section: LayoutSection) => {
      const type = section.type || 'section'
      const renderColumns = options.getRenderColumns(section)
      const sectionTitle =
        resolveTranslatableText(buildSectionTitlePayload(section), locale.value as 'zh-CN' | 'en-US') ||
        t('system.pageLayout.designer.defaults.untitledSection')

      if (type === 'tab') {
        const tabs = (section.tabs || []).map((tab) => ({
          id: tab.id,
          title:
            resolveTranslatableText(tab.title, locale.value as 'zh-CN' | 'en-US') ||
            String(tab.name || tab.id || ''),
          fields: buildDesignerRenderFields((tab.fields || []) as LayoutField[], renderColumns)
        }))
        return {
          id: section.id,
          title: sectionTitle,
          type,
          position: section.position,
          collapsible: section.collapsible === true,
          collapsed: section.collapsed === true,
          section,
          fields: [],
          tabs,
          items: []
        }
      }

      if (type === 'collapse') {
        const items = (section.items || []).map((item) => ({
          id: item.id,
          title:
            resolveTranslatableText(item.title, locale.value as 'zh-CN' | 'en-US') ||
            String(item.name || item.id || ''),
          fields: buildDesignerRenderFields((item.fields || []) as LayoutField[], renderColumns)
        }))
        return {
          id: section.id,
          title: sectionTitle,
          type,
          position: section.position,
          collapsible: section.collapsible === true,
          collapsed: section.collapsed === true,
          section,
          fields: [],
          tabs: [],
          items
        }
      }

      if (type === 'detail-region') {
        return {
          id: section.id,
          title: sectionTitle,
          type,
          position: section.position,
          collapsible: section.collapsible === true,
          collapsed: section.collapsed === true,
          section,
          fields: [],
          tabs: [],
          items: []
        }
      }

      return {
        id: section.id,
        title: sectionTitle,
        type,
        position: section.position,
        collapsible: section.collapsible === true,
        collapsed: section.collapsed === true,
        section,
        fields: buildDesignerRenderFields((section.fields || []) as LayoutField[], renderColumns),
        tabs: [],
        items: []
      }
    })
  })

  const designerCanvasSections = computed<DetailSection[]>(() => {
    return designerRenderSections.value.map((renderSection) => {
      if (renderSection.type === 'tab') {
        return {
          name: renderSection.id,
          title: renderSection.title,
          type: renderSection.type,
          position: renderSection.position,
          fields: [],
          tabs: (renderSection.tabs || []).map((tab) => ({
            id: tab.id,
            title: tab.title,
            fields: [buildSectionSlotField(`${renderSection.id}_${tab.id}`)]
          })),
          collapsible: renderSection.collapsible === true,
          collapsed: renderSection.collapsed === true
        }
      }

      return {
        name: renderSection.id,
        title: renderSection.title,
        type: renderSection.type,
        position: renderSection.position,
        fields: [buildSectionSlotField(renderSection.id)],
        collapsible: renderSection.collapsible === true,
        collapsed: renderSection.collapsed === true
      }
    })
  })

  const readAuditString = (...values: unknown[]): string => {
    for (const value of values) {
      if (typeof value !== 'string') continue
      const normalized = value.trim()
      if (normalized) return normalized
    }
    return ''
  }

  const previewAuditInfo = computed<AuditInfo>(() => ({
    createdBy: readAuditString(options.sampleData.value.createdBy, options.sampleData.value.created_by) || 'System',
    createdAt: readAuditString(options.sampleData.value.createdAt, options.sampleData.value.created_at) || '2026-03-01 10:00:00',
    updatedBy: readAuditString(options.sampleData.value.updatedBy, options.sampleData.value.updated_by) || 'System',
    updatedAt: readAuditString(options.sampleData.value.updatedAt, options.sampleData.value.updated_at) || '2026-03-01 12:30:00'
  }))

  const previewObjectName = computed(() => {
    return options.props.objectCode || options.props.layoutName || 'Record'
  })

  const previewRelationGroupScopeId = computed(() => {
    return buildDesignerRelationGroupScopeId({
      mode: options.props.mode,
      layoutId: options.props.layoutId
    })
  })

  const previewPageTitle = computed(() => {
    const fields = previewFieldDefinitions.value || []
    const identifier = fields.find((field) => {
      const candidate = field as unknown as Record<string, unknown>
      return candidate?.isIdentifier || candidate?.is_identifier || candidate?.code === 'name'
    })
    const candidateKeys = [identifier?.code, 'name', 'title', 'code'].filter(Boolean) as string[]

    for (const key of candidateKeys) {
      const value = options.sampleData.value?.[key]
      if (value !== undefined && value !== null && String(value).trim()) {
        return String(value)
      }
    }

    return options.props.layoutName || previewObjectName.value
  })

  return {
    fieldToDesignDisplayField,
    getSampleValue,
    previewFieldDefinitions,
    designerRenderSections,
    designerCanvasSections,
    previewAuditInfo,
    previewObjectName,
    previewRelationGroupScopeId,
    previewPageTitle
  }
}
