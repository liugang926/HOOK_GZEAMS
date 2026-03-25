import type { ComputedRef, Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { normalizeFieldType } from '@/utils/fieldType'
import { cloneLayoutConfig, generateId } from '@/utils/layoutValidation'
import { getFieldDisabledReason } from '@/platform/layout/designerFieldGuard'
import {
  applyDetailRegionPreset,
  applyDetailRegionDefinition,
  clearDetailRegionSelection
} from '@/components/designer/detailRegionMetadata'
import {
  DESIGNER_COMPONENT_PROP_KEYS,
  setDesignerComponentProp
} from '@/components/designer/designerComponentProps'
import type {
  DesignerConfigNode,
  DesignerDetailRegionOption,
  DesignerFieldDefinition,
  DesignerSectionTemplateOption,
  DesignerSectionTemplatePreset,
  LayoutConfig,
  LayoutField,
  LayoutSection,
  SectionTemplateType
} from '@/components/designer/designerTypes'
import type { RuntimeAggregateDetailRegion } from '@/types/runtime'

interface UseDesignerFieldEditingOptions {
  mode: string
  layoutConfig: Ref<LayoutConfig>
  layoutMode: Ref<string>
  sampleData: Ref<Record<string, unknown>>
  selectedId: Ref<string>
  selectedSection: Ref<LayoutSection | null>
  elementType: ComputedRef<'field' | 'section' | null>
  fieldProps: Ref<Partial<LayoutField>>
  sectionProps: Ref<Partial<LayoutSection>>
  detailRegionDefinitions: Ref<RuntimeAggregateDetailRegion[]>
  activeTabs: Ref<Record<string, string>>
  canAddField: (field: DesignerFieldDefinition) => boolean
  notifyUnsupportedField: (field: DesignerFieldDefinition) => void
  isFieldAdded: (code: string) => boolean
  buildLayoutField: (field: DesignerFieldDefinition) => LayoutField
  getSampleValue: (field: LayoutField) => unknown
  commitLayoutChange: (nextConfig: LayoutConfig, description: string, previousConfig?: LayoutConfig) => void
  findItemById: (config: LayoutConfig, id: string) => DesignerConfigNode | null
  getColumns: (section: Partial<LayoutSection> | null | undefined) => number
  setLayoutFieldMinHeight: (field: LayoutField, value: unknown) => void
  showPropertySizeFeedback: (fieldId: string) => Promise<void> | void
  t: (key: string, params?: Record<string, unknown> | string) => string
}

interface DetailRegionInsertOptions {
  insertIndex?: number | null
}

interface SectionMoveOptions {
  insertIndex?: number | null
}

interface SectionTemplateInsertOptions {
  insertIndex?: number | null
}

export function useDesignerFieldEditing(options: UseDesignerFieldEditingOptions) {
  const findDetailRegionDefinition = (relationCode: string): RuntimeAggregateDetailRegion | null => {
    const nextCode = String(relationCode || '').trim()
    if (!nextCode) return null
    return options.detailRegionDefinitions.value.find((region) => region.relationCode === nextCode) || null
  }

  const findExistingDetailRegionSection = (
    sections: LayoutSection[] | undefined,
    relationCode: string,
    fieldCode: string
  ): LayoutSection | null => {
    const nextRelationCode = String(relationCode || '').trim()
    const nextFieldCode = String(fieldCode || '').trim()
    for (const section of sections || []) {
      if (String(section?.type || '') !== 'detail-region') continue
      const sectionRelationCode = String(section?.relationCode || section?.relation_code || '').trim()
      const sectionFieldCode = String(section?.fieldCode || section?.field_code || '').trim()
      if (nextRelationCode && sectionRelationCode === nextRelationCode) return section
      if (nextFieldCode && sectionFieldCode === nextFieldCode) return section
    }
    return null
  }

  const buildStandardSection = (): LayoutSection => ({
    id: generateId('section'),
    type: 'section',
    title: options.t('system.pageLayout.designer.defaults.newSection'),
    collapsible: true,
    collapsed: false,
    columns: 2,
    border: true,
    fields: []
  })

  const buildTabbedSection = (): LayoutSection => {
    const tabId = generateId('tab')
    return {
      id: generateId('section'),
      type: 'tab',
      title: options.t('system.pageLayout.designer.sectionProperties.options.types.tab'),
      collapsible: true,
      collapsed: false,
      columns: 2,
      border: true,
      tabs: [
        {
          id: tabId,
          name: tabId,
          title: options.t('system.pageLayout.designer.defaults.newTab'),
          fields: []
        }
      ]
    }
  }

  const buildCollapseSection = (): LayoutSection => ({
    id: generateId('section'),
    type: 'collapse',
    title: options.t('system.pageLayout.designer.sectionProperties.options.types.collapse'),
    collapsible: true,
    collapsed: false,
    columns: 2,
    border: true,
    items: [
      {
        id: generateId('collapse'),
        title: options.t('system.pageLayout.designer.defaults.basicInformation'),
        fields: []
      }
    ]
  })

  const applySectionTemplatePreset = (
    section: LayoutSection,
    preset?: DesignerSectionTemplatePreset | null
  ): LayoutSection => {
    if (!preset) return section

    if (preset.position) {
      section.position = preset.position
    }
    if (typeof preset.columns === 'number') {
      section.columns = preset.columns
    }
    if (typeof preset.collapsible === 'boolean') {
      section.collapsible = preset.collapsible
    }
    if (typeof preset.collapsed === 'boolean') {
      section.collapsed = preset.collapsed
    }
    if (typeof preset.border === 'boolean') {
      section.border = preset.border
    }
    if (preset.labelPosition) {
      section.labelPosition = preset.labelPosition
    }

    return section
  }

  const normalizeSectionTemplate = (
    template?: SectionTemplateType | DesignerSectionTemplateOption
  ): DesignerSectionTemplateOption => {
    if (template && typeof template === 'object') {
      return template
    }

    const templateType: SectionTemplateType =
      template === 'tab' || template === 'collapse' ? template : 'section'

    if (templateType === 'tab') {
      return {
        templateCode: 'tab-main',
        templateType: 'tab',
        title: options.t('system.pageLayout.designer.templates.tabMain.title'),
        description: options.t('system.pageLayout.designer.templates.tabMain.description'),
        icon: 'tab',
        preset: {
          position: 'main',
          columns: 2,
          collapsible: false,
          collapsed: false
        }
      }
    }

    if (templateType === 'collapse') {
      return {
        templateCode: 'collapse-main',
        templateType: 'collapse',
        title: options.t('system.pageLayout.designer.templates.collapseMain.title'),
        description: options.t('system.pageLayout.designer.templates.collapseMain.description'),
        icon: 'collapse',
        preset: {
          position: 'main',
          columns: 2,
          collapsible: true,
          collapsed: false
        }
      }
    }

    return {
      templateCode: 'section-main',
      templateType: 'section',
      title: options.t('system.pageLayout.designer.templates.sectionMain.title'),
      description: options.t('system.pageLayout.designer.templates.sectionMain.description'),
      icon: 'section',
      preset: {
        position: 'main',
        columns: 2,
        collapsible: true,
        collapsed: false,
        border: true
      }
    }
  }

  const clearSelection = () => {
    options.selectedId.value = ''
    options.selectedSection.value = null
    options.fieldProps.value = {}
    options.sectionProps.value = {}
  }

  const selectSectionFallback = (section: LayoutSection | null) => {
    if (!section) {
      clearSelection()
      return
    }

    options.selectedId.value = section.id
    options.selectedSection.value = section
    options.fieldProps.value = {}
    options.sectionProps.value = {
      ...section
    }
  }

  const addSection = () => {
    addSectionTemplate('section')

    if (options.layoutMode.value === 'Compact') {
      const totalFields = (options.layoutConfig.value.sections || []).reduce((count, section) => {
        const sectionFields = section.fields?.length || 0
        const tabFields = (section.tabs || []).reduce((tabCount, tab) => tabCount + (tab.fields?.length || 0), 0)
        const collapseFields = (section.items || []).reduce((itemCount, item) => itemCount + (item.fields?.length || 0), 0)
        return count + sectionFields + tabFields + collapseFields
      }, 0)
      if (totalFields > 10) {
        ElMessage.warning(
          options.t(
            'system.pageLayout.designer.messages.compactFieldLimit',
            'Compact layouts work best with 10 or fewer fields.'
          )
        )
      }
    }
  }

  const addSectionTemplate = (
    template: SectionTemplateType | DesignerSectionTemplateOption = 'section',
    insertOptions?: SectionTemplateInsertOptions
  ) => {
    const normalizedTemplate = normalizeSectionTemplate(template)
    const normalizedType: SectionTemplateType = normalizedTemplate.templateType

    const newSection = applySectionTemplatePreset(
      normalizedType === 'tab'
        ? buildTabbedSection()
        : normalizedType === 'collapse'
          ? buildCollapseSection()
          : buildStandardSection(),
      normalizedTemplate.preset
    )

    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    if (!nextConfig.sections) {
      nextConfig.sections = []
    }

    const requestedIndex = Number(insertOptions?.insertIndex)
    const insertIndex = Number.isFinite(requestedIndex)
      ? Math.max(0, Math.min(nextConfig.sections.length, requestedIndex))
      : nextConfig.sections.length
    nextConfig.sections.splice(insertIndex, 0, newSection)

    if (normalizedType === 'tab' && Array.isArray(newSection.tabs) && newSection.tabs[0]?.id) {
      options.activeTabs.value[newSection.id] = newSection.tabs[0].id
    }

    options.commitLayoutChange(
      nextConfig,
      `${options.t('system.pageLayout.designer.actions.addSection')} ${normalizedTemplate.title}`,
      previousConfig
    )
    options.selectedId.value = newSection.id
    options.selectedSection.value = newSection
    options.fieldProps.value = {}
    options.sectionProps.value = { ...newSection }
  }

  const addDetailRegion = (
    detailRegionInput?: string | DesignerDetailRegionOption,
    insertOptions?: DetailRegionInsertOptions
  ) => {
    const detailRegionOption =
      detailRegionInput && typeof detailRegionInput === 'object' ? detailRegionInput : null
    const detailRegionCode =
      typeof detailRegionInput === 'string'
        ? detailRegionInput
        : detailRegionOption?.relationCode

    const detailRegion =
      (detailRegionCode ? findDetailRegionDefinition(detailRegionCode) : null) ||
      options.detailRegionDefinitions.value[0] ||
      null

    if (!detailRegion) {
      return
    }

    const detailFieldCode = String(detailRegion.fieldCode || '').trim()
    const existingSection = findExistingDetailRegionSection(
      options.layoutConfig.value.sections,
      detailRegion.relationCode,
      detailFieldCode
    )
    if (existingSection) {
      options.selectedId.value = existingSection.id
      options.selectedSection.value = existingSection
      options.fieldProps.value = {}
      options.sectionProps.value = { ...existingSection }
      ElMessage.warning(options.t('system.pageLayout.designer.messages.fieldAlreadyAdded'))
      return
    }

    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    const newSection: LayoutSection = {
      id: generateId('section'),
      type: 'detail-region',
      title: options.t('system.pageLayout.designer.defaults.detailRegion'),
      collapsible: true,
      collapsed: false,
      columns: 1,
      position: 'main'
    }

    applyDetailRegionDefinition(newSection, detailRegion)
    applyDetailRegionPreset(newSection, detailRegionOption)

    if (!nextConfig.sections) {
      nextConfig.sections = []
    }
    const requestedIndex = Number(insertOptions?.insertIndex)
    const insertIndex = Number.isFinite(requestedIndex)
      ? Math.max(0, Math.min(nextConfig.sections.length, requestedIndex))
      : nextConfig.sections.length
    nextConfig.sections.splice(insertIndex, 0, newSection)

    if (detailFieldCode && options.sampleData.value[detailFieldCode] === undefined) {
      options.sampleData.value[detailFieldCode] = []
    }

    options.commitLayoutChange(
      nextConfig,
      `${options.t('system.pageLayout.designer.actions.addSection')} ${newSection.title || detailRegion.relationCode}`,
      previousConfig
    )
    options.selectedId.value = newSection.id
    options.selectedSection.value = newSection
    options.fieldProps.value = {}
    options.sectionProps.value = { ...newSection }
  }

  const handleFieldClick = (field: DesignerFieldDefinition) => {
    if (!options.canAddField(field)) {
      options.notifyUnsupportedField(field)
      return
    }

    if (!options.layoutConfig.value.sections || options.layoutConfig.value.sections.length === 0) {
      addSection()
    }

    if (options.isFieldAdded(field.code)) {
      ElMessage.warning(options.t('system.pageLayout.designer.messages.fieldAlreadyAdded'))
      return
    }

    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    let firstSection = nextConfig.sections?.find((section) => {
      const type = String(section?.type || 'section')
      return type !== 'tab' && type !== 'collapse' && type !== 'detail-region'
    })
    if (!firstSection) {
      firstSection = buildStandardSection()
      nextConfig.sections = [...(nextConfig.sections || []), firstSection]
    }
    if (!firstSection.fields) firstSection.fields = []

    const newField = options.buildLayoutField(field)
    firstSection.fields.push(newField)
    if (newField.fieldCode && options.sampleData.value[newField.fieldCode] === undefined) {
      options.sampleData.value[newField.fieldCode] = options.getSampleValue(newField)
    }
    options.commitLayoutChange(nextConfig, `Add field ${field.code}`, previousConfig)
  }

  const updateField = (key: string, value: unknown) => {
    if (!options.selectedId.value || options.elementType.value !== 'field') return

    if (key === 'fieldType') {
      const nextType = normalizeFieldType(String(value || 'text'))
      const reason = getFieldDisabledReason(nextType, options.mode as any)
      if (reason) {
        ElMessage.warning(
          options.t('system.pageLayout.designer.messages.cannotSwitchFieldType', { reason })
        )
        const current = options.findItemById(options.layoutConfig.value, options.selectedId.value)
        if (current) {
          options.fieldProps.value = {
            ...options.fieldProps.value,
            fieldType: normalizeFieldType((current as LayoutField).fieldType || 'text')
          }
        }
        return
      }
    }

    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    const item = options.findItemById(nextConfig, options.selectedId.value)
    if (!item) return

    const itemRecord = item as unknown as Record<string, unknown>
    if (key === 'fieldType') {
      itemRecord[key] = normalizeFieldType(String(value || 'text'))
    } else if (key === 'visibilityRule') {
      if (value && typeof value === 'object') {
        itemRecord.visibilityRule = value
        itemRecord.visibility_rule = value
      } else {
        delete itemRecord.visibilityRule
        delete itemRecord.visibility_rule
      }
    } else if (key === 'span') {
      const columns = options.selectedSection.value ? options.getColumns(options.selectedSection.value) : 2
      itemRecord[key] = Math.max(1, Math.min(columns, Number(value || 1)))
    } else if (key === 'minHeight') {
      options.setLayoutFieldMinHeight(item as LayoutField, value)
    } else if (DESIGNER_COMPONENT_PROP_KEYS.has(key)) {
      setDesignerComponentProp(item as unknown as Record<string, unknown>, key, value)
    } else {
      itemRecord[key] = value
    }

    options.commitLayoutChange(nextConfig, `Update field ${key}`, previousConfig)
    if (key === 'span' || key === 'minHeight') {
      void options.showPropertySizeFeedback(options.selectedId.value)
    }
  }

  const handleFieldPropertyUpdate = (payload: { key: string; value: unknown }) => {
    updateField(payload.key, payload.value)
  }

  const updateFieldLabel = (fieldId: string, label: string) => {
    const nextLabel = String(label || '').trim()
    if (!fieldId || !nextLabel) return

    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    const item = options.findItemById(nextConfig, fieldId)
    if (!item || !('fieldCode' in item)) return

    const field = item as LayoutField
    if (field.label === nextLabel) return

    field.label = nextLabel
    options.commitLayoutChange(nextConfig, `Rename field ${field.fieldCode || fieldId}`, previousConfig)

    if (options.selectedId.value === fieldId) {
      options.fieldProps.value = {
        ...options.fieldProps.value,
        label: nextLabel
      }
    }
  }

  const updateSectionTitle = (sectionId: string, title: string) => {
    const nextTitle = String(title || '').trim()
    if (!sectionId || !nextTitle) return

    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    const item = options.findItemById(nextConfig, sectionId)
    if (!item || 'fieldCode' in item) return

    const section = item as LayoutSection
    if (section.title === nextTitle) return

    section.title = nextTitle
    options.commitLayoutChange(nextConfig, `Rename section ${sectionId}`, previousConfig)

    if (options.selectedId.value === sectionId) {
      options.selectedSection.value = section
      options.sectionProps.value = {
        ...options.sectionProps.value,
        title: nextTitle
      }
    }
  }

  const handleFieldSizeReset = (fieldId: string) => {
    if (!fieldId) return
    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    const item = options.findItemById(nextConfig, fieldId)
    if (!item || !('fieldCode' in item)) return

    const field = item as LayoutField
    field.span = 1
    options.setLayoutFieldMinHeight(field, undefined)
    options.commitLayoutChange(nextConfig, `Reset field size ${field.fieldCode || fieldId}`, previousConfig)

    if (options.selectedId.value === fieldId) {
      options.fieldProps.value = {
        ...options.fieldProps.value,
        span: 1,
        minHeight: undefined
      }
    }
    void options.showPropertySizeFeedback(fieldId)
  }

  const applySectionPropertyMutation = (
    section: LayoutSection & { name?: string },
    key: string,
    value: unknown
  ) => {
    (section as unknown as Record<string, unknown>)[key] = value

    if (section.type === 'detail-region' && key === 'relationCode') {
      const relationCode = String(value || '').trim()
      if (!relationCode) {
        clearDetailRegionSelection(section)
      } else {
        const detailRegion = findDetailRegionDefinition(relationCode)
        if (detailRegion) {
          applyDetailRegionDefinition(section, detailRegion)
          const detailFieldCode = String(section.fieldCode || section.field_code || '').trim()
          if (detailFieldCode && options.sampleData.value[detailFieldCode] === undefined) {
            options.sampleData.value[detailFieldCode] = []
          }
        } else {
          section.relationCode = relationCode
          section.relation_code = relationCode
        }
      }
    }

    if (key === 'type' && value === 'detail-region') {
      delete section.tabs
      delete section.items
      delete section.fields
      section.columns = 1
      section.collapsible = section.collapsible !== false
      section.collapsed = section.collapsed === true
      if (!section.title) {
        section.title = options.t('system.pageLayout.designer.defaults.detailRegion')
      }
      if (!section.detailEditMode && !section.detail_edit_mode) {
        section.detailEditMode = 'inline_table'
        section.detail_edit_mode = 'inline_table'
      }
      if (!section.relationCode && !section.relation_code && options.detailRegionDefinitions.value.length > 0) {
        applyDetailRegionDefinition(section, options.detailRegionDefinitions.value[0])
      }
      const detailFieldCode = String(section.fieldCode || section.field_code || '').trim()
      if (detailFieldCode && options.sampleData.value[detailFieldCode] === undefined) {
        options.sampleData.value[detailFieldCode] = []
      }
    }

    if (key === 'type' && value === 'tab') {
      delete section.items
      delete section.relationCode
      delete section.relation_code
      delete section.fieldCode
      delete section.field_code
      delete section.targetObjectCode
      delete section.target_object_code
      delete section.detailEditMode
      delete section.detail_edit_mode
      delete section.toolbarConfig
      delete section.toolbar_config
      delete section.summaryRules
      delete section.summary_rules
      delete section.validationRules
      delete section.validation_rules
      delete section.lookupColumns
      delete section.lookup_columns
      delete section.relatedFields
      delete section.related_fields
      if (!Array.isArray(section.tabs) || section.tabs.length === 0) {
        const tabId = `tab_${Date.now()}`
        section.tabs = [
          {
            id: tabId,
            title: options.t('system.pageLayout.designer.defaults.tabTitle', { index: 1 }),
            name: tabId,
            fields: []
          }
        ]
        options.activeTabs.value[section.id] = tabId
      }
      delete section.fields
      if (!Number.isFinite(Number(section.columns)) || Number(section.columns) <= 0) {
        section.columns = 2
      }
    }

    if (key === 'type' && value === 'collapse') {
      delete section.tabs
      delete section.relationCode
      delete section.relation_code
      delete section.fieldCode
      delete section.field_code
      delete section.targetObjectCode
      delete section.target_object_code
      delete section.detailEditMode
      delete section.detail_edit_mode
      delete section.toolbarConfig
      delete section.toolbar_config
      delete section.summaryRules
      delete section.summary_rules
      delete section.validationRules
      delete section.validation_rules
      delete section.lookupColumns
      delete section.lookup_columns
      delete section.relatedFields
      delete section.related_fields
      if (!Array.isArray(section.items) || section.items.length === 0) {
        section.items = [
          {
            id: `collapse_${Date.now()}`,
            title: options.t('system.pageLayout.designer.defaults.basicInformation'),
            fields: []
          }
        ]
      }
      delete section.fields
      if (!Number.isFinite(Number(section.columns)) || Number(section.columns) <= 0) {
        section.columns = 2
      }
    }

    if (key === 'type' && value === 'section') {
      delete section.tabs
      delete section.items
      delete section.relationCode
      delete section.relation_code
      delete section.fieldCode
      delete section.field_code
      delete section.targetObjectCode
      delete section.target_object_code
      delete section.detailEditMode
      delete section.detail_edit_mode
      delete section.toolbarConfig
      delete section.toolbar_config
      delete section.summaryRules
      delete section.summary_rules
      delete section.validationRules
      delete section.validation_rules
      delete section.lookupColumns
      delete section.lookup_columns
      delete section.relatedFields
      delete section.related_fields
      if (!Array.isArray(section.fields)) {
        section.fields = []
      }
      if (!Number.isFinite(Number(section.columns)) || Number(section.columns) <= 0) {
        section.columns = 2
      }
    }
  }

  const updateSectionBatch = (patch: Record<string, unknown>, description?: string) => {
    if (!options.selectedId.value || options.elementType.value !== 'section') return
    if (!patch || typeof patch !== 'object' || Object.keys(patch).length === 0) return

    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    const item = options.findItemById(nextConfig, options.selectedId.value)
    if (!item) return

    const section = item as LayoutSection & { name?: string }
    const orderedEntries = Object.entries(patch).sort(([leftKey], [rightKey]) => {
      const priority = (key: string) => {
        if (key === 'type') return 0
        if (key === 'relationCode') return 1
        return 2
      }
      return priority(leftKey) - priority(rightKey)
    })

    orderedEntries.forEach(([key, value]) => {
      applySectionPropertyMutation(section, key, value)
    })

    options.selectedSection.value = section
    options.sectionProps.value = {
      ...options.sectionProps.value,
      ...patch
    }
    options.commitLayoutChange(
      nextConfig,
      description || `Update section ${orderedEntries.map(([key]) => key).join(', ')}`,
      previousConfig
    )
  }

  const updateSection = (key: string, value: unknown) => {
    updateSectionBatch({ [key]: value }, `Update section ${key}`)
  }

  const handleSectionPropertyUpdate = (payload: { key: string; value: unknown }) => {
    updateSection(payload.key, payload.value)
  }

  const handleSectionPropertyBatchUpdate = (payload: Record<string, unknown>) => {
    updateSectionBatch(payload)
  }

  const moveSection = (sectionId: string, direction: 'up' | 'down') => {
    if (!sectionId) return

    const currentSections = options.layoutConfig.value.sections || []
    const currentIndex = currentSections.findIndex((section) => section.id === sectionId)
    if (currentIndex === -1) return

    const insertIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 2
    if (direction === 'up' && insertIndex < 0) return
    if (direction === 'down' && insertIndex > currentSections.length) return

    moveSectionToIndex(sectionId, { insertIndex })
  }

  const moveSectionToIndex = (sectionId: string, moveOptions?: SectionMoveOptions) => {
    if (!sectionId) return

    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    const sections = nextConfig.sections || []
    const currentIndex = sections.findIndex((section) => section.id === sectionId)
    if (currentIndex === -1) return

    const [movedSection] = sections.splice(currentIndex, 1)
    const requestedIndex = Number(moveOptions?.insertIndex)
    const normalizedIndex = Number.isFinite(requestedIndex)
      ? Math.max(0, Math.min(sections.length, requestedIndex - (currentIndex < requestedIndex ? 1 : 0)))
      : sections.length

    sections.splice(normalizedIndex, 0, movedSection)
    nextConfig.sections = sections

    const resultingIndex = sections.findIndex((section) => section.id === sectionId)
    if (resultingIndex === currentIndex) {
      return
    }

    if (options.selectedSection.value?.id === sectionId) {
      options.selectedSection.value = movedSection
      if (options.selectedId.value === sectionId) {
        options.sectionProps.value = {
          ...options.sectionProps.value,
          ...movedSection
        }
      }
    }

    options.commitLayoutChange(
      nextConfig,
      `Move section ${movedSection.title || sectionId} to position ${resultingIndex + 1}`,
      previousConfig
    )
  }

  const removeField = (fieldId: string, sectionId: string, _sectionIndex?: number) => {
    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    const section = nextConfig.sections?.find((item) => item.id === sectionId)
    if (!section) return
    const shouldRelocateSelection = options.selectedId.value === fieldId

    if (section.type === 'tab') {
      for (const tab of section.tabs || []) {
        tab.fields = tab.fields?.filter((field) => field.id !== fieldId) || []
      }
    } else if (section.type === 'collapse') {
      for (const item of section.items || []) {
        item.fields = item.fields?.filter((field) => field.id !== fieldId) || []
      }
    } else {
      section.fields = section.fields?.filter((field) => field.id !== fieldId) || []
    }

    options.commitLayoutChange(nextConfig, `Remove field ${fieldId}`, previousConfig)
    if (shouldRelocateSelection) {
      selectSectionFallback(section)
    }
  }

  const deleteSection = async (sectionId: string) => {
    try {
      await ElMessageBox.confirm(
        options.t('system.pageLayout.designer.messages.deleteSectionConfirm'),
        options.t('system.pageLayout.designer.messages.deleteSectionTitle'),
        { type: 'warning' }
      )

      const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
      const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
      const sections = nextConfig.sections || []
      const sectionIndex = sections.findIndex((section) => section.id === sectionId)
      if (sectionIndex === -1) return

      const shouldRelocateSelection = options.selectedSection.value?.id === sectionId
      sections.splice(sectionIndex, 1)
      nextConfig.sections = sections
      options.commitLayoutChange(nextConfig, `Delete section ${sectionId}`, previousConfig)

      if (shouldRelocateSelection) {
        const fallbackSection = sections[sectionIndex] || sections[sectionIndex - 1] || null
        selectSectionFallback(fallbackSection)
      }

      ElMessage.success(options.t('system.pageLayout.designer.messages.sectionDeleted'))
    } catch {
      return
    }
  }

  const toggleSectionCollapse = (sectionId: string) => {
    const section = options.findItemById(options.layoutConfig.value, sectionId)
    if (section && 'collapsible' in section && section.collapsible !== undefined) {
      (section as LayoutSection).collapsed = !(section as LayoutSection).collapsed
    }
  }

  return {
    addSection,
    addSectionTemplate,
    addDetailRegion,
    handleFieldClick,
    handleFieldPropertyUpdate,
    updateFieldLabel,
    updateSectionTitle,
    handleFieldSizeReset,
    handleSectionPropertyUpdate,
    handleSectionPropertyBatchUpdate,
    moveSection,
    moveSectionToIndex,
    removeField,
    deleteSection,
    toggleSectionCollapse
  }
}
