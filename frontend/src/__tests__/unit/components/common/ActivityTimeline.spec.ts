import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { defineComponent, nextTick } from 'vue'

vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn()
  }
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn()
  })
}))

const mountTimeline = async (response: unknown) => {
  vi.resetModules()
  const i18n = (await import('@/locales')).default
  const request = (await import('@/utils/request')).default
  const ActivityTimeline = (await import('@/components/common/ActivityTimeline.vue')).default
  vi.mocked(request.get).mockResolvedValue(response as any)

  const wrapper = mount(ActivityTimeline, {
    props: {
      objectCode: 'Asset',
      recordId: 'asset-1'
    },
    global: {
      plugins: [i18n],
      stubs: {
        BaseEmptyState: defineComponent({
          name: 'BaseEmptyState',
          template: '<div class="empty-state-stub"></div>'
        }),
        'el-skeleton': defineComponent({
          name: 'ElSkeleton',
          template: '<div class="el-skeleton-stub"></div>'
        }),
        'el-button': defineComponent({
          name: 'ElButton',
          emits: ['click'],
          template: '<button @click="$emit(\'click\')"><slot /></button>'
        }),
        'el-tag': defineComponent({
          name: 'ElTag',
          template: '<span class="el-tag-stub"><slot /></span>'
        }),
        'el-select': defineComponent({
          name: 'ElSelect',
          template: '<div class="el-select-stub"><slot /></div>'
        }),
        'el-option': defineComponent({
          name: 'ElOption',
          template: '<div class="el-option-stub"></div>'
        }),
        'el-segmented': defineComponent({
          name: 'ElSegmented',
          template: '<div class="el-segmented-stub"></div>'
        }),
        'el-table': defineComponent({
          name: 'ElTable',
          props: {
            data: { type: Array, default: () => [] }
          },
          template: '<div class="el-table-stub"><slot /></div>'
        }),
        'el-table-column': defineComponent({
          name: 'ElTableColumn',
          props: ['label', 'prop'],
          template: '<div class="el-table-column-stub"></div>'
        }),
        'el-icon': defineComponent({
          name: 'ElIcon',
          template: '<i class="el-icon-stub"><slot /></i>'
        }),
        'el-collapse-transition': defineComponent({
          name: 'ElCollapseTransition',
          template: '<div class="el-collapse-transition-stub"><slot /></div>'
        })
      }
    }
  })

  await flushPromises()
  return { wrapper, request }
}

describe('ActivityTimeline', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('flattens field changes into Salesforce-style history rows', async () => {
    const response = {
      count: 2,
      next: null,
      results: [
        {
          id: 'log-1',
          action: 'update',
          userName: 'alice',
          timestamp: '2026-03-07 10:00:00',
          description: 'Updated asset fields',
          changes: [
            { fieldCode: 'name', fieldLabel: 'Asset Name', oldValue: 'Old', newValue: 'New' },
            { fieldCode: 'status', fieldLabel: 'Status', oldValue: 'Draft', newValue: 'Active' }
          ]
        },
        {
          id: 'log-2',
          action: 'create',
          userName: '',
          timestamp: '2026-03-07 09:00:00',
          description: 'Created record',
          changes: []
        }
      ]
    }
    const { wrapper, request } = await mountTimeline(response)

    await flushPromises()
    ;(wrapper.vm as any).viewMode = 'table'
    await nextTick()

    const table = wrapper.findComponent({ name: 'ElTable' })
    const data = (table.props('data') || []) as Array<Record<string, any>>

    expect(vi.mocked(request.get)).toHaveBeenCalledWith('/system/objects/Asset/asset-1/history/', {
      params: {
        page: 1,
        page_size: 20
      }
    })
    expect(data).toHaveLength(3)
    expect(data[0]).toMatchObject({
      action: 'update',
      fieldLabel: 'Asset Name',
      oldValue: 'Old',
      newValue: 'New'
    })
    expect(data[1]).toMatchObject({
      action: 'update',
      fieldLabel: 'Status',
      oldValue: 'Draft',
      newValue: 'Active'
    })
    expect(data[2]).toMatchObject({
      action: 'create',
      fieldLabel: '',
      description: 'Created record'
    })
  })
})
