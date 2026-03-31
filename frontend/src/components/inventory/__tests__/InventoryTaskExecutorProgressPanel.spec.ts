/* eslint-disable vue/one-component-per-file */
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'

import InventoryTaskExecutorProgressPanel from '../InventoryTaskExecutorProgressPanel.vue'

const { getAssignmentsMock, getAssignmentProgressMock } = vi.hoisted(() => ({
  getAssignmentsMock: vi.fn(),
  getAssignmentProgressMock: vi.fn(),
}))

vi.mock('@/api/inventory', () => ({
  inventoryApi: {
    getAssignments: getAssignmentsMock,
    getAssignmentProgress: getAssignmentProgressMock,
  },
}))

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          'common.actions.refresh': 'Refresh',
          'common.messages.loadFailed': 'Load failed',
          'common.workbench.labels.summary': 'Summary',
          'inventory.workbench.panels.executorProgress': 'Executor Progress',
          'inventory.workbench.messages.executorProgressHint': 'Track executor workload',
          'inventory.assignment.messages.noAssignments': 'No assignments yet.',
          'inventory.assignment.summary.assigneeCount': 'Assigned Users',
          'inventory.assignment.summary.totalAssets': 'Assigned Assets',
          'inventory.assignment.summary.scannedCount': 'Scanned Total',
          'inventory.assignment.summary.abnormalCount': 'Abnormal Total',
        }
        return translations[key] || key
      },
      te: () => true,
    }),
  }
})

vi.mock('@/components/AssignmentProgressCard.vue', () => ({
  default: defineComponent({
    name: 'AssignmentProgressCardStub',
    props: {
      progress: {
        type: Object,
        required: true,
      },
      status: {
        type: String,
        default: '',
      },
    },
    template: '<div class="assignment-progress-card-stub">{{ progress.assigneeName }}|{{ progress.scannedCount }}|{{ status }}</div>',
  }),
}))

const ElButtonStub = defineComponent({
  name: 'ElButtonStub',
  props: {
    loading: Boolean,
  },
  emits: ['click'],
  template: '<button :disabled="loading" @click="$emit(\'click\')"><slot /></button>',
})

const ElCardStub = defineComponent({
  name: 'ElCardStub',
  template: '<div class="el-card-stub"><slot /></div>',
})

const ElStatisticStub = defineComponent({
  name: 'ElStatisticStub',
  props: {
    title: {
      type: String,
      default: '',
    },
    value: {
      type: Number,
      default: 0,
    },
  },
  template: '<div class="el-statistic-stub">{{ title }}:{{ value }}</div>',
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

const ElAlertStub = defineComponent({
  name: 'ElAlertStub',
  props: {
    title: {
      type: String,
      default: '',
    },
  },
  template: '<div class="el-alert-stub">{{ title }}</div>',
})

describe('InventoryTaskExecutorProgressPanel', () => {
  beforeEach(() => {
    getAssignmentsMock.mockReset()
    getAssignmentProgressMock.mockReset()
  })

  const mountPanel = () => {
    return mount(InventoryTaskExecutorProgressPanel, {
      props: {
        panel: {
          code: 'inventory_task_executor_progress_panel',
          titleKey: 'inventory.workbench.panels.executorProgress',
          descriptionKey: 'inventory.workbench.messages.executorProgressHint',
        },
        recordId: 'task-1',
      },
      global: {
        components: {
          ElAlert: ElAlertStub,
          ElButton: ElButtonStub,
          ElCard: ElCardStub,
          ElEmpty: ElEmptyStub,
          ElStatistic: ElStatisticStub,
        },
        directives: {
          loading: () => undefined,
        },
      },
    })
  }

  it('loads executor assignments and progress cards on mount', async () => {
    getAssignmentsMock.mockResolvedValue([
      {
        id: 'a-1',
        taskId: 'task-1',
        assigneeId: 'u-1',
        assigneeName: 'Alice',
        assignedBy: '',
        assignedAt: '2026-03-31T08:00:00Z',
        status: 'pending',
        scanCount: 0,
        assetCount: 8,
        locationNames: [],
      },
    ])
    getAssignmentProgressMock.mockResolvedValue([
      {
        assignmentId: 'a-1',
        assigneeId: 'u-1',
        assigneeName: 'Alice',
        totalAssets: 8,
        scannedCount: 5,
        normalCount: 4,
        abnormalCount: 1,
        progress: 63,
        status: 'in_progress',
      },
      {
        assignmentId: 'a-2',
        assigneeId: 'u-2',
        assigneeName: 'Bob',
        totalAssets: 6,
        scannedCount: 6,
        normalCount: 6,
        abnormalCount: 0,
        progress: 100,
        status: 'completed',
      },
    ])

    const wrapper = mountPanel()
    await flushPromises()

    expect(getAssignmentsMock).toHaveBeenCalledWith('task-1')
    expect(getAssignmentProgressMock).toHaveBeenCalledWith('task-1')
    expect(wrapper.text()).toContain('Executor Progress')
    expect(wrapper.text()).toContain('Assigned Users:2')
    expect(wrapper.text()).toContain('Assigned Assets:14')
    expect(wrapper.text()).toContain('Alice|5|in_progress')
    expect(wrapper.text()).toContain('Bob|6|completed')
  })

  it('reloads panel data when panelRefreshVersion changes', async () => {
    getAssignmentsMock.mockResolvedValue([])
    getAssignmentProgressMock.mockResolvedValue([])

    const wrapper = mountPanel()
    await flushPromises()

    expect(getAssignmentsMock).toHaveBeenCalledTimes(1)
    expect(getAssignmentProgressMock).toHaveBeenCalledTimes(1)

    await wrapper.setProps({
      panelRefreshVersion: 1,
    })
    await flushPromises()

    expect(getAssignmentsMock).toHaveBeenCalledTimes(2)
    expect(getAssignmentProgressMock).toHaveBeenCalledTimes(2)
  })

  it('shows an inline warning when panel data fails to load', async () => {
    getAssignmentsMock.mockRejectedValue(new Error('boom'))
    getAssignmentProgressMock.mockResolvedValue([])

    const wrapper = mountPanel()
    await flushPromises()

    expect(wrapper.text()).toContain('Load failed')
  })
})
