import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DesignerWorkbenchMetadataPanel from '../DesignerWorkbenchMetadataPanel.vue'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string, params?: Record<string, unknown>) => {
      if (key === 'system.pageLayout.designer.workbench.labels.order') {
        return `Order ${params?.index || ''}`.trim()
      }
      return key
    },
  }),
}))

const stubs = {
  'el-button': {
    props: ['disabled', 'size', 'text', 'ariaLabel'],
    emits: ['click'],
    template: `
      <button
        :disabled="disabled"
        :data-testid="$attrs['data-testid']"
        @click="$emit('click')"
      >
        <slot />
      </button>
    `,
  },
  'el-select': {
    props: ['modelValue'],
    emits: ['update:modelValue'],
    template: `
      <select
        :value="modelValue"
        :data-testid="$attrs['data-testid']"
        @change="$emit('update:modelValue', $event.target.value)"
      >
        <slot />
      </select>
    `,
  },
  'el-option': {
    props: ['label', 'value'],
    template: '<option :value="value">{{ label }}</option>',
  },
  'el-icon': {
    template: '<i><slot /></i>',
  },
  ArrowUp: true,
  ArrowDown: true,
}

describe('DesignerWorkbenchMetadataPanel', () => {
  it('hydrates all default summary sections when the payload is partial', () => {
    const wrapper = mount(DesignerWorkbenchMetadataPanel, {
      props: {
        sections: [
          { code: 'workflow', surfacePriority: 'primary' },
        ],
      },
      global: { stubs },
    })

    expect(wrapper.findAll('.designer-workbench-metadata__row')).toHaveLength(4)
  })

  it('emits normalized sections when priority changes', async () => {
    const wrapper = mount(DesignerWorkbenchMetadataPanel, {
      props: {
        sections: [
          { code: 'process_summary', surfacePriority: 'primary' },
          { code: 'record', surfacePriority: 'context' },
          { code: 'workflow', surfacePriority: 'context' },
          { code: 'batch_tools', surfacePriority: 'admin' },
        ],
      },
      global: { stubs },
    })

    await wrapper.get('[data-testid="layout-workbench-priority-record"]').setValue('activity')

    const emitted = wrapper.emitted('update:sections')
    expect(emitted).toBeTruthy()
    expect(emitted?.[0]?.[0]).toEqual([
      { code: 'process_summary', surfacePriority: 'primary' },
      { code: 'record', surfacePriority: 'activity' },
      { code: 'workflow', surfacePriority: 'context' },
      { code: 'batch_tools', surfacePriority: 'admin' },
    ])
  })

  it('reorders sections and emits the updated sequence', async () => {
    const wrapper = mount(DesignerWorkbenchMetadataPanel, {
      props: {
        sections: [
          { code: 'process_summary', surfacePriority: 'primary' },
          { code: 'record', surfacePriority: 'context' },
          { code: 'workflow', surfacePriority: 'context' },
          { code: 'batch_tools', surfacePriority: 'admin' },
        ],
      },
      global: { stubs },
    })

    await wrapper.get('[data-testid="layout-workbench-move-down-process_summary"]').trigger('click')

    const emitted = wrapper.emitted('update:sections')
    expect(emitted).toBeTruthy()
    expect(emitted?.[0]?.[0]).toEqual([
      { code: 'record', surfacePriority: 'context' },
      { code: 'process_summary', surfacePriority: 'primary' },
      { code: 'workflow', surfacePriority: 'context' },
      { code: 'batch_tools', surfacePriority: 'admin' },
    ])
  })
})
