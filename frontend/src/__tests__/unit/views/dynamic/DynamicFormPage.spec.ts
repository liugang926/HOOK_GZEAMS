import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { createDynamicFormGlobalOptions } from './testUtils'
import { createRouteMockContext } from './routerTestUtils'
import { createCrudApiMockContext, createRuntimeLayoutMockContext } from './apiTestUtils'
import { createMappedI18nMock, dynamicFormTranslations } from './i18nTestUtils'

const { getMetadataMock, getRecordMock, createMock, updateMock } = createCrudApiMockContext()
const { resolveRuntimeLayoutMock } = createRuntimeLayoutMockContext()
const { pushMock, routeState } = createRouteMockContext({
  params: { code: 'Asset' },
  path: '/objects/Asset/create',
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

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    createI18n: actual.createI18n,
    useI18n: () => createMappedI18nMock(dynamicFormTranslations),
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
      name: 'Asset Card',
      icon: 'Box',
      module: 'Asset Center',
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
      global: createDynamicFormGlobalOptions(
        defineComponent({
          setup(_props, { expose }) {
            expose({
              validate: vi.fn().mockResolvedValue(true),
              getSubmitData: vi.fn().mockReturnValue({ asset_code: 'A-001', asset_name: 'Asset 1' }),
            })
            return () => h('div', { class: 'dynamic-form-stub' }, 'dynamic form')
          },
        })
      ),
    })
  }

  it('renders the enhanced create page header and summary', async () => {
    const wrapper = await buildWrapper()

    await flushPromises()

    expect(wrapper.find('.form-hero__title').text()).toContain('Asset Card')
    expect(wrapper.find('.form-panel__title').text()).not.toHaveLength(0)
    expect(wrapper.find('.form-info-card__title').text()).toContain('Asset Card')
    expect(wrapper.text()).toContain('Asset Center')
    expect(wrapper.text()).toContain('3')
    expect(wrapper.text()).toContain('2')
  })

  it('returns to the object list when cancel is clicked', async () => {
    const wrapper = await buildWrapper()

    await flushPromises()

    const cancelButton = wrapper.findAll('button').find((button) => button.text().includes('Cancel'))

    expect(cancelButton).toBeDefined()

    await cancelButton!.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/objects/Asset')
  })

  it('shows the permission denied state when create access is unavailable', async () => {
    getMetadataMock.mockResolvedValueOnce({
      code: 'Asset',
      name: 'Asset Card',
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

    expect(wrapper.text()).toContain('Permission denied')
  })

  it('updates the record and returns to the object list in edit mode', async () => {
    routeState.params = { code: 'Asset', id: 'asset-1' }
    routeState.path = '/objects/Asset/asset-1/edit'
    getRecordMock.mockResolvedValueOnce({ id: 'asset-1', asset_code: 'OLD-001' })

    const wrapper = await buildWrapper()

    await flushPromises()

    const saveButton = wrapper.findAll('button').find((button) => button.text().includes('Save'))

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
