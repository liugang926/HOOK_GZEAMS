import { computed, ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ActivityTimeline from '../ActivityTimeline.vue'

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: vi.fn(),
  }),
}))

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => ({
      t: (key: string) => {
        const overrides: Record<string, string> = {
          'common.history.title': 'Change History',
          'common.messages.noTimelineData': 'No timeline data',
          'common.messages.timelineHint': 'Timeline hint',
          'common.labels.timeline': 'Timeline',
          'common.labels.table': 'Table',
          'common.labels.system': 'System',
          'common.actions.view': 'View',
          'common.history.actions.approve': 'Approved',
        }
        return overrides[key] || key
      },
    }),
  }
})

vi.mock('@/composables/useActivityTimeline', () => ({
  useActivityTimeline: () => ({
    activities: ref([]),
    loading: ref(false),
    loadingMore: ref(false),
    hasMore: ref(false),
    groupedByDate: computed(() => []),
    loadMore: vi.fn(),
    refresh: vi.fn(),
  }),
}))

describe('ActivityTimeline', () => {
  it('renders direct entries without relying on fetched timeline data', () => {
    const wrapper = mount(ActivityTimeline, {
      props: {
        objectCode: 'AssetPickup',
        recordId: 'pickup-1',
        entries: [
          {
            id: 'timeline-1',
            action: 'approve',
            actionLabel: 'Approved',
            sourceCode: 'workflowApproval',
            sourceLabel: 'Workflow Approval',
            userName: 'Admin',
            createdAt: '2026-03-16T08:00:00Z',
            description: 'Department approval',
            highlights: [
              {
                code: 'approval_comment',
                label: 'Approval Comment',
                value: 'Budget owner confirmed',
                tone: 'info',
              },
            ],
          },
        ],
      },
      global: {
        config: {
          globalProperties: {
            $t: (key: string) => {
              const overrides: Record<string, string> = {
                'common.history.title': 'Change History',
                'common.messages.noTimelineData': 'No timeline data',
                'common.messages.timelineHint': 'Timeline hint',
                'common.labels.timeline': 'Timeline',
                'common.labels.table': 'Table',
                'common.labels.system': 'System',
                'common.actions.view': 'View',
                'common.history.actions.approve': 'Approved',
              }
              return overrides[key] || key
            },
          } as any,
        },
        stubs: {
          BaseEmptyState: { template: '<div class="empty-state-stub" />' },
          'el-skeleton': { template: '<div class="skeleton-stub" />' },
          'el-select': { template: '<div><slot /></div>' },
          'el-option': { template: '<div />' },
          'el-segmented': { template: '<div class="segmented-stub" />' },
          'el-tag': { template: '<span><slot /></span>' },
          'el-button': { template: '<button><slot /></button>' },
          'el-table': { template: '<div><slot /></div>' },
          'el-table-column': { template: '<div><slot :row="{}" /></div>' },
          'el-icon': { template: '<i><slot /></i>' },
          'el-collapse-transition': { template: '<div><slot /></div>' },
        },
      },
    })

    expect(wrapper.text()).toContain('Approved')
    expect(wrapper.text()).toContain('Department approval')
    expect(wrapper.text()).toContain('Workflow Approval')
    expect(wrapper.text()).toContain('Approval Comment')
    expect(wrapper.text()).toContain('Budget owner confirmed')
  })
})
