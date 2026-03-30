import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import TaskCenter from '../TaskCenter.vue'

const {
  pushMock,
  getMyTasksMock,
  getUserTasksMock,
  routeQueryMock,
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  getMyTasksMock: vi.fn(),
  getUserTasksMock: vi.fn(),
  routeQueryMock: {
    value: {} as Record<string, unknown>,
  },
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
  useRoute: () => ({
    query: routeQueryMock.value,
  }),
}))

vi.mock('@/api/workflow', () => ({
  workflowNodeApi: {
    getMyTasks: getMyTasksMock,
  },
  getUserTasks: getUserTasksMock,
}))

const stubs = {
  'el-tabs': { template: '<div><slot /></div>' },
  'el-tab-pane': { template: '<div><slot /></div>' },
  'el-table': { template: '<div><slot /></div>' },
  'el-table-column': { template: '<div><slot /></div>' },
  'el-button': { template: '<button><slot /></button>' },
}

describe('TaskCenter', () => {
  beforeEach(() => {
    pushMock.mockReset()
    getMyTasksMock.mockReset()
    getUserTasksMock.mockReset()
    routeQueryMock.value = {}

    getMyTasksMock.mockResolvedValue({
      results: [{ id: 'task-1', title: 'Pending Task' }],
    })
    getUserTasksMock.mockResolvedValue({
      results: [{ id: 'task-2', title: 'Drilldown Task' }],
    })
  })

  it('loads current user tasks by default', async () => {
    mount(TaskCenter, {
      global: {
        stubs,
        directives: {
          loading: () => undefined,
        },
      },
    })

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(getMyTasksMock).toHaveBeenCalledWith({
      page: 1,
      pageSize: 20,
      status: 'pending',
    })
    expect(getUserTasksMock).not.toHaveBeenCalled()
  })

  it('loads filtered workflow tasks in drilldown mode', async () => {
    routeQueryMock.value = {
      assignee: 'user-1',
      assignee_label: 'Metrics User',
      department: 'dept-1',
      department_label: 'Operations',
      source_label: 'Workflow Tasks',
      overdue_only: 'true',
    }

    mount(TaskCenter, {
      global: {
        stubs,
        directives: {
          loading: () => undefined,
        },
      },
    })

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(getUserTasksMock).toHaveBeenCalledWith({
      page: 1,
      page_size: 20,
      status: 'pending',
      assignee: 'user-1',
      department: 'dept-1',
      overdue_only: true,
    })
    expect(getMyTasksMock).not.toHaveBeenCalled()
  })

  it('renders drilldown chips and clears filters', async () => {
    routeQueryMock.value = {
      assignee: 'user-1',
      assignee_label: 'Metrics User',
      source_label: 'Workflow Tasks',
    }

    const wrapper = mount(TaskCenter, {
      global: {
        stubs,
        directives: {
          loading: () => undefined,
        },
      },
    })

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(wrapper.text()).toContain('当前正在查看驾驶舱下钻队列')
    expect(wrapper.text()).toContain('责任人: Metrics User')
    expect(wrapper.text()).toContain('来源: Workflow Tasks')

    await wrapper.findAll('.task-center__drilldown-button')[1].trigger('click')
    expect(pushMock).toHaveBeenCalledWith('/workflow/tasks')
  })
})
