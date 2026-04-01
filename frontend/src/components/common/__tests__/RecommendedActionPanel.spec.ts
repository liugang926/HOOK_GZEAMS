import { defineComponent } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage, ElMessageBox } from 'element-plus'

import request from '@/utils/request'
import RecommendedActionPanel from '../RecommendedActionPanel.vue'

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          'common.dialog.confirmTitle': 'Confirm',
          'common.actions.confirm': 'Confirm',
          'common.actions.cancel': 'Cancel',
          'common.messages.operationSuccess': 'Operation succeeded',
          'common.messages.operationFailed': 'Operation failed',
          'common.messages.formValidationFailed': 'Form validation failed',
          'common.workbench.eyebrows.recommendedActions': 'Recommended',
          'common.workbench.titles.recommendedActions': 'Recommended Actions',
          'common.workbench.messages.recommendedActionHint': 'Do the next best thing.',
          'common.workbench.actions.run': 'Run',
        }
        return translations[key] || key
      },
      te: () => false,
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
    disabled: Boolean,
    type: {
      type: String,
      default: 'default',
    },
  },
  emits: ['click'],
  template: `
    <button
      :data-type="type"
      :disabled="disabled || loading"
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

const mountPanel = () => {
  return mount(RecommendedActionPanel, {
    props: {
      objectCode: 'DisposalRequest',
      recordId: 'request-1',
      actions: [
        {
          code: 'reject_disposal',
          label: 'Reject disposal',
          description: 'Collect the rejection reason before stopping the request.',
          actionPath: 'approve',
          confirmMessage: 'Reject this disposal request?',
          payload: {
            decision: 'rejected',
          },
          prompt: {
            title: 'Rejection Reason',
            fields: [
              {
                key: 'reason',
                payloadKey: 'comment',
                label: 'Reason',
                type: 'textarea',
                required: true,
              },
            ],
          },
        },
      ],
    },
    global: {
      stubs: {
        'el-button': ElButtonStub,
        'el-dialog': ElDialogStub,
        'el-form': { template: '<form><slot /></form>' },
        'el-form-item': { template: '<div><slot /></div>' },
        'el-input': ElInputStub,
        'el-select': { template: '<select><slot /></select>' },
        'el-option': { template: '<option><slot /></option>' },
        'el-date-picker': { template: '<input />' },
        'el-input-number': { template: '<input type="number" />' },
      },
    },
  })
}

describe('RecommendedActionPanel', () => {
  beforeEach(() => {
    vi.mocked(request).mockReset()
    vi.mocked(ElMessage.success).mockReset()
    vi.mocked(ElMessage.error).mockReset()
    vi.mocked(ElMessage.warning).mockReset()
    vi.mocked(ElMessageBox.confirm).mockReset()
    vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm' as any)
  })

  it('collects prompt values and executes recommended actions with merged payload', async () => {
    vi.mocked(request).mockResolvedValue({
      success: true,
      message: 'Disposal request rejected.',
      data: {},
    })

    const wrapper = mountPanel()
    const runButton = wrapper.findAll('button').find((button) => button.text() === 'Run')

    expect(runButton).toBeDefined()
    await runButton!.trigger('click')
    expect(wrapper.text()).toContain('Rejection Reason')

    await wrapper.get('textarea').setValue('Insufficient appraisal evidence')

    const confirmButton = wrapper.findAll('button').find((button) => button.text() === 'Confirm')
    expect(confirmButton).toBeDefined()
    await confirmButton!.trigger('click')
    await flushPromises()

    expect(ElMessageBox.confirm).toHaveBeenCalledWith(
      'Reject this disposal request?',
      'Confirm',
      expect.objectContaining({
        confirmButtonText: 'Confirm',
        cancelButtonText: 'Cancel',
      }),
    )
    expect(request).toHaveBeenCalledWith({
      url: '/system/objects/DisposalRequest/request-1/approve/',
      method: 'post',
      data: {
        decision: 'rejected',
        comment: 'Insufficient appraisal evidence',
      },
      unwrap: 'none',
    })
    expect(ElMessage.success).toHaveBeenCalledWith('Disposal request rejected.')
    expect(wrapper.emitted('refresh-requested')).toBeTruthy()
  })
})
