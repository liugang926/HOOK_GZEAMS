import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import BaseFormPage from '@/components/common/BaseFormPage.vue'

const ClickableButtonStub = defineComponent({
  emits: ['click'],
  template: '<button @click="$emit(\'click\')"><slot /></button>',
})

describe('BaseFormPage', () => {
  it('renders header, aside, and default footer actions', async () => {
    const wrapper = mount(BaseFormPage, {
      props: {
        panelKicker: 'Edit',
        panelTitle: 'Asset Form',
        panelDescription: 'Update asset data',
        summaryBadge: 'Edit',
        summaryText: 'All required fields are ready',
        cancelLabel: 'Cancel',
        submitLabel: 'Save',
      },
      slots: {
        default: '<div class="form-content">Form Content</div>',
        aside: '<div class="aside-content">Aside Content</div>',
      },
      global: {
        stubs: {
          'el-button': ClickableButtonStub,
        },
      },
    })

    expect(wrapper.text()).toContain('Asset Form')
    expect(wrapper.text()).toContain('Update asset data')
    expect(wrapper.text()).toContain('Form Content')
    expect(wrapper.text()).toContain('Aside Content')
    expect(wrapper.text()).toContain('All required fields are ready')

    const buttons = wrapper.findAll('button')
    await buttons[0].trigger('click')
    await buttons[1].trigger('click')

    expect(wrapper.emitted('cancel')).toHaveLength(1)
    expect(wrapper.emitted('submit')).toHaveLength(1)
  })

  it('uses custom summary and actions slots when provided', async () => {
    const wrapper = mount(BaseFormPage, {
      props: {
        showFooter: true,
        cancelVisible: false,
        submitVisible: false,
      },
      slots: {
        default: '<div>Form Content</div>',
        summary: '<div class="custom-summary">Custom Summary</div>',
        actions: '<button class="custom-action">Publish</button>',
      },
      global: {
        stubs: {
          'el-button': ClickableButtonStub,
        },
      },
    })

    expect(wrapper.find('.custom-summary').exists()).toBe(true)
    expect(wrapper.find('.custom-action').exists()).toBe(true)
    expect(wrapper.findAll('button')).toHaveLength(1)
  })
})
