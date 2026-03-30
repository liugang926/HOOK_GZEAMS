import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { useBaseDetailPageRelations } from '../useBaseDetailPageRelations'
import { dynamicApi } from '@/api/dynamic'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key
  })
}))

vi.mock('@/platform/reference/relationGrouping', () => ({
  defaultRelationGroupTitle: (_groupKey: string, resolver: (key: string, fallback: string) => string) =>
    resolver('relatedObjects.group.default', 'Related Objects'),
  groupRelations: (relations: Array<Record<string, any>>) => [
    {
      key: 'default',
      title: 'Related Objects',
      defaultExpanded: true,
      relations
    }
  ]
}))

vi.mock('@/composables/useRelationGroupExpansion', () => ({
  useRelationGroupExpansion: () => ({
    isExpanded: () => true,
    toggle: vi.fn()
  })
}))

vi.mock('@/api/dynamic', () => ({
  dynamicApi: {
    getRelations: vi.fn()
  }
}))

describe('useBaseDetailPageRelations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('routes L1 relations into lineItemRelations and keeps them out of Related tab groups', () => {
    const runtimeRelations = ref([
      {
        code: 'items',
        label: 'Items',
        displayMode: 'inline_readonly' as const,
        displayTier: 'L1' as const,
        relationKind: 'direct_fk',
        sortOrder: 1
      },
      {
        code: 'attachments',
        label: 'Attachments',
        displayMode: 'tab_readonly' as const,
        displayTier: 'L2' as const,
        sortOrder: 2
      },
      {
        code: 'hidden_notes',
        label: 'Hidden Notes',
        displayMode: 'hidden' as const,
        displayTier: 'L2' as const,
        sortOrder: 3
      }
    ])

    const relations = useBaseDetailPageRelations({
      props: {
        data: { id: 'pickup-1' },
        objectCode: 'AssetPickup',
        reverseRelations: [],
        showRelatedObjects: true,
        resolveRuntimeRelations: false,
        relationGroupScopeId: 'pickup-1'
      },
      runtimeRelations
    })

    expect(relations.lineItemRelations.value.map((item) => item.code)).toEqual(['items'])
    expect(relations.visibleReverseRelations.value.map((item) => item.code)).toEqual(['attachments'])
    expect(relations.groupedReverseRelationSections.value[0]?.relations.map((item: any) => item.code)).toEqual([
      'attachments'
    ])
  })

  it('keeps through-line-item asset relations in Related even if stale metadata marks them as L1', () => {
    const runtimeRelations = ref([
      {
        code: 'pickup_items',
        label: 'Pickup Items',
        displayMode: 'inline_readonly' as const,
        displayTier: 'L1' as const,
        relationKind: 'direct_fk',
        sortOrder: 1
      },
      {
        code: 'assets',
        label: 'Pickup Assets',
        displayMode: 'inline_readonly' as const,
        displayTier: 'L1' as const,
        relationKind: 'through_line_item',
        sortOrder: 2
      }
    ])

    const relations = useBaseDetailPageRelations({
      props: {
        data: { id: 'pickup-legacy' },
        objectCode: 'AssetPickup',
        reverseRelations: [],
        showRelatedObjects: true,
        resolveRuntimeRelations: false,
        relationGroupScopeId: 'pickup-legacy'
      },
      runtimeRelations
    })

    expect(relations.lineItemRelations.value.map((item) => item.code)).toEqual(['pickup_items'])
    expect(relations.visibleReverseRelations.value.map((item) => item.code)).toEqual(['assets'])
  })

  it('maps runtime getRelations payloads and preserves L1 display tier metadata', async () => {
    vi.mocked(dynamicApi.getRelations).mockResolvedValue({
      relations: [
        {
          relationCode: 'items',
          relationName: 'Items',
          displayMode: 'inline_readonly',
          displayTier: 'L1',
          relationKind: 'direct_fk',
          targetObjectCode: 'PickupItem',
          targetFkField: 'pickup',
          sortOrder: 1
        },
        {
          relationCode: 'comments',
          relationName: 'Comments',
          displayMode: 'tab_readonly',
          displayTier: 'L2',
          relationKind: 'direct_fk',
          targetObjectCode: 'Comment',
          targetFkField: 'record_id',
          sortOrder: 2
        }
      ]
    })

    const runtimeRelations = ref<Array<Record<string, any>>>([])
    const relations = useBaseDetailPageRelations({
      props: {
        data: { id: 'pickup-2' },
        objectCode: 'AssetPickup',
        reverseRelations: [],
        showRelatedObjects: true,
        resolveRuntimeRelations: true,
        relationGroupScopeId: 'pickup-2'
      },
      runtimeRelations
    })

    await relations.fetchRuntimeRelations()

    expect(dynamicApi.getRelations).toHaveBeenCalledWith('AssetPickup')
    expect(runtimeRelations.value.map((item) => item.code)).toEqual(['items', 'comments'])
    expect(runtimeRelations.value[0]).toMatchObject({
      code: 'items',
      displayTier: 'L1',
      relationKind: 'direct_fk',
      relatedObjectCode: 'PickupItem',
      reverseRelationField: 'pickup'
    })
    expect(relations.lineItemRelations.value.map((item) => item.code)).toEqual(['items'])
    expect(relations.visibleReverseRelations.value.map((item) => item.code)).toEqual(['comments'])
  })

  it('filters audit relations out of Related when metadata marks them as history/log sources', () => {
    const runtimeRelations = ref([
      {
        code: 'configuration_changes',
        label: 'Configuration Changes',
        displayMode: 'tab_readonly' as const,
        displayTier: 'L2' as const,
        targetObjectRole: 'log',
        extraConfig: {
          presentationZone: 'history'
        },
        sortOrder: 1
      },
      {
        code: 'attachments',
        label: 'Attachments',
        displayMode: 'tab_readonly' as const,
        displayTier: 'L2' as const,
        sortOrder: 2
      }
    ])

    const relations = useBaseDetailPageRelations({
      props: {
        data: { id: 'asset-1' },
        objectCode: 'Asset',
        reverseRelations: [],
        showRelatedObjects: true,
        resolveRuntimeRelations: false,
        relationGroupScopeId: 'asset-1'
      },
      runtimeRelations
    })

    expect(relations.lineItemRelations.value).toEqual([])
    expect(relations.visibleReverseRelations.value.map((item) => item.code)).toEqual(['attachments'])
  })
})
