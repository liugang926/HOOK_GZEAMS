import { describe, expect, it } from 'vitest'
import type { AggregateDocumentResponse, RuntimeAggregate } from '@/types/runtime'
import {
  buildDocumentWorkbenchCapabilityItems,
  buildDocumentWorkbenchDisposalBatchActions,
  buildDocumentWorkbenchFieldPermissions,
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
    'common.documentWorkbench.labels.systemActor': 'System',
    'common.documentWorkbench.sources.activity': 'Activity',
    'common.documentWorkbench.sources.workflowApproval': 'Workflow Approval',
    'common.documentWorkbench.sources.workflowOperation': 'Workflow Operation',
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
          },
        ],
      },
      timeline: [
        {
          id: 'timeline-1',
          source: 'workflowApproval',
          action: 'approve',
          actionDisplay: 'Approved',
          actorName: 'Admin',
          createdAt: '2026-03-19T08:35:00Z',
          changes: [
            {
              fieldCode: 'status',
              fieldLabel: 'Status',
              oldValue: 'pending',
              newValue: 'approved',
            },
          ],
        },
      ],
    })

    const activityItems = buildDocumentWorkbenchWorkflowActivityItems({
      document,
      locale: 'en-US',
      t,
    })
    expect(activityItems).toHaveLength(1)
    expect(activityItems[0]).toMatchObject({
      title: 'Approved',
      meta: 'Admin | Dept Approval',
      description: 'Looks good',
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
  })
})
