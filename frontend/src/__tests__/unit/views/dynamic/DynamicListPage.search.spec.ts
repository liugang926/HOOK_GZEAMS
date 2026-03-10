import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, h, onMounted } from 'vue'

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
    setup(props) {
      onMounted(async () => {
        await props.api({
          page: 1,
          pageSize: 20,
          __unifiedKeyword: '鎴村皵',
          __unifiedField: '__all',
          __visibleFieldCodes: ['asset_code', 'asset_name'],
        })
      })
      return () => h('div', { class: 'base-list-page-stub' })
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
    }),
  }
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
        directives: {
          loading: () => undefined,
        },
        stubs: {
          ContextDrawer: defineComponent({ template: '<div class="drawer-stub" />' }),
          FieldRenderer: defineComponent({ template: '<div class="field-stub" />' }),
          'el-alert': defineComponent({ template: '<div />' }),
          'el-result': defineComponent({ template: '<div><slot /><slot name="extra" /></div>' }),
          'el-skeleton': defineComponent({ template: '<div />' }),
          'el-button': defineComponent({ template: '<button><slot /></button>' }),
          'el-tag': defineComponent({ template: '<span><slot /></span>' }),
        },
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
})
