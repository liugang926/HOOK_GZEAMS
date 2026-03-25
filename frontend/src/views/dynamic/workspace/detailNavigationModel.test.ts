import { describe, expect, it } from 'vitest'
import {
  buildDynamicDetailNavigationSection,
  buildDynamicDetailTimelineConfig,
} from './detailNavigationModel'

const t = (key: string, params?: Record<string, unknown>) => {
  if (!params) return key
  return `${key}:${JSON.stringify(params)}`
}

describe('detailNavigationModel', () => {
  it('builds asset lifecycle navigation with source traceability and downstream links', () => {
    const section = buildDynamicDetailNavigationSection({
      objectCode: 'Asset',
      recordId: 'asset-1',
      record: {
        sourcePurchaseRequest: 'pr-1',
        sourcePurchaseRequestNo: 'PR-001',
        sourceReceipt: 'rc-1',
        sourceReceiptNo: 'RC-001',
      },
      counts: {
        maintenanceCount: 3,
        disposalCount: 1,
      },
      t,
    })

    expect(section?.title).toBe('common.detailNavigation.sections.lifecycleLinks')
    expect(section?.items).toEqual([
      {
        key: 'source-purchase-request',
        objectCode: 'PurchaseRequest',
        recordId: 'pr-1',
        label: 'common.detailNavigation.asset.purchaseRequestWithNo:{"no":"PR-001"}',
        type: 'primary',
      },
      {
        key: 'source-receipt',
        objectCode: 'AssetReceipt',
        recordId: 'rc-1',
        label: 'common.detailNavigation.asset.receiptWithNo:{"no":"RC-001"}',
        type: 'success',
      },
      {
        key: 'maintenance-list',
        objectCode: 'Maintenance',
        query: { asset_id: 'asset-1' },
        label: 'common.detailNavigation.asset.maintenanceRecords:{"count":3}',
        type: 'warning',
      },
      {
        key: 'disposal-list',
        objectCode: 'DisposalRequest',
        query: { asset_id: 'asset-1' },
        label: 'common.detailNavigation.asset.disposalRequests:{"count":1}',
        type: 'danger',
      },
    ])
  })

  it('returns null for unsupported objects and falls back when source links are missing', () => {
    expect(buildDynamicDetailNavigationSection({
      objectCode: 'Maintenance',
      recordId: 'mnt-1',
      record: {},
      counts: {},
      t,
    })).toBeNull()

    const section = buildDynamicDetailNavigationSection({
      objectCode: 'Asset',
      recordId: 'asset-2',
      record: {},
      counts: {},
      t,
    })

    expect(section?.items).toEqual([
      {
        key: 'maintenance-list',
        objectCode: 'Maintenance',
        query: { asset_id: 'asset-2' },
        label: 'common.detailNavigation.asset.maintenanceRecords:{"count":0}',
        type: 'warning',
      },
      {
        key: 'disposal-list',
        objectCode: 'DisposalRequest',
        query: { asset_id: 'asset-2' },
        label: 'common.detailNavigation.asset.disposalRequests:{"count":0}',
        type: 'danger',
      },
    ])
  })

  it('builds maintenance lifecycle navigation back to the asset and upstream documents', () => {
    const section = buildDynamicDetailNavigationSection({
      objectCode: 'Maintenance',
      recordId: 'mnt-1',
      record: {
        asset: { id: 'asset-9', assetCode: 'ASSET-009' },
      },
      relatedRecord: {
        sourceReceipt: 'rc-9',
        sourceReceiptNo: 'RC-009',
        sourcePurchaseRequest: 'pr-9',
        sourcePurchaseRequestNo: 'PR-009',
      },
      counts: {},
      t,
    })

    expect(section?.title).toBe('common.detailNavigation.sections.lifecycleLinks')
    expect(section?.items).toEqual([
      {
        key: 'maintenance-asset',
        objectCode: 'Asset',
        recordId: 'asset-9',
        label: 'common.detailNavigation.maintenance.assetWithLabel:{"label":"ASSET-009"}',
        type: 'primary',
      },
      {
        key: 'maintenance-source-receipt',
        objectCode: 'AssetReceipt',
        recordId: 'rc-9',
        label: 'common.detailNavigation.maintenance.receiptWithNo:{"no":"RC-009"}',
        type: 'success',
      },
      {
        key: 'maintenance-source-purchase-request',
        objectCode: 'PurchaseRequest',
        recordId: 'pr-9',
        label: 'common.detailNavigation.maintenance.purchaseRequestWithNo:{"no":"PR-009"}',
        type: 'warning',
      },
    ])
  })

  it('builds lifecycle-aware timeline config for the unified detail page', () => {
    expect(buildDynamicDetailTimelineConfig({
      objectCode: 'Asset',
      recordId: 'asset 1',
    })).toEqual({
      objectCode: 'Asset',
      recordId: 'asset 1',
      fetchUrl: '/assets/asset%201/lifecycle-timeline/',
    })

    expect(buildDynamicDetailTimelineConfig({
      objectCode: 'Maintenance',
      recordId: 'mnt-1',
    })).toEqual({
      objectCode: 'Maintenance',
      recordId: 'mnt-1',
      fetchUrl: '',
    })

    expect(buildDynamicDetailTimelineConfig({
      objectCode: 'PurchaseRequest',
      recordId: 'pr-1',
    })).toEqual({
      objectCode: 'PurchaseRequest',
      recordId: 'pr-1',
      fetchUrl: '/lifecycle/purchase-requests/pr-1/timeline/',
    })

    expect(buildDynamicDetailTimelineConfig({
      objectCode: 'UnknownObject',
      recordId: 'x-1',
    })).toBeNull()
  })
})
