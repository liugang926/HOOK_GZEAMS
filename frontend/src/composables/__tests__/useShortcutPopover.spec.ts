import { defineComponent, nextTick, ref } from 'vue'
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import { useShortcutPopover } from '@/composables/useShortcutPopover'

describe('useShortcutPopover', () => {
  it('toggles visible state and clears pinned when closing', async () => {
    const Host = defineComponent({
      setup() {
        const state = useShortcutPopover()
        return { ...state }
      },
      template: '<div />'
    })

    const wrapper = mount(Host)

    expect((wrapper.vm as any).visible).toBe(false)
    expect((wrapper.vm as any).pinned).toBe(false)

    ;(wrapper.vm as any).toggle()
    await nextTick()
    expect((wrapper.vm as any).visible).toBe(true)

    ;(wrapper.vm as any).togglePinned()
    await nextTick()
    expect((wrapper.vm as any).pinned).toBe(true)
    expect((wrapper.vm as any).visible).toBe(true)

    ;(wrapper.vm as any).toggle()
    await nextTick()
    expect((wrapper.vm as any).visible).toBe(false)
    expect((wrapper.vm as any).pinned).toBe(false)

    wrapper.unmount()
  })

  it('closes popover on Escape and reports handled state', async () => {
    const Host = defineComponent({
      setup() {
        const state = useShortcutPopover()
        return { ...state }
      },
      template: '<div />'
    })

    const wrapper = mount(Host)

    expect((wrapper.vm as any).handleEscape()).toBe(false)
    ;(wrapper.vm as any).toggle()
    await nextTick()
    expect((wrapper.vm as any).visible).toBe(true)

    expect((wrapper.vm as any).handleEscape()).toBe(true)
    await nextTick()
    expect((wrapper.vm as any).visible).toBe(false)
    expect((wrapper.vm as any).pinned).toBe(false)

    wrapper.unmount()
  })

  it('disables toggle behaviors when enabled flag becomes false', async () => {
    const Host = defineComponent({
      setup() {
        const enabled = ref(true)
        const state = useShortcutPopover({
          enabled: () => enabled.value
        })
        return { enabled, ...state }
      },
      template: '<div />'
    })

    const wrapper = mount(Host)

    ;(wrapper.vm as any).toggle()
    ;(wrapper.vm as any).togglePinned()
    await nextTick()
    expect((wrapper.vm as any).visible).toBe(true)
    expect((wrapper.vm as any).pinned).toBe(true)

    ;(wrapper.vm as any).enabled = false
    await nextTick()
    expect((wrapper.vm as any).visible).toBe(false)
    expect((wrapper.vm as any).pinned).toBe(false)

    ;(wrapper.vm as any).toggle()
    ;(wrapper.vm as any).togglePinned()
    await nextTick()
    expect((wrapper.vm as any).visible).toBe(false)
    expect((wrapper.vm as any).pinned).toBe(false)

    wrapper.unmount()
  })

  it('applies default pinned state when enabled and defaultPinned is true', async () => {
    const Host = defineComponent({
      setup() {
        const enabled = ref(true)
        const defaultPinned = ref(true)
        const state = useShortcutPopover({
          enabled: () => enabled.value,
          defaultPinned: () => defaultPinned.value
        })
        return { enabled, defaultPinned, ...state }
      },
      template: '<div />'
    })

    const wrapper = mount(Host)

    expect((wrapper.vm as any).visible).toBe(true)
    expect((wrapper.vm as any).pinned).toBe(true)

    ;(wrapper.vm as any).defaultPinned = false
    await nextTick()
    expect((wrapper.vm as any).visible).toBe(true)
    expect((wrapper.vm as any).pinned).toBe(true)

    ;(wrapper.vm as any).enabled = false
    await nextTick()
    expect((wrapper.vm as any).visible).toBe(false)
    expect((wrapper.vm as any).pinned).toBe(false)

    wrapper.unmount()
  })
})
