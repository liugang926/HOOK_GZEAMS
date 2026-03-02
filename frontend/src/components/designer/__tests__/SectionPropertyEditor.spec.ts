import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import SectionPropertyEditor from '../SectionPropertyEditor.vue'

const stubs = {
  'el-form': { name: 'el-form', template: '<form><slot /></form>' },
  'el-divider': { name: 'el-divider', template: '<hr />' },
  'el-form-item': {
    name: 'el-form-item',
    props: ['label'],
    template: '<div class="form-item-stub" :data-label="label"><slot /></div>'
  },
  'el-switch': { name: 'el-switch', template: '<div class="el-switch-stub"></div>' },
  'el-select': { name: 'el-select', template: '<div class="el-select-stub"><slot /></div>' },
  'el-option': { name: 'el-option', template: '<div class="el-option-stub"></div>' },
  'el-input': { name: 'el-input', template: '<div class="el-input-stub"></div>' }
}

describe('SectionPropertyEditor', () => {
  it('renders core section properties from schema', () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: { type: 'section', title: 'Basic', columns: 2 },
        sectionType: 'section'
      },
      global: { stubs }
    })

    const labels = wrapper.findAll('.form-item-stub').map((node) => node.attributes('data-label'))
    expect(labels).toEqual(expect.arrayContaining(['Title', 'Columns', 'Border', 'Collapsible']))
  })

  it('hides section-only properties for tab section type', () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: { type: 'tab', title: 'Tab Group' },
        sectionType: 'tab'
      },
      global: { stubs }
    })

    const labels = wrapper.findAll('.form-item-stub').map((node) => node.attributes('data-label'))
    expect(labels).toContain('Title')
    expect(labels).not.toContain('Border')
  })

  it('emits update events when section property changes', async () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: { type: 'section', title: 'Old Title' },
        sectionType: 'section'
      },
      global: { stubs }
    })

    const input = wrapper.findComponent({ name: 'el-input' })
    expect(input.exists()).toBe(true)

    input.vm.$emit('input', 'New Title')
    await nextTick()

    const emitted = wrapper.emitted('update-property')
    expect(emitted).toBeTruthy()
    expect(emitted?.[0]?.[0]).toEqual({ key: 'title', value: 'New Title' })
  })
})
