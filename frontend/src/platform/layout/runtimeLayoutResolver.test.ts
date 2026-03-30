import { beforeEach, describe, expect, it, vi } from 'vitest'
import { resolveRuntimeLayout } from './runtimeLayoutResolver'
import { dynamicApi } from '@/api/dynamic'
import { businessObjectApi, pageLayoutApi } from '@/api/system'

type RuntimeLayoutSections = {
  sections?: Array<{
    fields?: Array<{ fieldCode?: string }>
  }>
}

vi.mock('@/api/dynamic', () => ({
  dynamicApi: {
    getRuntime: vi.fn()
  }
}))

vi.mock('@/api/system', () => ({
  businessObjectApi: {
    getFieldsWithContext: vi.fn()
  },
  pageLayoutApi: {
    getDefault: vi.fn()
  }
}))

describe('resolveRuntimeLayout', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('returns readonly runtime payload directly from backend shared model', async () => {
    vi.mocked(dynamicApi.getRuntime).mockResolvedValue({
      context: 'form',
      fields: {
        editableFields: [{ code: 'name', fieldType: 'text' }],
        reverseRelations: [{ code: 'maintenanceRecords', fieldType: 'sub_table' }]
      },
      permissions: {
        view: true,
        add: true,
        change: false,
        delete: false
      },
      aggregate: {
        objectCode: 'AssetPickup',
        objectRole: 'root',
        isAggregateRoot: true,
        isDetailObject: false,
        detailRegions: [
          {
            relationCode: 'pickup_items',
            fieldCode: 'items',
            title: '领用明细',
            titleEn: 'Pickup Items',
            relationType: 'master_detail',
            detailEditMode: 'inline_table',
          }
        ]
      },
      workbench: {
        workspaceMode: 'extended',
        primaryEntryRoute: '/objects/Asset',
        legacyAliases: ['/assets'],
        toolbar: {
          primaryActions: [{ code: 'saveDraft' }],
          secondaryActions: [{ code: 'openAudit' }],
        },
        detailPanels: [{ code: 'integration_logs', component: 'integration-log-table' }],
        asyncIndicators: [{ code: 'voucher_push', type: 'sync-task' }],
        summaryCards: [{ code: 'pending_count', valueField: 'pendingCount' }],
        queuePanels: [{ code: 'approval_queue', queueCode: 'review' }],
        exceptionPanels: [{ code: 'push_failed', queueCode: 'exception' }],
        closurePanel: { stageField: 'status' },
        slaIndicators: [{ code: 'approval_sla', statusField: 'slaStatus' }],
        recommendedActions: [{ code: 'follow_up', actionPath: 'follow_up' }],
      },
      isDefault: false,
      layout: {
        status: 'published',
        version: '2.1.0',
        layoutConfig: {
          sections: [
            {
              id: 'basic',
              type: 'section',
              title: 'Basic Information',
              fields: [{ fieldCode: 'name', label: 'Name', span: 12 }]
            }
          ]
        }
      }
    } as unknown as Awaited<ReturnType<typeof dynamicApi.getRuntime>>)

    const result = await resolveRuntimeLayout('Asset', 'readonly', { includeRelations: true })
    const layoutConfig = result.layoutConfig as RuntimeLayoutSections | null

    expect(result.source).toBe('runtime')
    expect(result.runtimeMode).toBe('readonly')
    expect(result.metadataContext).toBe('form')
    expect(result.layoutType).toBe('form')
    expect(result.layoutStatus).toBe('published')
    expect(result.layoutVersion).toBe('2.1.0')
    expect(result.isDefault).toBe(false)
    expect(result.permissions).toEqual({
      view: true,
      add: true,
      change: false,
      delete: false
    })
    expect(result.workbench.workspaceMode).toBe('extended')
    expect(result.workbench.primaryEntryRoute).toBe('/objects/Asset')
    expect(result.workbench.legacyAliases).toEqual(['/assets'])
    expect(result.workbench.toolbar.primaryActions).toHaveLength(1)
    expect(result.workbench.detailPanels[0]?.code).toBe('integration_logs')
    expect(result.workbench.asyncIndicators[0]?.code).toBe('voucher_push')
    expect(result.workbench.summaryCards[0]?.code).toBe('pending_count')
    expect(result.workbench.queuePanels[0]?.code).toBe('approval_queue')
    expect(result.workbench.exceptionPanels[0]?.code).toBe('push_failed')
    expect(result.workbench.closurePanel?.stageField).toBe('status')
    expect(result.workbench.slaIndicators[0]?.code).toBe('approval_sla')
    expect(result.workbench.recommendedActions[0]?.code).toBe('follow_up')
    expect(result.aggregate?.isAggregateRoot).toBe(true)
    expect(result.aggregate?.detailRegions?.[0]?.relationCode).toBe('pickup_items')
    expect(result.aggregate?.detailRegions?.[0]?.fieldCode).toBe('items')
    expect(result.fields).toHaveLength(2)
    expect(layoutConfig?.sections?.length).toBe(1)
    expect(layoutConfig?.sections?.[0]?.fields?.[0]?.fieldCode).toBe('name')
    expect(dynamicApi.getRuntime).toHaveBeenCalledTimes(1)
    expect(businessObjectApi.getFieldsWithContext).not.toHaveBeenCalled()
    expect(pageLayoutApi.getDefault).not.toHaveBeenCalled()
  })

  it('returns runtime payload when non-readonly runtime endpoint succeeds', async () => {
    vi.mocked(dynamicApi.getRuntime).mockResolvedValue({
      fields: {
        editableFields: [{ code: 'name', fieldType: 'text' }],
        reverseRelations: [{ code: 'maintenanceRecords', fieldType: 'sub_table' }]
      },
      permissions: {
        view: true,
        add: true,
        change: false,
        delete: false
      },
      isDefault: false,
      layout: {
        status: 'published',
        version: '2.1.0',
        layoutConfig: {
          sections: [
            {
              id: 'basic',
              type: 'section',
              fields: [{ fieldCode: 'name', label: 'Name', span: 12 }]
            }
          ]
        }
      }
    } as unknown as Awaited<ReturnType<typeof dynamicApi.getRuntime>>)

    const result = await resolveRuntimeLayout('Asset', 'edit', { includeRelations: true })
    const layoutConfig = result.layoutConfig as RuntimeLayoutSections | null

    expect(result.source).toBe('runtime')
    expect(result.runtimeMode).toBe('edit')
    expect(result.layoutType).toBe('form')
    expect(result.layoutStatus).toBe('published')
    expect(result.layoutVersion).toBe('2.1.0')
    expect(result.isDefault).toBe(false)
    expect(result.permissions).toEqual({
      view: true,
      add: true,
      change: false,
      delete: false
    })
    expect(result.fields).toHaveLength(2)
    expect(layoutConfig?.sections?.length).toBe(1)
    expect(dynamicApi.getRuntime).toHaveBeenCalledTimes(1)
    expect(businessObjectApi.getFieldsWithContext).not.toHaveBeenCalled()
    expect(pageLayoutApi.getDefault).not.toHaveBeenCalled()
  })

  it('falls back to legacy endpoints when runtime fails', async () => {
    vi.mocked(dynamicApi.getRuntime).mockRejectedValue(new Error('runtime failed'))
    vi.mocked(businessObjectApi.getFieldsWithContext).mockResolvedValue({
      editableFields: [{ code: 'assetName', fieldType: 'text' }],
      reverseRelations: []
    } as unknown as Awaited<ReturnType<typeof businessObjectApi.getFieldsWithContext>>)
    vi.mocked(pageLayoutApi.getDefault).mockResolvedValue({
      isDefault: true,
      version: '1.0.0',
      layoutConfig: {
        sections: [{ id: 's1', type: 'section', fields: [{ fieldCode: 'assetName' }] }]
      }
    } as unknown as Awaited<ReturnType<typeof pageLayoutApi.getDefault>>)

    const result = await resolveRuntimeLayout('Asset', 'detail')
    const layoutConfig = result.layoutConfig as RuntimeLayoutSections | null

    expect(result.source).toBe('legacy')
    expect(result.runtimeMode).toBe('readonly')
    expect(result.metadataContext).toBe('form')
    expect(result.layoutType).toBe('form')
    expect(result.isDefault).toBe(true)
    expect(result.layoutVersion).toBe('1.0.0')
    expect(result.permissions).toBeNull()
    expect(result.aggregate).toBeNull()
    expect(result.workbench.workspaceMode).toBe('standard')
    expect(result.workbench.primaryEntryRoute).toBe('/objects/Asset')
    expect(result.workbench.legacyAliases).toEqual([])
    expect(result.workbench.toolbar.primaryActions).toEqual([])
    expect(result.workbench.detailPanels).toEqual([])
    expect(result.workbench.asyncIndicators).toEqual([])
    expect(result.workbench.summaryCards).toEqual([])
    expect(result.workbench.queuePanels).toEqual([])
    expect(result.workbench.exceptionPanels).toEqual([])
    expect(result.workbench.closurePanel).toBeNull()
    expect(result.workbench.slaIndicators).toEqual([])
    expect(result.workbench.recommendedActions).toEqual([])
    expect(result.fields).toHaveLength(1)
    expect(layoutConfig?.sections?.[0]?.fields?.[0]?.fieldCode).toBe('assetName')
    expect(businessObjectApi.getFieldsWithContext).toHaveBeenCalledWith('Asset', 'form', { includeRelations: true })
    expect(pageLayoutApi.getDefault).toHaveBeenCalledTimes(1)
    expect(pageLayoutApi.getDefault).toHaveBeenCalledWith('Asset', 'form')
  })

  it('passes view_mode to runtime API when preferredViewMode is Compact', async () => {
    vi.mocked(dynamicApi.getRuntime).mockResolvedValue({
      fields: {
        editableFields: [
          { code: 'name', fieldType: 'text', isRequired: true },
          { code: 'description', fieldType: 'text' }
        ],
        reverseRelations: []
      },
      permissions: { view: true, add: true, change: true, delete: false },
      isDefault: false,
      layout: {
        status: 'published',
        version: '1.0.0',
        layoutConfig: {
          sections: [
            {
              id: 'basic',
              type: 'section',
              fields: [
                { fieldCode: 'name', label: 'Name', span: 12 },
                { fieldCode: 'description', label: 'Desc', span: 12 }
              ]
            }
          ]
        }
      }
    } as unknown as Awaited<ReturnType<typeof dynamicApi.getRuntime>>)

    const result = await resolveRuntimeLayout('Asset', 'edit', {
      includeRelations: false,
      preferredViewMode: 'Compact'
    })

    expect(result.viewMode).toBe('Compact')
    expect(result.layoutConfig?.layoutType).toBe('Compact')
    expect(result.layoutConfig?.sections).toHaveLength(1)
    expect(dynamicApi.getRuntime).toHaveBeenCalledWith(
      'Asset', 'edit',
      expect.objectContaining({ view_mode: 'Compact' })
    )
  })
})
