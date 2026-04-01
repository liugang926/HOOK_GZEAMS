import { describe, expect, it } from 'vitest'
import type { AggregateDocumentResponse, RuntimeAggregate } from '@/types/runtime'
import { resolveDocumentWorkflowProgress } from '@/platform/workflow/documentWorkflowProgress'
import { formatTimelineHighlightTimestamp } from '@/utils/timelineHighlights'
import {
  buildDocumentWorkbenchAuditRows,
  buildDocumentWorkbenchCapabilityItems,
  buildDocumentWorkbenchDisposalBatchActions,
  buildDocumentWorkbenchFieldPermissions,
  buildDocumentWorkbenchLatestSignalSummary,
  buildDocumentWorkbenchProcessSummaryRows,
  buildDocumentWorkbenchProcessSummaryStats,
  buildDocumentWorkbenchSignalRows,
  buildDocumentWorkbenchTimelineEntries,
  buildDocumentWorkbenchWorkflowActivityItems,
  shouldShowDocumentWorkbenchHeaderShell,
} from '../documentWorkbenchViewModel'

const t = (key: string) => {
  const overrides: Record<string, string> = {
    'common.documentWorkbench.batchTools.actions.applyAppraisalResult': 'Apply Appraisal Result',
    'common.documentWorkbench.batchTools.actions.copyNetValueToResidual': 'Copy Net Value to Residual',
    'common.documentWorkbench.batchTools.actions.applyBuyerInfo': 'Apply Buyer Info',
    'common.documentWorkbench.batchTools.actions.copyResidualToActual': 'Copy Residual To Actual',
    'common.documentWorkbench.capabilities.editMaster': 'Edit Master',
    'common.documentWorkbench.capabilities.editDetails': 'Edit Details',
    'common.documentWorkbench.capabilities.save': 'Save',
    'common.documentWorkbench.capabilities.submit': 'Submit',
    'common.documentWorkbench.capabilities.approve': 'Approve',
    'common.documentWorkbench.capabilities.readOnly': 'Read Only',
    'common.documentWorkbench.labels.reasonSignals': 'Reason Signals',
    'common.documentWorkbench.labels.latestSignal': 'Latest Signal',
    'common.documentWorkbench.labels.signalSource': 'Signal Source',
    'common.documentWorkbench.labels.signalTime': 'Signal Time',
    'common.documentWorkbench.labels.totalItems': 'Total Items',
    'common.documentWorkbench.labels.totalQualified': 'Qualified Quantity',
    'common.documentWorkbench.labels.generatedAssets': 'Generated Assets',
    'common.documentWorkbench.labels.pendingGeneration': 'Pending Generation',
    'common.documentWorkbench.labels.appraisedItems': 'Appraised Items',
    'common.documentWorkbench.labels.pendingAppraisal': 'Pending Appraisal',
    'common.documentWorkbench.labels.executedItems': 'Executed Items',
    'common.documentWorkbench.labels.pendingExecution': 'Pending Execution',
    'common.documentWorkbench.labels.workflowComment': 'Workflow Comment',
    'common.documentWorkbench.labels.workflowResult': 'Workflow Result',
    'common.documentWorkbench.labels.systemActor': 'System',
    'common.documentWorkbench.sections.workflowProgress': 'Workflow Progress',
    'common.documentWorkbench.actions.openSource': 'Open Source',
    'common.documentWorkbench.actions.jumpToTimeline': 'Jump to Timeline',
    'common.documentWorkbench.sources.activity': 'Activity',
    'common.documentWorkbench.sources.workflowApproval': 'Workflow Approval',
    'common.documentWorkbench.sources.workflowOperation': 'Workflow Operation',
    'assets.lifecycle.disposalRequest.status.draft': 'Draft',
    'assets.lifecycle.disposalRequest.status.submitted': 'Submitted',
    'assets.lifecycle.disposalRequest.status.appraising': 'Appraising',
    'assets.lifecycle.disposalRequest.status.approved': 'Approved',
    'assets.lifecycle.disposalRequest.status.executing': 'Executing',
    'assets.lifecycle.disposalRequest.status.completed': 'Completed',
    'common.yes': 'Yes',
    'common.no': 'No',
  }
  return overrides[key] || key
}

const disposalAggregate = {
  objectCode: 'DisposalRequest',
  objectRole: 'root',
  isAggregateRoot: true,
  isDetailObject: false,
  detailRegions: [
    {
      relationCode: 'disposal_items',
      fieldCode: 'items',
      title: 'Items',
      targetObjectCode: 'DisposalItem',
    },
  ],
} as RuntimeAggregate

const buildDocument = (
  objectCode: string,
  aggregate: RuntimeAggregate,
  overrides: Partial<AggregateDocumentResponse> = {},
): AggregateDocumentResponse => ({
  documentVersion: 1,
  context: {
    objectCode,
    recordId: `${objectCode}-1`,
    pageMode: 'edit',
    recordLabel: `${objectCode}-001`,
  },
  aggregate,
  master: {
    status: 'draft',
    request_date: '2026-03-19',
  },
  details: {
    disposal_items: {
      relationCode: 'disposal_items',
      fieldCode: 'items',
      title: 'Items',
      targetObjectCode: 'DisposalItem',
      rows: [],
      rowCount: 2,
      editable: true,
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
    businessObjectCode: objectCode,
    hasPublishedDefinition: true,
    definition: {
      id: 'wf-1',
      code: 'wf_1',
      name: 'Workflow',
      status: 'published',
    },
    hasInstance: true,
    isActive: true,
    instance: {
      id: 'inst-1',
      title: 'Instance 1',
      status: 'pending',
    },
    timeline: [],
  },
  timeline: [],
  audit: {
    counts: {
      activityLogs: 1,
      workflowApprovals: 2,
      workflowOperationLogs: 3,
    },
    activityLogs: [],
    workflowApprovals: [],
    workflowOperationLogs: [],
  },
  ...overrides,
})

describe('documentWorkbenchViewModel', () => {
  it('builds field permissions and header shell state for detail-only edit flows', () => {
    const document = buildDocument('DisposalRequest', disposalAggregate, {
      capabilities: {
        canEditMaster: false,
        canEditDetails: true,
        canSave: true,
        canSubmit: false,
        canDelete: false,
        canApprove: true,
        readOnly: false,
      },
      master: {
        status: 'appraising',
        request_date: '2026-03-19',
      },
    })

    expect(buildDocumentWorkbenchFieldPermissions({
      document,
      readonly: false,
    })).toMatchObject({
      request_date: { readonly: true },
      requestDate: { readonly: true },
      items: { readonly: false },
      disposal_items: { readonly: false },
    })

    const capabilityItems = buildDocumentWorkbenchCapabilityItems({ document, t })
    expect(capabilityItems).toHaveLength(6)
    expect(shouldShowDocumentWorkbenchHeaderShell({
      statusActionCount: 0,
      showObjectActions: false,
      effectiveRecordId: '',
      capabilityItems,
      hasLatestSignal: false,
    })).toBe(true)
  })

  it('derives disposal batch actions from lifecycle stage and pending detail counts', () => {
    const document = buildDocument('DisposalRequest', disposalAggregate, {
      master: {
        status: 'executing',
      },
    })

    const actions = buildDocumentWorkbenchDisposalBatchActions({
      objectCode: 'DisposalRequest',
      document,
      modelValue: {
        items: [
          {
            id: 'line-1',
            residualValue: '100.00',
            actualResidualValue: '',
            buyerInfo: '',
          },
          {
            id: 'line-2',
            residualValue: '80.00',
            actualResidualValue: '80.00',
            buyerInfo: 'Auction buyer',
          },
        ],
      },
      readonly: false,
      recordStatusLabel: 'executing',
      t,
    })

    expect(actions).toEqual([
      {
        key: 'applyBuyerInfo',
        label: 'Apply Buyer Info',
        type: 'primary',
        count: 1,
      },
      {
        key: 'copyResidualToActual',
        label: 'Copy Residual To Actual',
        type: 'success',
        count: 1,
      },
    ])
  })

  it('maps workflow activity and timeline entries into display-ready records', () => {
    const document = buildDocument('DisposalRequest', disposalAggregate, {
      master: {
        status: 'approved',
      },
      workflow: {
        businessObjectCode: 'DisposalRequest',
        hasPublishedDefinition: true,
        definition: {
          id: 'wf-1',
          code: 'wf_1',
          name: 'Workflow',
          status: 'published',
        },
        hasInstance: true,
        isActive: true,
        instance: {
          id: 'inst-1',
          title: 'Instance 1',
          status: 'pending',
        },
        timeline: [
          {
            id: 'wf-log-1',
            title: 'Approved',
            actorName: 'Admin',
            taskName: 'Dept Approval',
            comment: 'Looks good',
            createdAt: '2026-03-19T08:30:00Z',
            source: 'workflowApproval',
          },
        ],
      },
      timeline: [
        {
          id: 'timeline-1',
          source: 'workflowApproval',
          sourceLabel: 'Purchase Request',
          action: 'approve',
          actionDisplay: 'Approved',
          actorName: 'Admin',
          createdAt: '2026-03-19T08:35:00Z',
          objectCode: 'PurchaseRequest',
          objectId: 'pr-1',
          changes: [
            {
              fieldCode: 'status',
              fieldLabel: 'Status',
              oldValue: 'pending',
              newValue: 'approved',
            },
          ],
          highlights: [
            {
              code: 'workflow_comment',
              label: 'Workflow Comment',
              value: 'Looks good',
              tone: 'info',
            },
          ],
        },
      ],
    })
    const workflowProgress = resolveDocumentWorkflowProgress({
      objectCode: 'DisposalRequest',
      document,
      t,
    })
    const activityItems = buildDocumentWorkbenchWorkflowActivityItems({
      document,
      locale: 'en-US',
      t,
    })
    const expectedTime = formatTimelineHighlightTimestamp('2026-03-19T08:35:00Z', 'en-US')
    const latestSignalSummary = buildDocumentWorkbenchLatestSignalSummary({
      document,
      locale: 'en-US',
      t,
      objectCode: 'DisposalRequest',
      effectiveRecordId: 'disposal-1',
    })
    const signalRows = buildDocumentWorkbenchSignalRows({
      document,
      locale: 'en-US',
      t,
      objectCode: 'DisposalRequest',
      effectiveRecordId: 'disposal-1',
    })
    const auditRows = buildDocumentWorkbenchAuditRows({
      document,
      locale: 'en-US',
      t,
      objectCode: 'DisposalRequest',
      effectiveRecordId: 'disposal-1',
    })
    const processSummaryStats = buildDocumentWorkbenchProcessSummaryStats({
      objectCode: 'DisposalRequest',
      document,
      modelValue: {
        items: [
          {
            id: 'line-1',
            appraisalResult: 'scrap',
            residualValue: '120.00',
            disposalExecuted: true,
            actualResidualValue: '120.00',
            buyerInfo: 'Buyer A',
          },
          {
            id: 'line-2',
            appraisalResult: '',
            residualValue: '',
            disposalExecuted: false,
            actualResidualValue: '',
            buyerInfo: '',
          },
        ],
      },
      t,
    })
    const processSummaryRows = buildDocumentWorkbenchProcessSummaryRows({
      document,
      locale: 'en-US',
      t,
      objectCode: 'DisposalRequest',
      effectiveRecordId: 'disposal-1',
      workflowProgress,
    })
    expect(auditRows).toContainEqual({
      label: 'Reason Signals',
      value: 1,
    })
    expect(auditRows).toContainEqual({
      label: 'Latest Signal',
      value: 'Workflow Comment: Looks good',
      meta: `Purchase Request · ${expectedTime}`,
      actions: [
        { label: 'Open Source', to: '/objects/PurchaseRequest/pr-1' },
        { label: 'Jump to Timeline', to: { hash: '#document-workbench-timeline' } },
      ],
    })
    expect(latestSignalSummary).toEqual({
      label: 'Latest Signal',
      value: 'Workflow Comment: Looks good',
      meta: `Purchase Request · ${expectedTime}`,
      sourceValue: 'Purchase Request',
      timeValue: expectedTime,
      actions: [
        { label: 'Open Source', to: '/objects/PurchaseRequest/pr-1' },
        { label: 'Jump to Timeline', to: { hash: '#document-workbench-timeline' } },
      ],
      sourceActions: [{ label: 'Open Source', to: '/objects/PurchaseRequest/pr-1' }],
      timelineActions: [{ label: 'Jump to Timeline', to: { hash: '#document-workbench-timeline' } }],
    })
    expect(signalRows).toEqual([
      {
        label: 'Latest Signal',
        value: 'Workflow Comment: Looks good',
        meta: `Purchase Request · ${expectedTime}`,
        actions: [
          { label: 'Open Source', to: '/objects/PurchaseRequest/pr-1' },
          { label: 'Jump to Timeline', to: { hash: '#document-workbench-timeline' } },
        ],
      },
      {
        label: 'Signal Source',
        value: 'Purchase Request',
        actions: [{ label: 'Open Source', to: '/objects/PurchaseRequest/pr-1' }],
      },
      {
        label: 'Signal Time',
        value: expectedTime,
        actions: [{ label: 'Jump to Timeline', to: { hash: '#document-workbench-timeline' } }],
      },
    ])
    expect(processSummaryStats).toEqual([
      { label: 'Total Items', value: 2, tooltip: undefined, meta: undefined, actions: undefined },
      { label: 'Appraised Items', value: 1, tooltip: undefined, meta: undefined, actions: undefined },
      { label: 'Pending Appraisal', value: 1, tooltip: undefined, meta: undefined, actions: undefined },
      { label: 'Executed Items', value: 1, tooltip: undefined, meta: undefined, actions: undefined },
      { label: 'Pending Execution', value: 1, tooltip: undefined, meta: undefined, actions: undefined },
    ])
    expect(processSummaryRows).toContainEqual({
      label: 'Workflow Progress',
      value: 'Approved',
      meta: '4/6',
    })
    expect(processSummaryRows).toContainEqual({
      label: 'Latest Signal',
      value: 'Workflow Comment: Looks good',
      meta: `Purchase Request · ${expectedTime}`,
      actions: [
        { label: 'Open Source', to: '/objects/PurchaseRequest/pr-1' },
        { label: 'Jump to Timeline', to: { hash: '#document-workbench-timeline' } },
      ],
    })
    expect(activityItems).toHaveLength(1)
    expect(activityItems[0]).toMatchObject({
      title: 'Approved',
      meta: 'Admin | Dept Approval',
      description: 'Looks good',
      highlights: [
        {
          code: 'workflow_comment',
          label: 'Workflow Comment',
          value: 'Looks good',
          tone: 'info',
        },
      ],
    })

    const timelineEntries = buildDocumentWorkbenchTimelineEntries({
      objectCode: 'DisposalRequest',
      effectiveRecordId: 'disposal-1',
      document,
      sourceLabels: {
        activity: 'Activity',
        workflowApproval: 'Workflow Approval',
        workflowOperation: 'Workflow Operation',
      },
    })

    expect(timelineEntries).toEqual([
      expect.objectContaining({
        id: 'timeline-1',
        action: 'approve',
        actionLabel: 'Approved',
        objectCode: 'DisposalRequest',
        objectId: 'disposal-1',
        sourceLabel: 'Workflow Approval',
        userName: 'Admin',
      }),
    ])
    expect(timelineEntries[0].changes).toEqual([
      {
        fieldCode: 'status',
        fieldLabel: 'Status',
        oldValue: 'pending',
        newValue: 'approved',
      },
    ])
    expect(timelineEntries[0].highlights).toEqual([
      {
        code: 'workflow_comment',
        label: 'Workflow Comment',
        value: 'Looks good',
        tone: 'info',
      },
    ])
  })
})
