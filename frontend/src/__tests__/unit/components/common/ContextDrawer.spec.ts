import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, nextTick } from 'vue'

const getMetadataMock = vi.fn()
const createMock = vi.fn()
const updateMock = vi.fn()
const resolveRuntimeLayoutMock = vi.fn()

vi.mock('@/components/engine/DynamicForm.vue', () => ({
  default: defineComponent({
    name: 'DynamicForm',
    template: '<div class="dynamic-form-stub"></div>'
  })
}))

vi.mock('@/api/dynamic', () => ({
  createObjectClient: () => ({
    getMetadata: getMetadataMock,
    create: createMock,
    update: updateMock
  })
}))

vi.mock('@/platform/layout/runtimeLayoutResolver', () => ({
  resolveRuntimeLayout: resolveRuntimeLayoutMock
}))

vi.mock('@/composables/useHotkeys', () => ({
  useHotkey: vi.fn(),
  useHotkeyContext: vi.fn(() => 'context-drawer-test')
}))

describe('ContextDrawer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getMetadataMock.mockResolvedValue({
      code: 'Asset',
      name: 'Asset',
      permissions: { view: true, add: true, change: true, delete: true }
    })
    resolveRuntimeLayoutMock.mockResolvedValue({
      permissions: { view: true, add: true, change: true, delete: true },
      viewMode: 'Detail'
    })
    createMock.mockResolvedValue({})
    updateMock.mockResolvedValue({})
  })

  it('does not render the drawer form while closed', async () => {
    const i18n = (await import('@/locales')).default
    const ContextDrawer = (await import('@/components/common/ContextDrawer.vue')).default

    const wrapper = mount(ContextDrawer, {
      props: {
        modelValue: false,
        objectCode: 'Asset',
        recordId: 'asset-1'
      },
      global: {
        plugins: [i18n],
        directives: {
          loading: () => undefined,
          focusTrap: () => undefined
        },
        stubs: {
          'el-drawer': defineComponent({
            name: 'ElDrawer',
            props: ['modelValue'],
            emits: ['update:modelValue'],
            template: '<div class="drawer-stub"><slot /><slot name="footer" /></div>'
          }),
          'el-dialog': defineComponent({
            name: 'ElDialog',
            props: ['modelValue'],
            emits: ['update:modelValue'],
            template: '<div class="dialog-stub"><slot /><slot name="footer" /></div>'
          }),
          'el-result': defineComponent({
            name: 'ElResult',
            template: '<div class="el-result-stub"><slot /><slot name="extra" /></div>'
          }),
          'el-button': defineComponent({
            name: 'ElButton',
            emits: ['click'],
            template: '<button @click="$emit(\'click\')"><slot /></button>'
          }),
          'el-icon': defineComponent({
            name: 'ElIcon',
            template: '<i><slot /></i>'
          }),
          Warning: true
        }
      }
    })

    await flushPromises()
    await nextTick()

    expect(wrapper.find('.dynamic-form-stub').exists()).toBe(false)
    expect(resolveRuntimeLayoutMock).not.toHaveBeenCalled()
    expect(getMetadataMock).not.toHaveBeenCalled()

    await wrapper.setProps({ modelValue: true })
    await flushPromises()
    await nextTick()

    expect(wrapper.find('.drawer-stub').exists() || wrapper.find('.dialog-stub').exists()).toBe(true)
    expect(resolveRuntimeLayoutMock).toHaveBeenCalledWith('Asset', 'edit', { includeRelations: false })
    expect(getMetadataMock).toHaveBeenCalled()
  })
})
