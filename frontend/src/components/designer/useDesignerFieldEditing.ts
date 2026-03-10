import type { ComputedRef, Ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { normalizeFieldType } from '@/utils/fieldType'
import { cloneLayoutConfig, generateId } from '@/utils/layoutValidation'
import { getFieldDisabledReason } from '@/platform/layout/designerFieldGuard'
import {
  DESIGNER_COMPONENT_PROP_KEYS,
  setDesignerComponentProp
} from '@/components/designer/designerComponentProps'
import type {
  DesignerConfigNode,
  DesignerFieldDefinition,
  LayoutConfig,
  LayoutField,
  LayoutSection
} from '@/components/designer/designerTypes'

interface UseDesignerFieldEditingOptions {
  mode: string
  layoutConfig: Ref<LayoutConfig>
  layoutMode: Ref<string>
  sampleData: Ref<Record<string, unknown>>
  selectedId: Ref<string>
  selectedSection: Ref<LayoutSection | null>
  elementType: ComputedRef<'field' | 'section' | null>
  fieldProps: Ref<Partial<LayoutField>>
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

export function useDesignerFieldEditing(options: UseDesignerFieldEditingOptions) {
  const clearSelection = () => {
    options.selectedId.value = ''
    options.selectedSection.value = null
  }

  const addSection = () => {
    const newSection: LayoutSection = {
      id: generateId('section'),
      type: 'section',
      title: options.t('system.pageLayout.designer.defaults.newSection'),
      collapsible: true,
      collapsed: false,
      columns: 2,
      border: true,
      fields: []
    }

    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    if (!nextConfig.sections) {
      nextConfig.sections = []
    }

    nextConfig.sections.push(newSection)
    options.commitLayoutChange(nextConfig, 'Add section', previousConfig)
    options.selectedId.value = newSection.id
    options.selectedSection.value = newSection

    if (options.layoutMode.value === 'Compact') {
      const totalFields = (nextConfig.sections || []).reduce((count, section) => {
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
    const firstSection = nextConfig.sections?.[0]
    if (!firstSection) return
    if (!firstSection.fields) {
      firstSection.fields = []
    }

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
      const nextType = normalizeFieldType(value || 'text')
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

    const itemRecord = item as Record<string, unknown>
    if (key === 'fieldType') {
      itemRecord[key] = normalizeFieldType(String(value || 'text'))
    } else if (key === 'span') {
      const columns = options.selectedSection.value ? options.getColumns(options.selectedSection.value) : 2
      itemRecord[key] = Math.max(1, Math.min(columns, Number(value || 1)))
    } else if (key === 'minHeight') {
      options.setLayoutFieldMinHeight(item as LayoutField, value)
    } else if (DESIGNER_COMPONENT_PROP_KEYS.has(key)) {
      setDesignerComponentProp(item as Record<string, unknown>, key, value)
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

  const updateSection = (key: string, value: unknown) => {
    if (!options.selectedId.value || options.elementType.value !== 'section') return

    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    const item = options.findItemById(nextConfig, options.selectedId.value)
    if (!item) return

    const section = item as LayoutSection & { name?: string }
    ;(section as Record<string, unknown>)[key] = value

    if (key === 'type' && value === 'tab') {
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
    }

    options.selectedSection.value = section
    options.commitLayoutChange(nextConfig, `Update section ${key}`, previousConfig)
  }

  const handleSectionPropertyUpdate = (payload: { key: string; value: unknown }) => {
    updateSection(payload.key, payload.value)
  }

  const removeField = (fieldId: string, sectionId: string, _sectionIndex?: number) => {
    const previousConfig = cloneLayoutConfig(options.layoutConfig.value)
    const nextConfig = cloneLayoutConfig(options.layoutConfig.value) as LayoutConfig
    const section = nextConfig.sections?.find((item) => item.id === sectionId)
    if (!section) return

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
    clearSelection()
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
      nextConfig.sections = nextConfig.sections?.filter((section) => section.id !== sectionId) || []
      options.commitLayoutChange(nextConfig, `Delete section ${sectionId}`, previousConfig)
      clearSelection()
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
    handleFieldClick,
    handleFieldPropertyUpdate,
    handleFieldSizeReset,
    handleSectionPropertyUpdate,
    removeField,
    deleteSection,
    toggleSectionCollapse
  }
}
