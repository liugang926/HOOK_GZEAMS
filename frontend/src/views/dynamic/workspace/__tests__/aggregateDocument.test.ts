import { describe, expect, it } from 'vitest'
import type { AggregateDocumentResponse, RuntimeAggregate } from '@/types/runtime'
import {
  buildAggregateDocumentFormData,
  buildAggregateDocumentPayload,
  readAggregateDocumentDetailRows,
  resolveAggregateDocumentDetailPath,
  resolveAggregateDetailFieldCode,
  supportsAggregateDocument,
  writeAggregateDocumentDetailRows,
} from '../aggregateDocument'

const aggregate = {
  objectCode: 'AssetPickup',
  objectRole: 'root',
  isAggregateRoot: true,
  isDetailObject: false,
  detailRegions: [
    {
      relationCode: 'pickup_items',
      fieldCode: 'items',
      title: 'Pickup Items',
      targetObjectCode: 'PickupItem',
    },
  ],
} as RuntimeAggregate

const document = {
  documentVersion: 1,
  context: {
    objectCode: 'AssetPickup',
    recordId: 'pickup-1',
    pageMode: 'edit',
    recordLabel: 'PU-0001',
  },
  aggregate,
  master: {
    status: 'draft',
    pickupReason: 'Need a laptop',
  },
  details: {
    pickup_items: {
      relationCode: 'pickup_items',
      fieldCode: 'items',
      title: 'Pickup Items',
      targetObjectCode: 'PickupItem',
      rowCount: 1,
      editable: true,
      rows: [
        {
          id: 'row-1',
          quantity: 1,
          remark: 'Primary row',
        },
      ],
    },
  },
  capabilities: {
    canEditMaster: true,
    canEditDetails: true,
    canSave: true,
    canSubmit: true,
    canDelete: true,
    canApprove: false,
    readOnly: false,
  },
  workflow: {
    businessObjectCode: 'asset_pickup',
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
      activityLogs: 1,
      workflowApprovals: 0,
      workflowOperationLogs: 0,
    },
    activityLogs: [],
    workflowApprovals: [],
    workflowOperationLogs: [],
  },
} as AggregateDocumentResponse

describe('aggregateDocument helpers', () => {
  it('detects supported aggregate document objects from runtime aggregate metadata', () => {
    expect(supportsAggregateDocument('AssetPickup', aggregate)).toBe(true)
    expect(supportsAggregateDocument('AssetReceipt', {
      ...aggregate,
      objectCode: 'AssetReceipt',
    } as RuntimeAggregate)).toBe(true)
    expect(supportsAggregateDocument('DisposalRequest', {
      ...aggregate,
      objectCode: 'DisposalRequest',
    } as RuntimeAggregate)).toBe(true)
    expect(supportsAggregateDocument('Asset', aggregate)).toBe(false)
    expect(supportsAggregateDocument('AssetPickup', null)).toBe(false)
  })

  it('merges master and detail rows into the form model', () => {
    const formData = buildAggregateDocumentFormData(document)

    expect(formData).toMatchObject({
      id: 'pickup-1',
      status: 'draft',
      pickupReason: 'Need a laptop',
    })
    expect(formData.items).toEqual([
      {
        id: 'row-1',
        quantity: 1,
        remark: 'Primary row',
      },
    ])
    expect(formData.pickup_items).toEqual({
      rows: [
        {
          id: 'row-1',
          quantity: 1,
          remark: 'Primary row',
        },
      ],
    })
  })

  it('splits runtime submit data back into master/detail document payload', () => {
    const payload = buildAggregateDocumentPayload(
      {
        pickupReason: 'Updated reason',
        status: 'draft',
        items: [
          { id: 'row-1', quantity: 2 },
          { quantity: 1, remark: 'New row' },
        ],
      },
      aggregate,
    )

    expect(payload.master).toEqual({
      pickupReason: 'Updated reason',
      status: 'draft',
    })
    expect(payload.details).toEqual({
      pickup_items: {
        rows: [
          { id: 'row-1', quantity: 2 },
          { quantity: 1, remark: 'New row' },
        ],
      },
    })
  })

  it('resolves aggregate document detail paths from the returned document payload', () => {
    expect(resolveAggregateDocumentDetailPath('AssetPickup', document)).toBe('/objects/AssetPickup/pickup-1')
    expect(resolveAggregateDocumentDetailPath('AssetPickup', null)).toBeNull()
  })

  it('reads and writes aggregate detail rows using region metadata', () => {
    expect(resolveAggregateDetailFieldCode(aggregate.detailRegions[0])).toBe('items')
    expect(readAggregateDocumentDetailRows({
      pickupItems: [{ id: 'row-1', quantity: 3 }],
    }, aggregate)).toEqual([
      { id: 'row-1', quantity: 3 },
    ])

    expect(writeAggregateDocumentDetailRows(
      { pickupReason: 'Need a laptop' },
      aggregate,
      [{ id: 'row-2', quantity: 1 }],
    )).toEqual({
      pickupReason: 'Need a laptop',
      items: [{ id: 'row-2', quantity: 1 }],
      pickup_items: {
        rows: [{ id: 'row-2', quantity: 1 }],
      },
    })
  })
})
