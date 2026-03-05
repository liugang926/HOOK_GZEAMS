import { defineComponent, nextTick, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'
import { useHotkey, useHotkeyContext } from '@/composables/useHotkeys'

const dispatchCtrlS = (target: EventTarget = window) => {
  const event = new KeyboardEvent('keydown', {
    key: 's',
    ctrlKey: true,
    bubbles: true,
    cancelable: true
  })
  target.dispatchEvent(event)
}

describe('useHotkeys context stack', () => {
  it('dispatches only active context handlers and suppresses global handler', async () => {
    const onGlobal = vi.fn()
    const onDrawer = vi.fn()

    const Host = defineComponent({
      setup() {
        const drawerOpen = ref(false)
        const drawerContext = useHotkeyContext({ enabled: () => drawerOpen.value })

        useHotkey('ctrl+s', () => {
          onGlobal()
        }, { preventDefault: true })

        useHotkey('ctrl+s', () => {
          onDrawer()
          return false
        }, {
          context: drawerContext,
          preventDefault: true,
          stopPropagation: true,
          allowInInputs: true
        })

        return { drawerOpen }
      },
      template: '<div><input data-test="input" /></div>'
    })

    const wrapper = mount(Host)

    dispatchCtrlS(window)
    expect(onGlobal).toHaveBeenCalledTimes(1)
    expect(onDrawer).toHaveBeenCalledTimes(0)

    ;(wrapper.vm as any).drawerOpen = true
    await nextTick()

    dispatchCtrlS(window)
    expect(onGlobal).toHaveBeenCalledTimes(1)
    expect(onDrawer).toHaveBeenCalledTimes(1)

    ;(wrapper.vm as any).drawerOpen = false
    await nextTick()

    dispatchCtrlS(window)
    expect(onGlobal).toHaveBeenCalledTimes(2)
    expect(onDrawer).toHaveBeenCalledTimes(1)

    wrapper.unmount()
  })

  it('normalizes combo declaration order', () => {
    const onSave = vi.fn()

    const Host = defineComponent({
      setup() {
        useHotkey('shift+ctrl+s', () => {
          onSave()
        }, { preventDefault: true })
        return {}
      },
      template: '<div />'
    })

    const wrapper = mount(Host)

    const event = new KeyboardEvent('keydown', {
      key: 's',
      ctrlKey: true,
      shiftKey: true,
      bubbles: true,
      cancelable: true
    })
    window.dispatchEvent(event)

    expect(onSave).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })
})

