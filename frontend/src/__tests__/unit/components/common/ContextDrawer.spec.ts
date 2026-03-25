import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, nextTick, watchEffect } from 'vue'

const getMetadataMock = vi.fn()
const getMock = vi.fn()
const createMock = vi.fn()
const updateMock = vi.fn()
const resolveRuntimeLayoutMock = vi.fn()
let latestDynamicFormModelValue: Record<string, unknown> | null = null

vi.mock('@/components/engine/DynamicForm.vue', () => ({
  default: defineComponent({
    name: 'DynamicForm',
    props: {
      modelValue: { type: Object, default: () => ({}) },
      instanceId: { type: String, default: '' }
    },
    setup(props) {
      watchEffect(() => {
        latestDynamicFormModelValue = (props.modelValue || {}) as Record<string, unknown>
      })
      return {}
    },
    template: `
      <div
        class="dynamic-form-stub"
        :data-instance-id="instanceId"
        :data-field-value="(modelValue && (modelValue.asset_name || modelValue.assetName || '')) || ''"
      />
    `
  })
}))

vi.mock('@/api/dynamic', () => ({
  createObjectClient: () => ({
    getMetadata: getMetadataMock,
    get: getMock,
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

const drawerStubs = {
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

describe('ContextDrawer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    latestDynamicFormModelValue = null
    getMetadataMock.mockResolvedValue({
      code: 'Asset',
      name: 'Asset',
      permissions: { view: true, add: true, change: true, delete: true }
    })
    resolveRuntimeLayoutMock.mockResolvedValue({
      permissions: { view: true, add: true, change: true, delete: true },
      viewMode: 'Detail'
    })
    getMock.mockResolvedValue({
      id: 'asset-1',
      asset_name: 'MateBook'
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
        stubs: drawerStubs
      }
    })

    await flushPromises()
    await nextTick()

    expect(wrapper.find('.dynamic-form-stub').exists()).toBe(false)
    expect(resolveRuntimeLayoutMock).not.toHaveBeenCalled()
    expect(getMetadataMock).not.toHaveBeenCalled()
    expect(getMock).not.toHaveBeenCalled()

    await wrapper.setProps({ modelValue: true })
    await flushPromises()
    await nextTick()

    expect(wrapper.find('.drawer-stub').exists() || wrapper.find('.dialog-stub').exists()).toBe(true)
    expect(resolveRuntimeLayoutMock).toHaveBeenCalledWith('Asset', 'edit', {
      includeRelations: false,
      preferredViewMode: undefined
    })
    expect(getMetadataMock).toHaveBeenCalled()
    expect(getMock).toHaveBeenCalledWith('asset-1')
  })

  it('loads edit record data from unwrapped dynamic api responses', async () => {
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
        stubs: drawerStubs
      }
    })

    await wrapper.setProps({ modelValue: true })
    await flushPromises()
    await nextTick()
    await flushPromises()

    const formStub = wrapper.find('.dynamic-form-stub')
    expect(formStub.exists()).toBe(true)
    expect(formStub.attributes('data-instance-id')).toBe('asset-1')
    expect(latestDynamicFormModelValue?.asset_name).toBe('MateBook')
  })
})
