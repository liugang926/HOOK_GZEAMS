import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import FieldErrorFallback from '../FieldErrorFallback.vue'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key
  })
}))

describe('FieldErrorFallback', () => {
  const globalMountOptions = {
    global: {
      stubs: {
        'el-tooltip': { template: '<div><slot /></div>' },
        'el-icon': { template: '<span class="icon"><slot /></span>' },
        'el-button': {
          template: '<button class="retry-btn" @click="$attrs.onClick?.()"><slot /></button>',
          inheritAttrs: false
        },
        WarningFilled: { template: '<i />' }
      }
    }
  } as const

  it('renders field label and load-failed message', () => {
    const wrapper = mount(FieldErrorFallback, {
      ...globalMountOptions,
      props: { fieldLabel: 'Asset Name' }
    })

    expect(wrapper.text()).toContain('Asset Name')
    expect(wrapper.text()).toContain('common.messages.loadFailed')
  })

  it('shows retry button with correct i18n key', () => {
    const wrapper = mount(FieldErrorFallback, {
      ...globalMountOptions,
      props: { fieldLabel: 'Status' }
    })

    expect(wrapper.text()).toContain('system.fieldDefinition.actions.retry')
  })

  it('renders the error fallback container', () => {
    const wrapper = mount(FieldErrorFallback, {
      ...globalMountOptions,
      props: { fieldLabel: 'Category' }
    })

    expect(wrapper.find('.field-error-fallback').exists()).toBe(true)
    expect(wrapper.find('.field-error-fallback__icon').exists()).toBe(true)
    expect(wrapper.find('.field-error-fallback__msg').exists()).toBe(true)
  })

  it('renders gracefully without fieldLabel prop', () => {
    const wrapper = mount(FieldErrorFallback, {
      ...globalMountOptions
    })

    expect(wrapper.find('.field-error-fallback').exists()).toBe(true)
    expect(wrapper.text()).toContain('common.messages.loadFailed')
  })
})
