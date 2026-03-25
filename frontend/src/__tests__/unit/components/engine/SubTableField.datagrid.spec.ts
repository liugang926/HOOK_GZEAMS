/* eslint-disable vue/one-component-per-file */
import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, ref } from 'vue'
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

const field = {
  code: 'items',
  name: 'Items',
  relatedFields: [
    { code: 'item_code', name: 'Item Code', fieldType: 'text' },
    { code: 'qty', name: 'Qty', fieldType: 'number' }
  ]
}

const mountHarness = async (
  initialRows: Array<{ item_code: string; qty: number }> = [{ item_code: 'ITEM-1', qty: 1 }]
) => {
  vi.resetModules()
  const SubTableField = (await import('@/components/engine/fields/SubTableField.vue')).default
  const Host = defineComponent({
    name: 'SubTableHarness',
    components: { SubTableField },
    setup() {
      const rows = ref(initialRows)
      return {
        rows,
        field
      }
    },
    template: '<SubTableField v-model="rows" :field="field" :readonly="false" :disabled="false" />'
  })

  return mount(Host, {
    attachTo: document.body,
    global: {
      plugins: [ElementPlus],
      mocks: {
        $t: (key: string) => key
      }
    }
  })
}

describe('SubTableField datagrid keyboard navigation', () => {
  it('moves to next cell on Enter', async () => {
    const wrapper = await mountHarness()

    await flushPromises()
    const firstInput = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input')
    const secondInput = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="1"] input')
    expect(firstInput.exists()).toBe(true)
    expect(secondInput.exists()).toBe(true)

    ;(firstInput.element as HTMLInputElement).focus()
    await firstInput.trigger('keydown', { key: 'Enter' })
    await flushPromises()

    expect(document.activeElement).toBe(secondInput.element)
    wrapper.unmount()
  })

  it('adds a new row and focuses first cell when pressing Tab on last cell', async () => {
    const wrapper = await mountHarness()

    await flushPromises()
    const lastCellInput = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="1"] input')
    expect(lastCellInput.exists()).toBe(true)

    ;(lastCellInput.element as HTMLInputElement).focus()
    await lastCellInput.trigger('keydown', { key: 'Tab' })
    await flushPromises()

    expect((wrapper.vm as any).rows.length).toBe(2)

    const nextRowFirstInput = wrapper.find('.datagrid-cell[data-row-index="1"][data-col-index="0"] input')
    expect(nextRowFirstInput.exists()).toBe(true)
    expect(document.activeElement).toBe(nextRowFirstInput.element)
    wrapper.unmount()
  })

  it('blurs input when pressing Escape', async () => {
    const wrapper = await mountHarness()

    await flushPromises()
    const firstInput = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input')
    expect(firstInput.exists()).toBe(true)

    ;(firstInput.element as HTMLInputElement).focus()
    await firstInput.trigger('keydown', { key: 'Escape' })
    await flushPromises()

    expect(document.activeElement).not.toBe(firstInput.element)
    wrapper.unmount()
  })

  it('jumps to first cell in row when pressing Home', async () => {
    const wrapper = await mountHarness([{ item_code: 'ITEM-1', qty: 1 }])
    await flushPromises()

    const firstInput = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input')
    const secondInput = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="1"] input')
    ;(secondInput.element as HTMLInputElement).setSelectionRange(0, 0)
    ;(secondInput.element as HTMLInputElement).focus()

    await secondInput.trigger('keydown', { key: 'Home' })
    await flushPromises()

    expect(document.activeElement).toBe(firstInput.element)
    wrapper.unmount()
  })

  it('jumps to last cell in row when pressing End', async () => {
    const wrapper = await mountHarness([{ item_code: 'ITEM-1', qty: 1 }])
    await flushPromises()

    const firstInput = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input')
    const secondInput = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="1"] input')
    ;(firstInput.element as HTMLInputElement).focus()

    await firstInput.trigger('keydown', { key: 'End' })
    await flushPromises()

    expect(document.activeElement).toBe(secondInput.element)
    wrapper.unmount()
  })

  it('moves vertically with ArrowUp/ArrowDown in same column', async () => {
    const wrapper = await mountHarness([
      { item_code: 'ITEM-1', qty: 1 },
      { item_code: 'ITEM-2', qty: 2 }
    ])
    await flushPromises()

    const row0Col0 = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input')
    const row1Col0 = wrapper.find('.datagrid-cell[data-row-index="1"][data-col-index="0"] input')

    ;(row0Col0.element as HTMLInputElement).focus()
    await row0Col0.trigger('keydown', { key: 'ArrowDown' })
    await flushPromises()
    expect(document.activeElement).toBe(row1Col0.element)

    await row1Col0.trigger('keydown', { key: 'ArrowUp' })
    await flushPromises()
    expect(document.activeElement).toBe(row0Col0.element)
    wrapper.unmount()
  })

  it('emits request-save when pressing Ctrl+S inside datagrid', async () => {
    vi.resetModules()
    const SubTableField = (await import('@/components/engine/fields/SubTableField.vue')).default
    const wrapper = mount(SubTableField, {
      attachTo: document.body,
      props: {
        modelValue: [{ item_code: 'ITEM-1', qty: 1 }],
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
    const input = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input')
    ;(input.element as HTMLInputElement).focus()
    await flushPromises()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 's', ctrlKey: true, bubbles: true, cancelable: true }))
    await flushPromises()

    expect(wrapper.emitted('request-save')).toBeTruthy()
    expect(wrapper.emitted('request-save')?.length).toBe(1)
    wrapper.unmount()
  })

  it('emits request-save when pressing Meta+S inside datagrid', async () => {
    vi.resetModules()
    const SubTableField = (await import('@/components/engine/fields/SubTableField.vue')).default
    const wrapper = mount(SubTableField, {
      attachTo: document.body,
      props: {
        modelValue: [{ item_code: 'ITEM-1', qty: 1 }],
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
    const input = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input')
    ;(input.element as HTMLInputElement).focus()
    await flushPromises()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 's', metaKey: true, bubbles: true, cancelable: true }))
    await flushPromises()

    expect(wrapper.emitted('request-save')).toBeTruthy()
    expect(wrapper.emitted('request-save')?.length).toBe(1)
    wrapper.unmount()
  })

  it('renders shortcut help trigger in editable datagrid', async () => {
    const wrapper = await mountHarness([{ item_code: 'ITEM-1', qty: 1 }])
    await flushPromises()

    expect(wrapper.find('.shortcut-help-btn').exists()).toBe(true)
    const subTable = wrapper.findComponent({ name: 'SubTableField' })
    const shortcutItems = ((subTable.vm as any).shortcutItems || []) as Array<{ combo?: string }>
    const combos = shortcutItems.map((item) => item.combo || '')
    expect(combos).toContain('F1')
    expect(combos).toContain('Shift + F1')
    expect(combos.some((combo) => combo === 'Ctrl + Enter' || combo === '⌘ + Enter')).toBe(true)
    expect(combos.some((combo) => combo === 'Shift + Ctrl + D' || combo === 'Shift + ⌘ + D')).toBe(true)
    expect(combos.some((combo) => combo.includes('Ctrl/Cmd'))).toBe(false)
    wrapper.unmount()
  })

  it('toggles shortcut help popover with F1 when datagrid is focused', async () => {
    const wrapper = await mountHarness([{ item_code: 'ITEM-1', qty: 1 }])
    await flushPromises()

    const input = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input')
    ;(input.element as HTMLInputElement).focus()
    await flushPromises()

    const subTable = wrapper.findComponent({ name: 'SubTableField' })
    expect((subTable.vm as any).shortcutPopoverVisible).toBe(false)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'F1', bubbles: true, cancelable: true }))
    await flushPromises()
    expect((subTable.vm as any).shortcutPopoverVisible).toBe(true)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'F1', bubbles: true, cancelable: true }))
    await flushPromises()
    expect((subTable.vm as any).shortcutPopoverVisible).toBe(false)

    wrapper.unmount()
  })

  it('toggles shortcut help pinned state with Shift+F1', async () => {
    const wrapper = await mountHarness([{ item_code: 'ITEM-1', qty: 1 }])
    await flushPromises()

    const input = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input')
    ;(input.element as HTMLInputElement).focus()
    await flushPromises()

    const subTable = wrapper.findComponent({ name: 'SubTableField' })
    expect((subTable.vm as any).shortcutPopoverPinned).toBe(false)
    expect((subTable.vm as any).shortcutPopoverVisible).toBe(false)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'F1', shiftKey: true, bubbles: true, cancelable: true }))
    await flushPromises()
    expect((subTable.vm as any).shortcutPopoverPinned).toBe(true)
    expect((subTable.vm as any).shortcutPopoverVisible).toBe(true)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'F1', shiftKey: true, bubbles: true, cancelable: true }))
    await flushPromises()
    expect((subTable.vm as any).shortcutPopoverPinned).toBe(false)
    expect((subTable.vm as any).shortcutPopoverVisible).toBe(true)

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'F1', bubbles: true, cancelable: true }))
    await flushPromises()
    expect((subTable.vm as any).shortcutPopoverVisible).toBe(false)
    expect((subTable.vm as any).shortcutPopoverPinned).toBe(false)

    wrapper.unmount()
  })

  it('closes shortcut help with Escape before blurring active input', async () => {
    const wrapper = await mountHarness([{ item_code: 'ITEM-1', qty: 1 }])
    await flushPromises()

    const input = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input')
    ;(input.element as HTMLInputElement).focus()
    await flushPromises()

    const subTable = wrapper.findComponent({ name: 'SubTableField' })
    ;(subTable.vm as any).shortcutPopoverVisible = true
    await flushPromises()

    await input.trigger('keydown', { key: 'Escape' })
    await flushPromises()

    expect((subTable.vm as any).shortcutPopoverVisible).toBe(false)
    expect(document.activeElement).toBe(input.element)
    wrapper.unmount()
  })

  it('closes shortcut help with Escape from header help button', async () => {
    const wrapper = await mountHarness([{ item_code: 'ITEM-1', qty: 1 }])
    await flushPromises()

    const helpButton = wrapper.find('.shortcut-help-btn')
    expect(helpButton.exists()).toBe(true)
    ;(helpButton.element as HTMLButtonElement).focus()

    const subTable = wrapper.findComponent({ name: 'SubTableField' })
    ;(subTable.vm as any).shortcutPopoverVisible = true
    await flushPromises()

    await helpButton.trigger('keydown', { key: 'Escape' })
    await flushPromises()

    expect((subTable.vm as any).shortcutPopoverVisible).toBe(false)
    wrapper.unmount()
  })

  it('hides shortcut help trigger when showShortcutHelp is false in component props', async () => {
    vi.resetModules()
    const SubTableField = (await import('@/components/engine/fields/SubTableField.vue')).default
    const wrapper = mount(SubTableField, {
      attachTo: document.body,
      props: {
        modelValue: [{ item_code: 'ITEM-1', qty: 1 }],
        field: {
          ...field,
          componentProps: {
            showShortcutHelp: false
          }
        },
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
    expect(wrapper.find('.shortcut-help-btn').exists()).toBe(false)
    wrapper.unmount()
  })

  it('shows pinned shortcut help by default when defaultShortcutHelpPinned is true', async () => {
    vi.resetModules()
    const SubTableField = (await import('@/components/engine/fields/SubTableField.vue')).default
    const wrapper = mount(SubTableField, {
      attachTo: document.body,
      props: {
        modelValue: [{ item_code: 'ITEM-1', qty: 1 }],
        field: {
          ...field,
          componentProps: {
            defaultShortcutHelpPinned: true
          }
        },
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
    expect((wrapper.vm as any).shortcutPopoverVisible).toBe(true)
    expect((wrapper.vm as any).shortcutPopoverPinned).toBe(true)
    expect(wrapper.find('.shortcut-help-btn.is-pinned').exists()).toBe(true)
    wrapper.unmount()
  })

  it('jumps across paged data with PageDown/PageUp', async () => {
    vi.resetModules()
    const SubTableField = (await import('@/components/engine/fields/SubTableField.vue')).default
    const rows = [
      { item_code: 'ITEM-1', qty: 1 },
      { item_code: 'ITEM-2', qty: 2 },
      { item_code: 'ITEM-3', qty: 3 },
      { item_code: 'ITEM-4', qty: 4 }
    ]
    const wrapper = mount(SubTableField, {
      attachTo: document.body,
      props: {
        modelValue: rows,
        field: {
          ...field,
          componentProps: {
            paginationPageSize: 2
          }
        },
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
    const page1Row0Col0 = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input')
    ;(page1Row0Col0.element as HTMLInputElement).focus()

    await page1Row0Col0.trigger('keydown', { key: 'PageDown' })
    await flushPromises()

    const afterDown = document.activeElement as HTMLInputElement | null
    expect(afterDown?.value).toBe('ITEM-3')

    await wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input').trigger('keydown', { key: 'PageUp' })
    await flushPromises()

    const afterUp = document.activeElement as HTMLInputElement | null
    expect(afterUp?.value).toBe('ITEM-1')
    wrapper.unmount()
  })

  it('adds a new row and focuses first cell on Ctrl+Enter', async () => {
    const wrapper = await mountHarness([{ item_code: 'ITEM-1', qty: 1 }])
    await flushPromises()

    const firstInput = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input')
    ;(firstInput.element as HTMLInputElement).focus()

    await firstInput.trigger('keydown', { key: 'Enter', ctrlKey: true })
    await flushPromises()

    expect((wrapper.vm as any).rows.length).toBe(2)
    const nextRowFirstInput = wrapper.find('.datagrid-cell[data-row-index="1"][data-col-index="0"] input')
    expect(nextRowFirstInput.exists()).toBe(true)
    expect(document.activeElement).toBe(nextRowFirstInput.element)
    wrapper.unmount()
  })

  it('adds a new row and focuses first cell on Meta+Enter', async () => {
    const wrapper = await mountHarness([{ item_code: 'ITEM-1', qty: 1 }])
    await flushPromises()

    const firstInput = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="0"] input')
    ;(firstInput.element as HTMLInputElement).focus()

    await firstInput.trigger('keydown', { key: 'Enter', metaKey: true })
    await flushPromises()

    expect((wrapper.vm as any).rows.length).toBe(2)
    const nextRowFirstInput = wrapper.find('.datagrid-cell[data-row-index="1"][data-col-index="0"] input')
    expect(nextRowFirstInput.exists()).toBe(true)
    expect(document.activeElement).toBe(nextRowFirstInput.element)
    wrapper.unmount()
  })

  it('inserts a new row above current row on Shift+Ctrl+Enter', async () => {
    const wrapper = await mountHarness([
      { item_code: 'ITEM-1', qty: 1 },
      { item_code: 'ITEM-2', qty: 2 }
    ])
    await flushPromises()

    const row1Col1 = wrapper.find('.datagrid-cell[data-row-index="1"][data-col-index="1"] input')
    ;(row1Col1.element as HTMLInputElement).focus()

    await row1Col1.trigger('keydown', { key: 'Enter', ctrlKey: true, shiftKey: true })
    await flushPromises()

    expect((wrapper.vm as any).rows.length).toBe(3)
    expect((wrapper.vm as any).rows[2].item_code).toBe('ITEM-2')

    const insertedRowFirstInput = wrapper.find('.datagrid-cell[data-row-index="1"][data-col-index="0"] input')
    expect(insertedRowFirstInput.exists()).toBe(true)
    expect(document.activeElement).toBe(insertedRowFirstInput.element)
    wrapper.unmount()
  })

  it('removes current row and keeps keyboard focus on Ctrl+Backspace', async () => {
    const wrapper = await mountHarness([
      { item_code: 'ITEM-1', qty: 1 },
      { item_code: 'ITEM-2', qty: 2 },
      { item_code: 'ITEM-3', qty: 3 }
    ])
    await flushPromises()

    const row1Col0 = wrapper.find('.datagrid-cell[data-row-index="1"][data-col-index="0"] input')
    ;(row1Col0.element as HTMLInputElement).focus()
    await row1Col0.trigger('keydown', { key: 'Backspace', ctrlKey: true })
    await flushPromises()

    expect((wrapper.vm as any).rows.length).toBe(2)
    const focused = document.activeElement as HTMLInputElement | null
    expect(focused?.value).toBe('ITEM-3')
    wrapper.unmount()
  })

  it('duplicates current row and keeps focus on duplicated row with Ctrl+D', async () => {
    const wrapper = await mountHarness([
      { item_code: 'ITEM-1', qty: 1 },
      { item_code: 'ITEM-2', qty: 2 }
    ])
    await flushPromises()

    const row0Col1 = wrapper.find('.datagrid-cell[data-row-index="0"][data-col-index="1"] input')
    ;(row0Col1.element as HTMLInputElement).focus()

    await row0Col1.trigger('keydown', { key: 'd', ctrlKey: true })
    await flushPromises()

    expect((wrapper.vm as any).rows.length).toBe(3)
    expect((wrapper.vm as any).rows[1].item_code).toBe('ITEM-1')
    expect((wrapper.vm as any).rows[1].qty).toBe(1)

    const duplicatedRowSameCol = wrapper.find('.datagrid-cell[data-row-index="1"][data-col-index="1"] input')
    expect(duplicatedRowSameCol.exists()).toBe(true)
    expect(document.activeElement).toBe(duplicatedRowSameCol.element)
    wrapper.unmount()
  })

  it('duplicates current row above and keeps focus on duplicated row with Shift+Ctrl+D', async () => {
    const wrapper = await mountHarness([
      { item_code: 'ITEM-1', qty: 1 },
      { item_code: 'ITEM-2', qty: 2 },
      { item_code: 'ITEM-3', qty: 3 }
    ])
    await flushPromises()

    const row1Col0 = wrapper.find('.datagrid-cell[data-row-index="1"][data-col-index="0"] input')
    ;(row1Col0.element as HTMLInputElement).focus()

    await row1Col0.trigger('keydown', { key: 'd', ctrlKey: true, shiftKey: true })
    await flushPromises()

    expect((wrapper.vm as any).rows.length).toBe(4)
    expect((wrapper.vm as any).rows[1].item_code).toBe('ITEM-2')
    expect((wrapper.vm as any).rows[2].item_code).toBe('ITEM-2')

    const duplicatedAboveSameCol = wrapper.find('.datagrid-cell[data-row-index="1"][data-col-index="0"] input')
    expect(duplicatedAboveSameCol.exists()).toBe(true)
    expect(document.activeElement).toBe(duplicatedAboveSameCol.element)
    wrapper.unmount()
  })

  it('duplicates current row above and keeps focus on duplicated row with Shift+Meta+D', async () => {
    const wrapper = await mountHarness([
      { item_code: 'ITEM-1', qty: 1 },
      { item_code: 'ITEM-2', qty: 2 },
      { item_code: 'ITEM-3', qty: 3 }
    ])
    await flushPromises()

    const row1Col0 = wrapper.find('.datagrid-cell[data-row-index="1"][data-col-index="0"] input')
    ;(row1Col0.element as HTMLInputElement).focus()

    await row1Col0.trigger('keydown', { key: 'd', metaKey: true, shiftKey: true })
    await flushPromises()

    expect((wrapper.vm as any).rows.length).toBe(4)
    expect((wrapper.vm as any).rows[1].item_code).toBe('ITEM-2')
    expect((wrapper.vm as any).rows[2].item_code).toBe('ITEM-2')

    const duplicatedAboveSameCol = wrapper.find('.datagrid-cell[data-row-index="1"][data-col-index="0"] input')
    expect(duplicatedAboveSameCol.exists()).toBe(true)
    expect(document.activeElement).toBe(duplicatedAboveSameCol.element)
    wrapper.unmount()
  })
})
