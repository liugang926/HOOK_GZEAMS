import { defineComponent, h, nextTick, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import ErrorBoundary from '@/components/common/ErrorBoundary.vue'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key
  })
}))

describe('ErrorBoundary', () => {
  const globalMountOptions = {
    global: {
      stubs: {
        'el-alert': {
          template: '<div><slot /></div>'
        },
        'el-button': {
          template: '<button><slot /></button>'
        }
      }
    }
  } as const

  it('captures render errors and shows default fallback content', async () => {
    const Broken = defineComponent({
      name: 'BrokenComponent',
      setup() {
        return () => {
          throw new Error('boom')
        }
      }
    })

    const wrapper = mount(ErrorBoundary, {
      ...globalMountOptions,
      slots: {
        default: () => h(Broken)
      }
    })

    await nextTick()

    expect(wrapper.text()).toContain('boom')
    expect(wrapper.text()).toContain('system.fieldDefinition.actions.retry')
  })

  it('allows fallback slot to reset and remount children', async () => {
    const shouldThrow = ref(true)

    const Flaky = defineComponent({
      name: 'FlakyComponent',
      setup() {
        return () => {
          if (shouldThrow.value) {
            throw new Error('temporary-error')
          }
          return h('div', { class: 'recovered-content' }, 'Recovered')
        }
      }
    })

    const wrapper = mount(ErrorBoundary, {
      ...globalMountOptions,
      slots: {
        default: () => h(Flaky),
        fallback: ({ error, reset }: { error: string; reset: () => void }) =>
          h('button', {
            class: 'retry-btn',
            onClick: () => {
              shouldThrow.value = false
              reset()
            }
          }, `retry:${error}`)
      }
    })

    await nextTick()
    expect(wrapper.text()).toContain('temporary-error')

    await wrapper.get('.retry-btn').trigger('click')
    await nextTick()

    expect(wrapper.find('.recovered-content').exists()).toBe(true)
    expect(wrapper.text()).toContain('Recovered')
  })
})
