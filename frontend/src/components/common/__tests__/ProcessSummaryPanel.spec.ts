import { mount, RouterLinkStub } from '@vue/test-utils'
import { defineComponent } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import { createPassthroughI18nMock } from '@/__tests__/unit/views/dynamic/i18nTestUtils'
import ProcessSummaryPanel from '../ProcessSummaryPanel.vue'

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => createPassthroughI18nMock(),
  }
})

type ProcessSummaryPanelProps = Partial<InstanceType<typeof ProcessSummaryPanel>['$props']>

const mountPanel = (props: ProcessSummaryPanelProps) => {
  return mount(ProcessSummaryPanel, {
    props: props as InstanceType<typeof ProcessSummaryPanel>['$props'],
    global: {
      stubs: {
        RouterLink: RouterLinkStub,
        'el-card': defineComponent({
          template: '<div class="el-card-stub"><slot /></div>',
        }),
        'el-button': defineComponent({
          emits: ['click'],
          template: '<button class="el-button-stub" @click="$emit(\'click\')"><slot /></button>',
        }),
      },
    },
  })
}

describe('ProcessSummaryPanel', () => {
  it('renders process stats, closure rows, and navigation actions together', async () => {
    const wrapper = mountPanel({
      stats: [
        { label: 'Status', value: 'approved' },
      ],
      panel: {
        stageField: 'closure_summary.stage',
        ownerField: 'closure_summary.owner',
        progressField: 'closure_summary.completion_display',
      },
      recordData: {
        closure_summary: {
          stage: 'Awaiting closure',
          owner: 'Controller',
          completion_display: '80%',
        },
      },
      extraRows: [
        {
          label: 'Latest signal',
          value: 'Approval Comment: Ready to close',
          actions: [{ label: 'Jump to activity', to: { hash: '#detail-activity' } }],
        },
      ],
      navigationSection: {
        title: 'Lifecycle Links',
        hint: 'Follow the upstream and downstream records from one place.',
        items: [
          {
            key: 'asset',
            label: 'View Asset',
            objectCode: 'Asset',
            recordId: 'asset-1',
          },
        ],
      },
    })

    expect(wrapper.text()).toContain('common.workbench.titles.processSummary')
    expect(wrapper.text()).toContain('approved')
    expect(wrapper.text()).toContain('Awaiting closure')
    expect(wrapper.text()).toContain('Controller')
    expect(wrapper.text()).toContain('80%')
    expect(wrapper.text()).toContain('Approval Comment: Ready to close')
    expect(wrapper.text()).toContain('View Asset')

    await wrapper.get('.el-button-stub').trigger('click')
    expect(wrapper.emitted('select')).toEqual([
      [
        {
          key: 'asset',
          label: 'View Asset',
          objectCode: 'Asset',
          recordId: 'asset-1',
        },
      ],
    ])
  })

  it('stays hidden when there is no process content', () => {
    const wrapper = mountPanel({
      stats: [],
      panel: null,
      recordData: null,
      extraRows: [],
      navigationSection: null,
    })

    expect(wrapper.find('.process-summary-panel').exists()).toBe(false)
  })
})
