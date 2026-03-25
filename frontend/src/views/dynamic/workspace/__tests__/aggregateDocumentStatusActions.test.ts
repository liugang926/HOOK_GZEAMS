import { describe, expect, it } from 'vitest'
import type { AggregateDocumentResponse } from '@/types/runtime'
import { buildAggregateDocumentStatusActions } from '../aggregateDocumentStatusActions'

const t = (key: string) => key

const buildDocument = (
  objectCode: string,
  status: string,
  overrides: Partial<AggregateDocumentResponse['capabilities']> = {},
) => ({
  documentVersion: 1,
  context: {
    objectCode,
    recordId: `${objectCode}-1`,
    pageMode: 'readonly',
    recordLabel: `${objectCode}-001`,
  },
  aggregate: {
    objectCode,
    objectRole: 'root',
    isAggregateRoot: true,
    isDetailObject: false,
    detailRegions: [],
  },
  master: {
    status,
  },
  details: {},
  capabilities: {
    canEditMaster: true,
    canEditDetails: true,
    canSave: true,
    canSubmit: true,
    canDelete: true,
    canApprove: true,
    readOnly: false,
    ...overrides,
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
}) as AggregateDocumentResponse

const visibleActionKeys = (objectCode: string, status: string, overrides: Partial<AggregateDocumentResponse['capabilities']> = {}) => {
  const actions = buildAggregateDocumentStatusActions({
    objectCode,
    recordId: `${objectCode}-1`,
    document: buildDocument(objectCode, status, overrides),
    t,
  })

  return actions
    .filter(action => action.visibleWhen(status))
    .map(action => action.key)
}

describe('aggregateDocumentStatusActions', () => {
  it('maps pickup statuses to the expected action set', () => {
    expect(visibleActionKeys('AssetPickup', 'draft')).toEqual(['submit', 'cancel'])
    expect(visibleActionKeys('AssetPickup', 'pending')).toEqual(['approve', 'reject', 'cancel'])
    expect(visibleActionKeys('AssetPickup', 'approved')).toEqual(['complete'])
  })

  it('maps purchase request statuses to the expected action set', () => {
    expect(visibleActionKeys('PurchaseRequest', 'draft')).toEqual(['submit', 'cancel'])
    expect(visibleActionKeys('PurchaseRequest', 'submitted')).toEqual(['approve', 'reject', 'cancel'])
    expect(visibleActionKeys('PurchaseRequest', 'processing')).toEqual(['complete'])
  })

  it('maps transfer and loan statuses to the expected action set', () => {
    expect(visibleActionKeys('AssetTransfer', 'out_approved')).toEqual(['approveTo'])
    expect(visibleActionKeys('AssetTransfer', 'approved')).toEqual(['complete'])
    expect(visibleActionKeys('AssetLoan', 'borrowed')).toEqual(['confirmReturn'])
    expect(visibleActionKeys('AssetLoan', 'approved')).toEqual(['confirmBorrow'])
  })

  it('maps asset receipt statuses to the expected action set', () => {
    expect(visibleActionKeys('AssetReceipt', 'draft')).toEqual(['submitInspection', 'cancel'])
    expect(visibleActionKeys('AssetReceipt', 'rejected')).toEqual(['submitInspection', 'cancel'])
    expect(visibleActionKeys('AssetReceipt', 'inspecting')).toEqual(['passInspection', 'rejectInspection', 'cancel'])
    expect(visibleActionKeys('AssetReceipt', 'passed')).toEqual([])
  })

  it('maps disposal request statuses to the expected action set', () => {
    expect(visibleActionKeys('DisposalRequest', 'draft')).toEqual(['submit', 'cancel'])
    expect(visibleActionKeys('DisposalRequest', 'rejected')).toEqual(['submit', 'cancel'])
    expect(visibleActionKeys('DisposalRequest', 'submitted')).toEqual(['startAppraisal', 'reject', 'cancel'])
    expect(visibleActionKeys('DisposalRequest', 'appraising')).toEqual(['approve', 'reject', 'cancel'])
    expect(visibleActionKeys('DisposalRequest', 'approved')).toEqual(['startExecution', 'cancel'])
    expect(visibleActionKeys('DisposalRequest', 'executing')).toEqual(['complete', 'cancel'])
  })

  it('respects aggregate capabilities when building actions', () => {
    expect(visibleActionKeys('AssetPickup', 'draft', { canSubmit: false })).toEqual(['cancel'])
    expect(visibleActionKeys('AssetPickup', 'pending', { canApprove: false })).toEqual(['cancel'])
    expect(visibleActionKeys('AssetLoan', 'approved', { readOnly: true })).toEqual(['confirmBorrow'])
    expect(visibleActionKeys('PurchaseRequest', 'submitted', { canApprove: false })).toEqual(['cancel'])
    expect(visibleActionKeys('AssetReceipt', 'draft', { canSubmit: false })).toEqual(['cancel'])
    expect(visibleActionKeys('AssetReceipt', 'inspecting', { canApprove: false })).toEqual(['cancel'])
    expect(visibleActionKeys('DisposalRequest', 'submitted', { canApprove: false })).toEqual(['startAppraisal', 'cancel'])
  })

  it('uses return-specific actions for pending return documents', () => {
    expect(visibleActionKeys('AssetReturn', 'pending')).toEqual(['confirmReturn', 'reject'])
    expect(visibleActionKeys('Asset', 'draft')).toEqual([])
  })

  it('adds prompt metadata for rejection and loan return actions', () => {
    const pickupActions = buildAggregateDocumentStatusActions({
      objectCode: 'AssetPickup',
      recordId: 'AssetPickup-1',
      document: buildDocument('AssetPickup', 'pending'),
      t,
    })
    const loanActions = buildAggregateDocumentStatusActions({
      objectCode: 'AssetLoan',
      recordId: 'AssetLoan-1',
      document: buildDocument('AssetLoan', 'borrowed'),
      t,
    })

    const rejectAction = pickupActions.find(action => action.key === 'reject')
    const confirmReturnAction = loanActions.find(action => action.key === 'confirmReturn')
    const receiptActions = buildAggregateDocumentStatusActions({
      objectCode: 'AssetReceipt',
      recordId: 'AssetReceipt-1',
      document: buildDocument('AssetReceipt', 'inspecting'),
      t,
    })
    const disposalActions = buildAggregateDocumentStatusActions({
      objectCode: 'DisposalRequest',
      recordId: 'DisposalRequest-1',
      document: buildDocument('DisposalRequest', 'submitted'),
      t,
    })
    const rejectInspectionAction = receiptActions.find(action => action.key === 'rejectInspection')
    const startAppraisalAction = disposalActions.find(action => action.key === 'startAppraisal')

    expect(rejectAction?.prompt?.fields).toMatchObject([
      {
        key: 'reason',
        required: true,
      },
    ])
    expect(confirmReturnAction?.prompt?.fields).toMatchObject([
      {
        key: 'condition',
        type: 'select',
        required: true,
      },
      {
        key: 'comment',
        type: 'textarea',
      },
    ])
    expect(rejectInspectionAction?.prompt?.fields).toMatchObject([
      {
        key: 'result',
        required: true,
      },
    ])
    expect(startAppraisalAction?.confirmMessage).toBe('common.documentWorkbench.confirmations.startAppraisal')
  })
})
