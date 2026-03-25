/* eslint-disable vue/one-component-per-file */
import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent } from 'vue'
import ElementPlus from 'element-plus'

vi.mock('@/components/engine/FieldRenderer.vue', () => ({
  default: defineComponent({
    name: 'FieldRenderer',
    props: {
      modelValue: { type: [String, Number, Boolean, Array, Object, null], default: null }
    },
    emits: ['update:modelValue'],
    template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target && $event.target.value)" />'
  })
}))

const buildRows = (size: number) => {
  return Array.from({ length: size }).map((_, index) => ({
    line_no: index + 1,
    item_code: `ITEM-${index + 1}`,
    qty: index + 1
  }))
}

describe('SubTableField pagination', () => {
  it('renders paged rows instead of mounting all 200 rows at once', async () => {
    vi.resetModules()
    const SubTableField = (await import('@/components/engine/fields/SubTableField.vue')).default
    const rows = buildRows(200)
    const field = {
      code: 'items',
      name: 'Items',
      relatedFields: [
        { code: 'line_no', name: 'Line No', fieldType: 'number' },
        { code: 'item_code', name: 'Item Code', fieldType: 'text' },
        { code: 'qty', name: 'Qty', fieldType: 'number' }
      ]
    }

    const wrapper = mount(SubTableField, {
      props: {
        modelValue: rows,
        field,
        readonly: false,
        disabled: false
      },
      global: {
        plugins: [ElementPlus],
        mocks: {
          $t: (key: string) => key
        }
      }
    })

    await flushPromises()
    await new Promise((resolve) => setTimeout(resolve, 100))

    const renderedRows = wrapper.findAll('.el-table__row').length
    expect(renderedRows).toBeGreaterThan(0)
    expect(renderedRows).toBeLessThan(200)
    expect(wrapper.find('.el-pagination').exists()).toBe(true)
  })
})

