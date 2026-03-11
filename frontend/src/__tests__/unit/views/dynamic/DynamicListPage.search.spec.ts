import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, h, onMounted } from 'vue'
import {
  createClickableButtonStub,
  createElementResultStub,
  createObjectAvatarStub,
  createPlainButtonStub,
  loadingDirectiveStubs,
} from './testUtils'

const listMock = vi.fn()
const getMetadataMock = vi.fn()
const pushMock = vi.fn()
const resolveRuntimeLayoutMock = vi.fn()

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  return {
    ...actual,
    useRoute: () => ({
      params: { code: 'Asset' },
      path: '/objects/Asset',
    }),
    useRouter: () => ({
      push: pushMock,
    }),
  }
})

vi.mock('@/api/dynamic', () => ({
  createObjectClient: () => ({
    list: listMock,
    getMetadata: getMetadataMock,
    batchDelete: vi.fn(),
    delete: vi.fn(),
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
      ])
    },
  }),
}))

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    createI18n: actual.createI18n,
    useI18n: () => ({
      t: (key: string) => key,
      te: () => true,
      locale: { value: 'zh-CN' },
    }),
  }
})

const createListWrapperStubs = (clickableButtons = false) => ({
  ContextDrawer: defineComponent({ template: '<div class="drawer-stub" />' }),
  FieldRenderer: defineComponent({ template: '<div class="field-stub" />' }),
  ObjectAvatar: createObjectAvatarStub(),
  ExportButton: defineComponent({ template: '<div class="export-button-stub" />' }),
  ImportButton: defineComponent({ template: '<div class="import-button-stub" />' }),
  ExportFieldSelector: defineComponent({ template: '<div class="export-selector-stub" />' }),
  ImportConfigDialog: defineComponent({ template: '<div class="import-config-stub" />' }),
  'el-alert': defineComponent({ template: '<div />' }),
  'el-input': defineComponent({ template: '<input />' }),
  'el-option': defineComponent({ template: '<option />' }),
  'el-result': createElementResultStub(),
  'el-select': defineComponent({ template: '<select><slot /></select>' }),
  'el-skeleton': defineComponent({ template: '<div />' }),
  'el-button': clickableButtons ? createClickableButtonStub() : createPlainButtonStub(),
  'el-tag': defineComponent({ template: '<span><slot /></span>' }),
})

describe('DynamicListPage unified search', () => {
  beforeEach(() => {
    vi.clearAllMocks()
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
      global: {
        directives: loadingDirectiveStubs,
        stubs: createListWrapperStubs(),
      },
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
      global: {
        directives: loadingDirectiveStubs,
        stubs: createListWrapperStubs(true),
      },
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
      global: {
        directives: loadingDirectiveStubs,
        stubs: createListWrapperStubs(),
      },
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
      global: {
        directives: loadingDirectiveStubs,
        stubs: createListWrapperStubs(),
      },
    })

    await flushPromises()

    expect(wrapper.text()).toContain('common.messages.loadFailed')
    expect(wrapper.text()).toContain('runtime failed')
    expect(wrapper.find('.base-list-page-stub').exists()).toBe(false)
  })
})
