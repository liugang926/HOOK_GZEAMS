import type { ClosedLoopNavigationItem } from '@/composables/useClosedLoopNavigation'
import { hasLifecycleExtension } from '@/platform/lifecycle/lifecycleDetailExtensions'

type TranslateFn = (key: string, params?: Record<string, unknown>) => string

export type DynamicDetailNavigationCounts = Record<string, number>

export interface DynamicDetailNavigationSection {
  title: string
  hint: string
  items: ClosedLoopNavigationItem[]
}

export interface DynamicDetailTimelineConfig {
  objectCode: string
  recordId: string
  fetchUrl: string
}

const toRecordKey = (value: unknown) => String(value || '').trim()

const readRecordValue = (record: Record<string, any> | null | undefined, keys: string[]) => {
  for (const key of keys) {
    if (!key) continue
    const value = record?.[key]
    if (value !== undefined && value !== null && String(value).trim()) {
      return value
    }
  }
  return null
}

const toCount = (value: unknown) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : 0
}

const toReferenceId = (value: unknown) => {
  if (value && typeof value === 'object') {
    const candidate = value as Record<string, any>
    return toRecordKey(candidate.id || candidate.pk || candidate.value)
  }
  return toRecordKey(value)
}

const readReferenceId = (
  record: Record<string, any> | null | undefined,
  keys: string[],
) => {
  for (const key of keys) {
    if (!key) continue
    const value = toReferenceId(record?.[key])
    if (value) {
      return value
    }
  }
  return ''
}

const readReferenceLabel = (
  record: Record<string, any> | null | undefined,
  keys: string[],
) => {
  const labelCandidateKeys = ['label', 'display', 'displayName', 'name', 'title', 'assetCode', 'code']

  for (const key of keys) {
    if (!key) continue
    const value = record?.[key]
    if (typeof value === 'string' || typeof value === 'number') {
      const normalized = toRecordKey(value)
      if (normalized) {
        return normalized
      }
      continue
    }
    if (!value || typeof value !== 'object') {
      continue
    }

    for (const candidateKey of labelCandidateKeys) {
      const candidateValue = toRecordKey((value as Record<string, any>)[candidateKey])
      if (candidateValue) {
        return candidateValue
      }
    }
  }

  return ''
}

const buildAssetNavigationSection = ({
  record,
  recordId,
  counts,
  t,
}: {
  record?: Record<string, any> | null
  recordId: string
  counts?: DynamicDetailNavigationCounts | null
  t: TranslateFn
}): DynamicDetailNavigationSection => {
  const items: ClosedLoopNavigationItem[] = []
  const sourcePurchaseRequestId = toRecordKey(readRecordValue(record, [
    'sourcePurchaseRequest',
    'source_purchase_request',
  ]))
  const sourcePurchaseRequestNo = toRecordKey(readRecordValue(record, [
    'sourcePurchaseRequestNo',
    'source_purchase_request_no',
  ]))
  const sourceReceiptId = toRecordKey(readRecordValue(record, [
    'sourceReceipt',
    'source_receipt',
  ]))
  const sourceReceiptNo = toRecordKey(readRecordValue(record, [
    'sourceReceiptNo',
    'source_receipt_no',
  ]))

  if (sourcePurchaseRequestId) {
    items.push({
      key: 'source-purchase-request',
      objectCode: 'PurchaseRequest',
      recordId: sourcePurchaseRequestId,
      label: sourcePurchaseRequestNo
        ? t('common.detailNavigation.asset.purchaseRequestWithNo', { no: sourcePurchaseRequestNo })
        : t('common.detailNavigation.asset.purchaseRequest'),
      type: 'primary',
    })
  }

  if (sourceReceiptId) {
    items.push({
      key: 'source-receipt',
      objectCode: 'AssetReceipt',
      recordId: sourceReceiptId,
      label: sourceReceiptNo
        ? t('common.detailNavigation.asset.receiptWithNo', { no: sourceReceiptNo })
        : t('common.detailNavigation.asset.receipt'),
      type: 'success',
    })
  }

  items.push({
    key: 'maintenance-list',
    objectCode: 'Maintenance',
    query: { asset_id: recordId },
    label: t('common.detailNavigation.asset.maintenanceRecords', {
      count: toCount(counts?.maintenanceCount),
    }),
    type: 'warning',
  })

  items.push({
    key: 'disposal-list',
    objectCode: 'DisposalRequest',
    query: { asset_id: recordId },
    label: t('common.detailNavigation.asset.disposalRequests', {
      count: toCount(counts?.disposalCount),
    }),
    type: 'danger',
  })

  return {
    title: t('common.detailNavigation.sections.lifecycleLinks'),
    hint: t('common.detailNavigation.asset.hint'),
    items,
  }
}

const buildMaintenanceNavigationSection = ({
  record,
  relatedRecord,
  t,
}: {
  record?: Record<string, any> | null
  relatedRecord?: Record<string, any> | null
  t: TranslateFn
}): DynamicDetailNavigationSection | null => {
  const items: ClosedLoopNavigationItem[] = []
  const assetId = readReferenceId(record, ['asset', 'assetId', 'asset_id'])
  const assetLabel = toRecordKey(readRecordValue(record, [
    'assetDisplay',
    'asset_display',
    'assetCode',
    'asset_code',
  ])) || readReferenceLabel(record, ['asset'])
  const sourceReceiptId = toRecordKey(readRecordValue(relatedRecord, [
    'sourceReceipt',
    'source_receipt',
  ]))
  const sourceReceiptNo = toRecordKey(readRecordValue(relatedRecord, [
    'sourceReceiptNo',
    'source_receipt_no',
  ]))
  const sourcePurchaseRequestId = toRecordKey(readRecordValue(relatedRecord, [
    'sourcePurchaseRequest',
    'source_purchase_request',
  ]))
  const sourcePurchaseRequestNo = toRecordKey(readRecordValue(relatedRecord, [
    'sourcePurchaseRequestNo',
    'source_purchase_request_no',
  ]))

  if (assetId) {
    items.push({
      key: 'maintenance-asset',
      objectCode: 'Asset',
      recordId: assetId,
      label: assetLabel
        ? t('common.detailNavigation.maintenance.assetWithLabel', { label: assetLabel })
        : t('common.detailNavigation.maintenance.asset'),
      type: 'primary',
    })
  }

  if (sourceReceiptId) {
    items.push({
      key: 'maintenance-source-receipt',
      objectCode: 'AssetReceipt',
      recordId: sourceReceiptId,
      label: sourceReceiptNo
        ? t('common.detailNavigation.maintenance.receiptWithNo', { no: sourceReceiptNo })
        : t('common.detailNavigation.maintenance.receipt'),
      type: 'success',
    })
  }

  if (sourcePurchaseRequestId) {
    items.push({
      key: 'maintenance-source-purchase-request',
      objectCode: 'PurchaseRequest',
      recordId: sourcePurchaseRequestId,
      label: sourcePurchaseRequestNo
        ? t('common.detailNavigation.maintenance.purchaseRequestWithNo', { no: sourcePurchaseRequestNo })
        : t('common.detailNavigation.maintenance.purchaseRequest'),
      type: 'warning',
    })
  }

  if (items.length === 0) {
    return null
  }

  return {
    title: t('common.detailNavigation.sections.lifecycleLinks'),
    hint: t('common.detailNavigation.maintenance.hint'),
    items,
  }
}

export const buildDynamicDetailNavigationSection = ({
  objectCode,
  recordId,
  record,
  relatedRecord,
  counts,
  t,
}: {
  objectCode: string
  recordId: string
  record?: Record<string, any> | null
  relatedRecord?: Record<string, any> | null
  counts?: DynamicDetailNavigationCounts | null
  t: TranslateFn
}): DynamicDetailNavigationSection | null => {
  const normalizedObjectCode = toRecordKey(objectCode)
  const normalizedRecordId = toRecordKey(recordId)

  if (!normalizedRecordId) {
    return null
  }

  if (normalizedObjectCode === 'Asset') {
    return buildAssetNavigationSection({
      record,
      recordId: normalizedRecordId,
      counts,
      t,
    })
  }

  if (normalizedObjectCode === 'Maintenance') {
    return buildMaintenanceNavigationSection({
      record,
      relatedRecord,
      t,
    })
  }

  return null
}

export const buildDynamicDetailTimelineConfig = ({
  objectCode,
  recordId,
}: {
  objectCode: string
  recordId: string
}): DynamicDetailTimelineConfig | null => {
  const normalizedObjectCode = toRecordKey(objectCode)
  const normalizedRecordId = toRecordKey(recordId)

  if (!normalizedRecordId) {
    return null
  }

  if (normalizedObjectCode === 'Asset') {
    return {
      objectCode: normalizedObjectCode,
      recordId: normalizedRecordId,
      fetchUrl: `/assets/${encodeURIComponent(normalizedRecordId)}/lifecycle-timeline/`,
    }
  }

  if (normalizedObjectCode === 'PurchaseRequest') {
    return {
      objectCode: normalizedObjectCode,
      recordId: normalizedRecordId,
      fetchUrl: `/lifecycle/purchase-requests/${encodeURIComponent(normalizedRecordId)}/timeline/`,
    }
  }

  if (normalizedObjectCode === 'AssetReceipt') {
    return {
      objectCode: normalizedObjectCode,
      recordId: normalizedRecordId,
      fetchUrl: `/lifecycle/asset-receipts/${encodeURIComponent(normalizedRecordId)}/timeline/`,
    }
  }

  if (!hasLifecycleExtension(normalizedObjectCode)) {
    return null
  }

  return {
    objectCode: normalizedObjectCode,
    recordId: normalizedRecordId,
    fetchUrl: '',
  }
}
