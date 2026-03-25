import { computed, ref, watch, type ComputedRef, type Ref } from 'vue'
import { normalizeFieldType } from '@/utils/fieldType'
import { resolveTranslatableText } from '@/utils/localeText'
import { resolveDesignerFieldProps } from '@/components/designer/designerComponentProps'
import type {
  DesignerAnyRecord,
  DesignerConfigNode,
  LayoutField,
  LayoutSection
} from '@/components/designer/designerTypes'

interface UseDesignerSelectionOptions {
  layoutConfig: Ref<{ sections?: LayoutSection[] }>
  selectedId: Ref<string>
  selectedSection: Ref<LayoutSection | null>
  isDesignMode: ComputedRef<boolean>
  locale: Ref<string>
  clearPropertySizeFeedback: (clearHint?: boolean) => void
  findItemById: (config: { sections?: LayoutSection[] }, id: string) => DesignerConfigNode | null
  getColumns: (section: Partial<LayoutSection> | null | undefined) => number
  resolveLayoutFieldMinHeight: (field: LayoutField | null | undefined) => number | undefined
}

export function useDesignerSelection(options: UseDesignerSelectionOptions) {
  const fieldProps = ref<Partial<LayoutField>>({})
  const sectionProps = ref<Partial<LayoutSection>>({})

  const selectedItem = computed<DesignerConfigNode | null>(() => {
    if (!options.selectedId.value) return null
    return options.findItemById(options.layoutConfig.value, options.selectedId.value)
  })

  const elementType = computed<'field' | 'section' | null>(() => {
    if (!selectedItem.value) return null
    if ('fieldCode' in selectedItem.value) return 'field'
    return 'section'
  })

  const availableSpanColumns = computed(() => {
    return options.selectedSection.value ? options.getColumns(options.selectedSection.value) : 2
  })

  const availableSpans = computed(() => {
    const columns = availableSpanColumns.value
    return Array.from({ length: columns }, (_, index) => index + 1)
  })

  function selectField(field: LayoutField, section: LayoutSection) {
    options.selectedId.value = field.id
    options.selectedSection.value = section
    fieldProps.value = {
      ...field,
      minHeight: options.resolveLayoutFieldMinHeight(field)
    }
  }

  function maybeSelectField(field: LayoutField, section: LayoutSection) {
    if (!options.isDesignMode.value) return
    selectField(field, section)
  }

  function selectSection(id: string) {
    options.selectedId.value = id
    const section = options.findItemById(options.layoutConfig.value, id) as LayoutSection | null
    options.selectedSection.value = section
    sectionProps.value = section ? { ...section } : {}
  }

  function maybeSelectSection(id: string) {
    if (!options.isDesignMode.value) return
    selectSection(id)
  }

  function deselect() {
    options.clearPropertySizeFeedback()
    options.selectedId.value = ''
    options.selectedSection.value = null
    fieldProps.value = {}
    sectionProps.value = {}
  }

  watch([options.selectedId, options.locale], () => {
    const item = selectedItem.value
    if (!item) {
      fieldProps.value = {}
      sectionProps.value = {}
      return
    }

    if (elementType.value === 'field') {
      const field = item as LayoutField
      const nextFieldProps: DesignerAnyRecord = {
        ...field,
        fieldType: normalizeFieldType(field.fieldType || field.field_type || 'text'),
        minHeight: options.resolveLayoutFieldMinHeight(field)
      }
      Object.assign(nextFieldProps, resolveDesignerFieldProps(field as unknown as Record<string, unknown>))
      fieldProps.value = nextFieldProps
      return
    }

    const section = { ...(item as unknown as Record<string, unknown>) }
    if ('title' in section) {
      section.title = resolveTranslatableText(buildSectionTitlePayload(section), options.locale.value as 'zh-CN' | 'en-US')
    }
    if (Array.isArray(section.tabs)) {
      section.tabs = section.tabs.map((tab: any) => ({
        ...tab,
        title: resolveTranslatableText(tab?.title, options.locale.value as 'zh-CN' | 'en-US') || String(tab?.name || tab?.id || '')
      }))
    }
    sectionProps.value = section as Partial<LayoutSection>
  }, { immediate: true })

  return {
    fieldProps,
    sectionProps,
    selectedItem,
    elementType,
    availableSpanColumns,
    availableSpans,
    selectField,
    maybeSelectField,
    selectSection,
    maybeSelectSection,
    deselect
  }
}
  const buildSectionTitlePayload = (section: Record<string, unknown>) => {
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
