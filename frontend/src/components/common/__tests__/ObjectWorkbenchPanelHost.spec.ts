import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import request from '@/utils/request'
import ObjectWorkbenchPanelHost from '../ObjectWorkbenchPanelHost.vue'

vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn(),
  },
}))

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          'common.actions.loadMore': 'Load More',
          'projects.panels.assets': 'Project assets',
          'projects.panels.assetsHint': 'Allocated assets, usage status, and cost snapshots.',
          'projects.messages.lazyPanelHint': 'This panel loads when it enters view. Click to load it immediately.',
        }
        return translations[key] || key
      },
      te: (key: string) => [
        'projects.panels.assets',
        'projects.panels.assetsHint',
      ].includes(key),
    }),
  }
})

const { panelStubFactories } = vi.hoisted(() => {
  const buildPanelStub = (name: string) => ({
    name,
    props: {
      panel: {
        type: Object,
        default: () => ({}),
      },
      workspaceDashboard: {
        type: Object,
        default: null,
      },
      workspaceDashboardEnabled: Boolean,
      workspaceDashboardLoading: Boolean,
      panelRefreshVersion: {
        type: Number,
        default: 0,
      },
    },
    emits: ['refresh-requested', 'task-complete', 'workbench-refresh-requested'],
    template: `
      <div class="panel-stub-shell">
        <div class="panel-stub">
          {{ panel.code }}|{{ workspaceDashboardEnabled ? 'shared' : 'local' }}|{{ workspaceDashboard?.assets?.totalCount ?? '--' }}|{{ workspaceDashboard?.returns?.pendingCount ?? '--' }}|{{ workspaceDashboardLoading ? 'loading' : 'loaded' }}|{{ panelRefreshVersion }}
        </div>
        <button
          class="panel-refresh-button"
          @click="$emit('workbench-refresh-requested', { summary: true, panels: ['project_return_history'] })"
        >
          emit-refresh
        </button>
      </div>
    `,
  })

  return {
    panelStubFactories: {
      assetProjectOverview: buildPanelStub('AssetProjectOverviewPanelStub'),
      assetProjectAssets: buildPanelStub('AssetProjectAssetsPanelStub'),
      assetProjectMembers: buildPanelStub('AssetProjectMembersPanelStub'),
      assetProjectReturns: buildPanelStub('AssetProjectReturnsPanelStub'),
      assetProjectReturnHistory: buildPanelStub('AssetProjectReturnHistoryPanelStub'),
      financeVoucherEntries: buildPanelStub('FinanceVoucherEntriesPanelStub'),
      financeVoucherIntegrationLogs: buildPanelStub('FinanceVoucherIntegrationLogsPanelStub'),
      financeVoucherSyncStatus: buildPanelStub('FinanceVoucherSyncStatusPanelStub'),
      inventoryDifferenceClosure: buildPanelStub('InventoryDifferenceClosurePanelStub'),
      inventoryTaskExecutorProgress: buildPanelStub('InventoryTaskExecutorProgressPanelStub'),
    },
  }
})

vi.mock('@/components/projects/AssetProjectOverviewPanel.vue', () => ({
  default: panelStubFactories.assetProjectOverview,
}))

vi.mock('@/components/projects/AssetProjectAssetsPanel.vue', () => ({
  default: panelStubFactories.assetProjectAssets,
}))

vi.mock('@/components/projects/AssetProjectMembersPanel.vue', () => ({
  default: panelStubFactories.assetProjectMembers,
}))

vi.mock('@/components/projects/AssetProjectReturnsPanel.vue', () => ({
  default: panelStubFactories.assetProjectReturns,
}))

vi.mock('@/components/projects/AssetProjectReturnHistoryPanel.vue', () => ({
  default: panelStubFactories.assetProjectReturnHistory,
}))

vi.mock('@/components/finance/FinanceVoucherEntriesPanel.vue', () => ({
  default: panelStubFactories.financeVoucherEntries,
}))

vi.mock('@/components/finance/FinanceVoucherIntegrationLogsPanel.vue', () => ({
  default: panelStubFactories.financeVoucherIntegrationLogs,
}))

vi.mock('@/components/finance/FinanceVoucherSyncStatusPanel.vue', () => ({
  default: panelStubFactories.financeVoucherSyncStatus,
}))

vi.mock('@/components/inventory/InventoryDifferenceClosurePanel.vue', () => ({
  default: panelStubFactories.inventoryDifferenceClosure,
}))

vi.mock('@/components/inventory/InventoryTaskExecutorProgressPanel.vue', () => ({
  default: panelStubFactories.inventoryTaskExecutorProgress,
}))

describe('ObjectWorkbenchPanelHost', () => {
  beforeEach(() => {
    vi.mocked(request.get).mockReset()
    ;(globalThis as { IntersectionObserver?: typeof IntersectionObserver }).IntersectionObserver = class {
      observe = vi.fn()
      unobserve = vi.fn()
      disconnect = vi.fn()
      constructor(_callback: IntersectionObserverCallback, _options?: IntersectionObserverInit) {}
    } as unknown as typeof IntersectionObserver
  })

  it('loads shared workspace dashboard once and defers list panels until activation', async () => {
    vi.mocked(request.get).mockResolvedValue({
      assets: { totalCount: 8 },
      returns: { pendingCount: 2 },
    })

    const wrapper = mount(ObjectWorkbenchPanelHost, {
      props: {
        objectCode: 'AssetProject',
        recordId: 'project-1',
        recordData: { status: 'active' },
        workbench: {
          workspaceMode: 'extended',
          primaryEntryRoute: '/objects/AssetProject',
          detailPanels: [
            { code: 'project_overview', component: 'asset-project-overview' },
            { code: 'project_assets', component: 'asset-project-assets' },
          ],
          toolbar: { primaryActions: [], secondaryActions: [] },
          asyncIndicators: [],
          summaryCards: [],
          queuePanels: [],
          exceptionPanels: [],
          closurePanel: null,
          slaIndicators: [],
          recommendedActions: [],
          legacyAliases: [],
        },
      },
    })

    await flushPromises()

    expect(request.get).toHaveBeenCalledWith(
      '/system/objects/AssetProject/project-1/workspace_dashboard/'
    )
    expect(wrapper.text()).toContain('project_overview|shared|8|2|loaded|0')
    expect(wrapper.text()).not.toContain('project_assets|shared|8|2|loaded|0')
    expect(wrapper.text()).toContain('project_assets')
    expect(wrapper.text()).toContain('Load More')

    const loadButton = wrapper.findAll('button').find((button) => button.text() === 'Load More')

    expect(loadButton).toBeDefined()

    await loadButton!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('project_assets|shared|8|2|loaded|0')
    expect(request.get).toHaveBeenCalledTimes(1)
  })

  it('handles targeted panel refresh requests without bubbling a full detail refresh', async () => {
    vi.mocked(request.get)
      .mockResolvedValueOnce({
        assets: { totalCount: 8 },
        returns: { pendingCount: 2 },
      })
      .mockResolvedValueOnce({
        assets: { totalCount: 6 },
        returns: { pendingCount: 1 },
      })

    const wrapper = mount(ObjectWorkbenchPanelHost, {
      props: {
        objectCode: 'AssetProject',
        recordId: 'project-1',
        recordData: { status: 'active' },
        workbench: {
          workspaceMode: 'extended',
          primaryEntryRoute: '/objects/AssetProject',
          detailPanels: [
            { code: 'project_overview', component: 'asset-project-overview' },
            { code: 'project_return_history', component: 'asset-project-return-history' },
          ],
          toolbar: { primaryActions: [], secondaryActions: [] },
          asyncIndicators: [],
          summaryCards: [],
          queuePanels: [],
          exceptionPanels: [],
          closurePanel: null,
          slaIndicators: [],
          recommendedActions: [],
          legacyAliases: [],
        },
      },
    })

    await flushPromises()

    const loadButtons = wrapper.findAll('button').filter((button) => button.text() === 'Load More')
    expect(loadButtons).toHaveLength(1)

    await loadButtons[0].trigger('click')
    await flushPromises()

    const refreshButtons = wrapper.findAll('.panel-refresh-button')
    expect(refreshButtons).toHaveLength(2)

    await refreshButtons[0].trigger('click')
    await flushPromises()

    expect(request.get).toHaveBeenCalledTimes(2)
    expect(wrapper.text()).toContain('project_return_history|shared|6|1|loaded|1')
    expect(wrapper.emitted('refresh-requested')).toBeFalsy()
  })

  it('does not request shared workspace dashboard for non-project workbenches', async () => {
    const wrapper = mount(ObjectWorkbenchPanelHost, {
      props: {
        objectCode: 'FinanceVoucher',
        recordId: 'voucher-1',
        recordData: { status: 'draft' },
        workbench: {
          workspaceMode: 'extended',
          primaryEntryRoute: '/objects/FinanceVoucher',
          detailPanels: [
            { code: 'integration_logs', component: 'finance-voucher-integration-logs' },
          ],
          toolbar: { primaryActions: [], secondaryActions: [] },
          asyncIndicators: [],
          summaryCards: [],
          queuePanels: [],
          exceptionPanels: [],
          closurePanel: null,
          slaIndicators: [],
          recommendedActions: [],
          legacyAliases: [],
        },
      },
    })

    await flushPromises()

    expect(request.get).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('integration_logs|local|--|--|loaded')
  })

  it('renders the inventory difference closure panel for InventoryItem workbenches', async () => {
    const wrapper = mount(ObjectWorkbenchPanelHost, {
      props: {
        objectCode: 'InventoryItem',
        recordId: 'difference-1',
        recordData: { status: 'confirmed' },
        workbench: {
          workspaceMode: 'extended',
          primaryEntryRoute: '/objects/InventoryItem',
          detailPanels: [
            { code: 'difference_closure', component: 'inventory-difference-closure' },
          ],
          toolbar: { primaryActions: [], secondaryActions: [] },
          asyncIndicators: [],
          summaryCards: [],
          queuePanels: [],
          exceptionPanels: [],
          closurePanel: null,
          slaIndicators: [],
          recommendedActions: [],
          legacyAliases: [],
        },
      },
    })

    await flushPromises()

    expect(request.get).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('difference_closure|local|--|--|loaded')
  })

  it('renders the executor progress panel for InventoryTask workbenches', async () => {
    const wrapper = mount(ObjectWorkbenchPanelHost, {
      props: {
        objectCode: 'InventoryTask',
        recordId: 'task-1',
        recordData: { status: 'in_progress' },
        workbench: {
          workspaceMode: 'extended',
          primaryEntryRoute: '/objects/InventoryTask',
          detailPanels: [
            { code: 'executor_progress', component: 'inventory-task-executor-progress' },
          ],
          toolbar: { primaryActions: [], secondaryActions: [] },
          asyncIndicators: [],
          summaryCards: [],
          queuePanels: [],
          exceptionPanels: [],
          closurePanel: null,
          slaIndicators: [],
          recommendedActions: [],
          legacyAliases: [],
        },
      },
    })

    await flushPromises()

    expect(request.get).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('executor_progress|local|--|--|loaded')
  })
})
