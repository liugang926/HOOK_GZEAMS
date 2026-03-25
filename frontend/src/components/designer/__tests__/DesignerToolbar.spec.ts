import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DesignerToolbar from '../DesignerToolbar.vue'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (_key: string, fallback?: string) => fallback || _key
  })
}))

const stubs = {
  'el-button': {
    props: ['disabled', 'loading', 'type', 'plain', 'size'],
    emits: ['click'],
    template: `
      <button
        :disabled="disabled || loading"
        :data-type="type"
        :data-plain="plain"
        @click="$emit('click')"
      >
        <slot />
      </button>
    `
  },
  'el-button-group': {
    template: '<div><slot /></div>'
  },
  'el-segmented': {
    props: ['modelValue', 'options'],
    template: '<div class="segmented-stub">{{ modelValue }}</div>'
  },
  'el-divider': {
    template: '<div class="divider-stub"></div>'
  },
  'el-tooltip': {
    template: '<div><slot /></div>'
  },
  'el-dropdown': {
    template: '<div><slot /><slot name="dropdown" /></div>'
  },
  'el-dropdown-menu': {
    template: '<div><slot /></div>'
  },
  'el-dropdown-item': {
    emits: ['command'],
    template: '<button @click="$emit(\'command\')"><slot /></button>'
  },
  'el-tag': {
    template: '<span><slot /></span>'
  },
  'el-icon': {
    template: '<i><slot /></i>'
  },
  ArrowLeft: true,
  RefreshLeft: true,
  RefreshRight: true,
  MoreFilled: true
}

const baseProps = {
  layoutName: 'Asset Layout',
  modeLabel: 'Edit',
  isDefault: false,
  translationMode: false,
  canUndo: true,
  canRedo: true,
  renderMode: 'design' as const,
  previewLoading: false,
  previewMode: 'current' as const,
  publishing: false,
  viewMode: 'Detail' as const,
  viewport: 'desktop' as const
}

describe('DesignerToolbar', () => {
  it('renders preview mode toggles and emits mode changes', async () => {
    const wrapper = mount(DesignerToolbar, {
      props: baseProps,
      global: { stubs }
    })

    const currentButton = wrapper.find('[data-testid="layout-preview-current-button"]')
    const activeButton = wrapper.find('[data-testid="layout-preview-active-button"]')
    const saveButton = wrapper.find('[data-testid="layout-save-button"]')
    const publishButton = wrapper.find('[data-testid="layout-publish-button"]')

    expect(currentButton.exists()).toBe(true)
    expect(activeButton.exists()).toBe(true)
    expect((currentButton.element as HTMLButtonElement).disabled).toBe(true)
    expect((activeButton.element as HTMLButtonElement).disabled).toBe(false)
    expect((saveButton.element as HTMLButtonElement).disabled).toBe(false)
    expect((publishButton.element as HTMLButtonElement).disabled).toBe(false)

    await activeButton.trigger('click')
    expect(wrapper.emitted('setPreviewMode')?.[0]).toEqual(['active'])
  })

  it('disables save and publish while previewing active layout', async () => {
    const wrapper = mount(DesignerToolbar, {
      props: {
        ...baseProps,
        previewMode: 'active'
      },
      global: { stubs }
    })

    const currentButton = wrapper.find('[data-testid="layout-preview-current-button"]')
    const activeButton = wrapper.find('[data-testid="layout-preview-active-button"]')
    const saveButton = wrapper.find('[data-testid="layout-save-button"]')
    const publishButton = wrapper.find('[data-testid="layout-publish-button"]')

    expect((currentButton.element as HTMLButtonElement).disabled).toBe(false)
    expect((activeButton.element as HTMLButtonElement).disabled).toBe(true)
    expect((saveButton.element as HTMLButtonElement).disabled).toBe(true)
    expect((publishButton.element as HTMLButtonElement).disabled).toBe(true)

    await currentButton.trigger('click')
    expect(wrapper.emitted('setPreviewMode')?.[0]).toEqual(['current'])
  })
})
