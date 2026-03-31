import { defineComponent, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import i18n from '@/locales'
import { useDesignerPreview } from '@/components/designer/useDesignerPreview'

const mountHarness = (sections: Array<Record<string, any>>) => {
  const Harness = defineComponent({
    setup() {
      const { designerCanvasSections } = useDesignerPreview({
        props: {
          objectCode: 'Asset',
          layoutName: 'Asset Layout',
          layoutId: 'layout_asset_test',
          mode: 'readonly'
        },
        availableFields: ref([]),
        layoutConfig: ref({ sections }) as any,
        sampleData: ref({}),
        readComponentProps: () => ({}),
        readLayoutPlacement: () => null,
        resolveLayoutFieldMinHeight: () => 1,
        getRenderColumns: () => 2
      })

      return {
        designerCanvasSections
      }
    },
    template: '<div />'
  })

  return mount(Harness, {
    global: {
      plugins: [i18n]
    }
  })
}

describe('useDesignerPreview', () => {
  it('injects slot placeholder fields so canvas sections are not filtered out by BaseDetailPage', () => {
    const wrapper = mountHarness([
      {
        id: 'section_basic',
        type: 'section',
        title: 'Basic Information',
        fields: [
          {
            id: 'field_name',
            fieldCode: 'name',
            label: 'Name',
            fieldType: 'text',
            span: 1
          }
        ]
      },
      {
        id: 'section_tabs',
        type: 'tab',
        title: 'More Info',
        tabs: [
          {
            id: 'tab_1',
            title: 'Primary',
            fields: [
              {
                id: 'field_status',
                fieldCode: 'status',
                label: 'Status',
                fieldType: 'text',
                span: 1
              }
            ]
          }
        ]
      }
    ])

    const sections = (wrapper.vm as any).designerCanvasSections as Array<Record<string, any>>

    expect(sections).toHaveLength(2)
    expect(sections[0].fields).toEqual([
      expect.objectContaining({
        prop: '__designer_section_slot__section_basic',
        type: 'slot',
        visible: true
      })
    ])
    expect(sections[1].tabs).toEqual([
      expect.objectContaining({
        id: 'tab_1',
        fields: [
          expect.objectContaining({
            prop: '__designer_section_slot__section_tabs_tab_1',
            type: 'slot',
            visible: true
          })
        ]
      })
    ])
  })
})
