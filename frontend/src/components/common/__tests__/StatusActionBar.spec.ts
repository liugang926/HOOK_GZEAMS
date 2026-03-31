import { defineComponent } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ElMessage, ElMessageBox } from 'element-plus'
import StatusActionBar from '../StatusActionBar.vue'

interface StatusActionPromptFieldOption {
  label: string
  value: string | number | boolean
}

interface StatusActionPromptField {
  key: string
  label: string
  type: 'text' | 'textarea' | 'select' | 'date' | 'number'
  required?: boolean
  defaultValue?: string | number | boolean | null
  precision?: number
  options?: StatusActionPromptFieldOption[]
}

interface StatusActionPrompt {
  title: string
  width?: string | number
  labelWidth?: string | number
  fields: StatusActionPromptField[]
}

interface StatusAction {
  key: string
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  icon?: string
  loading?: boolean
  disabled?: boolean
  disabledTooltip?: string
  confirmMessage?: string
  confirmTitle?: string
  prompt?: StatusActionPrompt
  visibleWhen?: (status: string) => boolean
  apiCall: (context?: { values?: Record<string, unknown> }) => Promise<unknown>
}

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => ({
      t: (key: string) => {
        const overrides: Record<string, string> = {
          'common.dialog.confirmTitle': 'Confirm',
          'common.actions.confirm': 'Confirm',
          'common.actions.cancel': 'Cancel',
          'common.messages.operationSuccess': 'Operation succeeded',
          'common.messages.operationFailed': 'Operation failed',
          'common.messages.formValidationFailed': 'Form validation failed',
        }
        return overrides[key] || key
      },
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

const ElButtonStub = defineComponent({
  name: 'ElButtonStub',
  props: {
    disabled: Boolean,
    loading: Boolean,
    type: {
      type: String,
      default: 'default',
    },
  },
  emits: ['click'],
  template: `
    <button
      :disabled="disabled || loading"
      :data-type="type"
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

const mountActionBar = (actions: any[]) => {
  return mount(StatusActionBar, {
    props: {
      status: 'pending',
      actions,
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

describe('StatusActionBar', () => {
  beforeEach(() => {
    vi.mocked(ElMessage.success).mockReset()
    vi.mocked(ElMessage.error).mockReset()
    vi.mocked(ElMessage.warning).mockReset()
    vi.mocked(ElMessageBox.confirm).mockReset()
    vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm' as any)
  })

  it('collects prompt values before calling the action api', async () => {
    const apiCall = vi.fn().mockResolvedValue(undefined)
    const wrapper = mountActionBar([
      {
        key: 'reject',
        label: 'Reject',
        type: 'danger',
        prompt: {
          title: 'Rejection Reason',
          fields: [
            {
              key: 'reason',
              label: 'Reason',
              type: 'textarea',
              required: true,
            },
          ],
        },
        apiCall,
        visibleWhen: () => true,
      },
    ])

    await wrapper.get('button').trigger('click')
    expect(wrapper.text()).toContain('Rejection Reason')

    await wrapper.get('textarea').setValue('Missing required approval note')

    const confirmButton = wrapper.findAll('button').find(button => button.text() === 'Confirm')
    expect(confirmButton).toBeDefined()
    await confirmButton!.trigger('click')
    await flushPromises()

    expect(apiCall).toHaveBeenCalledWith({
      values: {
        reason: 'Missing required approval note',
      },
    })
    expect(ElMessage.success).toHaveBeenCalled()
  })

  it('blocks prompt actions when required fields are empty', async () => {
    const apiCall = vi.fn().mockResolvedValue(undefined)
    const wrapper = mountActionBar([
      {
        key: 'reject',
        label: 'Reject',
        type: 'danger',
        prompt: {
          title: 'Rejection Reason',
          fields: [
            {
              key: 'reason',
              label: 'Reason',
              type: 'textarea',
              required: true,
            },
          ],
        },
        apiCall,
        visibleWhen: () => true,
      },
    ])

    await wrapper.get('button').trigger('click')
    const confirmButton = wrapper.findAll('button').find(button => button.text() === 'Confirm')
    expect(confirmButton).toBeDefined()
    await confirmButton!.trigger('click')
    await flushPromises()

    expect(apiCall).not.toHaveBeenCalled()
    expect(ElMessage.warning).toHaveBeenCalled()
  })

  it('supports date and number prompt fields', async () => {
    const apiCall = vi.fn().mockResolvedValue(undefined)
    const wrapper = mountActionBar([
      {
        key: 'renew',
        label: 'Renew',
        type: 'warning',
        prompt: {
          title: 'Renew Warranty',
          fields: [
            {
              key: 'end_date',
              label: 'New End Date',
              type: 'date',
              required: true,
            },
            {
              key: 'warranty_cost',
              label: 'Warranty Cost',
              type: 'number',
              defaultValue: 100,
              precision: 2,
            },
          ],
        },
        apiCall,
        visibleWhen: () => true,
      },
    ])

    await wrapper.get('button').trigger('click')
    await wrapper.get('.date-picker-stub').setValue('2026-12-31')
    await wrapper.get('.input-number-stub').setValue('288.5')

    const confirmButton = wrapper.findAll('button').find(button => button.text() === 'Confirm')
    expect(confirmButton).toBeDefined()
    await confirmButton!.trigger('click')
    await flushPromises()

    expect(apiCall).toHaveBeenCalledWith({
      values: {
        end_date: '2026-12-31',
        warranty_cost: 288.5,
      },
    })
  })
})
