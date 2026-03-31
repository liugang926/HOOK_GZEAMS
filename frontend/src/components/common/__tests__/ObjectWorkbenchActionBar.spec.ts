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

const mountActionBar = (status = 'active') => {
  return mount(ObjectWorkbenchActionBar, {
    props: {
      objectCode: 'AssetProject',
      recordId: 'project-1',
      recordData: { status },
      workbench: {
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
      },
    },
    global: {
      stubs: {
        'el-button': ElButtonStub,
      },
    },
  })
}

describe('ObjectWorkbenchActionBar', () => {
  beforeEach(() => {
    vi.mocked(request).mockReset()
    vi.mocked(ElMessage.success).mockReset()
    vi.mocked(ElMessage.error).mockReset()
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
})
