import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { describe, expect, it, vi } from 'vitest'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key
  })
}))

vi.mock('@/components/common/FieldDisplay.vue', () => ({
  default: defineComponent({
    name: 'FieldDisplayStub',
    props: {
      field: {
        type: Object,
        required: true
      },
      value: {
        type: null,
        required: false,
        default: undefined
      }
    },
    setup(props) {
      return () => h('div', {
        class: 'field-display-stub',
        'data-field-type': (props.field as Record<string, any>).fieldType || (props.field as Record<string, any>).type,
        'data-object-code': (props.field as Record<string, any>).referenceObject || '',
        'data-value': JSON.stringify(props.value ?? null)
      })
    }
  })
}))

describe('FieldRenderer reference rendering', () => {
  it('delegates table-mode reference fields to FieldDisplay', async () => {
    const FieldRenderer = (await import('@/components/common/FieldRenderer.vue')).default

    const wrapper = mount(FieldRenderer, {
      props: {
        field: {
          prop: 'department',
          label: 'Department',
          type: 'department',
          fieldType: 'department',
          referenceObject: 'Department',
          referenceDisplayField: 'name'
        },
        modelValue: {
          id: 'dept-1',
          name: 'Finance'
        },
        mode: 'table'
      },
      global: {
        stubs: {
          'el-input': true,
          'el-input-number': true,
          'el-option': true,
          'el-select': true,
          'el-date-picker': true,
          'el-button': true,
          'el-tag': true,
          'el-icon': true,
          'el-progress': true
        }
      }
    })

    const stub = wrapper.get('.field-display-stub')
    expect(stub.attributes('data-field-type')).toBe('department')
    expect(stub.attributes('data-object-code')).toBe('Department')
    expect(stub.attributes('data-value')).toBe(JSON.stringify({
      id: 'dept-1',
      name: 'Finance'
    }))
  })
})
