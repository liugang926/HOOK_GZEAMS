import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
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

const { getMetadataMock } = createMetadataApiMockContext()
const { resolveRuntimeLayoutMock } = createRuntimeLayoutMockContext()
const { pushMock, routeState } = createRouteMockContext({
  params: { code: 'Asset', id: 'asset-1' },
})

const CommonDynamicDetailPageStub = defineComponent({
  name: 'CommonDynamicDetailPage',
  emits: ['related-record-click', 'related-record-edit'],
  setup(_props, { emit, slots }) {
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
      push: pushMock
    })
  }
})

vi.mock('@/api/dynamic', () => ({
  createObjectClient: () => ({
    getMetadata: getMetadataMock
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

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => createPassthroughI18nMock(),
  }
})

const buildWrapper = async () => {
  const DynamicDetailPage = (await import('@/views/dynamic/DynamicDetailPage.vue')).default
  return mount(DynamicDetailPage, {
    global: createDynamicDetailGlobalOptions()
  })
}

describe('DynamicDetailPage navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    routeState.params = { code: 'Asset', id: 'asset-1' }
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

    expect(wrapper.find('.closed-loop-card-stub').exists()).toBe(true)
    expect(wrapper.find('.closed-loop-card-stub').text()).toContain('common.detailNavigation.sections.lifecycleLinks')
    expect(wrapper.find('.activity-timeline-stub').text()).toContain('Asset|asset-1|/assets/asset-1/lifecycle-timeline/')
    expect(maintenanceListMock).toHaveBeenCalledWith({ asset_id: 'asset-1', page: 1, page_size: 1 })
    expect(disposalListMock).toHaveBeenCalledWith({ asset_id: 'asset-1', page: 1, page_size: 1 })
  })

  it('renders runtime workbench action and panel hosts for finance vouchers', async () => {
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
        detailPanels: [{ code: 'integration_logs', component: 'finance-voucher-integration-logs' }],
        asyncIndicators: [],
      },
    })

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.find('.object-workbench-action-bar-stub').exists()).toBe(true)
    expect(wrapper.find('.object-workbench-panel-host-stub').exists()).toBe(true)
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
      },
    })

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.text()).toContain('Projects')
    expect(wrapper.find('.object-workbench-action-bar-stub').exists()).toBe(true)
    expect(wrapper.find('.object-workbench-panel-host-stub').exists()).toBe(true)
  })
})
