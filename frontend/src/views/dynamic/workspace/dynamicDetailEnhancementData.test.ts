import { describe, expect, it, vi } from 'vitest'
import {
  createEmptyDynamicDetailNavigationCounts,
  extractDynamicDetailReferenceId,
  loadDynamicDetailEnhancementData,
} from './dynamicDetailEnhancementData'

describe('dynamicDetailEnhancementData', () => {
  it('extracts reference ids from object and primitive fields', () => {
    expect(extractDynamicDetailReferenceId({
      asset: {
        id: 'asset-1',
      },
    }, ['asset', 'assetId'])).toBe('asset-1')

    expect(extractDynamicDetailReferenceId({
      assetId: 'asset-2',
    }, ['asset', 'assetId'])).toBe('asset-2')

    expect(extractDynamicDetailReferenceId({}, ['asset', 'assetId'])).toBe('')
  })

  it('loads asset-related closed-loop counts and keeps related record empty', async () => {
    const loadAssetRelatedCounts = vi.fn().mockResolvedValue({
      maintenanceCount: 2,
      disposalCount: 1,
      receiptCount: 0,
      assetCount: 0,
    })

    const result = await loadDynamicDetailEnhancementData({
      objectCode: 'Asset',
      recordId: 'asset-1',
      loadAssetRelatedCounts,
    })

    expect(loadAssetRelatedCounts).toHaveBeenCalledWith('asset-1')
    expect(result).toEqual({
      relatedCounts: {
        maintenanceCount: 2,
        disposalCount: 1,
        receiptCount: 0,
        assetCount: 0,
      },
      relatedRecord: null,
    })
  })

  it('loads the related asset record for maintenance pages and falls back safely', async () => {
    const loadAssetRecord = vi.fn().mockResolvedValue({
      id: 'asset-9',
      sourceReceipt: 'rc-9',
    })

    const maintenanceResult = await loadDynamicDetailEnhancementData({
      objectCode: 'Maintenance',
      recordId: 'mnt-1',
      loadedRecord: {
        asset: { id: 'asset-9' },
      },
      loadAssetRecord,
    })

    expect(loadAssetRecord).toHaveBeenCalledWith('asset-9')
    expect(maintenanceResult.relatedCounts).toEqual(createEmptyDynamicDetailNavigationCounts())
    expect(maintenanceResult.relatedRecord).toEqual({
      id: 'asset-9',
      sourceReceipt: 'rc-9',
    })

    const fallbackResult = await loadDynamicDetailEnhancementData({
      objectCode: 'Maintenance',
      recordId: 'mnt-1',
      loadedRecord: {
        asset: { id: 'asset-10' },
      },
      loadAssetRecord: vi.fn().mockRejectedValue(new Error('boom')),
    })

    expect(fallbackResult).toEqual({
      relatedCounts: createEmptyDynamicDetailNavigationCounts(),
      relatedRecord: null,
    })
  })

  it('returns empty enhancement data for unsupported objects or missing record ids', async () => {
    await expect(loadDynamicDetailEnhancementData({
      objectCode: 'Asset',
      recordId: '',
    })).resolves.toEqual({
      relatedCounts: createEmptyDynamicDetailNavigationCounts(),
      relatedRecord: null,
    })

    await expect(loadDynamicDetailEnhancementData({
      objectCode: 'PurchaseRequest',
      recordId: 'pr-1',
    })).resolves.toEqual({
      relatedCounts: createEmptyDynamicDetailNavigationCounts(),
      relatedRecord: null,
    })
  })
})
