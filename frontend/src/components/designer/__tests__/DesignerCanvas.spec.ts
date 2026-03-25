import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DesignerCanvas from '../DesignerCanvas.vue'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => {
      if (key === 'common.actions.add') return 'Add'
      if (key === 'system.pageLayout.designer.defaults.detailRegion') return 'Detail Region'
      return key
    }
  })
}))

const stubs = {
  'el-button': {
    name: 'el-button',
    template: '<button class="el-button-stub" @click="$emit(\'click\')"><slot /></button>'
  },
  'el-dropdown': {
    name: 'el-dropdown',
    template: '<div class="el-dropdown-stub"><slot /><slot name="dropdown" /></div>'
  },
  'el-dropdown-menu': {
    name: 'el-dropdown-menu',
    template: '<div class="el-dropdown-menu-stub"><slot /></div>'
  },
  'el-dropdown-item': {
    name: 'el-dropdown-item',
    props: ['command'],
    template: '<button class="el-dropdown-item-stub" @click="$emit(\'command\', command)"><slot /></button>'
  },
  'el-icon': {
    name: 'el-icon',
    template: '<i class="el-icon-stub"><slot /></i>'
  },
  Plus: true,
  Grid: true
}

describe('DesignerCanvas', () => {
  it('shows a detail-region add action and emits selected relation code', async () => {
    const wrapper = mount(DesignerCanvas, {
      props: {
        renderMode: 'design',
        layoutMode: 'Detail',
        isDragOverCanvas: false,
        resizeHint: null,
        resizeHintStyle: {},
        detailRegionOptions: [
          { label: 'Pickup Items (pickup_items)', value: 'pickup_items' }
        ]
      },
      slots: {
        default: '<div class="canvas-slot-stub"></div>'
      },
      global: { stubs }
    })

    expect(wrapper.text()).toContain('Add Detail Region')

    const dropdown = wrapper.findComponent({ name: 'el-dropdown' })
    expect(dropdown.exists()).toBe(true)
    dropdown.vm.$emit('command', 'pickup_items')

    expect(wrapper.emitted('addDetailRegion')?.[0]).toEqual(['pickup_items'])
  })
})
