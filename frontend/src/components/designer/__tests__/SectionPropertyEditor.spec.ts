import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import SectionPropertyEditor from '../SectionPropertyEditor.vue'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key
  })
}))

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
  'el-radio-group': { name: 'el-radio-group', template: '<div class="el-radio-group-stub"><slot /></div>' },
  'el-radio-button': { name: 'el-radio-button', template: '<button class="el-radio-button-stub"><slot /></button>' },
  'el-input': { name: 'el-input', template: '<div class="el-input-stub"></div>' },
  'el-button': { name: 'el-button', template: '<button class="el-button-stub"><slot /></button>' }
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

  it('preserves earlier changes when multiple section properties update quickly', async () => {
    const wrapper = mount(SectionPropertyEditor, {
      props: {
        modelValue: {
          type: 'section',
          title: 'Basic',
          columns: 2,
          collapsible: false,
          collapsed: false
        },
        sectionType: 'section'
      },
      global: { stubs }
    })

    const columnsItem = wrapper.findAll('.form-item-stub').find((node) => node.attributes('data-label') === 'Columns')
    const collapsibleItem = wrapper.findAll('.form-item-stub').find((node) => node.attributes('data-label') === 'Collapsible')

    expect(columnsItem).toBeTruthy()
    expect(collapsibleItem).toBeTruthy()

    columnsItem!.findComponent({ name: 'el-radio-group' }).vm.$emit('change', 1)
    await nextTick()
    collapsibleItem!.findComponent({ name: 'el-switch' }).vm.$emit('change', true)
    await nextTick()

    const emittedModelValues = wrapper.emitted('update:modelValue') || []
    expect(emittedModelValues.at(-1)?.[0]).toMatchObject({
      columns: 1,
      collapsible: true
    })
  })
})
