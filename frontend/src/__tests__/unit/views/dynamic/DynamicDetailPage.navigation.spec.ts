import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, h, onMounted } from 'vue'
import {
  createDynamicDetailGlobalOptions,
} from './testUtils'
import { createRouteMockContext } from './routerTestUtils'
import {
  createMetadataApiMockContext,
  createRuntimeLayoutMockContext,
} from './apiTestUtils'
import { createPassthroughI18nMock } from './i18nTestUtils'

const {
  maintenanceListMock,
  disposalListMock,
} = vi.hoisted(() => ({
  maintenanceListMock: vi.fn(),
  disposalListMock: vi.fn(),
}))

const { getMetadataMock, getSlaMock, getClosureMock } = createMetadataApiMockContext()
const { resolveRuntimeLayoutMock } = createRuntimeLayoutMockContext()
const { pushMock, replaceMock, routeState } = createRouteMockContext({
  params: { code: 'Asset', id: 'asset-1' },
})
const getDocumentMock = vi.fn()

const CommonDynamicDetailPageStub = defineComponent({
  name: 'CommonDynamicDetailPage',
  props: {
    objectCode: {
      type: String,
      default: '',
    },
  },
  emits: ['related-record-click', 'related-record-edit', 'loaded'],
  setup(props, { emit, slots }) {
    onMounted(() => {
      const statusByObjectCode: Record<string, string> = {
        AssetProject: 'active',
        FinanceVoucher: 'submitted',
        InventoryItem: 'confirmed',
      }
      emit('loaded', {
        id: 'record-1',
        status: statusByObjectCode[props.objectCode] || 'draft',
        status_label: statusByObjectCode[props.objectCode] || 'draft',
        task_code: 'INV-001',
        difference_type_label: 'Missing',
        quantity_difference: -1,
        owner: {
          username: 'inventory-owner',
        },
      })
    })

    return () => h('div', { class: 'dynamic-detail-page-stub' }, [
      h('button', {
        class: 'emit-related-click',
        onClick: () => emit('related-record-click', 'maintenance_records', { id: 'm 1' }, 'Maintenance')
      }),
      h('button', {
        class: 'emit-related-edit',
        onClick: () => emit('related-record-edit', 'loan_records', { id: 'loan/1' })
      }),
      slots['action-bar']?.(),
      slots['after-sections']?.(),
    ])
  }
})

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  return {
    ...actual,
    useRoute: () => routeState,
    useRouter: () => ({
      push: pushMock,
      replace: replaceMock,
    })
  }
})

vi.mock('@/api/dynamic', () => ({
  createObjectClient: () => ({
    getMetadata: getMetadataMock,
    getSla: getSlaMock,
    getClosure: getClosureMock,
    getDocument: getDocumentMock,
  }),
  purchaseRequestApi: {},
  assetReceiptApi: {},
  maintenanceApi: {
    list: maintenanceListMock,
  },
  maintenancePlanApi: {},
  maintenanceTaskApi: {},
  disposalRequestApi: {
    list: disposalListMock,
  },
  assetWarrantyApi: {}
}))

vi.mock('@/platform/layout/runtimeLayoutResolver', () => ({
  resolveRuntimeLayout: resolveRuntimeLayoutMock
}))

vi.mock('@/components/common/DynamicDetailPage.vue', () => ({
  default: CommonDynamicDetailPageStub
}))

vi.mock('@/components/common/ClosedLoopNavigationCard.vue', () => ({
  default: defineComponent({
    name: 'ClosedLoopNavigationCard',
    props: ['title', 'hint', 'items'],
    template: '<div class="closed-loop-card-stub">{{ title }}|{{ hint }}|{{ Array.isArray(items) ? items.length : 0 }}</div>',
  }),
}))

vi.mock('@/components/common/ActivityTimeline.vue', () => ({
  default: defineComponent({
    name: 'ActivityTimeline',
    props: ['objectCode', 'recordId', 'fetchUrl'],
    template: '<div class="activity-timeline-stub">{{ objectCode }}|{{ recordId }}|{{ fetchUrl }}</div>',
  }),
}))

vi.mock('@/components/common/DocumentWorkbench.vue', () => ({
  default: defineComponent({
    name: 'DocumentWorkbench',
    props: ['objectCode', 'recordId', 'document', 'workbench'],
    template: '<div class="document-workbench-stub">{{ objectCode }}|{{ recordId }}|{{ workbench?.defaultPageMode || "--" }}</div>',
  }),
}))

vi.mock('@/components/common/ObjectActionBar.vue', () => ({
  default: defineComponent({
    name: 'ObjectActionBar',
    template: '<div class="object-action-bar-stub" />',
  }),
}))

vi.mock('@/components/common/ObjectWorkbenchActionBar.vue', () => ({
  default: defineComponent({
    name: 'ObjectWorkbenchActionBar',
    template: '<div class="object-workbench-action-bar-stub" />',
  }),
}))

vi.mock('@/components/common/ObjectWorkbenchPanelHost.vue', () => ({
  default: defineComponent({
    name: 'ObjectWorkbenchPanelHost',
    template: '<div class="object-workbench-panel-host-stub" />',
  }),
}))

vi.mock('@/components/common/WorkbenchSummaryCards.vue', () => ({
  default: defineComponent({
    name: 'WorkbenchSummaryCards',
    template: '<div class="workbench-summary-cards-stub" />',
  }),
}))

vi.mock('@/components/common/WorkbenchQueuePanel.vue', () => ({
  default: defineComponent({
    name: 'WorkbenchQueuePanel',
    template: '<div class="workbench-queue-panel-stub" />',
  }),
}))

vi.mock('@/components/common/ProcessSummaryPanel.vue', () => ({
  default: defineComponent({
    name: 'ProcessSummaryPanel',
    props: ['stats', 'panel', 'recordData', 'extraRows', 'navigationSection'],
    template: `
      <div class="process-summary-panel-stub">
        {{ navigationSection?.title || "--" }}|
        {{ Array.isArray(stats) ? stats.length : 0 }}|
        {{ Array.isArray(extraRows) ? extraRows.length : 0 }}|
        {{ navigationSection && Array.isArray(navigationSection.items) ? navigationSection.items.length : 0 }}|
        {{ recordData?.closure_summary?.stage || recordData?.closureSummary?.stage || "--" }}|
        {{ recordData?.closure_summary?.completion_display || recordData?.closureSummary?.completionDisplay || "--" }}
      </div>
    `,
  }),
}))

vi.mock('@/components/common/SlaIndicatorBar.vue', () => ({
  default: defineComponent({
    name: 'SlaIndicatorBar',
    props: ['indicators', 'recordData', 'slaData'],
    template: `
      <div class="sla-indicator-bar-stub">
        {{ Array.isArray(indicators) ? indicators.length : 0 }}|{{ slaData?.status || '--' }}|{{ slaData?.assignee?.displayName || '--' }}
      </div>
    `,
  }),
}))

vi.mock('@/components/common/RecommendedActionPanel.vue', () => ({
  default: defineComponent({
    name: 'RecommendedActionPanel',
    template: '<div class="recommended-action-panel-stub" />',
  }),
}))

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => createPassthroughI18nMock(),
  }
})

const ElTabsStub = defineComponent({
  name: 'ElTabsStub',
  props: {
    modelValue: {
      type: String,
      default: '',
    },
  },
  template: '<div class="el-tabs-stub" :data-model-value="modelValue"><slot /></div>',
})

const ElTabPaneStub = defineComponent({
  name: 'ElTabPaneStub',
  props: {
    label: {
      type: String,
      default: '',
    },
    name: {
      type: String,
      default: '',
    },
  },
  template: '<section class="el-tab-pane-stub" :data-label="label" :data-name="name"><slot /></section>',
})

const setHash = (hash = '') => {
  window.history.replaceState({}, '', `${window.location.pathname}${hash}`)
}

const buildWrapper = async (stubOverrides: Record<string, unknown> = {}) => {
  const DynamicDetailPage = (await import('@/views/dynamic/DynamicDetailPage.vue')).default
  return mount(DynamicDetailPage, {
    global: {
      ...createDynamicDetailGlobalOptions(),
      stubs: {
        ...createDynamicDetailGlobalOptions().stubs,
        ...stubOverrides,
      },
    },
  })
}

describe('DynamicDetailPage navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setHash('')
    routeState.params = { code: 'Asset', id: 'asset-1' }
    routeState.query = {}
    maintenanceListMock.mockResolvedValue({
      count: 2,
      results: [],
    })
    disposalListMock.mockResolvedValue({
      count: 1,
      results: [],
    })
    getMetadataMock.mockResolvedValue({
      code: 'Asset',
      name: 'Asset',
      module: 'Asset Center',
      permissions: { view: true, add: true, change: true, delete: true }
    })
    getSlaMock.mockResolvedValue({
      objectCode: 'Asset',
      businessId: 'asset-1',
      hasInstance: false,
      instanceId: null,
      instanceNo: null,
      instanceStatus: null,
      workflowName: '',
      status: 'unknown',
      dueDate: null,
      remainingHours: null,
      hoursOverdue: 0,
      isEscalated: false,
      assignee: null,
      currentNode: null,
      activeTaskId: null,
      activeTaskCount: 0,
      completedAt: null,
    })
    getClosureMock.mockResolvedValue({
      objectCode: 'Asset',
      businessId: 'asset-1',
      hasSummary: false,
      status: null,
      approvalStatus: null,
      workflowInstanceId: null,
      owner: '',
      stage: '',
      blocker: '',
      completion: null,
      completionDisplay: null,
      metrics: {},
    })
    getDocumentMock.mockResolvedValue({
      documentVersion: 1,
      context: {
        objectCode: 'Asset',
        recordId: 'asset-1',
        pageMode: 'readonly',
        recordLabel: 'REC-001',
      },
      aggregate: {
        objectCode: 'Asset',
        objectRole: 'root',
        isAggregateRoot: false,
        isDetailObject: false,
        detailRegions: [],
      },
      master: {
        status: 'draft',
      },
      details: {},
      capabilities: {
        canEditMaster: true,
        canEditDetails: true,
        canSave: true,
        canSubmit: true,
        canDelete: true,
        canApprove: true,
        readOnly: true,
      },
      workflow: {
        businessObjectCode: 'Asset',
        hasPublishedDefinition: false,
        definition: null,
        hasInstance: false,
        isActive: false,
        instance: null,
        timeline: [],
      },
      timeline: [],
      audit: {
        counts: {
          activityLogs: 0,
          workflowApprovals: 0,
          workflowOperationLogs: 0,
        },
        activityLogs: [],
        workflowApprovals: [],
        workflowOperationLogs: [],
      },
    })
    resolveRuntimeLayoutMock.mockResolvedValue({
      permissions: { view: true, add: true, change: true, delete: true }
    })
  })

  it('navigates to related detail using target object code', async () => {
    const wrapper = await buildWrapper()

    await flushPromises()
    await wrapper.get('.emit-related-click').trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/objects/Maintenance/m%201')
  })

  it('navigates to related edit using derived object code fallback', async () => {
    const wrapper = await buildWrapper()

    await flushPromises()
    await wrapper.get('.emit-related-edit').trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/objects/Loan/loan%2F1/edit')
  })

  it('renders the unified detail hero shell', async () => {
    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.find('.detail-hero__title').exists()).toBe(true)
    expect(wrapper.text()).toContain('Asset Center')
    expect(wrapper.text()).toContain('对象详情')
  })

  it('shows the permission denied state when view access is unavailable', async () => {
    getMetadataMock.mockResolvedValueOnce({
      code: 'Asset',
      name: 'Asset',
      module: 'Asset Center',
      permissions: { view: false, add: false, change: false, delete: false }
    })
    resolveRuntimeLayoutMock.mockResolvedValueOnce({
      permissions: { view: false, add: false, change: false, delete: false }
    })

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.text()).toContain('common.messages.permissionDenied')
    expect(wrapper.find('.dynamic-detail-page-stub').exists()).toBe(false)
  })

  it('shows the load failed state when metadata and runtime layout both fail', async () => {
    getMetadataMock.mockRejectedValueOnce(new Error('metadata failed'))
    resolveRuntimeLayoutMock.mockRejectedValueOnce(new Error('runtime failed'))

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.text()).toContain('common.messages.loadFailed')
    expect(wrapper.text()).toContain('metadata failed')
    expect(wrapper.find('.dynamic-detail-page-stub').exists()).toBe(false)
  })

  it('renders asset closed-loop navigation and lifecycle timeline enhancements', async () => {
    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.find('.process-summary-panel-stub').exists()).toBe(true)
    expect(wrapper.find('.process-summary-panel-stub').text()).toContain('common.detailNavigation.sections.lifecycleLinks')
    expect(wrapper.find('.activity-timeline-stub').text()).toContain('Asset|asset-1|/assets/asset-1/lifecycle-timeline/')
    expect(maintenanceListMock).toHaveBeenCalledWith({ asset_id: 'asset-1', page: 1, page_size: 1 })
    expect(disposalListMock).toHaveBeenCalledWith({ asset_id: 'asset-1', page: 1, page_size: 1 })
  })

  it('switches the detail surface tab when the activity hash is present', async () => {
    setHash('#detail-activity')

    const wrapper = await buildWrapper({
      'el-tabs': ElTabsStub,
      'el-tab-pane': ElTabPaneStub,
    })

    await flushPromises()

    expect(wrapper.get('.el-tabs-stub').attributes('data-model-value')).toBe('activity')
  })

  it('keeps finance voucher record mode focused on primary and context surfaces', async () => {
    routeState.params = { code: 'FinanceVoucher', id: 'voucher-1' }
    getMetadataMock.mockResolvedValueOnce({
      code: 'FinanceVoucher',
      name: 'Finance Voucher',
      module: 'Finance',
      permissions: { view: true, add: true, change: true, delete: true }
    })
    resolveRuntimeLayoutMock.mockResolvedValueOnce({
      permissions: { view: true, add: true, change: true, delete: false },
      workbench: {
        workspaceMode: 'extended',
        primaryEntryRoute: '/objects/FinanceVoucher',
        legacyAliases: ['/finance/vouchers'],
        toolbar: {
          primaryActions: [{ code: 'post' }],
          secondaryActions: [],
        },
        detailPanels: [{ code: 'integration_logs', component: 'finance-voucher-integration-logs', surfacePriority: 'related' }],
        asyncIndicators: [],
        summaryCards: [{ code: 'total_amount', valueField: 'total_amount', surfacePriority: 'primary' }],
        queuePanels: [{ code: 'approval_queue', count: 1, route: '/objects/FinanceVoucher?status=submitted', surfacePriority: 'related' }],
        exceptionPanels: [{ code: 'push_failed', count: 0, route: '/objects/FinanceVoucher?status=approved', surfacePriority: 'related' }],
        closurePanel: { stageField: 'status', ownerField: 'created_by.username', surfacePriority: 'context' },
        slaIndicators: [{ code: 'approval_sla', status: 'approaching_sla', surfacePriority: 'context' }],
        recommendedActions: [{ code: 'submit', actionPath: 'submit', surfacePriority: 'admin' }],
      },
    })

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.find('.object-workbench-action-bar-stub').exists()).toBe(true)
    expect(wrapper.find('.workbench-summary-cards-stub').exists()).toBe(true)
    expect(wrapper.find('.workbench-queue-panel-stub').exists()).toBe(false)
    expect(wrapper.find('.process-summary-panel-stub').exists()).toBe(true)
    expect(wrapper.find('.sla-indicator-bar-stub').exists()).toBe(true)
    expect(wrapper.find('.recommended-action-panel-stub').exists()).toBe(false)
    expect(wrapper.find('.object-workbench-panel-host-stub').exists()).toBe(false)
  })

  it('expands related and admin surfaces for extended workbench objects in workspace mode', async () => {
    routeState.params = { code: 'FinanceVoucher', id: 'voucher-1' }
    routeState.query = { page_mode: 'workspace' }
    getMetadataMock.mockResolvedValueOnce({
      code: 'FinanceVoucher',
      name: 'Finance Voucher',
      module: 'Finance',
      permissions: { view: true, add: true, change: true, delete: true }
    })
    resolveRuntimeLayoutMock.mockResolvedValueOnce({
      permissions: { view: true, add: true, change: true, delete: false },
      workbench: {
        workspaceMode: 'extended',
        primaryEntryRoute: '/objects/FinanceVoucher',
        legacyAliases: ['/finance/vouchers'],
        toolbar: {
          primaryActions: [{ code: 'post' }],
          secondaryActions: [],
        },
        detailPanels: [{ code: 'integration_logs', component: 'finance-voucher-integration-logs', surfacePriority: 'related' }],
        asyncIndicators: [],
        summaryCards: [{ code: 'total_amount', valueField: 'total_amount', surfacePriority: 'primary' }],
        queuePanels: [{ code: 'approval_queue', count: 1, route: '/objects/FinanceVoucher?status=submitted', surfacePriority: 'related' }],
        exceptionPanels: [{ code: 'push_failed', count: 0, route: '/objects/FinanceVoucher?status=approved', surfacePriority: 'related' }],
        closurePanel: { stageField: 'status', ownerField: 'created_by.username', surfacePriority: 'context' },
        slaIndicators: [{ code: 'approval_sla', status: 'approaching_sla', surfacePriority: 'context' }],
        recommendedActions: [{ code: 'submit', actionPath: 'submit', surfacePriority: 'admin' }],
      },
    })

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.find('.workbench-summary-cards-stub').exists()).toBe(true)
    expect(wrapper.find('.workbench-queue-panel-stub').exists()).toBe(true)
    expect(wrapper.find('.recommended-action-panel-stub').exists()).toBe(true)
    expect(wrapper.find('.object-workbench-panel-host-stub').exists()).toBe(true)
  })

  it('passes object-level SLA data into the workbench indicator area', async () => {
    getSlaMock.mockResolvedValueOnce({
      objectCode: 'Asset',
      businessId: 'asset-1',
      hasInstance: true,
      instanceId: 'wf-1',
      instanceNo: 'WF-001',
      instanceStatus: 'pending_approval',
      workflowName: 'Asset Approval',
      status: 'overdue',
      dueDate: '2026-03-30 12:00:00',
      remainingHours: 0,
      hoursOverdue: 4,
      isEscalated: false,
      assignee: {
        id: 'user-1',
        username: 'approver',
        displayName: 'Approver',
      },
      currentNode: {
        id: 'approval_1',
        name: 'Department Approval',
      },
      activeTaskId: 'task-1',
      activeTaskCount: 1,
      completedAt: null,
    })
    resolveRuntimeLayoutMock.mockResolvedValueOnce({
      permissions: { view: true, add: true, change: true, delete: true },
      workbench: {
        workspaceMode: 'extended',
        primaryEntryRoute: '/objects/Asset',
        legacyAliases: [],
        toolbar: {
          primaryActions: [],
          secondaryActions: [],
        },
        detailPanels: [],
        asyncIndicators: [],
        summaryCards: [],
        queuePanels: [],
        exceptionPanels: [],
        closurePanel: null,
        slaIndicators: [
          {
            code: 'approval_sla',
            label: 'Approval SLA',
          },
        ],
        recommendedActions: [],
      },
    })

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(getSlaMock).toHaveBeenCalledWith('asset-1')
    expect(wrapper.find('.sla-indicator-bar-stub').text()).toContain('1|overdue|Approver')
  })

  it('merges object-level closure data into the workbench record payload', async () => {
    getClosureMock.mockResolvedValueOnce({
      objectCode: 'InventoryTask',
      businessId: 'asset-1',
      hasSummary: true,
      status: 'completed',
      approvalStatus: 'approved',
      workflowInstanceId: 'wf-1',
      owner: 'Primary Executor',
      stage: 'Awaiting closure',
      blocker: 'Resolved differences still need final closure.',
      completion: 80,
      completionDisplay: '80%',
      metrics: {},
    })
    resolveRuntimeLayoutMock.mockResolvedValueOnce({
      permissions: { view: true, add: true, change: true, delete: true },
      workbench: {
        workspaceMode: 'extended',
        primaryEntryRoute: '/objects/InventoryTask',
        legacyAliases: [],
        toolbar: {
          primaryActions: [],
          secondaryActions: [],
        },
        detailPanels: [],
        asyncIndicators: [],
        summaryCards: [],
        queuePanels: [],
        exceptionPanels: [],
        closurePanel: {
          stageField: 'closure_summary.stage',
          ownerField: 'closure_summary.owner',
          progressField: 'closure_summary.completion_display',
        },
        slaIndicators: [],
        recommendedActions: [],
      },
    })

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(getClosureMock).toHaveBeenCalledWith('asset-1')
    expect(wrapper.find('.process-summary-panel-stub').text()).toContain('Awaiting closure')
    expect(wrapper.find('.process-summary-panel-stub').text()).toContain('80%')
  })

  it('renders AssetProject workbench actions and panels on the unified detail page', async () => {
    routeState.params = { code: 'AssetProject', id: 'project-1' }
    getMetadataMock.mockResolvedValueOnce({
      code: 'AssetProject',
      name: 'Asset Project',
      module: 'Projects',
      permissions: { view: true, add: true, change: true, delete: true }
    })
    resolveRuntimeLayoutMock.mockResolvedValueOnce({
      permissions: { view: true, add: true, change: true, delete: false },
      workbench: {
        workspaceMode: 'extended',
        primaryEntryRoute: '/objects/AssetProject',
        legacyAliases: [],
        toolbar: {
          primaryActions: [{ code: 'refresh_rollups' }],
          secondaryActions: [],
        },
        detailPanels: [
          { code: 'project_overview', component: 'asset-project-overview' },
          { code: 'project_assets', component: 'asset-project-assets' },
          { code: 'project_members', component: 'asset-project-members' },
          { code: 'project_returns', component: 'asset-project-returns' },
          { code: 'project_return_history', component: 'asset-project-return-history' },
        ],
        asyncIndicators: [],
        summaryCards: [],
        queuePanels: [],
        exceptionPanels: [],
        closurePanel: null,
        slaIndicators: [],
        recommendedActions: [],
      },
    })

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.text()).toContain('Projects')
    expect(wrapper.find('.object-workbench-action-bar-stub').exists()).toBe(true)
    expect(wrapper.find('.object-workbench-panel-host-stub').exists()).toBe(true)
  })

  it('renders InventoryItem closure workbench actions on the unified detail page', async () => {
    routeState.params = { code: 'InventoryItem', id: 'difference-1' }
    getMetadataMock.mockResolvedValueOnce({
      code: 'InventoryItem',
      name: 'Inventory Difference',
      module: 'Inventory',
      permissions: { view: true, add: true, change: true, delete: true }
    })
    resolveRuntimeLayoutMock.mockResolvedValueOnce({
      permissions: { view: true, add: true, change: true, delete: false },
      workbench: {
        workspaceMode: 'extended',
        primaryEntryRoute: '/objects/InventoryItem',
        legacyAliases: ['/inventory/items'],
        toolbar: {
          primaryActions: [{ code: 'submit_review', actionPath: 'submit-review' }],
          secondaryActions: [{ code: 'ignore', actionPath: 'ignore' }],
        },
        detailPanels: [],
        asyncIndicators: [],
        summaryCards: [{ code: 'difference_type', valueField: 'difference_type_label' }],
        queuePanels: [],
        exceptionPanels: [],
        closurePanel: { stageField: 'status_label', ownerField: 'owner.username', progressField: 'closure_completed_at' },
        slaIndicators: [],
        recommendedActions: [{ code: 'submit_review_hint', actionPath: 'submit-review' }],
      },
    })

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.find('.object-workbench-action-bar-stub').exists()).toBe(true)
    expect(wrapper.find('.workbench-summary-cards-stub').exists()).toBe(true)
    expect(wrapper.find('.process-summary-panel-stub').exists()).toBe(true)
    expect(wrapper.find('.recommended-action-panel-stub').exists()).toBe(true)
  })

  it('defaults aggregate objects to record mode when configured by runtime workbench', async () => {
    routeState.params = { code: 'AssetPickup', id: 'pickup-1' }
    getMetadataMock.mockResolvedValueOnce({
      code: 'AssetPickup',
      name: 'Asset Pickup',
      module: 'Operations',
      permissions: { view: true, add: true, change: true, delete: true },
    })
    resolveRuntimeLayoutMock.mockResolvedValueOnce({
      permissions: { view: true, add: true, change: true, delete: true },
      aggregate: {
        objectCode: 'AssetPickup',
        objectRole: 'root',
        isAggregateRoot: true,
        isDetailObject: false,
        detailRegions: [
          {
            relationCode: 'pickup_items',
            fieldCode: 'items',
            title: 'Pickup Items',
            targetObjectCode: 'PickupItem',
          },
        ],
      },
      workbench: {
        workspaceMode: 'extended',
        primaryEntryRoute: '/objects/AssetPickup',
        defaultPageMode: 'record',
        defaultDetailSurfaceTab: 'process',
        defaultDocumentSurfaceTab: 'summary',
        legacyAliases: [],
        toolbar: { primaryActions: [], secondaryActions: [] },
        detailPanels: [],
        asyncIndicators: [],
        summaryCards: [],
        queuePanels: [],
        exceptionPanels: [],
        closurePanel: null,
        slaIndicators: [],
        recommendedActions: [],
      },
    })
    getDocumentMock.mockResolvedValueOnce({
      documentVersion: 1,
      context: {
        objectCode: 'AssetPickup',
        recordId: 'pickup-1',
        pageMode: 'readonly',
        recordLabel: 'PU-0001',
      },
      aggregate: {
        objectCode: 'AssetPickup',
        objectRole: 'root',
        isAggregateRoot: true,
        isDetailObject: false,
        detailRegions: [
          {
            relationCode: 'pickup_items',
            fieldCode: 'items',
            title: 'Pickup Items',
            targetObjectCode: 'PickupItem',
          },
        ],
      },
      master: { status: 'draft' },
      details: {},
      capabilities: {
        canEditMaster: true,
        canEditDetails: true,
        canSave: true,
        canSubmit: true,
        canDelete: true,
        canApprove: true,
        readOnly: true,
      },
      workflow: {
        businessObjectCode: 'AssetPickup',
        hasPublishedDefinition: false,
        definition: null,
        hasInstance: false,
        isActive: false,
        instance: null,
        timeline: [],
      },
      timeline: [],
      audit: {
        counts: {
          activityLogs: 0,
          workflowApprovals: 0,
          workflowOperationLogs: 0,
        },
        activityLogs: [],
        workflowApprovals: [],
        workflowOperationLogs: [],
      },
    })

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.find('.dynamic-detail-page-stub').exists()).toBe(true)
    expect(wrapper.find('.document-workbench-stub').exists()).toBe(false)
    expect(getDocumentMock).toHaveBeenCalledWith('pickup-1', 'readonly')
  })

  it('supports page_mode query override for aggregate workspace mode', async () => {
    routeState.params = { code: 'AssetPickup', id: 'pickup-1' }
    routeState.query = { page_mode: 'workspace' }
    getMetadataMock.mockResolvedValueOnce({
      code: 'AssetPickup',
      name: 'Asset Pickup',
      module: 'Operations',
      permissions: { view: true, add: true, change: true, delete: true },
    })
    resolveRuntimeLayoutMock.mockResolvedValueOnce({
      permissions: { view: true, add: true, change: true, delete: true },
      aggregate: {
        objectCode: 'AssetPickup',
        objectRole: 'root',
        isAggregateRoot: true,
        isDetailObject: false,
        detailRegions: [
          {
            relationCode: 'pickup_items',
            fieldCode: 'items',
            title: 'Pickup Items',
            targetObjectCode: 'PickupItem',
          },
        ],
      },
      workbench: {
        workspaceMode: 'extended',
        primaryEntryRoute: '/objects/AssetPickup',
        defaultPageMode: 'record',
        defaultDetailSurfaceTab: 'process',
        defaultDocumentSurfaceTab: 'summary',
        legacyAliases: [],
        toolbar: { primaryActions: [], secondaryActions: [] },
        detailPanels: [],
        asyncIndicators: [],
        summaryCards: [],
        queuePanels: [],
        exceptionPanels: [],
        closurePanel: null,
        slaIndicators: [],
        recommendedActions: [],
      },
    })
    getDocumentMock.mockResolvedValueOnce({
      documentVersion: 1,
      context: {
        objectCode: 'AssetPickup',
        recordId: 'pickup-1',
        pageMode: 'readonly',
        recordLabel: 'PU-0001',
      },
      aggregate: {
        objectCode: 'AssetPickup',
        objectRole: 'root',
        isAggregateRoot: true,
        isDetailObject: false,
        detailRegions: [
          {
            relationCode: 'pickup_items',
            fieldCode: 'items',
            title: 'Pickup Items',
            targetObjectCode: 'PickupItem',
          },
        ],
      },
      master: { status: 'draft' },
      details: {},
      capabilities: {
        canEditMaster: true,
        canEditDetails: true,
        canSave: true,
        canSubmit: true,
        canDelete: true,
        canApprove: true,
        readOnly: true,
      },
      workflow: {
        businessObjectCode: 'AssetPickup',
        hasPublishedDefinition: false,
        definition: null,
        hasInstance: false,
        isActive: false,
        instance: null,
        timeline: [],
      },
      timeline: [],
      audit: {
        counts: {
          activityLogs: 0,
          workflowApprovals: 0,
          workflowOperationLogs: 0,
        },
        activityLogs: [],
        workflowApprovals: [],
        workflowOperationLogs: [],
      },
    })

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.find('.document-workbench-stub').exists()).toBe(true)
    expect(wrapper.find('.document-workbench-stub').text()).toContain('AssetPickup|pickup-1|record')
    expect(wrapper.find('.dynamic-detail-page-stub').exists()).toBe(false)
  })
})
