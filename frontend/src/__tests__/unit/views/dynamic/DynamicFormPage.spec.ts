import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import {
  createClickableButtonStub,
  createElementResultStub,
  createObjectAvatarStub,
  loadingDirectiveStubs,
} from './testUtils'

const pushMock = vi.fn()
const getMetadataMock = vi.fn()
const getRecordMock = vi.fn()
const createMock = vi.fn()
const updateMock = vi.fn()
const resolveRuntimeLayoutMock = vi.fn()
const routeState = {
  params: { code: 'Asset' } as Record<string, string>,
  path: '/objects/Asset/create',
}

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

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  const translations: Record<string, string> = {
    'common.actions.back': '返回',
    'common.actions.cancel': '取消',
    'common.actions.create': '新建',
    'common.actions.edit': '编辑',
    'common.actions.refresh': '刷新',
    'common.actions.save': '保存',
    'common.messages.createSuccess': '创建成功',
    'common.messages.loadFailed': '加载失败',
    'common.messages.operationFailed': '操作失败',
    'common.messages.permissionDenied': '无权限访问',
    'common.messages.permissionDeniedHint': '您没有访问此页面的权限。',
    'common.messages.updateSuccess': '更新成功',
  }

  return {
    ...actual,
    createI18n: actual.createI18n,
    useI18n: () => ({
      t: (key: string) => translations[key] || key,
      te: () => false,
      locale: { value: 'zh-CN' },
    }),
  }
})

vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal<typeof import('element-plus')>()
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
    },
  }
})

vi.mock('@/api/dynamic', () => ({
  createObjectClient: () => ({
    getMetadata: getMetadataMock,
    get: getRecordMock,
    create: createMock,
    update: updateMock,
  }),
}))

vi.mock('@/platform/layout/runtimeLayoutResolver', () => ({
  resolveRuntimeLayout: resolveRuntimeLayoutMock,
}))

describe('DynamicFormPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    routeState.params = { code: 'Asset' }
    routeState.path = '/objects/Asset/create'

    getMetadataMock.mockResolvedValue({
      code: 'Asset',
      name: '资产卡片',
      icon: 'Box',
      module: '资产管理',
      fields: [
        { code: 'asset_code', required: true },
        { code: 'asset_name', required: true },
        { code: 'brand' },
      ],
      layouts: {},
      permissions: { view: true, add: true, change: true, delete: true },
      isHardcoded: true,
      enableWorkflow: false,
      enableVersion: false,
      enableSoftDelete: true,
    })

    getRecordMock.mockResolvedValue({})
    createMock.mockResolvedValue({})
    updateMock.mockResolvedValue({})
    resolveRuntimeLayoutMock.mockResolvedValue({
      permissions: { view: true, add: true, change: true, delete: true },
    })
  })

  const buildWrapper = async () => {
    const DynamicFormPage = (await import('@/views/dynamic/DynamicFormPage.vue')).default

    return mount(DynamicFormPage, {
      global: {
        directives: loadingDirectiveStubs,
        stubs: {
          DynamicForm: defineComponent({
            setup(_props, { expose }) {
              expose({
                validate: vi.fn().mockResolvedValue(true),
                getSubmitData: vi.fn().mockReturnValue({ asset_code: 'A-001', asset_name: 'Asset 1' }),
              })
              return () => h('div', { class: 'dynamic-form-stub' }, 'dynamic form')
            },
          }),
          ObjectAvatar: createObjectAvatarStub(),
          'el-result': createElementResultStub(),
          'el-button': createClickableButtonStub(),
        },
      },
    })
  }

  it('renders the enhanced create page header and summary', async () => {
    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.find('.form-hero__title').text()).toContain('新建 资产卡片')
    expect(wrapper.find('.form-panel__title').text()).toContain('填写对象信息')
    expect(wrapper.find('.form-info-card__title').text()).toContain('资产卡片')
    expect(wrapper.text()).toContain('资产管理')
    expect(wrapper.text()).toContain('3')
    expect(wrapper.text()).toContain('2')
  })

  it('returns to the object list when cancel is clicked', async () => {
    const wrapper = await buildWrapper()

    await flushPromises()

    const cancelButton = wrapper.findAll('button').find((button) => button.text() === '取消')

    expect(cancelButton).toBeDefined()

    await cancelButton!.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/objects/Asset')
  })

  it('shows the permission denied state when create access is unavailable', async () => {
    getMetadataMock.mockResolvedValueOnce({
      code: 'Asset',
      name: '璧勪骇鍗＄墖',
      fields: [],
      layouts: {},
      permissions: { view: true, add: false, change: false, delete: false },
      isHardcoded: true,
      enableWorkflow: false,
      enableVersion: false,
      enableSoftDelete: true,
    })
    resolveRuntimeLayoutMock.mockResolvedValueOnce({
      permissions: { view: true, add: false, change: false, delete: false },
    })

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.text()).toContain('无权限访问')
  })

  it('updates the record and returns to the object list in edit mode', async () => {
    routeState.params = { code: 'Asset', id: 'asset-1' }
    routeState.path = '/objects/Asset/asset-1/edit'
    getRecordMock.mockResolvedValueOnce({ id: 'asset-1', asset_code: 'OLD-001' })

    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.text()).toContain('保存')

    const saveButton = wrapper.findAll('button').find((button) => button.text().includes('保存'))

    expect(saveButton).toBeDefined()

    await saveButton!.trigger('click')
    await flushPromises()

    expect(updateMock).toHaveBeenCalledWith('asset-1', {
      asset_code: 'A-001',
      asset_name: 'Asset 1',
    })
    expect(pushMock).toHaveBeenCalledWith('/objects/Asset')
  })
})
