import { computed, ref } from 'vue'
import { describe, expect, it } from 'vitest'
import { useDynamicDetailWorkspace } from './useDynamicDetailWorkspace'
import { formatTimelineHighlightTimestamp } from '@/utils/timelineHighlights'

describe('useDynamicDetailWorkspace', () => {
  it('surfaces cancel reason in detail info rows and status tooltip', () => {
    const loadedRecord = ref<Record<string, unknown> | null>({
      status: 'cancelled',
      custom_fields: {
        cancel_reason: 'Merged into the replacement procurement batch',
      },
    })

    const workspace = useDynamicDetailWorkspace({
      isZhLocale: computed(() => false),
      objectCode: ref('PurchaseRequest'),
      recordId: ref('record-1'),
      objectMetadata: ref({ module: 'lifecycle' } as any),
      objectDisplayName: computed(() => 'Purchase Request'),
      loadedRecord,
      documentPayload: ref(null),
      hasActivitySection: computed(() => false),
    })

    expect(workspace.detailHeroStats.value).toEqual([])
    expect(workspace.processSummaryStats.value[0]).toMatchObject({
      label: 'Status',
      value: 'cancelled',
      tooltip: 'Cancel reason: Merged into the replacement procurement batch',
    })
    expect(workspace.infoRows.value[3]).toEqual({
      label: 'Cancel reason',
      value: 'Merged into the replacement procurement batch',
    })
  })

  it('does not add cancel reason decorations for active records', () => {
    const loadedRecord = ref<Record<string, unknown> | null>({
      status: 'active',
      custom_fields: {
        cancel_reason: 'Should stay hidden',
      },
    })

    const workspace = useDynamicDetailWorkspace({
      isZhLocale: computed(() => false),
      objectCode: ref('InsurancePolicy'),
      recordId: ref('record-2'),
      objectMetadata: ref({ module: 'insurance' } as any),
      objectDisplayName: computed(() => 'Insurance Policy'),
      loadedRecord,
      documentPayload: ref(null),
      hasActivitySection: computed(() => false),
    })

    expect(workspace.detailHeroStats.value).toEqual([])
    expect(workspace.processSummaryStats.value[0]).toMatchObject({
      label: 'Status',
      value: 'active',
    })
    expect(workspace.processSummaryStats.value[0]?.tooltip).toBeUndefined()
    expect(workspace.infoRows.value).toHaveLength(3)
  })

  it('surfaces latest timeline highlight in process summary rows', () => {
    const loadedRecord = ref<Record<string, unknown> | null>({
      status: 'approved',
    })

    const workspace = useDynamicDetailWorkspace({
      isZhLocale: computed(() => false),
      objectCode: ref('AssetLoan'),
      recordId: ref('record-3'),
      objectMetadata: ref({ module: 'assets' } as any),
      objectDisplayName: computed(() => 'Asset Loan'),
      loadedRecord,
      documentPayload: ref({
        timeline: [
          {
            id: 'timeline-1',
            createdAt: '2026-03-18T08:15:00Z',
            sourceLabel: 'Purchase Request',
            objectCode: 'PurchaseRequest',
            objectId: 'pr-1',
            highlights: [
              {
                code: 'approval_comment',
                label: 'Approval Comment',
                value: 'Approved for audit remediation',
                tone: 'info',
              },
            ],
          },
        ],
      } as any),
      hasActivitySection: computed(() => true),
    })

    const expectedTime = formatTimelineHighlightTimestamp('2026-03-18T08:15:00Z', 'en-US')
    expect(workspace.detailHeroStats.value).toEqual([])
    expect(workspace.processSummaryStats.value[0]).toMatchObject({
      label: 'Status',
      value: 'approved',
    })
    expect(workspace.infoRows.value[3]).toEqual({
      label: 'Latest signal',
      value: 'Approval Comment: Approved for audit remediation',
      tooltip: `Approval Comment: Approved for audit remediation · Purchase Request · ${expectedTime}`,
      meta: `Purchase Request · ${expectedTime}`,
      actions: [
        { label: 'Open source', to: '/objects/PurchaseRequest/pr-1' },
        { label: 'Jump to activity', to: { hash: '#detail-activity' } },
      ],
    })
    expect(workspace.infoRows.value[4]).toEqual({
      label: 'Source object',
      value: 'Purchase Request',
      actions: [{ label: 'Open source', to: '/objects/PurchaseRequest/pr-1' }],
    })
    expect(workspace.infoRows.value[5]).toEqual({
      label: 'Signal time',
      value: expectedTime,
      actions: [{ label: 'Jump to activity', to: { hash: '#detail-activity' } }],
    })
    expect(workspace.closureRows.value[0]).toEqual({
      label: 'Latest signal',
      value: 'Approval Comment: Approved for audit remediation',
      tooltip: `Approval Comment: Approved for audit remediation · Purchase Request · ${expectedTime}`,
      meta: `Purchase Request · ${expectedTime}`,
      actions: [
        { label: 'Open source', to: '/objects/PurchaseRequest/pr-1' },
        { label: 'Jump to activity', to: { hash: '#detail-activity' } },
      ],
    })
  })
})
