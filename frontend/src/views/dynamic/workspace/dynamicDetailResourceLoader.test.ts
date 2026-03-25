import { describe, expect, it, vi } from 'vitest'
import type { ObjectMetadata } from '@/api/dynamic'
import type { AggregateDocumentResponse, RuntimeAggregate, RuntimeWorkbench } from '@/types/runtime'
import {
  buildDynamicDetailFallbackMetadata,
  loadDynamicDetailResources,
  resolveDynamicDetailLoadError,
} from './dynamicDetailResourceLoader'

const t = (key: string) => key

const aggregate = {
  objectCode: 'PurchaseRequest',
  objectRole: 'root',
  isAggregateRoot: true,
  isDetailObject: false,
  detailRegions: [
    {
      relationCode: 'purchase_request_items',
      fieldCode: 'items',
      title: 'Items',
      targetObjectCode: 'PurchaseRequestItem',
    },
  ],
} as RuntimeAggregate

const defaultWorkbench: RuntimeWorkbench = {
  workspaceMode: 'standard',
  primaryEntryRoute: '/objects/PurchaseRequest',
  legacyAliases: [],
  toolbar: {
    primaryActions: [],
    secondaryActions: [],
  },
  detailPanels: [],
  asyncIndicators: [],
}

const documentPayload: AggregateDocumentResponse = {
  documentVersion: 1,
  context: {
    objectCode: 'PurchaseRequest',
    recordId: 'pr-1',
    pageMode: 'readonly',
    recordLabel: 'PR-001',
  },
  aggregate,
  master: {
    status: 'draft',
  },
  details: {
    purchase_request_items: {
      relationCode: 'purchase_request_items',
      fieldCode: 'items',
      title: 'Items',
      targetObjectCode: 'PurchaseRequestItem',
      rows: [{ id: 'line-1', itemName: 'Laptop' }],
      rowCount: 1,
      editable: false,
    },
  },
  capabilities: {
    canEditMaster: true,
    canEditDetails: true,
    canSave: true,
    canSubmit: true,
    canDelete: true,
    canApprove: false,
    readOnly: true,
  },
  workflow: {
    businessObjectCode: 'PurchaseRequest',
    hasPublishedDefinition: false,
    definition: null,
    hasInstance: false,
    isActive: false,
    instance: null,
    timeline: [],
  },
  timeline: [],
  audit: {
    counts: {
      activityLogs: 0,
      workflowApprovals: 0,
      workflowOperationLogs: 0,
    },
    activityLogs: [],
    workflowApprovals: [],
    workflowOperationLogs: [],
  },
}

describe('dynamicDetailResourceLoader', () => {
  it('builds fallback metadata for unresolved objects', () => {
    expect(buildDynamicDetailFallbackMetadata('UnknownObject')).toMatchObject({
      code: 'UnknownObject',
      name: 'UnknownObject',
      permissions: {
        view: true,
        add: true,
        change: true,
        delete: true,
      },
    })
  })

  it('loads runtime, metadata, and aggregate document data into a normalized result', async () => {
    const loadDocument = vi.fn().mockResolvedValue(documentPayload)

    const result = await loadDynamicDetailResources({
      objectCode: 'PurchaseRequest',
      recordId: 'pr-1',
      t,
      loadRuntimeLayout: async () => ({
        source: 'runtime',
        runtimeMode: 'readonly',
        metadataContext: 'detail',
        layoutType: 'detail',
        viewMode: 'Detail',
        layoutConfig: null,
        layoutStatus: null,
        layoutVersion: null,
        isDefault: true,
        permissions: { view: true, add: true, change: true, delete: false },
        fields: [],
        editableFields: [],
        reverseRelations: [],
        aggregate,
        workbench: defaultWorkbench,
      }),
      loadMetadata: async () => ({
        code: 'PurchaseRequest',
        name: 'Purchase Request',
        permissions: { view: true, add: true, change: true, delete: true },
      } as ObjectMetadata),
      loadDocument,
    })

    expect(loadDocument).toHaveBeenCalledWith('pr-1')
    expect(result.runtimePermissions).toEqual({ view: true, add: true, change: true, delete: false })
    expect(result.runtimeWorkbench).toEqual(defaultWorkbench)
    expect(result.objectMetadata?.name).toBe('Purchase Request')
    expect(result.usesAggregateDocument).toBe(true)
    expect(result.documentPayload).toEqual(documentPayload)
    expect(result.loadedRecord).toMatchObject({
      id: 'pr-1',
      items: [{ id: 'line-1', itemName: 'Laptop' }],
    })
    expect(result.lifecycleRecordData).toEqual(result.loadedRecord)
    expect(result.loadError).toBeNull()
  })

  it('falls back to metadata shell and surfaces document load errors when needed', async () => {
    const result = await loadDynamicDetailResources({
      objectCode: 'PurchaseRequest',
      recordId: 'pr-1',
      t,
      loadRuntimeLayout: async () => ({
        source: 'runtime',
        runtimeMode: 'readonly',
        metadataContext: 'detail',
        layoutType: 'detail',
        viewMode: 'Detail',
        layoutConfig: null,
        layoutStatus: null,
        layoutVersion: null,
        isDefault: true,
        permissions: { view: true, add: true, change: true, delete: false },
        fields: [],
        editableFields: [],
        reverseRelations: [],
        aggregate,
        workbench: defaultWorkbench,
      }),
      loadMetadata: async () => {
        throw new Error('metadata failed')
      },
      loadDocument: async () => {
        throw new Error('document failed')
      },
    })

    expect(result.usedFallbackMetadata).toBe(true)
    expect(result.objectMetadata?.code).toBe('PurchaseRequest')
    expect(result.runtimeWorkbench).toEqual(defaultWorkbench)
    expect(result.loadError).toBe('document failed')
    expect(result.documentPayload).toBeNull()
    expect(result.loadedRecord).toBeNull()
  })

  it('resolves combined load errors when runtime and metadata both fail', async () => {
    await expect(loadDynamicDetailResources({
      objectCode: 'Asset',
      recordId: 'asset-1',
      t,
      loadRuntimeLayout: async () => {
        throw new Error('runtime failed')
      },
      loadMetadata: async () => {
        throw new Error('metadata failed')
      },
      loadDocument: async () => documentPayload,
    })).resolves.toMatchObject({
      loadError: 'metadata failed',
      usedFallbackMetadata: true,
      usesAggregateDocument: false,
      runtimeWorkbench: null,
    })

    expect(resolveDynamicDetailLoadError({
      runtimeError: new Error('runtime'),
      metadataError: new Error('metadata'),
      documentError: new Error('document'),
      t,
    })).toBe('document')
  })
})
