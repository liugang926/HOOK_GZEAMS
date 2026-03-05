import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import FieldPropertyEditor from '../FieldPropertyEditor.vue'

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
  'el-select': { name: 'el-select', template: '<div class="el-select-stub"><slot /></div>' },
  'el-option': { name: 'el-option', template: '<div class="el-option-stub"></div>' },
  'el-switch': {
    name: 'el-switch',
    props: ['disabled'],
    template: '<div class="el-switch-stub" :data-disabled="disabled ? \'true\' : \'false\'"></div>'
  },
  'el-input-number': { name: 'el-input-number', template: '<div class="el-input-number-stub"></div>' },
  'el-input': { name: 'el-input', template: '<div class="el-input-stub"></div>' },
  'el-button': {
    name: 'el-button',
    template: '<button class="el-button-stub" @click="$emit(\'click\')"><slot /></button>'
  }
}

describe('FieldPropertyEditor', () => {
  it('renders text validation properties from schema', () => {
    const wrapper = mount(FieldPropertyEditor, {
      props: {
        modelValue: { fieldType: 'text' },
        fieldType: 'text',
        availableSpans: [1, 2],
        availableSpanColumns: 2
      },
      global: { stubs }
    })

    const labels = wrapper.findAll('.form-item-stub').map((node) => node.attributes('data-label'))
    expect(labels).toEqual(expect.arrayContaining(['Field Type', 'Label', 'Min Length', 'Max Length', 'Regex']))
  })

  it('supports legacy aliases and renders rich-text advanced toolbar', () => {
    const wrapper = mount(FieldPropertyEditor, {
      props: {
        modelValue: { fieldType: 'richtext' },
        fieldType: 'richtext',
        availableSpans: [1, 2],
        availableSpanColumns: 2
      },
      global: { stubs }
    })

    const labels = wrapper.findAll('.form-item-stub').map((node) => node.attributes('data-label'))
    expect(labels).toContain('Toolbar')
  })

  it('renders reference lookup compact keys property', () => {
    const wrapper = mount(FieldPropertyEditor, {
      props: {
        modelValue: { fieldType: 'reference' },
        fieldType: 'reference',
        availableSpans: [1, 2],
        availableSpanColumns: 2
      },
      global: { stubs }
    })

    const labels = wrapper.findAll('.form-item-stub').map((node) => node.attributes('data-label'))
    expect(labels).toContain('Lookup Compact Keys')
  })

  it('renders lookup compact keys quick actions and supports select-all', async () => {
    const wrapper = mount(FieldPropertyEditor, {
      props: {
        modelValue: {
          fieldType: 'reference',
          lookupCompactKeys: [],
          lookupColumns: [
            { key: 'name', label: 'Name' },
            { key: 'email', label: 'Email' }
          ]
        },
        fieldType: 'reference',
        availableSpans: [1, 2],
        availableSpanColumns: 2
      },
      global: { stubs }
    })

    const buttons = wrapper.findAll('.el-button-stub')
    const selectAllButton = buttons.find((node) => node.text().includes('Select all'))
    const clearButton = buttons.find((node) => node.text().includes('Clear'))

    expect(selectAllButton).toBeTruthy()
    expect(clearButton).toBeTruthy()

    await selectAllButton!.trigger('click')
    const updateProperty = wrapper.emitted('update-property') || []
    expect(updateProperty[0]?.[0]).toEqual({ key: 'lookupCompactKeys', value: ['name', 'email'] })
  })

  it('emits update-property and update:modelValue when span changes', async () => {
    const wrapper = mount(FieldPropertyEditor, {
      props: {
        modelValue: { fieldType: 'text', label: 'Name', span: 1 },
        fieldType: 'text',
        availableSpans: [1, 2, 3],
        availableSpanColumns: 3
      },
      global: { stubs }
    })

    const selects = wrapper.findAllComponents({ name: 'el-select' })
    expect(selects.length).toBeGreaterThan(1)
    const select = selects[1]

    select.vm.$emit('change', 3)
    await nextTick()

    const updateProperty = wrapper.emitted('update-property')
    const updateModelValue = wrapper.emitted('update:modelValue')

    expect(updateProperty).toBeTruthy()
    expect(updateProperty?.[0]?.[0]).toEqual({ key: 'span', value: 3 })
    expect(updateModelValue).toBeTruthy()
    expect(updateModelValue?.[0]?.[0]).toMatchObject({ span: 3, label: 'Name' })
  })

  it('disables default shortcut pinned switch when showShortcutHelp is false for subtable', () => {
    const wrapper = mount(FieldPropertyEditor, {
      props: {
        modelValue: {
          fieldType: 'subtable',
          showShortcutHelp: false,
          defaultShortcutHelpPinned: true
        },
        fieldType: 'subtable',
        availableSpans: [1, 2],
        availableSpanColumns: 2
      },
      global: { stubs }
    })

    const labels = wrapper.findAll('.form-item-stub').map((node) => node.attributes('data-label'))
    expect(labels).toContain('Show Shortcut Help')
    expect(labels).toContain('Default Shortcut Help Pinned')

    const pinnedWrapper = wrapper.find('[data-testid="field-prop-defaultShortcutHelpPinned"]')
    expect(pinnedWrapper.exists()).toBe(true)
    expect(pinnedWrapper.find('.el-switch-stub').attributes('data-disabled')).toBe('true')
  })
})


