import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import SlaIndicatorBar from '../SlaIndicatorBar.vue'

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  const translations: Record<string, string> = {
    'common.workbench.eyebrows.sla': 'SLA',
    'common.workbench.titles.sla': 'Service Level',
    'common.workbench.messages.slaHint': 'Track workflow deadlines on the record.',
    'common.workbench.labels.dueDate': 'Due Date',
    'common.workbench.labels.owner': 'Owner',
    'common.workbench.status.overdue': 'Overdue',
    'common.workbench.status.unknown': 'Unknown',
  }

  return {
    ...actual,
    useI18n: () => ({
      t: (key: string) => translations[key] || key,
      te: (key: string) => key in translations,
    }),
  }
})

describe('SlaIndicatorBar', () => {
  it('renders workflow SLA status from object-level SLA data', () => {
    const wrapper = mount(SlaIndicatorBar, {
      props: {
        indicators: [
          {
            code: 'approval_sla',
            label: 'Approval SLA',
          },
        ],
        slaData: {
          objectCode: 'Asset',
          businessId: 'asset-1',
          hasInstance: true,
          instanceId: 'wf-1',
          instanceNo: 'WF-001',
          instanceStatus: 'pending_approval',
          workflowName: 'Asset Approval',
          status: 'overdue',
          dueDate: '2026-03-30 12:00:00',
          remainingHours: 0,
          hoursOverdue: 6,
          isEscalated: false,
          assignee: {
            id: 'user-1',
            username: 'approver',
            displayName: 'Approver',
          },
          currentNode: {
            id: 'approval_1',
            name: 'Department Approval',
          },
          activeTaskId: 'task-1',
          activeTaskCount: 1,
          completedAt: null,
        },
      },
    })

    expect(wrapper.text()).toContain('Approval SLA')
    expect(wrapper.text()).toContain('Overdue')
    expect(wrapper.text()).toContain('Due Date: 2026-03-30 12:00:00')
    expect(wrapper.text()).toContain('Owner: Approver')
  })

  it('stays hidden when the record has no workflow instance and no status fields', () => {
    const wrapper = mount(SlaIndicatorBar, {
      props: {
        indicators: [
          {
            code: 'approval_sla',
            label: 'Approval SLA',
          },
        ],
        slaData: {
          objectCode: 'Asset',
          businessId: 'asset-1',
          hasInstance: false,
          instanceId: null,
          instanceNo: null,
          instanceStatus: null,
          workflowName: '',
          status: 'unknown',
          dueDate: null,
          remainingHours: null,
          hoursOverdue: 0,
          isEscalated: false,
          assignee: null,
          currentNode: null,
          activeTaskId: null,
          activeTaskCount: 0,
          completedAt: null,
        },
      },
    })

    expect(wrapper.find('.sla-indicator-bar').exists()).toBe(false)
  })
})
