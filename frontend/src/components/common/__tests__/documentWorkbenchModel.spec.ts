import { describe, expect, it } from 'vitest'
import type { AggregateDocumentResponse, RuntimeAggregate } from '@/types/runtime'
import {
  applyDisposalBatchAppraisalResult,
  applyDisposalBatchBuyerInfo,
  buildDocumentWorkbenchNavigation,
  buildDocumentWorkbenchStageRows,
  copyDisposalNetValueToResidual,
  copyDisposalResidualToActual,
  summarizeAssetReceiptGeneration,
  summarizeDisposalProgress,
} from '../documentWorkbenchModel'

const t = (key: string, params?: Record<string, unknown>) => {
  if (key === 'common.documentWorkbench.navigation.generatedAssets') {
    return `View Generated Assets (${params?.count ?? 0})`
  }
  return key
}

const receiptAggregate = {
  objectCode: 'AssetReceipt',
  objectRole: 'root',
  isAggregateRoot: true,
  isDetailObject: false,
  detailRegions: [
    {
      relationCode: 'receipt_items',
      fieldCode: 'items',
      title: 'Receipt Items',
      targetObjectCode: 'AssetReceiptItem',
    },
  ],
} as RuntimeAggregate

const disposalAggregate = {
  objectCode: 'DisposalRequest',
  objectRole: 'root',
  isAggregateRoot: true,
  isDetailObject: false,
  detailRegions: [
    {
      relationCode: 'disposal_items',
      fieldCode: 'items',
      title: 'Disposal Items',
      targetObjectCode: 'DisposalItem',
    },
  ],
} as RuntimeAggregate

const buildDocument = (
  objectCode: string,
  aggregate: RuntimeAggregate,
  master: Record<string, unknown>,
): AggregateDocumentResponse => ({
  documentVersion: 1,
  context: {
    objectCode,
    recordId: `${objectCode}-1`,
    pageMode: 'edit',
    recordLabel: `${objectCode}-001`,
  },
  aggregate,
  master,
  details: {},
  capabilities: {
    canEditMaster: true,
    canEditDetails: true,
    canSave: true,
    canSubmit: true,
    canDelete: true,
    canApprove: true,
    readOnly: false,
  },
  workflow: {
    businessObjectCode: objectCode,
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
})

describe('documentWorkbenchModel', () => {
  it('summarizes asset receipt generation progress and navigation', () => {
    const document = buildDocument('AssetReceipt', receiptAggregate, {
      status: 'passed',
      purchaseRequest: {
        id: 'pr-1',
      },
    })
    const modelValue = {
      items: [
        { id: 'r-1', qualifiedQuantity: 2, assetGenerated: true },
        { id: 'r-2', qualifiedQuantity: 1, assetGenerated: false },
      ],
    }

    expect(summarizeAssetReceiptGeneration(modelValue, receiptAggregate)).toMatchObject({
      totalItems: 2,
      totalQualified: 3,
      generatedAssets: 2,
      pendingGeneration: 1,
    })

    expect(buildDocumentWorkbenchStageRows({
      objectCode: 'AssetReceipt',
      document,
      modelValue,
      t,
    })).toMatchObject([
      { value: 2 },
      { value: 3 },
      { value: 2 },
      { value: 1 },
    ])

    expect(buildDocumentWorkbenchNavigation({
      objectCode: 'AssetReceipt',
      document,
      modelValue,
      t,
    })).toMatchObject({
      items: [
        {
          objectCode: 'PurchaseRequest',
          recordId: 'pr-1',
        },
        {
          objectCode: 'Asset',
          query: {
            source_receipt: 'AssetReceipt-1',
          },
        },
      ],
    })
  })

  it('summarizes disposal progress and supports batch updates while preserving key style', () => {
    const document = buildDocument('DisposalRequest', disposalAggregate, {
      status: 'executing',
    })
    const modelValue = {
      items: [
        {
          id: 'd-1',
          asset: 'asset-1',
          assetCode: 'FA-001',
          assetName: 'Monitor',
          netValue: '120.00',
          residualValue: '',
          appraisalResult: '',
          actualResidualValue: '',
          buyerInfo: '',
          disposalExecuted: false,
        },
        {
          id: 'd-2',
          asset: 'asset-2',
          assetCode: 'FA-002',
          assetName: 'Laptop',
          netValue: '180.00',
          residualValue: '80.00',
          appraisalResult: 'Reusable parts',
          actualResidualValue: '',
          buyerInfo: '',
          disposalExecuted: false,
        },
      ],
    }

    expect(summarizeDisposalProgress(modelValue, disposalAggregate)).toMatchObject({
      totalItems: 2,
      appraisedItems: 1,
      pendingAppraisal: 1,
      executedItems: 0,
      pendingExecution: 2,
      pendingAppraisalResult: 1,
      pendingResidualValue: 1,
      pendingBuyerInfo: 2,
      pendingActualResidual: 1,
    })

    const appraisalPatched = applyDisposalBatchAppraisalResult({
      modelValue,
      aggregate: disposalAggregate,
      appraisalResult: 'Batch appraisal',
    })
    expect(appraisalPatched.changedRows).toBe(1)
    expect(appraisalPatched.modelValue.items[0].appraisalResult).toBe('Batch appraisal')

    const residualPatched = copyDisposalNetValueToResidual({
      modelValue: appraisalPatched.modelValue,
      aggregate: disposalAggregate,
    })
    expect(residualPatched.changedRows).toBe(1)
    expect(residualPatched.modelValue.items[0].residualValue).toBe('120.00')

    const buyerPatched = applyDisposalBatchBuyerInfo({
      modelValue: residualPatched.modelValue,
      aggregate: disposalAggregate,
      buyerInfo: 'Auction buyer',
    })
    expect(buyerPatched.changedRows).toBe(2)
    expect(buyerPatched.modelValue.items[1].buyerInfo).toBe('Auction buyer')

    const actualPatched = copyDisposalResidualToActual({
      modelValue: buyerPatched.modelValue,
      aggregate: disposalAggregate,
    })
    expect(actualPatched.changedRows).toBe(2)
    expect(actualPatched.modelValue.items[0].actualResidualValue).toBe('120.00')
    expect(actualPatched.modelValue.items[1].actualResidualValue).toBe('80.00')

    expect(buildDocumentWorkbenchNavigation({
      objectCode: 'DisposalRequest',
      document,
      modelValue,
      t,
    })).toMatchObject({
      items: [
        {
          objectCode: 'Asset',
          recordId: 'asset-1',
        },
        {
          objectCode: 'Asset',
          recordId: 'asset-2',
        },
      ],
    })
  })
})
