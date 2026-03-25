import { assetApi } from '@/api/assets'
import { disposalRequestApi, maintenanceApi } from '@/api/dynamic'
import { loadClosedLoopCounts } from '@/composables/useClosedLoopNavigation'
import type { DynamicDetailNavigationCounts } from './detailNavigationModel'

export interface DynamicDetailEnhancementData {
  relatedCounts: DynamicDetailNavigationCounts
  relatedRecord: Record<string, any> | null
}

interface LoadDynamicDetailEnhancementDataOptions {
  objectCode: string
  recordId: string
  loadedRecord?: Record<string, any> | null
  loadAssetRelatedCounts?: (recordId: string) => Promise<DynamicDetailNavigationCounts>
  loadAssetRecord?: (assetId: string) => Promise<Record<string, any> | null>
}

export const createEmptyDynamicDetailNavigationCounts = (): DynamicDetailNavigationCounts => ({
  maintenanceCount: 0,
  disposalCount: 0,
  receiptCount: 0,
  assetCount: 0,
})

export const extractDynamicDetailReferenceId = (
  record: Record<string, any> | null | undefined,
  keys: string[],
) => {
  for (const key of keys) {
    if (!key) continue
    const value = record?.[key]
    if (value && typeof value === 'object') {
      const candidate = String((value as Record<string, any>).id || (value as Record<string, any>).pk || '').trim()
      if (candidate) {
        return candidate
      }
      continue
    }

    const candidate = String(value || '').trim()
    if (candidate) {
      return candidate
    }
  }

  return ''
}

const loadDefaultAssetRelatedCounts = async (recordId: string) => {
  return loadClosedLoopCounts(
    {
      maintenanceCount: () => maintenanceApi.list({ asset_id: recordId, page: 1, page_size: 1 }),
      disposalCount: () => disposalRequestApi.list({ asset_id: recordId, page: 1, page_size: 1 }),
    },
    createEmptyDynamicDetailNavigationCounts(),
  )
}

const loadDefaultAssetRecord = async (assetId: string) => {
  return (await assetApi.get(assetId)) as Record<string, any>
}

export const loadDynamicDetailEnhancementData = async ({
  objectCode,
  recordId,
  loadedRecord,
  loadAssetRelatedCounts = loadDefaultAssetRelatedCounts,
  loadAssetRecord = loadDefaultAssetRecord,
}: LoadDynamicDetailEnhancementDataOptions): Promise<DynamicDetailEnhancementData> => {
  const normalizedObjectCode = String(objectCode || '').trim()
  const normalizedRecordId = String(recordId || '').trim()

  if (!normalizedRecordId) {
    return {
      relatedCounts: createEmptyDynamicDetailNavigationCounts(),
      relatedRecord: null,
    }
  }

  if (normalizedObjectCode === 'Asset') {
    return {
      relatedCounts: await loadAssetRelatedCounts(normalizedRecordId),
      relatedRecord: null,
    }
  }

  if (normalizedObjectCode !== 'Maintenance') {
    return {
      relatedCounts: createEmptyDynamicDetailNavigationCounts(),
      relatedRecord: null,
    }
  }

  const assetId = extractDynamicDetailReferenceId(loadedRecord, ['asset', 'assetId', 'asset_id'])
  if (!assetId) {
    return {
      relatedCounts: createEmptyDynamicDetailNavigationCounts(),
      relatedRecord: null,
    }
  }

  try {
    return {
      relatedCounts: createEmptyDynamicDetailNavigationCounts(),
      relatedRecord: await loadAssetRecord(assetId),
    }
  } catch {
    return {
      relatedCounts: createEmptyDynamicDetailNavigationCounts(),
      relatedRecord: null,
    }
  }
}
