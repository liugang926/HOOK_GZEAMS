import { ref } from 'vue'
import { describe, expect, it } from 'vitest'
import type { RuntimeWorkbench, RuntimeWorkbenchSurfacePriority } from '@/types/runtime'
import { useObjectWorkbench } from '../useObjectWorkbench'

const buildWorkbench = (overrides: Partial<RuntimeWorkbench> = {}): RuntimeWorkbench => ({
  workspaceMode: 'extended',
  primaryEntryRoute: '/objects/TestObject',
  legacyAliases: [],
  defaultPageMode: 'record',
  defaultDetailSurfaceTab: 'process',
  defaultDocumentSurfaceTab: 'summary',
  toolbar: {
    primaryActions: [],
    secondaryActions: [],
  },
  detailPanels: [],
  asyncIndicators: [],
  summaryCards: [],
  queuePanels: [],
  exceptionPanels: [],
  closurePanel: null,
  slaIndicators: [],
  recommendedActions: [],
  ...overrides,
})

describe('useObjectWorkbench', () => {
  it('filters workbench sections by record status and exposes queue and insight flags', () => {
    const workbench = ref(buildWorkbench({
      primaryEntryRoute: '/objects/FinanceVoucher',
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
    }))
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
    const workbench = ref(buildWorkbench({
      workspaceMode: 'standard',
      primaryEntryRoute: '/objects/InventoryTask',
      closurePanel: {},
    }))
    const recordData = ref({
      status: 'draft',
    })

    const state = useObjectWorkbench({ workbench, recordData })

    expect(state.closurePanel.value).toBeNull()
    expect(state.hasInsights.value).toBe(false)
  })

  it('shows only the status-matched InventoryItem closure actions', () => {
    const workbench = ref(buildWorkbench({
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
    }))
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

  it('hides workspace-priority surfaces on record mode while keeping primary and context cards', () => {
    const workbench = ref(buildWorkbench({
      primaryEntryRoute: '/objects/Asset',
      detailPanels: [
        { code: 'asset_history', component: 'asset-history-panel', surfacePriority: 'related' as RuntimeWorkbenchSurfacePriority },
      ],
      summaryCards: [
        { code: 'asset_code', valueField: 'asset_code', surfacePriority: 'primary' as RuntimeWorkbenchSurfacePriority },
      ],
      queuePanels: [
        { code: 'asset_returns', surfacePriority: 'related' as RuntimeWorkbenchSurfacePriority },
      ],
      exceptionPanels: [
        { code: 'asset_alerts', surfacePriority: 'related' as RuntimeWorkbenchSurfacePriority },
      ],
      closurePanel: {
        stageField: 'status',
        surfacePriority: 'context' as RuntimeWorkbenchSurfacePriority,
      },
      slaIndicators: [
        { code: 'asset_sla', surfacePriority: 'context' as RuntimeWorkbenchSurfacePriority },
      ],
      recommendedActions: [
        { code: 'schedule_follow_up', surfacePriority: 'admin' as RuntimeWorkbenchSurfacePriority },
      ],
    }))
    const recordData = ref({
      status: 'active',
      asset_code: 'ASSET-001',
    })
    const allowedSurfacePriorities = ref<RuntimeWorkbenchSurfacePriority[]>(['primary', 'context'])

    const state = useObjectWorkbench({ workbench, recordData, allowedSurfacePriorities })

    expect(state.summaryCards.value.map((card) => card.code)).toEqual(['asset_code'])
    expect(state.queuePanels.value).toEqual([])
    expect(state.exceptionPanels.value).toEqual([])
    expect(state.detailPanels.value).toEqual([])
    expect(state.recommendedActions.value).toEqual([])
    expect(state.closurePanel.value?.stageField).toBe('status')
    expect(state.slaIndicators.value.map((indicator) => indicator.code)).toEqual(['asset_sla'])
    expect(state.hasInsights.value).toBe(true)
    expect(state.hasQueues.value).toBe(false)
    expect(state.hasPanels.value).toBe(false)
  })
})
