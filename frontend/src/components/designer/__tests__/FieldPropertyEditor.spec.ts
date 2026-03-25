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
  'el-collapse': { name: 'el-collapse', template: '<div><slot /></div>' },
  'el-collapse-item': { name: 'el-collapse-item', template: '<div><slot /></div>' },
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

  it('hides unsupported common properties for subtable fields', () => {
    const wrapper = mount(FieldPropertyEditor, {
      props: {
        modelValue: {
          fieldType: 'subtable'
        },
        fieldType: 'subtable',
        availableSpans: [1, 2],
        availableSpanColumns: 2
      },
      global: { stubs }
    })

    const labels = wrapper.findAll('.form-item-stub').map((node) => node.attributes('data-label'))
    expect(labels).not.toContain('Placeholder')
    expect(labels).not.toContain('Default Value')
    expect(labels).not.toContain('Visibility Rule')
  })

  it('locks readonly switch for system fields', () => {
    const wrapper = mount(FieldPropertyEditor, {
      props: {
        modelValue: {
          fieldType: 'text',
          isSystem: true,
          readonly: true
        },
        fieldType: 'text',
        availableSpans: [1, 2],
        availableSpanColumns: 2
      },
      global: { stubs }
    })

    const readonlyWrapper = wrapper.find('[data-testid="field-prop-readonly"]')
    expect(readonlyWrapper.exists()).toBe(true)
    expect(readonlyWrapper.find('.el-switch-stub').attributes('data-disabled')).toBe('true')
    expect(wrapper.text()).toContain('System fields stay readonly in the layout designer.')
  })

  it('renders visibility rule editor and emits structured rule payload', async () => {
    const wrapper = mount(FieldPropertyEditor, {
      props: {
        modelValue: {
          fieldType: 'text'
        },
        fieldType: 'text',
        availableSpans: [1, 2],
        availableSpanColumns: 2,
        visibilityFieldOptions: [
          { label: 'Status', value: 'status' }
        ]
      },
      global: { stubs }
    })

    const labels = wrapper.findAll('.form-item-stub').map((node) => node.attributes('data-label'))
    expect(labels).toContain('Visibility Rule')

    const visibilityEditor = wrapper.find('[data-testid="field-prop-visibilityRule"]')
    const selects = visibilityEditor.findAllComponents({ name: 'el-select' })
    selects[0].vm.$emit('change', 'status')
    await nextTick()
    selects[1].vm.$emit('change', 'in')
    await nextTick()

    const input = visibilityEditor.findComponent({ name: 'el-input' })
    input.vm.$emit('input', 'draft, published')
    await nextTick()

    const updateProperty = wrapper.emitted('update-property') || []
    expect(updateProperty.at(-1)?.[0]).toEqual({
      key: 'visibilityRule',
      value: {
        field: 'status',
        operator: 'in',
        value: ['draft', 'published']
      }
    })
  })

  it('uses schema-provided select options for related object display mode', async () => {
    const wrapper = mount(FieldPropertyEditor, {
      props: {
        modelValue: {
          fieldType: 'related_object',
          displayMode: 'inline_readonly'
        },
        fieldType: 'related_object',
        availableSpans: [1, 2],
        availableSpanColumns: 2
      },
      global: { stubs }
    })

    const labels = wrapper.findAll('.form-item-stub').map((node) => node.attributes('data-label'))
    expect(labels).toContain('Display Mode')

    const displayModeWrapper = wrapper.find('[data-testid="field-prop-displayMode"]')
    const select = displayModeWrapper.findComponent({ name: 'el-select' })
    select.vm.$emit('change', 'inline_editable')
    await nextTick()

    const updateProperty = wrapper.emitted('update-property') || []
    expect(updateProperty.at(-1)?.[0]).toEqual({
      key: 'displayMode',
      value: 'inline_editable'
    })
  })

  it('renders lookup columns config for reference fields', () => {
    const wrapper = mount(FieldPropertyEditor, {
      props: {
        modelValue: {
          fieldType: 'reference'
        },
        fieldType: 'reference',
        availableSpans: [1, 2],
        availableSpanColumns: 2
      },
      global: { stubs }
    })

    const labels = wrapper.findAll('.form-item-stub').map((node) => node.attributes('data-label'))
    expect(labels).toContain('Lookup Columns')
  })

  it('emits related fields config updates for subtable fields', async () => {
    const wrapper = mount(FieldPropertyEditor, {
      props: {
        modelValue: {
          fieldType: 'subtable'
        },
        fieldType: 'subtable',
        availableSpans: [1, 2],
        availableSpanColumns: 2
      },
      global: { stubs }
    })

    const relatedFieldsWrapper = wrapper.find('[data-testid="field-prop-relatedFields"]')
    const input = relatedFieldsWrapper.findComponent({ name: 'el-input' })
    input.vm.$emit('input', JSON.stringify([{ code: 'amount', label: 'Amount', fieldType: 'number' }]))
    await nextTick()

    const updateProperty = wrapper.emitted('update-property') || []
    expect(updateProperty.at(-1)?.[0]).toEqual({
      key: 'relatedFields',
      value: [{ code: 'amount', label: 'Amount', fieldType: 'number' }]
    })
  })

  it('preserves earlier changes when multiple field properties update quickly', async () => {
    const wrapper = mount(FieldPropertyEditor, {
      props: {
        modelValue: {
          fieldType: 'text',
          label: 'Name',
          required: false
        },
        fieldType: 'text',
        availableSpans: [1, 2],
        availableSpanColumns: 2
      },
      global: { stubs }
    })

    const labelItem = wrapper.findAll('.form-item-stub').find((node) => node.attributes('data-label') === 'Label')
    const requiredItem = wrapper.findAll('.form-item-stub').find((node) => node.attributes('data-label') === 'Required')

    expect(labelItem).toBeTruthy()
    expect(requiredItem).toBeTruthy()

    labelItem!.findComponent({ name: 'el-input' }).vm.$emit('input', 'Customer Name')
    await nextTick()
    requiredItem!.findComponent({ name: 'el-switch' }).vm.$emit('change', true)
    await nextTick()

    const emittedModelValues = wrapper.emitted('update:modelValue') || []
    expect(emittedModelValues.at(-1)?.[0]).toMatchObject({
      label: 'Customer Name',
      required: true
    })
  })
})


