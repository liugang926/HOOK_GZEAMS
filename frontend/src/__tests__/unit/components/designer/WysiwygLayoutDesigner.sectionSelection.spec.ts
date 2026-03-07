import { describe, it, expect } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { defineComponent, h, nextTick } from 'vue'

const BaseDetailPageStub = defineComponent({
  name: 'BaseDetailPage',
  props: {
    sections: {
      type: Array,
      default: () => []
    }
  },
  emits: ['section-click'],
  setup(props, { emit, slots }) {
    return () => h('div', { class: 'base-detail-page-stub' }, [
      h('button', {
        class: 'emit-section-click',
        onClick: () => emit('section-click', (props.sections as any[])[0]?.name || '')
      }, 'emit'),
      ...((props.sections as any[]) || []).flatMap((section) => {
        const slot = slots[`section-${section.name}`]
        return slot ? slot() : []
      })
    ])
  }
})

const SectionPropertyEditorStub = defineComponent({
  name: 'SectionPropertyEditor',
  props: {
    modelValue: {
      type: Object,
      default: () => ({})
    }
  },
  setup(props) {
    return () => h('div', { class: 'section-property-editor-stub' }, (props.modelValue as any)?.id || '')
  }
})

describe('WysiwygLayoutDesigner section selection bridge', () => {
  it('selects the matching section when BaseDetailPage emits section-click', async () => {
    const i18n = (await import('@/locales')).default
    const WysiwygLayoutDesigner = (await import('@/components/designer/WysiwygLayoutDesigner.vue')).default

    const wrapper = shallowMount(WysiwygLayoutDesigner, {
      props: {
        layoutName: 'Test Layout',
        mode: 'edit',
        layoutConfig: {
          sections: [
            {
              id: 'section-1',
              type: 'section',
              title: 'Basic',
              position: 'main',
              fields: []
            }
          ]
        }
      },
      global: {
        plugins: [i18n],
        stubs: {
          BaseDetailPage: BaseDetailPageStub,
          FieldPropertyEditor: true,
          SectionPropertyEditor: SectionPropertyEditorStub,
          DesignerFieldCard: true,
          'el-button': true,
          'el-button-group': true,
          'el-collapse': true,
          'el-collapse-item': true,
          'el-col': true,
          'el-divider': true,
          'el-empty': true,
          'el-icon': true,
          'el-input': true,
          'el-radio-button': true,
          'el-radio-group': true,
          'el-row': true,
          'el-switch': true,
          'el-tab-pane': true,
          'el-tabs': true,
          'el-tag': true,
          ElMessage: true,
          ElMessageBox: true
        }
      }
    })

    expect(wrapper.find('.designer-section-slot').classes()).not.toContain('is-selected')

    wrapper.getComponent(BaseDetailPageStub).vm.$emit('section-click', 'section-1')
    await nextTick()

    const section = wrapper.get('.designer-section-slot')
    expect(section.attributes('data-section-id')).toBe('section-1')
    expect(wrapper.get('.section-property-editor-stub').text()).toContain('section-1')
  })
})
