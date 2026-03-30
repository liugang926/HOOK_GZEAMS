import { ref } from 'vue'
import { describe, expect, it } from 'vitest'
import { useObjectWorkbench } from '../useObjectWorkbench'

describe('useObjectWorkbench', () => {
  it('filters workbench sections by record status and exposes queue and insight flags', () => {
    const workbench = ref({
      workspaceMode: 'extended',
      primaryEntryRoute: '/objects/FinanceVoucher',
      legacyAliases: [],
      toolbar: {
        primaryActions: [],
        secondaryActions: [],
      },
      detailPanels: [],
      asyncIndicators: [],
      summaryCards: [
        { code: 'total_amount', valueField: 'total_amount' },
      ],
      queuePanels: [
        { code: 'approval_queue', visibleWhen: { statusIn: ['submitted'] } },
      ],
      exceptionPanels: [
        { code: 'push_failed', visibleWhen: { statusIn: ['approved'] } },
      ],
      closurePanel: {
        stageField: 'status',
      },
      slaIndicators: [
        { code: 'approval_sla', visibleWhen: { statusIn: ['submitted'] } },
      ],
      recommendedActions: [
        { code: 'approve', visibleWhen: { statusIn: ['submitted'] } },
      ],
    })
    const recordData = ref({
      status: 'submitted',
      total_amount: 1200,
    })

    const state = useObjectWorkbench({ workbench, recordData })

    expect(state.summaryCards.value).toHaveLength(1)
    expect(state.queuePanels.value).toHaveLength(1)
    expect(state.exceptionPanels.value).toHaveLength(0)
    expect(state.slaIndicators.value).toHaveLength(1)
    expect(state.recommendedActions.value).toHaveLength(1)
    expect(state.closurePanel.value?.stageField).toBe('status')
    expect(state.hasInsights.value).toBe(true)
    expect(state.hasQueues.value).toBe(true)
  })

  it('treats an empty closure panel payload as absent', () => {
    const workbench = ref({
      workspaceMode: 'standard',
      primaryEntryRoute: '/objects/InventoryTask',
      legacyAliases: [],
      toolbar: {
        primaryActions: [],
        secondaryActions: [],
      },
      detailPanels: [],
      asyncIndicators: [],
      summaryCards: [],
      queuePanels: [],
      exceptionPanels: [],
      closurePanel: {},
      slaIndicators: [],
      recommendedActions: [],
    })
    const recordData = ref({
      status: 'draft',
    })

    const state = useObjectWorkbench({ workbench, recordData })

    expect(state.closurePanel.value).toBeNull()
    expect(state.hasInsights.value).toBe(false)
  })

  it('shows only the status-matched InventoryItem closure actions', () => {
    const workbench = ref({
      workspaceMode: 'extended',
      primaryEntryRoute: '/objects/InventoryItem',
      legacyAliases: ['/inventory/items'],
      toolbar: {
        primaryActions: [
          { code: 'confirm', visibleWhen: { statusIn: ['pending'] } },
          { code: 'submit_review', visibleWhen: { statusIn: ['confirmed'] } },
          { code: 'approve', visibleWhen: { statusIn: ['in_review'] } },
        ],
        secondaryActions: [
          { code: 'ignore', visibleWhen: { statusIn: ['pending', 'confirmed'] } },
        ],
      },
      detailPanels: [],
      asyncIndicators: [],
      summaryCards: [
        { code: 'difference_type', valueField: 'difference_type_label' },
      ],
      queuePanels: [],
      exceptionPanels: [],
      closurePanel: {
        stageField: 'status_label',
        ownerField: 'owner.username',
      },
      slaIndicators: [],
      recommendedActions: [
        { code: 'submit_review_hint', visibleWhen: { statusIn: ['confirmed'] } },
      ],
    })
    const recordData = ref({
      status: 'confirmed',
      status_label: 'Confirmed',
      difference_type_label: 'Missing',
      owner: {
        username: 'inventory-owner',
      },
    })

    const state = useObjectWorkbench({ workbench, recordData })

    expect(state.primaryActions.value.map((action) => action.code)).toEqual(['submit_review'])
    expect(state.secondaryActions.value.map((action) => action.code)).toEqual(['ignore'])
    expect(state.summaryCards.value).toHaveLength(1)
    expect(state.recommendedActions.value.map((action) => action.code)).toEqual(['submit_review_hint'])
    expect(state.hasActions.value).toBe(true)
    expect(state.hasInsights.value).toBe(true)
  })
})
