import { computed, ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import { useDesignerFieldEditing } from '@/components/designer/useDesignerFieldEditing'
import type { LayoutConfig, LayoutField, LayoutSection } from '@/components/designer/designerTypes'

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
})
