import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi, beforeEach } from 'vitest'

import ClosedLoopDashboardPanel from '@/components/reports/ClosedLoopDashboardPanel.vue'

const {
  pushMock,
  getMeMock,
  switchOrganizationMock,
  setStoredCurrentOrgIdMock,
  getOverviewMock,
  getByObjectMock,
  getQueuesMock,
  getBottlenecksMock,
  listSnapshotsMock,
  createSnapshotMock,
  getSnapshotMock,
  deleteSnapshotApiMock,
  exportWorkbookMock,
} = vi.hoisted(() => ({
  pushMock: vi.fn(),
  getMeMock: vi.fn(),
  switchOrganizationMock: vi.fn(),
  setStoredCurrentOrgIdMock: vi.fn(),
  getOverviewMock: vi.fn(),
  getByObjectMock: vi.fn(),
  getQueuesMock: vi.fn(),
  getBottlenecksMock: vi.fn(),
  listSnapshotsMock: vi.fn(),
  createSnapshotMock: vi.fn(),
  getSnapshotMock: vi.fn(),
  deleteSnapshotApiMock: vi.fn(),
  exportWorkbookMock: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}))

vi.mock('@/api/closedLoopMetrics', () => ({
  closedLoopMetricsApi: {
    getOverview: getOverviewMock,
    getByObject: getByObjectMock,
    getQueues: getQueuesMock,
    getBottlenecks: getBottlenecksMock,
    listSnapshots: listSnapshotsMock,
    createSnapshot: createSnapshotMock,
    getSnapshot: getSnapshotMock,
    deleteSnapshot: deleteSnapshotApiMock,
  },
}))

vi.mock('@/api/users', () => ({
  userApi: {
    getMe: getMeMock,
    switchOrganization: switchOrganizationMock,
  },
}))

vi.mock('@/platform/auth/sessionPreference', () => ({
  getStoredCurrentOrgId: () => 'org-1',
  setStoredCurrentOrgId: setStoredCurrentOrgIdMock,
}))

vi.mock('@/platform/reports/closedLoopDashboardExport', () => ({
  exportClosedLoopDashboardWorkbook: exportWorkbookMock,
}))

describe('ClosedLoopDashboardPanel', () => {
  beforeEach(() => {
    pushMock.mockReset()
    getMeMock.mockReset()
    switchOrganizationMock.mockReset()
    setStoredCurrentOrgIdMock.mockReset()
    getOverviewMock.mockReset()
    getByObjectMock.mockReset()
    getQueuesMock.mockReset()
    getBottlenecksMock.mockReset()
    listSnapshotsMock.mockReset()
    createSnapshotMock.mockReset()
    getSnapshotMock.mockReset()
    deleteSnapshotApiMock.mockReset()
    exportWorkbookMock.mockReset()

    getMeMock.mockResolvedValue({
      id: 'user-1',
      primaryOrganization: {
        id: 'org-1',
        name: 'Metrics Org',
        code: 'METRICS',
      },
      accessibleOrganizations: [
        {
          id: 'org-1',
          name: 'Metrics Org',
          code: 'METRICS',
        },
        {
          id: 'org-2',
          name: 'Branch Org',
          code: 'BRANCH',
        },
      ],
    })
    getOverviewMock.mockResolvedValue({
      window: {
        key: '30d',
        days: 30,
        startDate: '2026-03-01',
        endDate: '2026-03-30',
      },
      summary: {
        openedCount: 12,
        closedCount: 8,
        backlogCount: 5,
        overdueCount: 2,
        autoClosedCount: 3,
        exceptionBacklogCount: 1,
        avgCycleHours: 18.5,
        closureRate: 66.7,
        overdueRate: 40,
        automaticClosureRate: 37.5,
      },
      workflowSla: {
        activeTaskCount: 4,
        overdueTaskCount: 1,
        escalatedTaskCount: 1,
        bottleneckCount: 2,
      },
      ownerRankings: [
        {
          userId: 'user-1',
          username: 'metrics_user',
          displayName: 'Metrics User',
          openCount: 6,
          overdueCount: 5,
          topSource: 'workflow_tasks',
          sourceCounts: {
            workflow_tasks: 3,
            inventory_differences: 2,
            finance_vouchers: 1,
          },
        },
      ],
      departmentRankings: [
        {
          departmentId: 'dept-1',
          departmentName: 'Operations',
          openCount: 7,
          overdueCount: 5,
          topSource: 'insurance_policies',
          sourceCounts: {
            insurance_policies: 2,
            workflow_tasks: 1,
            inventory_differences: 1,
          },
        },
      ],
      objectsCovered: [
        {
          objectCode: 'InventoryTask',
          objectName: 'Inventory Tasks',
          primaryRoute: '/objects/InventoryTask',
        },
        {
          objectCode: 'FinanceVoucher',
          objectName: 'Finance Vouchers',
          primaryRoute: '/objects/FinanceVoucher',
        },
      ],
      trend: {
        bucket: 'day',
        points: [
          { date: '2026-03-24', opened: 2, closed: 1 },
          { date: '2026-03-25', opened: 3, closed: 2 },
        ],
      },
      metricContract: {},
    })
    switchOrganizationMock.mockResolvedValue({
      success: true,
    })
    getByObjectMock.mockResolvedValue({
      window: {
        key: '30d',
        days: 30,
        startDate: '2026-03-01',
        endDate: '2026-03-30',
      },
      results: [
        {
          objectCode: 'InventoryTask',
          objectName: 'Inventory Tasks',
          primaryRoute: '/objects/InventoryTask',
          summary: {
            openedCount: 5,
            closedCount: 2,
            backlogCount: 2,
            overdueCount: 1,
            autoClosedCount: 1,
            exceptionBacklogCount: 1,
            avgCycleHours: 12.4,
            closureRate: 40,
            overdueRate: 50,
            automaticClosureRate: 50,
          },
          trend: {
            bucket: 'day',
            points: [],
          },
          queues: [],
          bottlenecks: [],
        },
      ],
    })
    getQueuesMock.mockResolvedValue({
      window: {
        key: '30d',
        days: 30,
        startDate: '2026-03-01',
        endDate: '2026-03-30',
      },
      results: [
        {
          sourceType: 'object',
          objectCode: 'InventoryTask',
          objectName: 'Inventory Tasks',
          code: 'inventory_manual_follow_up',
          label: 'Tasks awaiting manual follow-up',
          count: 2,
          route: '/objects/InventoryItem?manual_follow_up_only=true',
          tone: 'warning',
        },
      ],
    })
    getBottlenecksMock.mockResolvedValue({
      window: {
        key: '30d',
        days: 30,
        startDate: '2026-03-01',
        endDate: '2026-03-30',
      },
      results: [
        {
          sourceType: 'workflow',
          objectCode: 'WorkflowTask',
          objectName: 'Workflow Tasks',
          code: 'workflow::approval',
          label: 'Manager Approval',
          count: 3,
          route: '/workflow/dashboard',
          severity: 'high',
          metricType: 'workflow_sla',
        },
      ],
    })
    listSnapshotsMock.mockResolvedValue({
      results: [],
    })
    createSnapshotMock.mockResolvedValue({
      id: 'snapshot-created',
    })
    getSnapshotMock.mockResolvedValue({
      id: 'snapshot-1',
      label: 'Metrics Org · 30D · 2026-03-01 - 2026-03-30',
      dashboardCode: 'closed_loop',
      windowKey: '30d',
      objectCodes: ['InventoryTask'],
      createdAt: '2026-03-30T10:00:00.000Z',
      organization: {
        id: 'org-1',
        name: 'Metrics Org',
        code: 'METRICS',
      },
      payload: {
        overview: {
          window: {
            key: '30d',
            days: 30,
            startDate: '2026-03-01',
            endDate: '2026-03-30',
          },
          summary: {
            openedCount: 12,
            closedCount: 8,
            backlogCount: 5,
            overdueCount: 2,
            autoClosedCount: 3,
            exceptionBacklogCount: 1,
            avgCycleHours: 18.5,
            closureRate: 66.7,
            overdueRate: 40,
            automaticClosureRate: 37.5,
          },
          workflowSla: {
            activeTaskCount: 4,
            overdueTaskCount: 1,
            escalatedTaskCount: 1,
            bottleneckCount: 2,
          },
          ownerRankings: [],
          departmentRankings: [],
          objectsCovered: [],
          trend: {
            bucket: 'day',
            points: [],
          },
          metricContract: {},
        },
        byObjectItems: [
          {
            objectCode: 'InventoryTask',
            objectName: 'Inventory Tasks',
            primaryRoute: '/objects/InventoryTask',
            summary: {
              openedCount: 5,
              closedCount: 2,
              backlogCount: 2,
              overdueCount: 1,
              autoClosedCount: 1,
              exceptionBacklogCount: 1,
              avgCycleHours: 12.4,
              closureRate: 40,
              overdueRate: 50,
              automaticClosureRate: 50,
            },
            trend: {
              bucket: 'day',
              points: [],
            },
            queues: [],
            bottlenecks: [],
          },
        ],
        queues: [],
        bottlenecks: [],
      },
    })
    deleteSnapshotApiMock.mockResolvedValue(undefined)
  })

  it('loads overview, queues, and bottlenecks on mount', async () => {
    const wrapper = mount(ClosedLoopDashboardPanel)
    await flushPromises()

    expect(getMeMock).toHaveBeenCalled()
    expect(getOverviewMock).toHaveBeenCalledWith({ window: '30d', organizationId: 'org-1' })
    expect(getByObjectMock).toHaveBeenCalledWith({ window: '30d', organizationId: 'org-1' })
    expect(listSnapshotsMock).toHaveBeenCalledWith({ organizationId: 'org-1' })
    expect(wrapper.text()).toContain('闭环经营驾驶舱')
    expect(wrapper.text()).toContain('12')
    expect(wrapper.text()).toContain('Tasks awaiting manual follow-up')
    expect(wrapper.text()).toContain('Manager Approval')
    expect(wrapper.text()).toContain('Inventory Tasks')
    expect(wrapper.text()).toContain('Metrics User')
    expect(wrapper.text()).toContain('Operations')
    expect(wrapper.text()).toContain('组织范围')
  })

  it('changes the organization, window, and navigates to queue routes', async () => {
    const wrapper = mount(ClosedLoopDashboardPanel)
    await flushPromises()

    await wrapper.find('.closed-loop-panel__scope-select').setValue('org-2')
    await flushPromises()

    expect(getOverviewMock).toHaveBeenLastCalledWith({ window: '30d', organizationId: 'org-2' })
    expect(getByObjectMock).toHaveBeenLastCalledWith({ window: '30d', organizationId: 'org-2' })

    await wrapper.findAll('.closed-loop-panel__window-button')[0].trigger('click')
    await flushPromises()

    expect(getOverviewMock).toHaveBeenLastCalledWith({ window: '7d', organizationId: 'org-2' })
    expect(getByObjectMock).toHaveBeenLastCalledWith({ window: '7d', organizationId: 'org-2' })

    await wrapper.findAll('.closed-loop-panel__object-filter-chip')[1].trigger('click')
    await flushPromises()

    expect(getOverviewMock).toHaveBeenLastCalledWith({
      window: '7d',
      organizationId: 'org-2',
      objectCodes: ['InventoryTask'],
    })
    expect(getByObjectMock).toHaveBeenLastCalledWith({
      window: '7d',
      organizationId: 'org-2',
      objectCodes: ['InventoryTask'],
    })

    await wrapper.findAll('.closed-loop-panel__table-link')[0].trigger('click')
    await flushPromises()

    expect(switchOrganizationMock).toHaveBeenCalledWith('user-1', 'org-2')
    expect(setStoredCurrentOrgIdMock).toHaveBeenCalledWith('org-2')
    expect(pushMock).toHaveBeenCalled()
  })

  it('opens owner and department drilldowns with route actions', async () => {
    const wrapper = mount(ClosedLoopDashboardPanel)
    await flushPromises()

    const drilldownTriggers = wrapper.findAll('.closed-loop-panel__drilldown-trigger')
    expect(drilldownTriggers).toHaveLength(2)

    await drilldownTriggers[0].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Metrics User')
    expect(wrapper.text()).toContain('工作流待办')
    expect(wrapper.text()).toContain('盘点差异')

    const drilldownOpenButtons = wrapper.findAll('.closed-loop-panel__drilldown-open')
    expect(drilldownOpenButtons.length).toBeGreaterThan(0)
    const overdueButtons = wrapper.findAll('.closed-loop-panel__drilldown-overdue')
    expect(overdueButtons.length).toBe(1)

    await overdueButtons[0].trigger('click')
    await flushPromises()

    expect(pushMock).toHaveBeenCalledWith(expect.stringContaining('/workflow/tasks?'))
    expect(pushMock).toHaveBeenCalledWith(expect.stringContaining('overdue_only=true'))

    await drilldownTriggers[1].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Operations')
    expect(wrapper.text()).toContain('保险保单')
  })

  it('saves snapshots, restores a snapshot, exports the workbook, and deletes snapshots', async () => {
    const baseOverview = {
      window: {
        key: '30d',
        days: 30,
        startDate: '2026-03-01',
        endDate: '2026-03-30',
      },
      summary: {
        openedCount: 12,
        closedCount: 8,
        backlogCount: 5,
        overdueCount: 2,
        autoClosedCount: 3,
        exceptionBacklogCount: 1,
        avgCycleHours: 18.5,
        closureRate: 66.7,
        overdueRate: 40,
        automaticClosureRate: 37.5,
      },
      workflowSla: {
        activeTaskCount: 4,
        overdueTaskCount: 1,
        escalatedTaskCount: 1,
        bottleneckCount: 2,
      },
      ownerRankings: [],
      departmentRankings: [],
      objectsCovered: [],
      trend: {
        bucket: 'day',
        points: [],
      },
      metricContract: {},
    }

    const liveComparisonOverview = {
      ...baseOverview,
      summary: {
        ...baseOverview.summary,
        openedCount: 14,
        closedCount: 10,
        backlogCount: 4,
        overdueCount: 1,
        autoClosedCount: 4,
        avgCycleHours: 16.5,
      },
    }

    const baseByObject = {
      window: {
        key: '30d',
        days: 30,
        startDate: '2026-03-01',
        endDate: '2026-03-30',
      },
      results: [
        {
          objectCode: 'InventoryTask',
          objectName: 'Inventory Tasks',
          primaryRoute: '/objects/InventoryTask',
          summary: {
            openedCount: 5,
            closedCount: 2,
            backlogCount: 2,
            overdueCount: 1,
            autoClosedCount: 1,
            exceptionBacklogCount: 1,
            avgCycleHours: 12.4,
            closureRate: 40,
            overdueRate: 50,
            automaticClosureRate: 50,
          },
          trend: {
            bucket: 'day',
            points: [],
          },
          queues: [],
          bottlenecks: [],
        },
      ],
    }

    const liveComparisonByObject = {
      ...baseByObject,
      results: [
        {
          ...baseByObject.results[0],
          summary: {
            ...baseByObject.results[0].summary,
            closedCount: 3,
            backlogCount: 1,
            overdueCount: 0,
          },
        },
      ],
    }

    getOverviewMock.mockReset()
    getOverviewMock
      .mockResolvedValueOnce(baseOverview)
      .mockResolvedValueOnce(liveComparisonOverview)
    getByObjectMock.mockReset()
    getByObjectMock
      .mockResolvedValueOnce(baseByObject)
      .mockResolvedValueOnce(liveComparisonByObject)

    listSnapshotsMock
      .mockResolvedValueOnce({ results: [] })
      .mockResolvedValue({
        results: [
          {
            id: 'snapshot-1',
            label: 'Metrics Org · 30D · 2026-03-01 - 2026-03-30',
            dashboardCode: 'closed_loop',
            windowKey: '30d',
            objectCodes: ['InventoryTask'],
            createdAt: '2026-03-30T10:00:00.000Z',
            organization: {
              id: 'org-1',
              name: 'Metrics Org',
              code: 'METRICS',
            },
          },
        ],
      })

    const wrapper = mount(ClosedLoopDashboardPanel)
    await flushPromises()

    const toolbarButtons = wrapper.findAll('.closed-loop-panel__retry')
    const exportButton = toolbarButtons.find((button) => button.text() === '导出 Excel')
    const saveButton = toolbarButtons.find((button) => button.text() === '保存快照')

    expect(exportButton).toBeDefined()
    expect(saveButton).toBeDefined()

    await exportButton!.trigger('click')
    await flushPromises()

    expect(exportWorkbookMock).toHaveBeenCalledWith(expect.objectContaining({
      filename: expect.stringContaining('Metrics Org'),
    }))

    await saveButton!.trigger('click')
    await flushPromises()

    expect(createSnapshotMock).toHaveBeenCalledWith(expect.objectContaining({
      label: expect.stringContaining('Metrics Org'),
      window: '30d',
      organizationId: 'org-1',
      objectCodes: [],
    }))
    expect(wrapper.text()).toContain('已保存快照')
    expect(wrapper.text()).toContain('Metrics Org · 30D · 2026-03-01 - 2026-03-30')

    const snapshotButtons = wrapper.findAll('.closed-loop-panel__snapshot-card .closed-loop-panel__table-link')
    const snapshotOpenButton = snapshotButtons[0]
    await snapshotOpenButton.trigger('click')
    await flushPromises()

    expect(getSnapshotMock).toHaveBeenCalledWith('snapshot-1', {
      organizationId: 'org-1',
    })
    expect(wrapper.text()).toContain('当前查看已保存快照')
    expect(wrapper.text()).toContain('返回实时数据')

    const compareButton = wrapper.findAll('.closed-loop-panel__retry').find((button) => button.text() === '对比当前实时数据')
    expect(compareButton).toBeDefined()

    await compareButton!.trigger('click')
    await flushPromises()

    expect(getOverviewMock).toHaveBeenLastCalledWith({
      window: '30d',
      organizationId: 'org-1',
      objectCodes: ['InventoryTask'],
    })
    expect(getByObjectMock).toHaveBeenLastCalledWith({
      window: '30d',
      organizationId: 'org-1',
      objectCodes: ['InventoryTask'],
    })
    expect(wrapper.text()).toContain('快照与当前实时数据对比')
    expect(wrapper.text()).toContain('对象维度变化')
    expect(wrapper.text()).toContain('Inventory Tasks')
    expect(wrapper.text()).toContain('+1')
    expect(wrapper.text()).toContain('-1')

    const snapshotDeleteButton = snapshotButtons[1]
    await snapshotDeleteButton.trigger('click')
    await flushPromises()

    expect(deleteSnapshotApiMock).toHaveBeenCalledWith('snapshot-1', {
      organizationId: 'org-1',
    })
  })
})
