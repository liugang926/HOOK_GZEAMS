import { defineComponent } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import request from '@/utils/request'
import AssetProjectOverviewPanel from '../AssetProjectOverviewPanel.vue'

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          'projects.panels.overview': 'Workspace overview',
          'projects.panels.overviewHint': 'Unified project, asset, member, and return summary for this workspace.',
          'projects.panels.assets': 'Project assets',
          'projects.panels.members': 'Project members',
          'projects.panels.returnHistory': 'Return history',
          'projects.summary.plannedBudget': 'Planned budget',
          'projects.summary.actualCost': 'Actual cost',
          'projects.summary.assetCost': 'Allocated asset cost',
          'projects.summary.inUseAssets': 'In use',
          'projects.summary.returnedAssets': 'Returned',
          'projects.summary.transferredAssets': 'Transferred',
          'projects.summary.activeMembers': 'Active',
          'projects.summary.primaryMembers': 'Primary',
          'projects.summary.allocators': 'Allocators',
          'projects.summary.processedReturns': 'Processed',
          'projects.summary.completedReturns': 'Completed',
          'projects.summary.rejectedReturns': 'Rejected',
          'projects.overview.projectManager': 'Project manager',
          'projects.overview.department': 'Department',
          'projects.overview.projectType': 'Project type',
          'projects.overview.timeline': 'Timeline',
          'projects.overview.actualClosure': 'Actual closure',
          'projects.overview.milestones': 'Milestones',
          'projects.overview.overdue': 'Overdue',
          'projects.messages.loadOverviewFailed': 'Failed to load project workspace overview.',
          'common.actions.refresh': 'Refresh',
        }
        return translations[key] || key
      },
      te: (key: string) => key === 'projects.panels.overview',
    }),
  }
})

vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn(),
  },
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

const ElTagStub = defineComponent({
  name: 'ElTagStub',
  props: {
    type: {
      type: String,
      default: 'info',
    },
  },
  template: '<span class="el-tag-stub" :data-type="type"><slot /></span>',
})

const mountPanel = async (extraProps: Record<string, unknown> = {}) => {
  const wrapper = mount(AssetProjectOverviewPanel, {
    props: {
      panel: {
        code: 'project_overview',
        titleKey: 'projects.panels.overview',
      },
      recordId: 'project-1',
      recordData: {
        projectName: 'Fallback Project',
      },
      ...extraProps,
    },
    global: {
      directives: {
        loading: {},
      },
      stubs: {
        'el-card': ElCardStub,
        'el-button': ElButtonStub,
        'el-tag': ElTagStub,
      },
    },
  })

  await flushPromises()
  return wrapper
}

describe('AssetProjectOverviewPanel', () => {
  beforeEach(() => {
    vi.mocked(request.get).mockReset()
  })

  it('loads and renders the unified workspace dashboard payload', async () => {
    vi.mocked(request.get).mockResolvedValue({
      project: {
        projectCode: 'XM2026030001',
        projectName: 'Workspace Project',
        status: 'active',
        statusLabel: 'Active',
        projectTypeLabel: 'Development',
        projectManagerName: 'Alice',
        departmentName: 'R&D',
        startDate: '2026-03-01',
        endDate: '2026-04-15',
        plannedBudget: '88000.00',
        actualCost: '21000.00',
        assetCost: '15200.00',
        completedMilestones: 3,
        totalMilestones: 5,
        progress: 60,
      },
      assets: {
        totalCount: 3,
        inUseCount: 1,
        returnedCount: 1,
        transferredCount: 1,
      },
      members: {
        totalCount: 2,
        activeCount: 1,
        primaryCount: 1,
        allocatorsCount: 1,
      },
      returns: {
        pendingCount: 1,
        completedCount: 1,
        rejectedCount: 1,
        processedCount: 2,
      },
    })

    const wrapper = await mountPanel()

    expect(request.get).toHaveBeenCalledWith(
      '/system/objects/AssetProject/project-1/workspace_dashboard/'
    )
    expect(wrapper.text()).toContain('Workspace overview')
    expect(wrapper.text()).toContain('Workspace Project')
    expect(wrapper.text()).toContain('Alice')
    expect(wrapper.text()).toContain('R&D')
    expect(wrapper.text()).toContain('Project assets')
    expect(wrapper.text()).toContain('Project members')
    expect(wrapper.text()).toContain('Return history')
    expect(wrapper.text()).toContain('3')
    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('3/5')
  })

  it('refreshes the workspace dashboard on demand', async () => {
    vi.mocked(request.get).mockResolvedValue({
      project: {
        projectCode: 'XM2026030002',
        projectName: 'Refresh Project',
        statusLabel: 'Planning',
      },
      assets: { totalCount: 0 },
      members: { totalCount: 0 },
      returns: { pendingCount: 0, processedCount: 0, completedCount: 0, rejectedCount: 0 },
    })

    const wrapper = await mountPanel()
    const refreshButton = wrapper.findAll('button').find((button) => button.text() === 'Refresh')

    expect(refreshButton).toBeDefined()

    await refreshButton!.trigger('click')
    await flushPromises()

    expect(request.get).toHaveBeenCalledTimes(2)
    expect(request.get).toHaveBeenNthCalledWith(
      2,
      '/system/objects/AssetProject/project-1/workspace_dashboard/'
    )
  })

  it('uses the shared workspace dashboard when provided by the workbench host', async () => {
    const wrapper = await mountPanel({
      workspaceDashboardEnabled: true,
      workspaceDashboardLoading: false,
      workspaceDashboard: {
        project: {
          projectCode: 'XM2026030099',
          projectName: 'Shared Dashboard Project',
          statusLabel: 'Active',
          projectManagerName: 'Shared Owner',
        },
        assets: { totalCount: 5, inUseCount: 2, returnedCount: 2, transferredCount: 1 },
        members: { totalCount: 3, activeCount: 2, primaryCount: 1, allocatorsCount: 1 },
        returns: { pendingCount: 1, processedCount: 2, completedCount: 1, rejectedCount: 1 },
      },
    })
    const refreshButton = wrapper.findAll('button').find((button) => button.text() === 'Refresh')

    expect(request.get).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Shared Dashboard Project')
    expect(wrapper.text()).toContain('Shared Owner')

    expect(refreshButton).toBeDefined()

    await refreshButton!.trigger('click')

    expect(wrapper.emitted('workbench-refresh-requested')).toEqual([
      [{ summary: true }],
    ])
  })
})
