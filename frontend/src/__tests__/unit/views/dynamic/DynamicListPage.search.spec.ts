import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, h, onMounted } from 'vue'
import {
  createDynamicListGlobalOptions,
} from './testUtils'
import { createRouteMockContext } from './routerTestUtils'
import {
  createListApiMockContext,
  createRuntimeLayoutMockContext,
} from './apiTestUtils'
import { createPassthroughI18nMock } from './i18nTestUtils'

const { listMock, getMetadataMock, batchDeleteMock, deleteMock } = createListApiMockContext()
const { resolveRuntimeLayoutMock } = createRuntimeLayoutMockContext()
const { pushMock, routeState } = createRouteMockContext({
  params: { code: 'Asset' },
  path: '/objects/Asset',
})

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  return {
    ...actual,
    useRoute: () => routeState,
    useRouter: () => ({
      push: pushMock,
    }),
  }
})

vi.mock('@/api/dynamic', () => ({
  createObjectClient: () => ({
    list: listMock,
    getMetadata: getMetadataMock,
    batchDelete: batchDeleteMock,
    delete: deleteMock,
  }),
}))

vi.mock('@/platform/layout/runtimeLayoutResolver', () => ({
  resolveRuntimeLayout: resolveRuntimeLayoutMock,
}))

vi.mock('@/components/common/BaseListPage.vue', () => ({
  default: defineComponent({
    name: 'BaseListPageStub',
    props: ['api'],
    setup(props, { slots }) {
      onMounted(async () => {
        await props.api({
          page: 1,
          pageSize: 20,
          __unifiedKeyword: '鎴村皵',
          __unifiedField: '__all',
          __visibleFieldCodes: ['asset_code', 'asset_name'],
        })
      })
      return () => h('div', { class: 'base-list-page-stub' }, [
        slots.toolbar ? slots.toolbar() : null,
        slots.actions ? slots.actions({
          row: {
            id: 'project-1',
            assetCount: 3,
            memberCount: 2,
          },
        }) : null,
      ])
    },
  }),
}))

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    createI18n: actual.createI18n,
    useI18n: () => createPassthroughI18nMock('zh-CN', true),
  }
})

describe('DynamicListPage unified search', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    routeState.params = { code: 'Asset' }
    routeState.path = '/objects/Asset'
    routeState.query = {}
    getMetadataMock.mockResolvedValue({
      code: 'Asset',
      name: 'Asset',
      icon: 'Box',
      permissions: { view: true, add: true, change: true, delete: true },
      fields: [
        { code: 'asset_code', name: 'Asset code', fieldType: 'text', showInList: true, isSearchable: true },
        { code: 'asset_name', name: 'Asset name', fieldType: 'text', showInList: true, isSearchable: true },
        { code: 'brand', name: 'Brand', fieldType: 'text', showInList: false },
      ],
      layouts: {},
    })
    resolveRuntimeLayoutMock.mockResolvedValue({
      fields: [
        { code: 'asset_code', name: 'Asset code', fieldType: 'text', showInList: true, isSearchable: true },
        { code: 'asset_name', name: 'Asset name', fieldType: 'text', showInList: true, isSearchable: true },
        { code: 'brand', name: 'Brand', fieldType: 'text', showInList: false },
      ],
      layoutConfig: null,
      permissions: { view: true, add: true, change: true, delete: true },
    })
    listMock.mockResolvedValue({
      count: 0,
      results: [],
      next: null,
      previous: null,
    })
  })

  it('passes the unified search keyword to the list api', async () => {
    const DynamicListPage = (await import('@/views/dynamic/DynamicListPage.vue')).default

    mount(DynamicListPage, {
      global: createDynamicListGlobalOptions(),
    })

    await flushPromises()

    expect(listMock).toHaveBeenCalledWith(
      expect.objectContaining({
        page: 1,
        pageSize: 20,
        search: '鎴村皵',
      }),
    )
  })

  it('navigates to the create route when clicking the create button', async () => {
    const DynamicListPage = (await import('@/views/dynamic/DynamicListPage.vue')).default

    const wrapper = mount(DynamicListPage, {
      global: createDynamicListGlobalOptions(true),
    })

    await flushPromises()

    const createButton = wrapper.findAll('button').find((button) => button.text() === 'common.actions.create')

    expect(createButton).toBeDefined()

    await createButton!.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/objects/Asset/create')
  })

  it('renders the unified list hero shell', async () => {
    const DynamicListPage = (await import('@/views/dynamic/DynamicListPage.vue')).default

    const wrapper = mount(DynamicListPage, {
      global: createDynamicListGlobalOptions(),
    })

    await flushPromises()

    expect(wrapper.find('.list-hero__title').exists()).toBe(true)
    expect(wrapper.find('.list-panel__title').exists()).toBe(true)
    expect(wrapper.text()).toContain('Asset')
  })

  it('renders the load failed state when metadata and runtime layout both fail', async () => {
    getMetadataMock.mockRejectedValueOnce(new Error('metadata failed'))
    resolveRuntimeLayoutMock.mockRejectedValueOnce(new Error('runtime failed'))

    const DynamicListPage = (await import('@/views/dynamic/DynamicListPage.vue')).default

    const wrapper = mount(DynamicListPage, {
      global: createDynamicListGlobalOptions(),
    })

    await flushPromises()

    expect(wrapper.text()).toContain('common.messages.loadFailed')
    expect(wrapper.text()).toContain('runtime failed')
    expect(wrapper.find('.base-list-page-stub').exists()).toBe(false)
  })

  it('routes AssetProject row actions into filtered project asset and member lists', async () => {
    routeState.params = { code: 'AssetProject' }
    routeState.path = '/objects/AssetProject'
    getMetadataMock.mockResolvedValueOnce({
      code: 'AssetProject',
      name: 'Asset Project',
      icon: 'Collection',
      permissions: { view: true, add: true, change: true, delete: true },
      fields: [
        { code: 'project_code', name: 'Project code', fieldType: 'text', showInList: true, isSearchable: true },
        { code: 'project_name', name: 'Project name', fieldType: 'text', showInList: true, isSearchable: true },
      ],
      layouts: {},
    })
    resolveRuntimeLayoutMock.mockResolvedValueOnce({
      fields: [
        { code: 'project_code', name: 'Project code', fieldType: 'text', showInList: true, isSearchable: true },
        { code: 'project_name', name: 'Project name', fieldType: 'text', showInList: true, isSearchable: true },
      ],
      layoutConfig: null,
      permissions: { view: true, add: true, change: true, delete: true },
    })

    const DynamicListPage = (await import('@/views/dynamic/DynamicListPage.vue')).default

    const wrapper = mount(DynamicListPage, {
      global: createDynamicListGlobalOptions(true),
    })

    await flushPromises()

    const assetsButton = wrapper.findAll('button').find((button) => button.text() === 'projects.actions.viewAssets')
    const membersButton = wrapper.findAll('button').find((button) => button.text() === 'projects.actions.viewMembers')

    expect(assetsButton).toBeDefined()
    expect(membersButton).toBeDefined()

    await assetsButton!.trigger('click')
    await membersButton!.trigger('click')

    expect(pushMock).toHaveBeenNthCalledWith(1, {
      path: '/objects/ProjectAsset',
      query: { project: 'project-1' },
    })
    expect(pushMock).toHaveBeenNthCalledWith(2, {
      path: '/objects/ProjectMember',
      query: { project: 'project-1' },
    })
  })
})
