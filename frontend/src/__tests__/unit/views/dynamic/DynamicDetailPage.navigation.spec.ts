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

const { getMetadataMock } = createMetadataApiMockContext()
const { resolveRuntimeLayoutMock } = createRuntimeLayoutMockContext()
const { pushMock, routeState } = createRouteMockContext({
  params: { code: 'Asset', id: 'asset-1' },
})

const CommonDynamicDetailPageStub = defineComponent({
  name: 'CommonDynamicDetailPage',
  emits: ['related-record-click', 'related-record-edit'],
  setup(_props, { emit }) {
    return () => h('div', { class: 'dynamic-detail-page-stub' }, [
      h('button', {
        class: 'emit-related-click',
        onClick: () => emit('related-record-click', 'maintenance_records', { id: 'm 1' }, 'Maintenance')
      }),
      h('button', {
        class: 'emit-related-edit',
        onClick: () => emit('related-record-edit', 'loan_records', { id: 'loan/1' })
      })
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
  })
}))

vi.mock('@/platform/layout/runtimeLayoutResolver', () => ({
  resolveRuntimeLayout: resolveRuntimeLayoutMock
}))

vi.mock('@/components/common/DynamicDetailPage.vue', () => ({
  default: CommonDynamicDetailPageStub
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
})
