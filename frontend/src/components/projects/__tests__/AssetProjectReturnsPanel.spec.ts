import { defineComponent } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage, ElMessageBox } from 'element-plus'

import request from '@/utils/request'
import { createObjectClient } from '@/api/dynamic'
import AssetProjectReturnsPanel from '../AssetProjectReturnsPanel.vue'

const pushMock = vi.fn()
const listMock = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}))

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          'projects.panels.pendingReturns': 'Pending return orders',
          'projects.panels.returnsHint': 'Return orders waiting for confirmation.',
          'common.actions.refresh': 'Refresh',
          'projects.actions.viewAllReturns': 'View all returns',
          'projects.actions.confirmReturnOrder': 'Confirm return',
          'projects.messages.emptyReturns': 'No pending return orders.',
          'projects.messages.loadReturnsFailed': 'Failed to load project return orders.',
          'projects.messages.confirmReturnOrder': 'Confirm this return order now?',
          'projects.messages.confirmReturnSuccess': 'Return order confirmed successfully.',
          'projects.messages.confirmRejectReturnOrder': 'Provide a rejection reason before rejecting this return order.',
          'projects.messages.rejectReasonRequired': 'A rejection reason is required.',
          'projects.messages.rejectReturnSuccess': 'Return order rejected successfully.',
          'projects.columns.returnNo': 'Return No',
          'projects.columns.returner': 'Returner',
          'projects.columns.returnDate': 'Return Date',
          'projects.columns.itemsCount': 'Items',
          'projects.columns.returnReason': 'Return Reason',
          'common.columns.actions': 'Actions',
          'common.dialog.confirmTitle': 'Confirm',
          'common.actions.confirm': 'Confirm',
          'common.actions.reject': 'Reject',
          'common.actions.cancel': 'Cancel',
          'common.messages.operationFailed': 'Operation failed',
        }
        return translations[key] || key
      },
      te: (key: string) => key === 'projects.panels.pendingReturns',
    }),
  }
})

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn(),
  },
  ElMessageBox: {
    confirm: vi.fn().mockResolvedValue(undefined),
    prompt: vi.fn().mockResolvedValue({ value: 'Reason from panel' }),
  },
}))

vi.mock('@/api/dynamic', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/dynamic')>()
  return {
    ...actual,
    createObjectClient: vi.fn(() => ({
      list: listMock,
    })),
  }
})

vi.mock('@/utils/request', () => ({
  default: vi.fn(),
}))

const ElCardStub = defineComponent({
  name: 'ElCardStub',
  template: '<div><slot name="header" /><slot /></div>',
})

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
  template: '<button :disabled="loading" :data-type="type" @click="$emit(\'click\', $event)"><slot /></button>',
})

const ElEmptyStub = defineComponent({
  name: 'ElEmptyStub',
  props: {
    description: {
      type: String,
      default: '',
    },
  },
  template: '<div class="el-empty-stub">{{ description }}</div>',
})

const ElTableStub = defineComponent({
  name: 'ElTableStub',
  props: {
    data: {
      type: Array,
      default: () => [],
    },
  },
  template: '<div class="el-table-stub"><slot /></div>',
})

const ElTableColumnStub = defineComponent({
  name: 'ElTableColumnStub',
  props: {
    label: {
      type: String,
      default: '',
    },
  },
  template: '<div class="el-table-column-stub">{{ label }}<slot :row="{ id: \'return-1\', returnNo: \'RT001\', returner: { username: \'user1\' }, returnDate: \'2026-03-20\', itemsCount: 1, returnReason: \'Project completed\' }" /></div>',
})

const mountPanel = async (extraProps: Record<string, unknown> = {}) => {
  const wrapper = mount(AssetProjectReturnsPanel, {
    props: {
      panel: {
        code: 'project_returns',
        titleKey: 'projects.panels.pendingReturns',
      },
      recordId: 'project-1',
      ...extraProps,
    },
    global: {
      directives: {
        loading: {},
      },
      stubs: {
        'el-card': ElCardStub,
        'el-button': ElButtonStub,
        'el-empty': ElEmptyStub,
        'el-table': ElTableStub,
        'el-table-column': ElTableColumnStub,
      },
    },
  })

  await flushPromises()
  return wrapper
}

describe('AssetProjectReturnsPanel', () => {
  beforeEach(() => {
    pushMock.mockReset()
    listMock.mockReset()
    vi.mocked(request).mockReset()
    vi.mocked(ElMessage.success).mockReset()
    vi.mocked(ElMessage.error).mockReset()
    vi.mocked(ElMessageBox.confirm).mockReset()
    vi.mocked(ElMessageBox.confirm).mockResolvedValue(undefined)
    vi.mocked(ElMessageBox.prompt).mockReset()
    vi.mocked(ElMessageBox.prompt).mockResolvedValue({ value: 'Reason from panel' })
    vi.mocked(createObjectClient).mockClear()
  })

  it('loads pending return orders for the current project', async () => {
    listMock.mockResolvedValue({
      count: 1,
      results: [
        {
          id: 'return-1',
          returnNo: 'RT001',
          returner: { username: 'user1' },
          returnDate: '2026-03-20',
          itemsCount: 1,
          returnReason: 'Project completed',
        },
      ],
    })

    const wrapper = await mountPanel()

    expect(createObjectClient).toHaveBeenCalledWith('AssetReturn')
    expect(listMock).toHaveBeenCalledWith({
      project: 'project-1',
      status: 'pending',
      page: 1,
      page_size: 6,
    })
    expect(wrapper.text()).toContain('Pending return orders')
    expect(wrapper.text()).toContain('Confirm return')
  })

  it('navigates to the project-scoped AssetReturn list', async () => {
    listMock.mockResolvedValue({ count: 0, results: [] })
    const wrapper = await mountPanel()

    const viewAllButton = wrapper.findAll('button').find((button) => button.text() === 'View all returns')

    expect(viewAllButton).toBeDefined()

    await viewAllButton!.trigger('click')

    expect(pushMock).toHaveBeenCalledWith({
      path: '/objects/AssetReturn',
      query: { project: 'project-1' },
    })
  })

  it('confirms a pending return order from the panel', async () => {
    listMock.mockResolvedValue({ count: 1, results: [{ id: 'return-1' }] })
    vi.mocked(request).mockResolvedValue({
      success: true,
      message: 'Return confirmed and completed',
    })

    const wrapper = await mountPanel()
    const confirmButton = wrapper.findAll('button').find((button) => button.text() === 'Confirm return')

    expect(confirmButton).toBeDefined()

    await confirmButton!.trigger('click')
    await flushPromises()

    expect(ElMessageBox.confirm).toHaveBeenCalledWith(
      'Confirm this return order now?',
      'Confirm',
      expect.objectContaining({
        confirmButtonText: 'Confirm',
        cancelButtonText: 'Cancel',
      }),
    )
    expect(request).toHaveBeenCalledWith({
      url: '/system/objects/AssetReturn/return-1/confirm/',
      method: 'post',
      data: {},
      unwrap: 'none',
    })
    expect(ElMessage.success).toHaveBeenCalledWith('Return confirmed and completed')
    expect(wrapper.emitted('workbench-refresh-requested')).toEqual([
      [{
        summary: true,
        panels: ['project_assets', 'project_return_history'],
      }],
    ])
  })

  it('rejects a pending return order from the panel', async () => {
    listMock.mockResolvedValue({ count: 1, results: [{ id: 'return-1' }] })
    vi.mocked(request).mockResolvedValue({
      success: true,
      message: 'Return rejected and sent back',
    })

    const wrapper = await mountPanel()
    const rejectButton = wrapper.findAll('button').find((button) => button.text() === 'Reject')

    expect(rejectButton).toBeDefined()

    await rejectButton!.trigger('click')
    await flushPromises()

    expect(ElMessageBox.prompt).toHaveBeenCalledWith(
      'Provide a rejection reason before rejecting this return order.',
      'Reject',
      expect.objectContaining({
        inputPattern: /\S+/,
        inputErrorMessage: 'A rejection reason is required.',
      }),
    )
    expect(request).toHaveBeenCalledWith({
      url: '/system/objects/AssetReturn/return-1/reject/',
      method: 'post',
      data: { reason: 'Reason from panel' },
      unwrap: 'none',
    })
    expect(ElMessage.success).toHaveBeenCalledWith('Return rejected and sent back')
    expect(wrapper.emitted('workbench-refresh-requested')).toEqual([
      [{
        summary: true,
        panels: ['project_assets', 'project_return_history'],
      }],
    ])
  })

  it('prefers shared workspace dashboard pending totals in the panel header', async () => {
    listMock.mockResolvedValue({
      count: 1,
      results: [{ id: 'return-2' }],
    })

    const wrapper = await mountPanel({
      workspaceDashboard: {
        returns: {
          pendingCount: 4,
        },
      },
    })

    expect(wrapper.find('.asset-project-panel__meta').text()).toBe('4')
  })
})
