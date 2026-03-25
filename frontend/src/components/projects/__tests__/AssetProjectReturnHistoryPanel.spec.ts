import { computed, defineComponent, h, provide, type Ref } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import request from '@/utils/request'
import AssetProjectReturnHistoryPanel from '../AssetProjectReturnHistoryPanel.vue'

const pushMock = vi.fn()

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>()
  return {
    ...actual,
    useRouter: () => ({
      push: pushMock,
    }),
  }
})

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => ({
      t: (key: string, params?: Record<string, unknown>) => {
        const translations: Record<string, string> = {
          'projects.panels.returnHistory': 'Return history',
          'projects.panels.returnHistoryHint': 'Recent processed return orders and status totals for this project.',
          'projects.panels.returnTrend': 'Return trend',
          'projects.summary.pendingReturns': 'Pending return orders',
          'projects.summary.completedReturns': 'Completed returns',
          'projects.summary.rejectedReturns': 'Rejected returns',
          'projects.ranges.last7Days': 'Last 7 days',
          'projects.ranges.last30Days': 'Last 30 days',
          'projects.ranges.last90Days': 'Last 90 days',
          'common.actions.refresh': 'Refresh',
          'projects.actions.viewAllReturns': 'View all returns',
          'projects.columns.returnNo': 'Return No',
          'common.columns.status': 'Status',
          'projects.columns.returnDate': 'Return Date',
          'projects.columns.itemsCount': 'Items',
          'projects.columns.processingNote': 'Processing note',
          'projects.columns.processedAt': 'Processed at',
          'projects.messages.emptyReturnHistory': 'No processed return history for this project yet.',
          'projects.messages.emptyReturnTrend': 'No return activity in the selected time window.',
          'projects.messages.loadReturnHistoryFailed': 'Failed to load project return history.',
          'projects.messages.returnTrendWindow': 'Window: {start} to {end}',
        }
        return (translations[key] || key)
          .replace('{start}', String(params?.start || '{start}'))
          .replace('{end}', String(params?.end || '{end}'))
      },
      te: (key: string) => key === 'projects.panels.returnHistory',
    }),
  }
})

vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn(),
  },
}))

const ElCardStub = defineComponent({
  name: 'ElCardStub',
  template: '<div><slot name="header" /><slot /></div>',
})

const ElButtonStub = defineComponent({
  name: 'ElButtonStub',
  props: {
    loading: Boolean,
    type: {
      type: String,
      default: 'default',
    },
  },
  emits: ['click'],
  template: '<button :disabled="loading" :data-type="type" @click="$emit(\'click\', $event)"><slot /></button>',
})

const ElEmptyStub = defineComponent({
  name: 'ElEmptyStub',
  props: {
    description: {
      type: String,
      default: '',
    },
  },
  template: '<div class="el-empty-stub">{{ description }}</div>',
})

const ElTagStub = defineComponent({
  name: 'ElTagStub',
  props: {
    type: {
      type: String,
      default: 'info',
    },
  },
  template: '<span class="el-tag-stub" :data-type="type"><slot /></span>',
})

const ElTableStub = defineComponent({
  name: 'ElTableStub',
  props: {
    data: {
      type: Array,
      default: () => [],
    },
    border: {
      type: [Boolean, String],
      default: false,
    },
    stripe: {
      type: [Boolean, String],
      default: false,
    },
  },
  emits: ['rowClick'],
  setup(props, { slots }) {
    provide('tableRows', computed(() => props.data) as Ref<unknown[]>)
    return () => h('div', { class: 'el-table-stub' }, slots.default?.())
  },
})

const ElTableColumnStub = defineComponent({
  name: 'ElTableColumnStub',
  inject: ['tableRows'],
  props: {
    label: {
      type: String,
      default: '',
    },
    prop: {
      type: String,
      default: '',
    },
  },
  template: `
    <div class="el-table-column-stub">
      <div>{{ label }}</div>
      <div
        v-for="row in tableRows"
        :key="row.id || row.returnNo || row.return_no"
        class="el-table-column-stub__row"
      >
        <slot :row="row">
          {{ prop ? row[prop] : '' }}
        </slot>
      </div>
    </div>
  `,
})

const mountPanel = async () => {
  const wrapper = mount(AssetProjectReturnHistoryPanel, {
    props: {
      panel: {
        code: 'project_return_history',
        titleKey: 'projects.panels.returnHistory',
      },
      recordId: 'project-1',
    },
    global: {
      directives: {
        loading: {},
      },
      stubs: {
        'el-card': ElCardStub,
        'el-button': ElButtonStub,
        'el-empty': ElEmptyStub,
        'el-tag': ElTagStub,
        'el-table': ElTableStub,
        'el-table-column': ElTableColumnStub,
      },
    },
  })

  await flushPromises()
  return wrapper
}

describe('AssetProjectReturnHistoryPanel', () => {
  beforeEach(() => {
    pushMock.mockReset()
    vi.mocked(request.get).mockReset()
  })

  it('loads project return dashboard summary, history, and trend in one request', async () => {
    vi.mocked(request.get).mockResolvedValue({
      summary: {
        pendingCount: 2,
        completedCount: 3,
        rejectedCount: 1,
        processedCount: 4,
      },
      history: {
        totalCount: 4,
        rows: [
          {
            id: 'return-2',
            returnNo: 'RT2026030002',
            status: 'rejected',
            statusLabel: 'Rejected',
            returnDate: '2026-03-21',
            itemsCount: 1,
            rejectReason: 'Missing charger',
            processedAt: '2026-03-21T08:00:00Z',
          },
        ],
      },
      trend: {
        maxTotalCount: 3,
        points: [
          { date: '2026-03-19', label: '03-19', completedCount: 2, rejectedCount: 0, totalCount: 2 },
          { date: '2026-03-21', label: '03-21', completedCount: 0, rejectedCount: 1, totalCount: 1 },
        ],
      },
      window: {
        rangeKey: '30d',
        startDate: '2026-02-21',
        endDate: '2026-03-21',
      },
    })

    const wrapper = await mountPanel()

    expect(request.get).toHaveBeenCalledWith(
      '/system/objects/AssetProject/project-1/return_dashboard/',
      {
        params: { range_key: '30d' },
      },
    )
    expect(wrapper.text()).toContain('Return history')
    expect(wrapper.text()).toContain('Return trend')
    expect(wrapper.text()).toContain('Pending return orders')
    expect(wrapper.text()).toContain('Completed returns')
    expect(wrapper.text()).toContain('Rejected returns')
    expect(wrapper.text()).toContain('RT2026030002')
    expect(wrapper.text()).toContain('Missing charger')
    expect(wrapper.text()).toContain('03-19')
    expect(wrapper.text()).toContain('2/0/2')
  })

  it('navigates to return detail and refreshes dashboard when range changes', async () => {
    vi.mocked(request.get).mockResolvedValue({
      summary: {
        pendingCount: 0,
        completedCount: 1,
        rejectedCount: 0,
        processedCount: 1,
      },
      history: {
        totalCount: 1,
        rows: [
          {
            id: 'return-1',
            returnNo: 'RT2026030001',
            status: 'completed',
            statusLabel: 'Completed',
            returnDate: '2026-03-20',
            itemsCount: 2,
            returnReason: 'Project completed',
            processedAt: '2026-03-20T09:00:00Z',
          },
        ],
      },
      trend: {
        maxTotalCount: 1,
        points: [
          { date: '2026-03-20', label: '03-20', completedCount: 1, rejectedCount: 0, totalCount: 1 },
        ],
      },
      window: {
        rangeKey: '30d',
        startDate: '2026-02-20',
        endDate: '2026-03-20',
      },
    })

    const wrapper = await mountPanel()
    const detailButton = wrapper.findAll('button').find((button) => button.text() === 'RT2026030001')
    const rangeButton = wrapper.findAll('button').find((button) => button.text() === 'Last 7 days')
    const viewAllButton = wrapper.findAll('button').find((button) => button.text() === 'View all returns')

    expect(detailButton).toBeDefined()
    expect(rangeButton).toBeDefined()
    expect(viewAllButton).toBeDefined()

    await detailButton!.trigger('click')
    await rangeButton!.trigger('click')
    await flushPromises()
    await viewAllButton!.trigger('click')

    expect(pushMock).toHaveBeenNthCalledWith(1, '/objects/AssetReturn/return-1')
    expect(request.get).toHaveBeenNthCalledWith(2, '/system/objects/AssetProject/project-1/return_dashboard/', {
      params: { range_key: '7d' },
    })
    expect(pushMock).toHaveBeenNthCalledWith(2, {
      path: '/objects/AssetReturn',
      query: { project: 'project-1' },
    })
  })
})
