import { computed, ref } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useDesignerFieldEditing } from '@/components/designer/useDesignerFieldEditing'
import type { LayoutConfig, LayoutField, LayoutSection } from '@/components/designer/designerTypes'
import { ElMessage } from 'element-plus'

vi.mock('element-plus', () => ({
  ElMessage: {
    warning: vi.fn(),
    success: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn(() => Promise.resolve())
  }
}))

describe('useDesignerFieldEditing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renames a field and updates selected field props through history pipeline', () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        {
          id: 'section_1',
          type: 'section',
          title: 'Basic',
          fields: [
            {
              id: 'field_1',
              fieldCode: 'name',
              label: 'Name',
              span: 1,
              fieldType: 'text'
            }
          ]
        }
      ]
    })
    const selectedId = ref('field_1')
    const selectedSection = ref<LayoutSection | null>(layoutConfig.value.sections?.[0] as LayoutSection)
    const fieldProps = ref<Partial<LayoutField>>({ id: 'field_1', label: 'Name' })
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { updateFieldLabel } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'field'),
      fieldProps,
      sectionProps: ref({}),
      detailRegionDefinitions: ref([]),
      activeTabs: ref({}),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => {
        for (const section of config.sections || []) {
          for (const field of section.fields || []) {
            if (field.id === id) return field
          }
        }
        return null
      },
      getColumns: () => 2,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    updateFieldLabel('field_1', 'Customer Name')

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(layoutConfig.value.sections?.[0]?.fields?.[0]?.label).toBe('Customer Name')
    expect(fieldProps.value.label).toBe('Customer Name')
  })

  it('moves a section up and keeps selected section synced with the new layout snapshot', () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        {
          id: 'section_1',
          type: 'section',
          title: 'Basic',
          fields: []
        },
        {
          id: 'section_2',
          type: 'section',
          title: 'Advanced',
          fields: []
        }
      ]
    })
    const selectedId = ref('section_2')
    const selectedSection = ref<LayoutSection | null>(layoutConfig.value.sections?.[1] as LayoutSection)
    const sectionProps = ref<Partial<LayoutSection>>({ title: 'Advanced' })
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { moveSection } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'section'),
      fieldProps: ref({}),
      sectionProps,
      detailRegionDefinitions: ref([]),
      activeTabs: ref({}),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => (config.sections || []).find((section) => section.id === id) || null,
      getColumns: () => 2,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    moveSection('section_2', 'up')

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(layoutConfig.value.sections?.map((section) => section.id)).toEqual(['section_2', 'section_1'])
    expect(selectedSection.value?.id).toBe('section_2')
    expect(selectedSection.value).toBe(layoutConfig.value.sections?.[0])
    expect(sectionProps.value.title).toBe('Advanced')
  })

  it('moves a section to an explicit target index and keeps selection synced', () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        {
          id: 'section_1',
          type: 'section',
          title: 'Basic',
          fields: []
        },
        {
          id: 'section_2',
          type: 'detail-region',
          title: 'Pickup Items'
        },
        {
          id: 'section_3',
          type: 'section',
          title: 'Audit',
          fields: []
        }
      ]
    })
    const selectedId = ref('section_2')
    const selectedSection = ref<LayoutSection | null>(layoutConfig.value.sections?.[1] as LayoutSection)
    const sectionProps = ref<Partial<LayoutSection>>({ title: 'Pickup Items' })
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { moveSectionToIndex } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'section'),
      fieldProps: ref({}),
      sectionProps,
      detailRegionDefinitions: ref([]),
      activeTabs: ref({}),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => (config.sections || []).find((section) => section.id === id) || null,
      getColumns: () => 2,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    moveSectionToIndex('section_2', { insertIndex: 3 })

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(layoutConfig.value.sections?.map((section) => section.id)).toEqual(['section_1', 'section_3', 'section_2'])
    expect(selectedSection.value?.id).toBe('section_2')
    expect(selectedSection.value).toBe(layoutConfig.value.sections?.[2])
    expect(sectionProps.value.title).toBe('Pickup Items')
  })

  it('renames a section through the history pipeline', () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        {
          id: 'section_1',
          type: 'section',
          title: 'Basic',
          fields: []
        }
      ]
    })
    const selectedId = ref('section_1')
    const selectedSection = ref<LayoutSection | null>(layoutConfig.value.sections?.[0] as LayoutSection)
    const sectionProps = ref<Partial<LayoutSection>>({ title: 'Basic' })
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { updateSectionTitle } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'section'),
      fieldProps: ref({}),
      sectionProps,
      detailRegionDefinitions: ref([]),
      activeTabs: ref({}),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => (config.sections || []).find((section) => section.id === id) || null,
      getColumns: () => 2,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    updateSectionTitle('section_1', 'Overview')

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(layoutConfig.value.sections?.[0]?.title).toBe('Overview')
    expect(selectedSection.value).toBe(layoutConfig.value.sections?.[0])
    expect(sectionProps.value.title).toBe('Overview')
  })

  it('applies a section property batch as a single history commit', () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        {
          id: 'detail_region_1',
          type: 'detail-region',
          title: 'Pickup Items',
          relationCode: 'pickup_items',
          fieldCode: 'items',
          position: 'main',
          detailEditMode: 'inline_table'
        }
      ]
    })
    const selectedId = ref('detail_region_1')
    const selectedSection = ref<LayoutSection | null>(layoutConfig.value.sections?.[0] as LayoutSection)
    const sectionProps = ref<Partial<LayoutSection>>({
      id: 'detail_region_1',
      relationCode: 'pickup_items',
      fieldCode: 'items',
      position: 'main',
      detailEditMode: 'inline_table'
    })
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { handleSectionPropertyBatchUpdate } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'section'),
      fieldProps: ref({}),
      sectionProps,
      detailRegionDefinitions: ref([]),
      activeTabs: ref({}),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => (config.sections || []).find((section) => section.id === id) || null,
      getColumns: () => 1,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    handleSectionPropertyBatchUpdate({
      position: 'sidebar',
      detailEditMode: 'readonly_table',
      toolbarConfig: {},
      relatedFields: [
        { code: 'asset', label: 'Asset', fieldType: 'reference' },
        { code: 'status', label: 'Status', fieldType: 'select' }
      ]
    })

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(layoutConfig.value.sections?.[0]).toMatchObject({
      position: 'sidebar',
      detailEditMode: 'readonly_table',
      toolbarConfig: {},
      relatedFields: [
        { code: 'asset', label: 'Asset', fieldType: 'reference' },
        { code: 'status', label: 'Status', fieldType: 'select' }
      ]
    })
    expect(sectionProps.value).toMatchObject({
      position: 'sidebar',
      detailEditMode: 'readonly_table'
    })
  })

  it('deletes the selected section and focuses the next available section', async () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        {
          id: 'section_1',
          type: 'section',
          title: 'Basic',
          fields: []
        },
        {
          id: 'section_2',
          type: 'section',
          title: 'Advanced',
          fields: []
        },
        {
          id: 'section_3',
          type: 'section',
          title: 'Audit',
          fields: []
        }
      ]
    })
    const selectedId = ref('section_2')
    const selectedSection = ref<LayoutSection | null>(layoutConfig.value.sections?.[1] as LayoutSection)
    const fieldProps = ref<Partial<LayoutField>>({ id: 'field_legacy', label: 'Legacy' })
    const sectionProps = ref<Partial<LayoutSection>>({ title: 'Advanced' })
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { deleteSection } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'section'),
      fieldProps,
      sectionProps,
      detailRegionDefinitions: ref([]),
      activeTabs: ref({}),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => (config.sections || []).find((section) => section.id === id) || null,
      getColumns: () => 2,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    await deleteSection('section_2')

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(layoutConfig.value.sections?.map((section) => section.id)).toEqual(['section_1', 'section_3'])
    expect(selectedId.value).toBe('section_3')
    expect(selectedSection.value).toBe(layoutConfig.value.sections?.[1])
    expect(fieldProps.value).toEqual({})
    expect(sectionProps.value.title).toBe('Audit')
  })

  it('deletes the selected field and falls back to the parent section', () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        {
          id: 'section_1',
          type: 'section',
          title: 'Basic',
          fields: [
            {
              id: 'field_1',
              fieldCode: 'name',
              label: 'Name',
              span: 1,
              fieldType: 'text'
            },
            {
              id: 'field_2',
              fieldCode: 'status',
              label: 'Status',
              span: 1,
              fieldType: 'text'
            }
          ]
        }
      ]
    })
    const selectedId = ref('field_1')
    const selectedSection = ref<LayoutSection | null>(layoutConfig.value.sections?.[0] as LayoutSection)
    const fieldProps = ref<Partial<LayoutField>>({ id: 'field_1', label: 'Name' })
    const sectionProps = ref<Partial<LayoutSection>>({})
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { removeField } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'field'),
      fieldProps,
      sectionProps,
      detailRegionDefinitions: ref([]),
      activeTabs: ref({}),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => {
        for (const section of config.sections || []) {
          if (section.id === id) return section
          for (const field of section.fields || []) {
            if (field.id === id) return field
          }
        }
        return null
      },
      getColumns: () => 2,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    removeField('field_1', 'section_1')

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(layoutConfig.value.sections?.[0]?.fields?.map((field) => field.id)).toEqual(['field_2'])
    expect(selectedId.value).toBe('section_1')
    expect(selectedSection.value).toBe(layoutConfig.value.sections?.[0])
    expect(fieldProps.value).toEqual({})
    expect(sectionProps.value.title).toBe('Basic')
  })

  it('hydrates detail-region metadata when selecting a master-detail relation', () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        {
          id: 'section_detail',
          type: 'detail-region',
          title: 'Old Detail Region'
        }
      ]
    })
    const selectedId = ref('section_detail')
    const selectedSection = ref<LayoutSection | null>(layoutConfig.value.sections?.[0] as LayoutSection)
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { handleSectionPropertyUpdate } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'section'),
      fieldProps: ref({}),
      sectionProps: ref({}),
      detailRegionDefinitions: ref([
        {
          relationCode: 'pickup_items',
          fieldCode: 'items',
          title: '领用明细',
          titleEn: 'Pickup Items',
          titleI18n: {
            'zh-CN': '领用明细',
            'en-US': 'Pickup Items'
          },
          translationKey: 'objects.PickupItem.region',
          targetObjectCode: 'PickupItem',
          detailEditMode: 'readonly_table',
          toolbarConfig: { add: false },
          summaryRules: [{ field: 'quantity', aggregate: 'sum' }],
          validationRules: [{ rule: 'required' }]
        }
      ]),
      activeTabs: ref({}),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => (config.sections || []).find((section) => section.id === id) || null,
      getColumns: () => 1,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    handleSectionPropertyUpdate({ key: 'relationCode', value: 'pickup_items' })

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(layoutConfig.value.sections?.[0]).toMatchObject({
      relationCode: 'pickup_items',
      relation_code: 'pickup_items',
      fieldCode: 'items',
      field_code: 'items',
      targetObjectCode: 'PickupItem',
      target_object_code: 'PickupItem',
      detailEditMode: 'readonly_table',
      detail_edit_mode: 'readonly_table',
      translationKey: 'objects.PickupItem.region',
      translation_key: 'objects.PickupItem.region',
      title: '领用明细',
      titleEn: 'Pickup Items',
      title_i18n: {
        'zh-CN': '领用明细',
        'en-US': 'Pickup Items'
      }
    })
  })

  it('adds a new detail-region section directly from aggregate metadata', () => {
    const layoutConfig = ref<LayoutConfig>({ sections: [] })
    const selectedId = ref('')
    const selectedSection = ref<LayoutSection | null>(null)
    const sectionProps = ref<Partial<LayoutSection>>({})
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { addDetailRegion } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'section'),
      fieldProps: ref({}),
      sectionProps,
      detailRegionDefinitions: ref([
        {
          relationCode: 'pickup_items',
          fieldCode: 'items',
          title: '棰嗙敤鏄庣粏',
          titleEn: 'Pickup Items',
          titleI18n: {
            'zh-CN': '棰嗙敤鏄庣粏',
            'en-US': 'Pickup Items'
          },
          targetObjectCode: 'PickupItem',
          detailEditMode: 'inline_table'
        }
      ]),
      activeTabs: ref({}),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => (config.sections || []).find((section) => section.id === id) || null,
      getColumns: () => 1,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    addDetailRegion('pickup_items')

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(layoutConfig.value.sections).toHaveLength(1)
    expect(layoutConfig.value.sections?.[0]).toMatchObject({
      type: 'detail-region',
      relationCode: 'pickup_items',
      fieldCode: 'items',
      targetObjectCode: 'PickupItem'
    })
    expect(selectedId.value).toBe(layoutConfig.value.sections?.[0]?.id)
    expect(sectionProps.value.relationCode).toBe('pickup_items')
  })

  it('applies detail-region template presets on top of aggregate metadata defaults', () => {
    const layoutConfig = ref<LayoutConfig>({ sections: [] })
    const selectedId = ref('')
    const selectedSection = ref<LayoutSection | null>(null)
    const sectionProps = ref<Partial<LayoutSection>>({})
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { addDetailRegion } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'section'),
      fieldProps: ref({}),
      sectionProps,
      detailRegionDefinitions: ref([
        {
          relationCode: 'pickup_items',
          fieldCode: 'items',
          title: 'Pickup Items',
          titleEn: 'Pickup Items',
          targetObjectCode: 'PickupItem',
          detailEditMode: 'inline_table',
          toolbarConfig: { add: true, import: true },
          summaryRules: [{ field: 'quantity', aggregate: 'sum' }],
          validationRules: [{ rule: 'required' }],
          lookupColumns: [{ key: 'asset', label: 'Asset' }],
          relatedFields: [{ code: 'quantity', label: 'Quantity', fieldType: 'number' }]
        }
      ]),
      activeTabs: ref({}),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => (config.sections || []).find((section) => section.id === id) || null,
      getColumns: () => 1,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    addDetailRegion({
      templateCode: 'pickup_items:readonly',
      relationCode: 'pickup_items',
      fieldCode: 'items',
      title: 'Pickup Items',
      targetObjectCode: 'PickupItem',
      targetObjectLabel: 'Pickup Item',
      preset: {
        position: 'sidebar',
        collapsible: false,
        collapsed: false,
        detailEditMode: 'readonly_table',
        toolbarConfig: { add: false, import: false },
        summaryRules: [{ field: 'quantity', aggregate: 'count' }],
        validationRules: [{ rule: 'readonly' }],
        lookupColumns: [{ key: 'asset', label: 'Asset Name', minWidth: 200 }],
        relatedFields: [{ code: 'remark', label: 'Remark', fieldType: 'textarea' }]
      }
    })

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(layoutConfig.value.sections?.[0]).toMatchObject({
      type: 'detail-region',
      relationCode: 'pickup_items',
      detailEditMode: 'readonly_table',
      position: 'sidebar',
      collapsible: false,
      toolbarConfig: { add: false, import: false },
      summaryRules: [{ field: 'quantity', aggregate: 'count' }],
      validationRules: [{ rule: 'readonly' }],
      lookupColumns: [{ key: 'asset', label: 'Asset Name', minWidth: 200 }],
      relatedFields: [{ code: 'remark', label: 'Remark', fieldType: 'textarea' }]
    })
    expect(sectionProps.value.detailEditMode).toBe('readonly_table')
    expect(sectionProps.value.position).toBe('sidebar')
  })

  it('adds a tab section template with default tab metadata', () => {
    const layoutConfig = ref<LayoutConfig>({ sections: [] })
    const selectedId = ref('')
    const selectedSection = ref<LayoutSection | null>(null)
    const sectionProps = ref<Partial<LayoutSection>>({})
    const activeTabs = ref<Record<string, string>>({})
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { addSectionTemplate } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'section'),
      fieldProps: ref({}),
      sectionProps,
      detailRegionDefinitions: ref([]),
      activeTabs,
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => (config.sections || []).find((section) => section.id === id) || null,
      getColumns: () => 2,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    addSectionTemplate('tab')

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(layoutConfig.value.sections?.[0]).toMatchObject({
      type: 'tab',
      tabs: [
        {
          title: 'system.pageLayout.designer.defaults.newTab'
        }
      ]
    })
    expect(activeTabs.value[layoutConfig.value.sections?.[0]?.id || '']).toBe(
      layoutConfig.value.sections?.[0]?.tabs?.[0]?.id
    )
  })

  it('applies preset layout metadata when adding a sidebar section template', () => {
    const layoutConfig = ref<LayoutConfig>({ sections: [] })
    const selectedId = ref('')
    const selectedSection = ref<LayoutSection | null>(null)
    const sectionProps = ref<Partial<LayoutSection>>({})
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { addSectionTemplate } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'section'),
      fieldProps: ref({}),
      sectionProps,
      detailRegionDefinitions: ref([]),
      activeTabs: ref({}),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => (config.sections || []).find((section) => section.id === id) || null,
      getColumns: () => 1,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    addSectionTemplate({
      templateCode: 'section-sidebar',
      templateType: 'section',
      title: 'Sidebar Summary',
      description: 'One-column sidebar summary',
      icon: 'section',
      preset: {
        position: 'sidebar',
        columns: 1,
        collapsible: false,
        border: false,
        labelPosition: 'top'
      }
    })

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(layoutConfig.value.sections?.[0]).toMatchObject({
      type: 'section',
      position: 'sidebar',
      columns: 1,
      collapsible: false,
      border: false,
      labelPosition: 'top'
    })
    expect(sectionProps.value.position).toBe('sidebar')
  })

  it('inserts a detail-region section at the requested section index', () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        {
          id: 'section_1',
          type: 'section',
          title: 'Basic',
          fields: []
        },
        {
          id: 'section_2',
          type: 'section',
          title: 'Audit',
          fields: []
        }
      ]
    })
    const selectedId = ref('')
    const selectedSection = ref<LayoutSection | null>(null)
    const sectionProps = ref<Partial<LayoutSection>>({})
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { addDetailRegion } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'section'),
      fieldProps: ref({}),
      sectionProps,
      detailRegionDefinitions: ref([
        {
          relationCode: 'pickup_items',
          fieldCode: 'items',
          title: '妫板棛鏁ら弰搴ｇ矎',
          titleEn: 'Pickup Items',
          targetObjectCode: 'PickupItem',
          detailEditMode: 'inline_table'
        }
      ]),
      activeTabs: ref({}),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => (config.sections || []).find((section) => section.id === id) || null,
      getColumns: () => 1,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    addDetailRegion('pickup_items', { insertIndex: 1 })

    expect(commitLayoutChange).toHaveBeenCalledTimes(1)
    expect(layoutConfig.value.sections?.map((section) => section.type)).toEqual([
      'section',
      'detail-region',
      'section'
    ])
    expect(layoutConfig.value.sections?.[1]).toMatchObject({
      relationCode: 'pickup_items',
      fieldCode: 'items'
    })
  })

  it('prevents adding the same detail-region twice and focuses the existing section', () => {
    const layoutConfig = ref<LayoutConfig>({
      sections: [
        {
          id: 'detail_1',
          type: 'detail-region',
          relationCode: 'pickup_items',
          fieldCode: 'items',
          title: '棰嗙敤鏄庣粏'
        }
      ]
    })
    const selectedId = ref('')
    const selectedSection = ref<LayoutSection | null>(null)
    const sectionProps = ref<Partial<LayoutSection>>({})
    const commitLayoutChange = vi.fn((next: LayoutConfig) => {
      layoutConfig.value = next
    })

    const { addDetailRegion } = useDesignerFieldEditing({
      mode: 'edit',
      layoutConfig,
      layoutMode: ref('Detail'),
      sampleData: ref({}),
      selectedId,
      selectedSection,
      elementType: computed(() => 'section'),
      fieldProps: ref({}),
      sectionProps,
      detailRegionDefinitions: ref([
        {
          relationCode: 'pickup_items',
          fieldCode: 'items',
          title: '棰嗙敤鏄庣粏',
          titleEn: 'Pickup Items',
          targetObjectCode: 'PickupItem',
          detailEditMode: 'inline_table'
        }
      ]),
      activeTabs: ref({}),
      canAddField: () => true,
      notifyUnsupportedField: vi.fn(),
      isFieldAdded: () => false,
      buildLayoutField: vi.fn(),
      getSampleValue: vi.fn(),
      commitLayoutChange,
      findItemById: (config, id) => (config.sections || []).find((section) => section.id === id) || null,
      getColumns: () => 1,
      setLayoutFieldMinHeight: vi.fn(),
      showPropertySizeFeedback: vi.fn(),
      t: (key: string) => key
    })

    addDetailRegion('pickup_items')

    expect(commitLayoutChange).not.toHaveBeenCalled()
    expect(selectedId.value).toBe('detail_1')
    expect(selectedSection.value?.id).toBe('detail_1')
    expect(sectionProps.value.relationCode).toBe('pickup_items')
    expect(ElMessage.warning).toHaveBeenCalledWith('system.pageLayout.designer.messages.fieldAlreadyAdded')
  })
})
