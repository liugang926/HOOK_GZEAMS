import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DesignerFieldCard from '../DesignerFieldCard.vue'

const stubs = {
  FieldRenderer: {
    name: 'FieldRenderer',
    template: '<div class="field-renderer-stub"></div>'
  },
  FieldDisplay: {
    name: 'FieldDisplay',
    template: '<div class="field-display-stub"></div>'
  },
  'el-button': {
    name: 'el-button',
    template: '<button><slot /></button>'
  },
  'el-icon': {
    name: 'el-icon',
    template: '<i><slot /></i>'
  },
  'el-tag': {
    name: 'el-tag',
    template: '<span class="el-tag-stub"><slot /></span>'
  },
  'el-input': {
    name: 'el-input',
    template: '<input class="el-input-stub" />'
  }
}

const baseProps = {
  field: {
    id: 'field_1',
    fieldCode: 'status',
    fieldType: 'text',
    label: 'Status'
  },
  displayField: {
    prop: 'status',
    label: 'Status',
    type: 'text'
  },
  value: 'Draft',
  sectionId: 'section_1',
  sectionIndex: 0
}

describe('DesignerFieldCard', () => {
  it('renders reference fields with a dedicated preview shell', () => {
    const wrapper = mount(DesignerFieldCard, {
      props: {
        ...baseProps,
        field: {
          ...baseProps.field,
          fieldType: 'reference',
          referenceObject: 'Customer',
          placeholder: 'Select customer'
        },
        displayField: {
          ...baseProps.displayField,
          type: 'reference'
        },
        value: { id: 'cust_1', name: 'ACME' }
      },
      global: { stubs }
    })

    expect(wrapper.find('[data-testid="designer-reference-preview"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('ACME')
    expect(wrapper.text()).toContain('Customer')
    expect(wrapper.find('.field-renderer-stub').exists()).toBe(false)
  })

  it('renders related object fields with a table-style fallback preview', () => {
    const wrapper = mount(DesignerFieldCard, {
      props: {
        ...baseProps,
        field: {
          ...baseProps.field,
          fieldType: 'related_object',
          label: 'Orders'
        },
        displayField: {
          ...baseProps.displayField,
          prop: 'orders',
          label: 'Orders',
          type: 'related_object'
        },
        value: null
      },
      global: { stubs }
    })

    expect(wrapper.find('[data-testid="designer-table-preview"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Embedded relation preview')
  })

  it('supports inline label editing with enter confirm and escape cancel', async () => {
    const wrapper = mount(DesignerFieldCard, {
      props: {
        ...baseProps,
        selected: true,
        interactive: true
      },
      global: { stubs }
    })

    await wrapper.find('[data-testid="designer-field-label"]').trigger('dblclick')
    const input = wrapper.find('[data-testid="designer-field-label-input"]')
    expect(input.exists()).toBe(true)

    await input.setValue('Display Name')
    await input.trigger('keydown', { key: 'Enter' })

    expect(wrapper.emitted('labelUpdate')?.[0]).toEqual(['field_1', 'Display Name'])

    await wrapper.setProps({
      field: {
        ...baseProps.field,
        label: 'Status'
      }
    })

    await wrapper.find('[data-testid="designer-field-overlay-label"]').trigger('dblclick')
    const secondInput = wrapper.find('[data-testid="designer-field-label-input"]')
    await secondInput.setValue('Cancelled')
    await secondInput.trigger('keydown', { key: 'Escape' })

    expect(wrapper.find('[data-testid="designer-field-label-input"]').exists()).toBe(false)
    expect((wrapper.emitted('labelUpdate') || [])).toHaveLength(1)
  })
})
