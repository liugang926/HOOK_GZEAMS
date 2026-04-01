import { defineComponent } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage, ElMessageBox } from 'element-plus'

import request from '@/utils/request'
import ObjectWorkbenchActionBar from '../ObjectWorkbenchActionBar.vue'

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          'projects.actions.refreshRollups': 'Refresh summary',
          'projects.actions.closeProject': 'Close project',
          'projects.messages.confirmCloseProject': 'Close this project?',
          'common.dialog.confirmTitle': 'Confirm',
          'common.actions.confirm': 'Confirm',
          'common.actions.cancel': 'Cancel',
          'common.messages.operationSuccess': 'Operation succeeded',
          'common.messages.operationFailed': 'Operation failed',
        }
        return translations[key] || key
      },
      te: (key: string) => [
        'projects.actions.refreshRollups',
        'projects.actions.closeProject',
        'projects.messages.confirmCloseProject',
      ].includes(key),
    }),
  }
})

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
  ElMessageBox: {
    confirm: vi.fn().mockResolvedValue('confirm' as const),
  },
}))

vi.mock('@/utils/request', () => ({
  default: vi.fn(),
}))

const ElButtonStub = defineComponent({
  name: 'ElButtonStub',
  props: {
    loading: Boolean,
    type: {
      type: String,
      default: 'default',
    },
  },
  emits: ['click'],
  template: `
    <button
      :data-type="type"
      :disabled="loading"
      @click="$emit('click')"
    >
      <slot />
    </button>
  `,
})

const ElDialogStub = defineComponent({
  name: 'ElDialogStub',
  props: {
    modelValue: Boolean,
    title: {
      type: String,
      default: '',
    },
  },
  emits: ['update:modelValue'],
  template: `
    <div v-if="modelValue" class="dialog-stub">
      <div class="dialog-title">{{ title }}</div>
      <slot />
      <slot name="footer" />
    </div>
  `,
})

const ElInputStub = defineComponent({
  name: 'ElInputStub',
  props: {
    modelValue: {
      type: String,
      default: '',
    },
    type: {
      type: String,
      default: 'text',
    },
  },
  emits: ['update:modelValue'],
  template: `
    <textarea
      v-if="type === 'textarea'"
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <input
      v-else
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  `,
})

const ElSelectStub = defineComponent({
  name: 'ElSelectStub',
  props: {
    modelValue: {
      type: [String, Number, Boolean],
      default: '',
    },
  },
  emits: ['update:modelValue'],
  template: `
    <select
      :value="modelValue"
      @change="$emit('update:modelValue', $event.target.value)"
    >
      <slot />
    </select>
  `,
})

const ElOptionStub = defineComponent({
  name: 'ElOptionStub',
  props: {
    label: {
      type: String,
      default: '',
    },
    value: {
      type: [String, Number, Boolean],
      default: '',
    },
  },
  template: '<option :value="value">{{ label }}</option>',
})

const ElDatePickerStub = defineComponent({
  name: 'ElDatePickerStub',
  props: {
    modelValue: {
      type: String,
      default: '',
    },
  },
  emits: ['update:modelValue'],
  template: `
    <input
      class="date-picker-stub"
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  `,
})

const ElInputNumberStub = defineComponent({
  name: 'ElInputNumberStub',
  props: {
    modelValue: {
      type: Number,
      default: undefined,
    },
  },
  emits: ['update:modelValue'],
  template: `
    <input
      class="input-number-stub"
      type="number"
      :value="modelValue"
      @input="$emit('update:modelValue', Number($event.target.value))"
    />
  `,
})

const mountActionBar = (status = 'active', workbenchOverrides: Record<string, any> = {}) => {
  const workbench = {
    workspaceMode: 'extended',
    primaryEntryRoute: '/objects/AssetProject',
    legacyAliases: [],
    toolbar: {
      primaryActions: [
        {
          code: 'refresh_rollups',
          labelKey: 'projects.actions.refreshRollups',
          actionPath: 'refresh_rollups',
        },
      ],
      secondaryActions: [
        {
          code: 'close_project',
          labelKey: 'projects.actions.closeProject',
          actionPath: 'close',
          confirmMessageKey: 'projects.messages.confirmCloseProject',
          visibleWhen: {
            statusIn: ['active', 'suspended'],
          },
        },
      ],
    },
    detailPanels: [],
    asyncIndicators: [],
    summaryCards: [],
    queuePanels: [],
    exceptionPanels: [],
    closurePanel: null,
    slaIndicators: [],
    recommendedActions: [],
    ...workbenchOverrides,
  }

  return mount(ObjectWorkbenchActionBar, {
    props: {
      objectCode: 'AssetProject',
      recordId: 'project-1',
      recordData: { status },
      workbench,
    },
    global: {
      stubs: {
        'el-button': ElButtonStub,
        'el-dialog': ElDialogStub,
        'el-form': { template: '<form><slot /></form>' },
        'el-form-item': { template: '<div><slot /></div>' },
        'el-input': ElInputStub,
        'el-select': ElSelectStub,
        'el-option': ElOptionStub,
        'el-date-picker': ElDatePickerStub,
        'el-input-number': ElInputNumberStub,
      },
    },
  })
}

describe('ObjectWorkbenchActionBar', () => {
  beforeEach(() => {
    vi.mocked(request).mockReset()
    vi.mocked(ElMessage.success).mockReset()
    vi.mocked(ElMessage.error).mockReset()
    vi.mocked(ElMessage.warning).mockReset()
    vi.mocked(ElMessageBox.confirm).mockReset()
    vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm' as any)
  })

  it('shows status-gated workbench actions for active AssetProject records', () => {
    const wrapper = mountActionBar('active')

    expect(wrapper.text()).toContain('Refresh summary')
    expect(wrapper.text()).toContain('Close project')
  })

  it('hides the close action when the project is already completed', () => {
    const wrapper = mountActionBar('completed')

    expect(wrapper.text()).toContain('Refresh summary')
    expect(wrapper.text()).not.toContain('Close project')
  })

  it('executes the close action through the object custom-action endpoint', async () => {
    vi.mocked(request).mockResolvedValue({
      success: true,
      message: 'Project closed successfully.',
      data: {},
    })

    const wrapper = mountActionBar('active')
    const closeButton = wrapper.findAll('button').find((button) => button.text() === 'Close project')

    expect(closeButton).toBeDefined()

    await closeButton!.trigger('click')
    await flushPromises()

    expect(ElMessageBox.confirm).toHaveBeenCalledWith(
      'Close this project?',
      'Confirm',
      expect.objectContaining({
        confirmButtonText: 'Confirm',
        cancelButtonText: 'Cancel',
      }),
    )
    expect(request).toHaveBeenCalledWith({
      url: '/system/objects/AssetProject/project-1/close/',
      method: 'post',
      data: {},
      unwrap: 'none',
    })
    expect(ElMessage.success).toHaveBeenCalledWith('Project closed successfully.')
    expect(wrapper.emitted('refresh-requested')).toBeTruthy()
  })

  it('collects prompt values and merges static payload for workbench actions', async () => {
    vi.mocked(request).mockResolvedValue({
      success: true,
      message: 'Pickup order approved.',
      data: {},
    })

    const wrapper = mountActionBar('pending', {
      toolbar: {
        primaryActions: [
          {
            code: 'approve_pickup',
            label: 'Approve pickup',
            actionPath: 'approve',
            confirmMessage: 'Approve this pickup?',
            payload: {
              approval: 'approved',
            },
            prompt: {
              title: 'Approval Comment',
              fields: [
                {
                  key: 'comment',
                  label: 'Comment',
                  type: 'textarea',
                },
              ],
            },
            visibleWhen: {
              statusIn: ['pending'],
            },
          },
        ],
        secondaryActions: [],
      },
    })

    await wrapper.get('button').trigger('click')
    expect(wrapper.text()).toContain('Approval Comment')

    await wrapper.get('textarea').setValue('Approved from toolbar')

    const confirmButton = wrapper.findAll('button').find((button) => button.text() === 'Confirm')
    expect(confirmButton).toBeDefined()
    await confirmButton!.trigger('click')
    await flushPromises()

    expect(ElMessageBox.confirm).toHaveBeenCalledWith(
      'Approve this pickup?',
      'Confirm',
      expect.objectContaining({
        confirmButtonText: 'Confirm',
        cancelButtonText: 'Cancel',
      }),
    )
    expect(request).toHaveBeenCalledWith({
      url: '/system/objects/AssetProject/project-1/approve/',
      method: 'post',
      data: {
        approval: 'approved',
        comment: 'Approved from toolbar',
      },
      unwrap: 'none',
    })
    expect(ElMessage.success).toHaveBeenCalledWith('Pickup order approved.')
  })
})
