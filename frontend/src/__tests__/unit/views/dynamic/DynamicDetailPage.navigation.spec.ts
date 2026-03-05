import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { defineComponent, h } from 'vue'

const pushMock = vi.fn()
const getMetadataMock = vi.fn()
const resolveRuntimeLayoutMock = vi.fn()

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

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { code: 'Asset', id: 'asset-1' }
  }),
  useRouter: () => ({
    push: pushMock
  })
}))

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

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key
  })
}))

describe('DynamicDetailPage navigation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getMetadataMock.mockResolvedValue({
      code: 'Asset',
      name: 'Asset',
      permissions: { view: true, add: true, change: true, delete: true }
    })
    resolveRuntimeLayoutMock.mockResolvedValue({
      permissions: { view: true, add: true, change: true, delete: true }
    })
  })

  it('navigates to related detail using target object code', async () => {
    const DynamicDetailPage = (await import('@/views/dynamic/DynamicDetailPage.vue')).default
    const wrapper = mount(DynamicDetailPage, {
      global: {
        directives: {
          loading: () => undefined
        },
        stubs: {
          'el-result': defineComponent({ template: '<div><slot /><slot name="extra" /></div>' }),
          'el-button': defineComponent({ template: '<button><slot /></button>' })
        }
      }
    })

    await flushPromises()
    await wrapper.get('.emit-related-click').trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/objects/Maintenance/m%201')
  })

  it('navigates to related edit using derived object code fallback', async () => {
    const DynamicDetailPage = (await import('@/views/dynamic/DynamicDetailPage.vue')).default
    const wrapper = mount(DynamicDetailPage, {
      global: {
        directives: {
          loading: () => undefined
        },
        stubs: {
          'el-result': defineComponent({ template: '<div><slot /><slot name="extra" /></div>' }),
          'el-button': defineComponent({ template: '<button><slot /></button>' })
        }
      }
    })

    await flushPromises()
    await wrapper.get('.emit-related-edit').trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/objects/Loan/loan%2F1/edit')
  })
})
