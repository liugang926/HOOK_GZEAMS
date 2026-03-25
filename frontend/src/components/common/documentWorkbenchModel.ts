import type { AggregateDocumentResponse, RuntimeAggregate } from '@/types/runtime'
import type { ClosedLoopNavigationItem } from '@/composables/useClosedLoopNavigation'
import type { ObjectWorkspaceInfoRow } from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'
import {
  readAggregateDocumentDetailRows,
  writeAggregateDocumentDetailRows,
} from '@/views/dynamic/workspace/aggregateDocument'
import {
  buildFieldKeyCandidates,
  resolveFieldValue,
  toDataKey,
} from '@/utils/fieldKey'

type TranslateFn = (key: string, params?: Record<string, unknown>) => string

export interface DocumentWorkbenchNavigationSection {
  title: string
  hint: string
  items: ClosedLoopNavigationItem[]
}

export interface DisposalBatchUpdateResult {
  modelValue: Record<string, any>
  changedRows: number
}

const hasOwn = (record: Record<string, any>, key: string) =>
  Object.prototype.hasOwnProperty.call(record, key)

const hasMeaningfulValue = (value: unknown) => {
  if (value === null || value === undefined) return false
  if (typeof value === 'string') return value.trim().length > 0
  return true
}

const toNumber = (value: unknown) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : 0
}

const readRowValue = (row: Record<string, any>, fieldCode: string) => {
  return resolveFieldValue(row, {
    fieldCode,
    includeWrappedData: false,
    includeCustomBags: false,
    treatEmptyAsMissing: false,
    returnEmptyMatch: true,
  })
}

const writeRowValue = (
  row: Record<string, any>,
  fieldCode: string,
  value: unknown,
) => {
  const candidates = buildFieldKeyCandidates(fieldCode)
  const preferredKey = candidates.find((key) => hasOwn(row, key)) || toDataKey(fieldCode)
  return {
    ...row,
    [preferredKey]: value,
  }
}

const updateDisposalRows = (
  modelValue: Record<string, any>,
  aggregate: RuntimeAggregate | null | undefined,
  updater: (row: Record<string, any>) => Record<string, any>,
): DisposalBatchUpdateResult => {
  const rows = readAggregateDocumentDetailRows(modelValue, aggregate)
  let changedRows = 0
  const nextRows = rows.map((row) => {
    const nextRow = updater(row)
    if (nextRow !== row) {
      changedRows += 1
    }
    return nextRow
  })

  return {
    modelValue: changedRows > 0
      ? writeAggregateDocumentDetailRows(modelValue, aggregate, nextRows)
      : { ...(modelValue || {}) },
    changedRows,
  }
}

export const summarizeAssetReceiptGeneration = (
  modelValue: Record<string, any>,
  aggregate: RuntimeAggregate | null | undefined,
) => {
  const rows = readAggregateDocumentDetailRows(modelValue, aggregate)
  const totalQualified = rows.reduce((total, row) => total + toNumber(readRowValue(row, 'qualified_quantity')), 0)
  const generatedItems = rows.filter((row) => Boolean(readRowValue(row, 'asset_generated'))).length
  const generatedAssets = rows.reduce((total, row) => {
    if (!readRowValue(row, 'asset_generated')) return total
    return total + toNumber(readRowValue(row, 'qualified_quantity'))
  }, 0)

  return {
    totalItems: rows.length,
    totalQualified,
    generatedItems,
    generatedAssets,
    pendingGeneration: Math.max(totalQualified - generatedAssets, 0),
  }
}

export const summarizeDisposalProgress = (
  modelValue: Record<string, any>,
  aggregate: RuntimeAggregate | null | undefined,
) => {
  const rows = readAggregateDocumentDetailRows(modelValue, aggregate)

  const appraisedItems = rows.filter((row) => (
    hasMeaningfulValue(readRowValue(row, 'appraisal_result')) ||
    hasMeaningfulValue(readRowValue(row, 'residual_value')) ||
    hasMeaningfulValue(readRowValue(row, 'appraised_by')) ||
    hasMeaningfulValue(readRowValue(row, 'appraised_at'))
  )).length

  const executedItems = rows.filter((row) => (
    Boolean(readRowValue(row, 'disposal_executed')) ||
    hasMeaningfulValue(readRowValue(row, 'actual_residual_value')) ||
    hasMeaningfulValue(readRowValue(row, 'buyer_info')) ||
    hasMeaningfulValue(readRowValue(row, 'executed_at'))
  )).length

  const pendingAppraisalResult = rows.filter((row) => !hasMeaningfulValue(readRowValue(row, 'appraisal_result'))).length
  const pendingResidualValue = rows.filter((row) => (
    !hasMeaningfulValue(readRowValue(row, 'residual_value')) &&
    hasMeaningfulValue(readRowValue(row, 'net_value'))
  )).length
  const pendingBuyerInfo = rows.filter((row) => !hasMeaningfulValue(readRowValue(row, 'buyer_info'))).length
  const pendingActualResidual = rows.filter((row) => (
    !hasMeaningfulValue(readRowValue(row, 'actual_residual_value')) &&
    hasMeaningfulValue(readRowValue(row, 'residual_value'))
  )).length

  return {
    totalItems: rows.length,
    appraisedItems,
    pendingAppraisal: Math.max(rows.length - appraisedItems, 0),
    executedItems,
    pendingExecution: Math.max(rows.length - executedItems, 0),
    pendingAppraisalResult,
    pendingResidualValue,
    pendingBuyerInfo,
    pendingActualResidual,
  }
}

const readMasterRelation = (
  master: Record<string, unknown> | null | undefined,
  fieldCode: string,
) => {
  if (!master || typeof master !== 'object') return null
  const value = resolveFieldValue(master, {
    fieldCode,
    includeWrappedData: false,
    includeCustomBags: false,
    treatEmptyAsMissing: false,
    returnEmptyMatch: true,
  })
  return value && typeof value === 'object' ? value as Record<string, any> : null
}

export const buildDocumentWorkbenchStageRows = ({
  objectCode,
  document,
  modelValue,
  t,
}: {
  objectCode: string
  document?: AggregateDocumentResponse | null
  modelValue: Record<string, any>
  t: TranslateFn
}): ObjectWorkspaceInfoRow[] => {
  const aggregate = document?.aggregate
  switch (String(objectCode || '').trim()) {
    case 'AssetReceipt': {
      const summary = summarizeAssetReceiptGeneration(modelValue, aggregate)
      return [
        { label: t('common.documentWorkbench.labels.totalItems'), value: summary.totalItems },
        { label: t('common.documentWorkbench.labels.totalQualified'), value: summary.totalQualified },
        { label: t('common.documentWorkbench.labels.generatedAssets'), value: summary.generatedAssets },
        { label: t('common.documentWorkbench.labels.pendingGeneration'), value: summary.pendingGeneration },
      ]
    }
    case 'DisposalRequest': {
      const summary = summarizeDisposalProgress(modelValue, aggregate)
      return [
        { label: t('common.documentWorkbench.labels.totalItems'), value: summary.totalItems },
        { label: t('common.documentWorkbench.labels.appraisedItems'), value: summary.appraisedItems },
        { label: t('common.documentWorkbench.labels.pendingAppraisal'), value: summary.pendingAppraisal },
        { label: t('common.documentWorkbench.labels.executedItems'), value: summary.executedItems },
        { label: t('common.documentWorkbench.labels.pendingExecution'), value: summary.pendingExecution },
      ]
    }
    default:
      return []
  }
}

export const buildDocumentWorkbenchNavigation = ({
  objectCode,
  document,
  modelValue,
  t,
}: {
  objectCode: string
  document?: AggregateDocumentResponse | null
  modelValue: Record<string, any>
  t: TranslateFn
}): DocumentWorkbenchNavigationSection | null => {
  if (!document) return null

  switch (String(objectCode || '').trim()) {
    case 'AssetReceipt': {
      const items: ClosedLoopNavigationItem[] = []
      const purchaseRequest = readMasterRelation(document.master, 'purchase_request')
      const receiptSummary = summarizeAssetReceiptGeneration(modelValue, document.aggregate)

      if (purchaseRequest?.id) {
        items.push({
          key: 'purchase-request',
          label: t('common.documentWorkbench.navigation.purchaseRequest'),
          type: 'primary',
          objectCode: 'PurchaseRequest',
          recordId: String(purchaseRequest.id),
        })
      }

      if (receiptSummary.generatedAssets > 0) {
        items.push({
          key: 'generated-assets',
          label: t('common.documentWorkbench.navigation.generatedAssets', {
            count: receiptSummary.generatedAssets,
          }),
          type: 'success',
          objectCode: 'Asset',
          query: { source_receipt: String(document.context.recordId || '') },
        })
      }

      if (items.length === 0) return null

      return {
        title: t('common.documentWorkbench.sections.relatedRecords'),
        hint: t('common.documentWorkbench.navigation.receiptHint'),
        items,
      }
    }
    case 'DisposalRequest': {
      const rows = readAggregateDocumentDetailRows(modelValue, document.aggregate)
      const seen = new Set<string>()
      const items: ClosedLoopNavigationItem[] = []

      for (const row of rows) {
        const assetId = String(readRowValue(row, 'asset') || '').trim()
        if (!assetId || seen.has(assetId)) continue
        seen.add(assetId)

        const assetCode = String(readRowValue(row, 'asset_code') || '').trim()
        const assetName = String(readRowValue(row, 'asset_name') || '').trim()
        items.push({
          key: `asset-${assetId}`,
          label: assetCode
            ? `${assetCode}${assetName ? ` - ${assetName}` : ''}`
            : assetName || assetId,
          type: 'primary',
          objectCode: 'Asset',
          recordId: assetId,
        })
      }

      if (items.length === 0) return null

      return {
        title: t('common.documentWorkbench.sections.relatedRecords'),
        hint: t('common.documentWorkbench.navigation.disposalHint'),
        items,
      }
    }
    default:
      return null
  }
}

export const applyDisposalBatchAppraisalResult = ({
  modelValue,
  aggregate,
  appraisalResult,
}: {
  modelValue: Record<string, any>
  aggregate: RuntimeAggregate | null | undefined
  appraisalResult: string
}): DisposalBatchUpdateResult => {
  const normalizedResult = String(appraisalResult || '').trim()
  if (!normalizedResult) {
    return { modelValue: { ...(modelValue || {}) }, changedRows: 0 }
  }

  return updateDisposalRows(modelValue, aggregate, (row) => {
    if (hasMeaningfulValue(readRowValue(row, 'appraisal_result'))) {
      return row
    }
    return writeRowValue(row, 'appraisal_result', normalizedResult)
  })
}

export const applyDisposalBatchBuyerInfo = ({
  modelValue,
  aggregate,
  buyerInfo,
}: {
  modelValue: Record<string, any>
  aggregate: RuntimeAggregate | null | undefined
  buyerInfo: string
}): DisposalBatchUpdateResult => {
  const normalizedBuyerInfo = String(buyerInfo || '').trim()
  if (!normalizedBuyerInfo) {
    return { modelValue: { ...(modelValue || {}) }, changedRows: 0 }
  }

  return updateDisposalRows(modelValue, aggregate, (row) => {
    if (hasMeaningfulValue(readRowValue(row, 'buyer_info'))) {
      return row
    }
    return writeRowValue(row, 'buyer_info', normalizedBuyerInfo)
  })
}

export const copyDisposalNetValueToResidual = ({
  modelValue,
  aggregate,
}: {
  modelValue: Record<string, any>
  aggregate: RuntimeAggregate | null | undefined
}): DisposalBatchUpdateResult => {
  return updateDisposalRows(modelValue, aggregate, (row) => {
    if (hasMeaningfulValue(readRowValue(row, 'residual_value'))) {
      return row
    }

    const netValue = readRowValue(row, 'net_value')
    if (!hasMeaningfulValue(netValue)) {
      return row
    }

    return writeRowValue(row, 'residual_value', netValue)
  })
}

export const copyDisposalResidualToActual = ({
  modelValue,
  aggregate,
}: {
  modelValue: Record<string, any>
  aggregate: RuntimeAggregate | null | undefined
}): DisposalBatchUpdateResult => {
  return updateDisposalRows(modelValue, aggregate, (row) => {
    if (hasMeaningfulValue(readRowValue(row, 'actual_residual_value'))) {
      return row
    }

    const residualValue = readRowValue(row, 'residual_value')
    if (!hasMeaningfulValue(residualValue)) {
      return row
    }

    return writeRowValue(row, 'actual_residual_value', residualValue)
  })
}
