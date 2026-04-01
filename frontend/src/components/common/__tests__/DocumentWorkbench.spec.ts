import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { defineComponent } from 'vue'
import DocumentWorkbench from '../DocumentWorkbench.vue'

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => ({
      locale: {
        value: 'en-US',
      },
      t: (key: string) => {
        const overrides: Record<string, string> = {
          'common.documentWorkbench.sections.actions': 'Actions',
          'common.documentWorkbench.sections.record': 'Record',
          'common.documentWorkbench.sections.workflow': 'Workflow',
          'common.documentWorkbench.sections.workflowProgress': 'Workflow Progress',
          'common.documentWorkbench.sections.stageInsights': 'Stage Insights',
          'common.documentWorkbench.sections.relatedRecords': 'Related Records',
          'common.documentWorkbench.sections.moreSummary': 'More Summary',
          'common.documentWorkbench.sections.audit': 'Audit',
          'common.documentWorkbench.sections.workflowActivity': 'Recent Workflow Activity',
          'common.documentWorkbench.sections.batchTools': 'Batch Tools',
          'common.documentWorkbench.sections.signalSummary': 'Signal Summary',
          'common.documentWorkbench.tabs.summary': 'Summary',
          'common.documentWorkbench.tabs.form': 'Form',
          'common.documentWorkbench.tabs.activity': 'Activity',
          'common.documentWorkbench.labels.capabilities': 'Capabilities',
          'common.documentWorkbench.labels.mode': 'Mode',
          'common.documentWorkbench.labels.status': 'Status',
          'common.documentWorkbench.labels.workflowStatus': 'Workflow Status',
          'common.documentWorkbench.labels.rows': 'Rows',
          'common.documentWorkbench.labels.editable': 'Editable',
          'common.documentWorkbench.labels.totalItems': 'Total Items',
          'common.documentWorkbench.labels.totalQualified': 'Qualified Quantity',
          'common.documentWorkbench.labels.generatedAssets': 'Generated Assets',
          'common.documentWorkbench.labels.pendingGeneration': 'Pending Generation',
          'common.documentWorkbench.labels.appraisedItems': 'Appraised Items',
          'common.documentWorkbench.labels.pendingAppraisal': 'Pending Appraisal',
          'common.documentWorkbench.labels.executedItems': 'Executed Items',
          'common.documentWorkbench.labels.pendingExecution': 'Pending Execution',
          'common.documentWorkbench.labels.definition': 'Definition',
          'common.documentWorkbench.labels.instance': 'Instance',
          'common.documentWorkbench.labels.published': 'Published',
          'common.documentWorkbench.labels.activityLogs': 'Activity Logs',
          'common.documentWorkbench.labels.workflowApprovals': 'Workflow Approvals',
          'common.documentWorkbench.labels.workflowOperationLogs': 'Workflow Operations',
          'common.documentWorkbench.labels.reasonSignals': 'Reason Signals',
          'common.documentWorkbench.labels.latestSignal': 'Latest Signal',
          'common.documentWorkbench.labels.signalSource': 'Signal Source',
          'common.documentWorkbench.labels.signalTime': 'Signal Time',
          'common.documentWorkbench.labels.workflowComment': 'Workflow Comment',
          'common.documentWorkbench.labels.workflowResult': 'Workflow Result',
          'common.documentWorkbench.labels.systemActor': 'System',
          'common.documentWorkbench.actions.openSource': 'Open Source',
          'common.documentWorkbench.actions.jumpToTimeline': 'Jump to Timeline',
          'common.documentWorkbench.navigation.purchaseRequest': 'View Purchase Request',
          'common.documentWorkbench.navigation.generatedAssets': 'View Generated Assets (1)',
          'common.documentWorkbench.navigation.receiptHint': 'Receipt hint',
          'common.documentWorkbench.navigation.disposalHint': 'Disposal hint',
          'common.documentWorkbench.batchTools.hint': 'Batch hint',
          'common.documentWorkbench.batchTools.actions.applyAppraisalResult': 'Apply Appraisal Result',
          'common.documentWorkbench.batchTools.actions.copyNetValueToResidual': 'Copy Net Value to Residual',
          'common.documentWorkbench.batchTools.actions.applyBuyerInfo': 'Apply Buyer Info',
          'common.documentWorkbench.batchTools.actions.copyResidualToActual': 'Copy Residual to Actual',
          'common.documentWorkbench.capabilities.editMaster': 'Edit Master',
          'common.documentWorkbench.capabilities.editDetails': 'Edit Details',
          'common.documentWorkbench.capabilities.save': 'Save',
          'common.documentWorkbench.capabilities.submit': 'Submit',
          'common.documentWorkbench.capabilities.approve': 'Approve',
          'common.documentWorkbench.capabilities.readOnly': 'Read Only',
          'common.documentWorkbench.sources.activity': 'Activity',
          'common.documentWorkbench.sources.workflowApproval': 'Workflow Approval',
          'common.documentWorkbench.sources.workflowOperation': 'Workflow Operation',
          'common.workbench.eyebrows.processSummary': 'Process Summary',
          'common.workbench.titles.processSummary': 'Process Summary',
          'common.workbench.messages.processSummaryHint': 'Compact process summary',
          'common.actions.edit': 'Edit',
          'common.actions.detail': 'Detail',
          'common.actions.create': 'Create',
          'common.yes': 'Yes',
          'common.no': 'No',
          'common.detailPage.auditInfo': 'Audit Info',
        }
        return overrides[key] || key
      },
    }),
  }
})

vi.mock('@/composables/useClosedLoopNavigation', () => ({
  useClosedLoopNavigation: () => ({
    handleClosedLoopNavigation: vi.fn(),
  }),
}))

const DynamicFormStub = defineComponent({
  name: 'DynamicFormStub',
  props: {
    readonly: {
      type: Boolean,
      default: false,
    },
    fieldPermissions: {
      type: Object,
      default: () => ({}),
    },
  },
  template: '<div class="dynamic-form-stub" />',
})

const StatusActionBarStub = defineComponent({
  name: 'StatusActionBarStub',
  props: {
    status: {
      type: String,
      default: '',
    },
    actions: {
      type: Array,
      default: () => [],
    },
  },
  emits: ['action-success'],
  template: '<button class="status-action-stub" @click="$emit(\'action-success\', \'submit\', { ok: true })">status</button>',
})

const ObjectActionBarStub = defineComponent({
  name: 'ObjectActionBarStub',
  props: {
    objectCode: {
      type: String,
      default: '',
    },
    recordId: {
      type: String,
      default: '',
    },
  },
  emits: ['action-success'],
  template: '<button class="object-action-stub" @click="$emit(\'action-success\', \'archive\', { ok: true })">object</button>',
})

const ClosedLoopNavigationCardStub = defineComponent({
  name: 'ClosedLoopNavigationCardStub',
  props: {
    title: {
      type: String,
      default: '',
    },
    hint: {
      type: String,
      default: '',
    },
    items: {
      type: Array,
      default: () => [],
    },
  },
  template: '<div class="closed-loop-navigation-stub">{{ title }} {{ hint }}</div>',
})

const ObjectWorkspaceInfoCardStub = defineComponent({
  name: 'ObjectWorkspaceInfoCard',
  props: {
    eyebrow: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      default: '',
    },
    rows: {
      type: Array,
      default: () => [],
    },
  },
  template: `
    <div class="info-card-stub">
      {{ eyebrow }}|{{ title }}|
      {{ Array.isArray(rows) ? rows.map((row) => \`\${row.label}:\${row.value}\`).join('||') : '' }}
    </div>
  `,
})

const ElTabsStub = defineComponent({
  name: 'ElTabsStub',
  props: {
    modelValue: {
      type: String,
      default: '',
    },
  },
  template: '<div class="el-tabs-stub" :data-model-value="modelValue"><slot /></div>',
})

const ElTabPaneStub = defineComponent({
  name: 'ElTabPaneStub',
  props: {
    label: {
      type: String,
      default: '',
    },
    name: {
      type: String,
      default: '',
    },
  },
  template: '<section class="el-tab-pane-stub" :data-label="label" :data-name="name"><slot /></section>',
})

const ElCollapseStub = defineComponent({
  name: 'ElCollapseStub',
  props: {
    modelValue: {
      type: Array,
      default: () => [],
    },
  },
  template: '<div class="el-collapse-stub"><slot /></div>',
})

const ElCollapseItemStub = defineComponent({
  name: 'ElCollapseItemStub',
  props: {
    name: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      default: '',
    },
  },
  template: '<section class="el-collapse-item-stub">{{ title }}<slot /></section>',
})

const setHash = (hash = '') => {
  window.history.replaceState({}, '', `${window.location.pathname}${hash}`)
}

const createReadonlyDocumentPayload = () => ({
  documentVersion: 1,
  context: {
    objectCode: 'AssetPickup',
    recordId: 'pickup-1',
    pageMode: 'readonly',
    recordLabel: 'PU-0001',
  },
  aggregate: {
    objectCode: 'AssetPickup',
    objectRole: 'root',
    isAggregateRoot: true,
    isDetailObject: false,
    detailRegions: [],
  },
  master: {
    status: 'pending',
  },
  details: {},
  capabilities: {
    canEditMaster: true,
    canEditDetails: true,
    canSave: true,
    canSubmit: true,
    canDelete: true,
    canApprove: false,
    readOnly: true,
  },
  workflow: {
    businessObjectCode: 'AssetPickup',
    hasPublishedDefinition: true,
    definition: {
      id: 'wf-1',
      code: 'pickup_wf',
      name: 'Pickup Workflow',
      status: 'published',
    },
    hasInstance: true,
    isActive: true,
    instance: {
      id: 'inst-1',
      title: 'Pickup Workflow Instance',
      status: 'pending',
    },
    timeline: [
      {
        id: 'wf-log-1',
        title: 'Approved',
        actorName: 'Admin',
        taskName: 'Department Approval',
        comment: 'Looks good',
        createdAt: '2026-03-16T08:00:00Z',
        source: 'workflowApproval',
        highlights: [
          {
            code: 'workflow_comment',
            label: 'Workflow Comment',
            value: 'Approved for dispatch',
            tone: 'info',
          },
        ],
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
      createdAt: '2026-03-16T08:02:00Z',
      objectCode: 'PurchaseRequest',
      objectId: 'pr-1',
      highlights: [
        {
          code: 'workflow_comment',
          label: 'Workflow Comment',
          value: 'Approved for dispatch',
          tone: 'info',
        },
      ],
    },
  ],
  audit: {
    counts: {
      activityLogs: 2,
      workflowApprovals: 1,
      workflowOperationLogs: 0,
    },
    activityLogs: [],
    workflowApprovals: [],
    workflowOperationLogs: [],
  },
})

beforeEach(() => {
  setHash('')
})

describe('DocumentWorkbench', () => {
  it('renders action header, capability tags, and re-emits child actions', async () => {
    const wrapper = mount(DocumentWorkbench, {
      props: {
        objectCode: 'AssetPickup',
        recordId: 'pickup-1',
        mode: 'readonly',
        modelValue: { status: 'pending' },
        statusActions: [
          {
            key: 'submit',
            label: 'Submit',
            apiCall: vi.fn(),
            visibleWhen: () => true,
          },
        ],
        document: createReadonlyDocumentPayload(),
      },
      global: {
        stubs: {
          DynamicForm: DynamicFormStub,
          ActivityTimeline: { template: '<div class="timeline-stub" />' },
          DocumentWorkflowProgress: { template: '<div class="workflow-progress-stub" />' },
          StatusActionBar: StatusActionBarStub,
          ObjectActionBar: ObjectActionBarStub,
          ClosedLoopNavigationCard: ClosedLoopNavigationCardStub,
          ObjectWorkspaceInfoCard: ObjectWorkspaceInfoCardStub,
          RouterLink: { template: '<a><slot /></a>', props: ['to'] },
          'el-button': { template: '<button><slot /></button>' },
          'el-card': { template: '<section><slot /></section>' },
          'el-tag': { template: '<span><slot /></span>' },
          'el-tabs': ElTabsStub,
          'el-tab-pane': ElTabPaneStub,
          'el-collapse': ElCollapseStub,
          'el-collapse-item': ElCollapseItemStub,
        },
      },
    })

    expect(wrapper.text()).toContain('Actions')
    expect(wrapper.text()).toContain('PU-0001')
    expect(wrapper.text()).toContain('Capabilities')
    expect(wrapper.get('.el-tabs-stub').attributes('data-model-value')).toBe('summary')
    expect(wrapper.text()).toContain('Edit Master')
    expect(wrapper.text()).toContain('Read Only')
    expect(wrapper.text()).toContain('Recent Workflow Activity')
    expect(wrapper.text()).toContain('Process Summary')
    expect(wrapper.text()).toContain('Workflow Progress')
    expect(wrapper.text()).toContain('Workflow Comment: Approved for dispatch')
    expect(wrapper.text()).toContain('Open Source')
    expect(wrapper.text()).toContain('Jump to Timeline')
    expect(wrapper.text()).toContain('Approved')
    expect(wrapper.text()).toContain('Admin')
    expect(wrapper.text()).toContain('Workflow Comment')
    expect(wrapper.text()).toContain('Approved for dispatch')
    expect(wrapper.find('.document-workbench__signal-banner').exists()).toBe(false)
    expect(wrapper.find('.process-summary-panel').exists()).toBe(true)

    await wrapper.get('.status-action-stub').trigger('click')
    await wrapper.get('.object-action-stub').trigger('click')

    expect(wrapper.emitted('action-success')).toEqual([
      ['submit', { ok: true }],
      ['archive', { ok: true }],
    ])
  })

  it('locks master fields while keeping detail region editable in detail-only edit mode', () => {
    const wrapper = mount(DocumentWorkbench, {
      props: {
        objectCode: 'DisposalRequest',
        recordId: 'disposal-1',
        mode: 'edit',
        modelValue: {
          disposalReason: 'Retire legacy asset',
          items: [{ id: 'line-1', residual_value: '100.00' }],
        },
        document: {
          documentVersion: 1,
          context: {
            objectCode: 'DisposalRequest',
            recordId: 'disposal-1',
            pageMode: 'edit',
            recordLabel: 'DSP-0001',
          },
          aggregate: {
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
          },
          master: {
            disposalReason: 'Retire legacy asset',
            requestDate: '2026-03-18',
          },
          details: {
            disposal_items: {
              relationCode: 'disposal_items',
              fieldCode: 'items',
              title: 'Items',
              targetObjectCode: 'DisposalItem',
              rows: [{ id: 'line-1', residual_value: '100.00' }],
              rowCount: 1,
              editable: true,
            },
          },
          capabilities: {
            canEditMaster: false,
            canEditDetails: true,
            canSave: true,
            canSubmit: false,
            canDelete: false,
            canApprove: true,
            readOnly: false,
          },
          workflow: {
            businessObjectCode: 'disposal_request',
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
        },
      },
      global: {
        stubs: {
          DynamicForm: DynamicFormStub,
          ActivityTimeline: { template: '<div class="timeline-stub" />' },
          DocumentWorkflowProgress: { template: '<div class="workflow-progress-stub" />' },
          StatusActionBar: StatusActionBarStub,
          ObjectActionBar: ObjectActionBarStub,
          ClosedLoopNavigationCard: ClosedLoopNavigationCardStub,
          ObjectWorkspaceInfoCard: ObjectWorkspaceInfoCardStub,
          RouterLink: { template: '<a><slot /></a>', props: ['to'] },
          'el-button': { template: '<button><slot /></button>' },
          'el-card': { template: '<section><slot /></section>' },
          'el-tag': { template: '<span><slot /></span>' },
          'el-tabs': ElTabsStub,
          'el-tab-pane': ElTabPaneStub,
          'el-collapse': ElCollapseStub,
          'el-collapse-item': ElCollapseItemStub,
        },
      },
    })

    const dynamicForm = wrapper.findComponent(DynamicFormStub)
    expect(wrapper.get('.el-tabs-stub').attributes('data-model-value')).toBe('form')
    expect(dynamicForm.props('readonly')).toBe(false)
    expect(dynamicForm.props('fieldPermissions')).toMatchObject({
      disposalReason: { readonly: true },
      requestDate: { readonly: true },
      items: { readonly: false },
      disposal_items: { readonly: false },
    })
  })

  it('switches to the activity surface when the timeline hash is present', () => {
    setHash('#document-workbench-timeline')

    const wrapper = mount(DocumentWorkbench, {
      props: {
        objectCode: 'AssetPickup',
        recordId: 'pickup-1',
        mode: 'readonly',
        modelValue: { status: 'pending' },
        document: createReadonlyDocumentPayload(),
      },
      global: {
        stubs: {
          DynamicForm: DynamicFormStub,
          ActivityTimeline: { template: '<div class="timeline-stub" />' },
          DocumentWorkflowProgress: { template: '<div class="workflow-progress-stub" />' },
          StatusActionBar: StatusActionBarStub,
          ObjectActionBar: ObjectActionBarStub,
          ClosedLoopNavigationCard: ClosedLoopNavigationCardStub,
          ObjectWorkspaceInfoCard: ObjectWorkspaceInfoCardStub,
          RouterLink: { template: '<a><slot /></a>', props: ['to'] },
          'el-button': { template: '<button><slot /></button>' },
          'el-card': { template: '<section><slot /></section>' },
          'el-tag': { template: '<span><slot /></span>' },
          'el-tabs': ElTabsStub,
          'el-tab-pane': ElTabPaneStub,
          'el-collapse': ElCollapseStub,
          'el-collapse-item': ElCollapseItemStub,
        },
      },
    })

    expect(wrapper.get('.el-tabs-stub').attributes('data-model-value')).toBe('activity')
  })

  it('moves admin-priority summary sections into the secondary collapsed area', () => {
    const wrapper = mount(DocumentWorkbench, {
      props: {
        objectCode: 'DisposalRequest',
        recordId: 'disposal-1',
        mode: 'edit',
        modelValue: {
          items: [
            {
              id: 'line-1',
              residualValue: '100.00',
              actualResidualValue: '',
              buyerInfo: '',
            },
          ],
        },
        document: {
          documentVersion: 1,
          context: {
            objectCode: 'DisposalRequest',
            recordId: 'disposal-1',
            pageMode: 'edit',
            recordLabel: 'DSP-0001',
          },
          aggregate: {
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
          },
          master: {
            status: 'executing',
          },
          details: {
            disposal_items: {
              relationCode: 'disposal_items',
              fieldCode: 'items',
              title: 'Items',
              targetObjectCode: 'DisposalItem',
              rows: [{ id: 'line-1', residual_value: '100.00' }],
              rowCount: 1,
              editable: true,
            },
          },
          capabilities: {
            canEditMaster: true,
            canEditDetails: true,
            canSave: true,
            canSubmit: false,
            canDelete: false,
            canApprove: true,
            readOnly: false,
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
              status: 'executing',
            },
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
        },
        workbench: {
          workspaceMode: 'extended',
          primaryEntryRoute: '/objects/DisposalRequest',
          legacyAliases: [],
          defaultPageMode: 'workspace',
          defaultDetailSurfaceTab: 'process',
          defaultDocumentSurfaceTab: 'summary',
          toolbar: { primaryActions: [], secondaryActions: [] },
          detailPanels: [],
          asyncIndicators: [],
          summaryCards: [],
          queuePanels: [],
          exceptionPanels: [],
          closurePanel: null,
          slaIndicators: [],
          recommendedActions: [],
          documentSummarySections: [
            { code: 'process_summary', surfacePriority: 'primary' },
            { code: 'record', surfacePriority: 'context' },
            { code: 'workflow', surfacePriority: 'context' },
            { code: 'batch_tools', surfacePriority: 'admin' },
          ],
        },
      },
      global: {
        stubs: {
          DynamicForm: DynamicFormStub,
          ActivityTimeline: { template: '<div class="timeline-stub" />' },
          StatusActionBar: StatusActionBarStub,
          ObjectActionBar: ObjectActionBarStub,
          ObjectWorkspaceInfoCard: ObjectWorkspaceInfoCardStub,
          RouterLink: { template: '<a><slot /></a>', props: ['to'] },
          'el-button': { template: '<button><slot /></button>' },
          'el-card': { template: '<section><slot /></section>' },
          'el-tag': { template: '<span><slot /></span>' },
          'el-tabs': ElTabsStub,
          'el-tab-pane': ElTabPaneStub,
          'el-collapse': ElCollapseStub,
          'el-collapse-item': ElCollapseItemStub,
        },
      },
    })

    expect(wrapper.get('.el-tabs-stub').attributes('data-model-value')).toBe('summary')
    expect(wrapper.find('.el-collapse-stub').exists()).toBe(true)
    expect(wrapper.text()).toContain('More Summary')
    expect(wrapper.text()).toContain('Batch Tools')
  })

  it('respects runtime workbench default document surface metadata', () => {
    const wrapper = mount(DocumentWorkbench, {
      props: {
        objectCode: 'AssetPickup',
        recordId: 'pickup-1',
        mode: 'readonly',
        modelValue: { status: 'pending' },
        document: createReadonlyDocumentPayload(),
        workbench: {
          workspaceMode: 'extended',
          primaryEntryRoute: '/objects/AssetPickup',
          legacyAliases: [],
          defaultPageMode: 'record',
          defaultDetailSurfaceTab: 'process',
          defaultDocumentSurfaceTab: 'activity',
          toolbar: { primaryActions: [], secondaryActions: [] },
          detailPanels: [],
          asyncIndicators: [],
          summaryCards: [],
          queuePanels: [],
          exceptionPanels: [],
          closurePanel: null,
          slaIndicators: [],
          recommendedActions: [],
        },
      },
      global: {
        stubs: {
          DynamicForm: DynamicFormStub,
          ActivityTimeline: { template: '<div class="timeline-stub" />' },
          DocumentWorkflowProgress: { template: '<div class="workflow-progress-stub" />' },
          StatusActionBar: StatusActionBarStub,
          ObjectActionBar: ObjectActionBarStub,
          ClosedLoopNavigationCard: ClosedLoopNavigationCardStub,
          ObjectWorkspaceInfoCard: ObjectWorkspaceInfoCardStub,
          RouterLink: { template: '<a><slot /></a>', props: ['to'] },
          'el-button': { template: '<button><slot /></button>' },
          'el-card': { template: '<section><slot /></section>' },
          'el-tag': { template: '<span><slot /></span>' },
          'el-tabs': ElTabsStub,
          'el-tab-pane': ElTabPaneStub,
          'el-collapse': ElCollapseStub,
          'el-collapse-item': ElCollapseItemStub,
        },
      },
    })

    expect(wrapper.get('.el-tabs-stub').attributes('data-model-value')).toBe('activity')
  })
})
