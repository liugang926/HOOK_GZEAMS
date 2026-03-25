import { computed, defineComponent, h, provide, type Ref } from 'vue'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { createObjectClient } from '@/api/dynamic'
import AssetProjectAssetsPanel from '../AssetProjectAssetsPanel.vue'

const pushMock = vi.fn()
const assetProjectListMock = vi.fn()
const projectAssetListMock = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}))

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          'projects.panels.assets': 'Project assets',
          'projects.panels.assetsHint': 'Allocated assets, usage status, and cost snapshots.',
          'common.actions.refresh': 'Refresh',
          'projects.actions.viewAllAssets': 'View all assets',
          'projects.actions.addAsset': 'Add asset',
          'projects.actions.recycleAsset': 'Recycle asset',
          'projects.actions.transferToProject': 'Transfer to project',
          'projects.columns.allocationNo': 'Allocation No',
          'projects.columns.assetCode': 'Asset Code',
          'projects.columns.assetName': 'Asset Name',
          'projects.columns.allocationType': 'Allocation Type',
          'projects.columns.returnStatus': 'Return Status',
          'projects.columns.latestReturn': 'Recent return',
          'projects.columns.custodian': 'Custodian',
          'projects.columns.allocationDate': 'Allocation Date',
          'projects.columns.allocationCost': 'Allocation Cost',
          'projects.allocationType.temporary': 'Temporary',
          'projects.returnStatus.in_use': 'In use',
          'common.columns.actions': 'Actions',
          'projects.messages.emptyAssets': 'No assets have been allocated to this project yet.',
          'projects.messages.loadAssetsFailed': 'Failed to load project assets.',
          'projects.transferDialog.title': 'Cross-project transfer',
          'projects.transferDialog.asset': 'Current asset',
          'projects.transferDialog.targetProject': 'Target project',
          'projects.transferDialog.targetProjectPlaceholder': 'Select a target project',
          'projects.transferDialog.reason': 'Transfer reason',
          'projects.transferDialog.reasonPlaceholder': 'Describe why this asset is moving',
          'common.actions.cancel': 'Cancel',
          'common.actions.confirm': 'Confirm',
        }
        return translations[key] || key
      },
      te: (key: string) => [
        'projects.panels.assets',
        'projects.allocationType.temporary',
        'projects.returnStatus.in_use',
      ].includes(key),
    }),
  }
})

vi.mock('@/api/dynamic', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/dynamic')>()
  return {
    ...actual,
    createObjectClient: vi.fn((code: string) => ({
      list: code === 'AssetProject' ? assetProjectListMock : projectAssetListMock,
    })),
  }
})

vi.mock('@/utils/request', () => ({
  default: {
    post: vi.fn(),
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
    size: {
      type: String,
      default: '',
    },
  },
  template: '<span class="el-tag-stub" :data-type="type" :data-size="size"><slot /></span>',
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
        :key="row.id || row.allocationNo || row.assetCode"
        class="el-table-column-stub__row"
      >
        <slot :row="row">
          {{ prop ? row[prop] : '' }}
        </slot>
      </div>
    </div>
  `,
})

const ElDialogStub = defineComponent({
  name: 'ElDialogStub',
  template: '<div><slot /><slot name="footer" /></div>',
})

const ElFormStub = defineComponent({
  name: 'ElFormStub',
  template: '<form><slot /></form>',
})

const ElFormItemStub = defineComponent({
  name: 'ElFormItemStub',
  template: '<div><slot /></div>',
})

const ElInputStub = defineComponent({
  name: 'ElInputStub',
  template: '<input />',
})

const ElSelectStub = defineComponent({
  name: 'ElSelectStub',
  template: '<div><slot /></div>',
})

const ElOptionStub = defineComponent({
  name: 'ElOptionStub',
  template: '<option><slot /></option>',
})

const mountPanel = async (extraProps: Record<string, unknown> = {}) => {
  const wrapper = mount(AssetProjectAssetsPanel, {
    props: {
      panel: {
        code: 'assets',
        titleKey: 'projects.panels.assets',
      },
      recordId: 'project-1',
      recordData: {
        id: 'project-1',
        projectCode: 'XM2026030001',
        projectName: 'Alpha',
      },
      ...extraProps,
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
        'el-dialog': ElDialogStub,
        'el-form': ElFormStub,
        'el-form-item': ElFormItemStub,
        'el-input': ElInputStub,
        'el-select': ElSelectStub,
        'el-option': ElOptionStub,
      },
    },
  })

  await flushPromises()
  return wrapper
}

describe('AssetProjectAssetsPanel', () => {
  beforeEach(() => {
    pushMock.mockReset()
    assetProjectListMock.mockReset()
    projectAssetListMock.mockReset()
    vi.mocked(createObjectClient).mockClear()
  })

  it('renders the latest return summary for project assets', async () => {
    projectAssetListMock.mockResolvedValue({
      count: 1,
      results: [
        {
          id: 'allocation-1',
          allocationNo: 'FP2026030001',
          assetCode: 'ASSET-001',
          assetName: 'Docking Station',
          allocationType: 'temporary',
          returnStatus: 'in_use',
          allocationDate: '2026-03-20',
          allocationCost: 1200,
          latestReturnSummary: {
            returnId: 'return-1',
            returnNo: 'RT2026030001',
            status: 'rejected',
            statusLabel: 'Rejected',
            returnDate: '2026-03-20',
            rejectReason: 'Missing charger',
            eventAt: '2026-03-20T08:30:00Z',
          },
        },
      ],
    })

    const wrapper = await mountPanel()

    expect(createObjectClient).toHaveBeenCalledWith('ProjectAsset')
    expect(projectAssetListMock).toHaveBeenCalledWith({
      project: 'project-1',
      page: 1,
      page_size: 6,
      ordering: '-allocation_date',
    })
    expect(wrapper.text()).toContain('Recent return')
    expect(wrapper.text()).toContain('RT2026030001')
    expect(wrapper.text()).toContain('Rejected')
    expect(wrapper.text()).toContain('Missing charger')
  })

  it('opens the latest return order detail from the summary link', async () => {
    projectAssetListMock.mockResolvedValue({
      count: 1,
      results: [
        {
          id: 'allocation-1',
          allocationNo: 'FP2026030001',
          assetCode: 'ASSET-001',
          assetName: 'Docking Station',
          allocationType: 'temporary',
          returnStatus: 'in_use',
          latestReturnSummary: {
            returnId: 'return-1',
            returnNo: 'RT2026030001',
            status: 'pending',
            statusLabel: 'Pending',
            returnDate: '2026-03-20',
            eventAt: '2026-03-20T08:30:00Z',
          },
        },
      ],
    })

    const wrapper = await mountPanel()
    const returnLink = wrapper.findAll('button').find((button) => button.text() === 'RT2026030001')

    expect(returnLink).toBeDefined()

    await returnLink!.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/objects/AssetReturn/return-1')
  })

  it('prefers shared workspace dashboard totals in the panel header', async () => {
    projectAssetListMock.mockResolvedValue({
      count: 1,
      results: [
        {
          id: 'allocation-2',
          allocationNo: 'FP2026030002',
          assetCode: 'ASSET-002',
          assetName: 'Shared Screen',
        },
      ],
    })

    const wrapper = await mountPanel({
      workspaceDashboard: {
        assets: {
          totalCount: 9,
        },
      },
    })

    expect(wrapper.find('.asset-project-panel__meta').text()).toBe('9')
  })
})
