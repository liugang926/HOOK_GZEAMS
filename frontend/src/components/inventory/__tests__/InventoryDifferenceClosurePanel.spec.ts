import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'

import request from '@/utils/request'
import { ElMessage } from 'element-plus'
import InventoryDifferenceClosurePanel from '../InventoryDifferenceClosurePanel.vue'

const { pushMock } = vi.hoisted(() => ({
  pushMock: vi.fn(),
}))

vi.mock('@/utils/request', () => ({
  default: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: pushMock,
  }),
}))

vi.mock('element-plus', async (importOriginal) => {
  const actual = await importOriginal<typeof import('element-plus')>()
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
    },
  }
})

vi.mock('vue-i18n', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-i18n')>()
  return {
    ...actual,
    useI18n: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          'common.actions.refresh': 'Refresh',
          'common.messages.operationSuccess': 'Operation succeeded',
          'common.messages.operationFailed': 'Operation failed',
          'inventory.workbench.actions.submitReview': 'Submit Review',
          'inventory.workbench.actions.executeResolution': 'Execute Resolution',
          'inventory.workbench.actions.closeDifference': 'Close Difference',
          'inventory.workbench.actions.saveDraft': 'Save Draft',
          'inventory.workbench.actions.sendFollowUp': 'Send Follow-up',
          'inventory.workbench.actions.completeFollowUp': 'Complete Follow-up',
          'inventory.workbench.actions.reopenFollowUp': 'Reopen Follow-up',
          'inventory.workbench.messages.differenceClosureHint': 'Difference closure hint',
          'inventory.workbench.messages.pendingConfirmHint': 'Pending confirm hint',
          'inventory.workbench.messages.savedDraftHint': 'Draft already saved',
          'inventory.workbench.messages.unsavedDraftHint': 'Draft has unsaved changes',
          'inventory.workbench.panels.differenceClosure': 'Difference Closure',
          'inventory.workbench.execution.title': 'Linked Action Result',
          'inventory.workbench.execution.action': 'Linked Action',
          'inventory.workbench.execution.followUpOwner': 'Follow-up Owner',
          'inventory.workbench.execution.followUpTask': 'Follow-up Task',
          'inventory.workbench.execution.followUpTaskStatus': 'Follow-up Status',
          'inventory.workbench.execution.followUpCompletedAt': 'Follow-up Completed At',
          'inventory.workbench.execution.followUpCount': 'Follow-up Count',
          'inventory.workbench.execution.notification': 'Notification',
          'inventory.workbench.execution.openFollowUpTask': 'Open Follow-up Task',
          'inventory.workbench.execution.openNotificationCenter': 'Open Notification Center',
          'inventory.workbench.execution.targetRecord': 'Generated Record',
          'inventory.workbench.execution.executedAt': 'Executed At',
          'inventory.workbench.execution.states.pending': 'Pending',
          'inventory.workbench.execution.states.completed': 'Completed',
          'inventory.workbench.execution.states.cancelled': 'Cancelled',
          'inventory.workbench.execution.states.executed': 'Executed',
          'inventory.workbench.execution.states.manualFollowUp': 'Manual Follow-up',
          'inventory.workbench.summary.differenceType': 'Difference Type',
          'inventory.workbench.summary.taskCode': 'Task Code',
          'inventory.workbench.states.draftSaved': 'Draft Saved',
          'inventory.workbench.states.unsavedChanges': 'Unsaved Changes',
          'common.workbench.labels.owner': 'Owner',
          'inventory.workbench.form.resolution': 'Resolution',
          'inventory.workbench.form.closureType': 'Closure Type',
          'inventory.workbench.form.linkedActionCode': 'Linked Action Code',
          'inventory.workbench.form.evidenceRefs': 'Evidence References',
          'inventory.workbench.form.closureNotes': 'Closure Notes',
          'inventory.workbench.form.syncAsset': 'Sync Asset',
          'inventory.workbench.linkedActions.locationCorrection': 'Apply Location Correction',
          'inventory.workbench.linkedActions.custodianCorrection': 'Apply Custodian Correction',
          'inventory.workbench.linkedActions.createMaintenance': 'Create Maintenance Record',
          'inventory.workbench.linkedActions.createDisposal': 'Create Disposal Request',
          'inventory.workbench.linkedActions.createAssetCard': 'Create Asset Card',
          'inventory.workbench.linkedActions.financialAdjustment': 'Create Financial Adjustment',
          'inventory.workbench.linkedActions.invalidDifference': 'Mark Invalid Difference',
          'inventory.workbench.linkedActions.currentValue': 'Current Value: {code}',
          'inventory.workbench.placeholders.resolution': 'Enter resolution',
          'inventory.workbench.placeholders.closureType': 'Choose closure type',
          'inventory.workbench.placeholders.linkedActionCode': 'Enter linked action code',
          'inventory.workbench.placeholders.evidenceRefs': 'Enter evidence refs',
          'inventory.workbench.placeholders.closureNotes': 'Enter closure notes',
          'inventory.workbench.validation.resolutionRequired': 'Resolution required',
          'inventory.workbench.validation.closureTypeRequired': 'Closure type required',
          'inventory.workbench.closureTypes.locationCorrection': 'Location Correction',
          'inventory.workbench.closureTypes.custodianCorrection': 'Custodian Correction',
          'inventory.workbench.closureTypes.repair': 'Repair',
          'inventory.workbench.closureTypes.disposal': 'Disposal',
          'inventory.workbench.closureTypes.createAssetCard': 'Create Asset Card',
          'inventory.workbench.closureTypes.financialAdjustment': 'Financial Adjustment',
          'inventory.workbench.closureTypes.invalidDifference': 'Invalid Difference',
        }
        return translations[key] || key
      },
      te: () => true,
    }),
  }
})

const ElCardStub = defineComponent({
  name: 'ElCardStub',
  template: '<div class="el-card-stub"><slot name="header" /><slot /></div>',
})

const ElButtonStub = defineComponent({
  name: 'ElButtonStub',
  props: {
    type: {
      type: String,
      default: 'default',
    },
    loading: Boolean,
    disabled: Boolean,
  },
  emits: ['click'],
  template: '<button :data-type="type" :disabled="loading || disabled" @click="$emit(\'click\')"><slot /></button>',
})

const ElTagStub = defineComponent({
  name: 'ElTagStub',
  template: '<span class="el-tag-stub"><slot /></span>',
})

const ElAlertStub = defineComponent({
  name: 'ElAlertStub',
  props: {
    title: {
      type: String,
      default: '',
    },
  },
  template: '<div class="el-alert-stub">{{ title }}</div>',
})

const ElInputStub = defineComponent({
  name: 'ElInputStub',
  props: {
    modelValue: {
      type: String,
      default: '',
    },
    type: {
      type: String,
      default: 'text',
    },
    placeholder: {
      type: String,
      default: '',
    },
  },
  emits: ['update:modelValue'],
  template: `
    <textarea
      v-if="type === 'textarea'"
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <input
      v-else
      :value="modelValue"
      :placeholder="placeholder"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  `,
})

const ElSelectStub = defineComponent({
  name: 'ElSelectStub',
  props: {
    modelValue: {
      type: String,
      default: '',
    },
  },
  emits: ['update:modelValue'],
  template: `
    <select
      :value="modelValue"
      @change="$emit('update:modelValue', $event.target.value)"
    >
      <slot />
    </select>
  `,
})

const ElOptionStub = defineComponent({
  name: 'ElOptionStub',
  props: {
    label: {
      type: String,
      default: '',
    },
    value: {
      type: String,
      default: '',
    },
  },
  template: '<option :value="value">{{ label }}</option>',
})

const ElSwitchStub = defineComponent({
  name: 'ElSwitchStub',
  props: {
    modelValue: Boolean,
  },
  emits: ['update:modelValue'],
  template: `
    <input
      type="checkbox"
      :checked="modelValue"
      @change="$emit('update:modelValue', $event.target.checked)"
    />
  `,
})

describe('InventoryDifferenceClosurePanel', () => {
  beforeEach(() => {
    vi.mocked(request).mockReset()
    vi.mocked(ElMessage.success).mockReset()
    vi.mocked(ElMessage.error).mockReset()
    vi.mocked(ElMessage.warning).mockReset()
    pushMock.mockReset()
  })

  const mountPanel = (recordData: Record<string, unknown>) => {
    return mount(InventoryDifferenceClosurePanel, {
      props: {
        panel: {
          code: 'inventory_difference_closure_panel',
          title: 'Difference Closure',
          props: {
            linked_action_options: [
              {
                code: 'location_correction',
                label_key: 'inventory.workbench.linkedActions.locationCorrection',
                closure_types: ['location_correction'],
              },
              {
                code: 'custodian_correction',
                label_key: 'inventory.workbench.linkedActions.custodianCorrection',
                closure_types: ['custodian_correction'],
              },
              {
                code: 'asset.create_maintenance',
                label_key: 'inventory.workbench.linkedActions.createMaintenance',
                closure_types: ['repair'],
              },
              {
                code: 'asset.create_disposal',
                label_key: 'inventory.workbench.linkedActions.createDisposal',
                closure_types: ['disposal'],
              },
              {
                code: 'create_asset_card',
                label_key: 'inventory.workbench.linkedActions.createAssetCard',
                closure_types: ['create_asset_card'],
              },
              {
                code: 'finance_adjustment',
                label_key: 'inventory.workbench.linkedActions.financialAdjustment',
                closure_types: ['financial_adjustment'],
              },
              {
                code: 'invalid_difference',
                label_key: 'inventory.workbench.linkedActions.invalidDifference',
                closure_types: ['invalid_difference'],
              },
            ],
          },
        },
        objectCode: 'InventoryItem',
        recordId: 'diff-1',
        recordData,
      },
      global: {
        stubs: {
          'el-card': ElCardStub,
          'el-button': ElButtonStub,
          'el-tag': ElTagStub,
          'el-alert': ElAlertStub,
          'el-input': ElInputStub,
          'el-select': ElSelectStub,
          'el-option': ElOptionStub,
          'el-switch': ElSwitchStub,
        },
      },
    })
  }

  it('submits review payload with resolution, closure type, and evidence refs', async () => {
    vi.mocked(request).mockResolvedValue({
      success: true,
      message: 'Submitted successfully',
      data: {},
    })

    const wrapper = mountPanel({
      status: 'confirmed',
      status_label: 'Confirmed',
      difference_type_label: 'Missing',
      task_code: 'INV-001',
      resolution: '',
      closure_type: '',
      evidence_refs: [],
      closure_notes: '',
    })

    const textareas = wrapper.findAll('textarea')
    await textareas[0].setValue('Asset confirmed missing after recount')
    const selects = wrapper.findAll('select')
    await selects[0].setValue('financial_adjustment')
    await selects[1].setValue('finance_adjustment')
    await textareas[1].setValue('file-1\nfile-2')

    const submitButton = wrapper.findAll('button').find((button) => button.text() === 'Submit Review')
    expect(submitButton).toBeDefined()

    await submitButton!.trigger('click')
    await flushPromises()

    expect(request).toHaveBeenCalledWith(expect.objectContaining({
      url: '/system/objects/InventoryItem/diff-1/submit-review/',
      method: 'post',
      data: {
        resolution: 'Asset confirmed missing after recount',
        closureType: 'financial_adjustment',
        linkedActionCode: 'finance_adjustment',
        evidenceRefs: ['file-1', 'file-2'],
      },
      unwrap: 'none',
    }))
    expect(ElMessage.success).toHaveBeenCalledWith('Submitted successfully')
    expect(wrapper.emitted('workbench-refresh-requested')).toEqual([[{ detail: true }]])
  })

  it('saves draft payload without changing the workflow action', async () => {
    vi.mocked(request).mockResolvedValue({
      success: true,
      message: 'Draft saved successfully',
      data: {},
    })

    const wrapper = mountPanel({
      status: 'confirmed',
      status_label: 'Confirmed',
      difference_type_label: 'Missing',
      task_code: 'INV-003',
      resolution: 'Initial handling note',
      closure_type: 'financial_adjustment',
      linked_action_code: '',
      evidence_refs: ['draft-1'],
      closure_notes: 'Pending approver assignment',
    })

    const textareas = wrapper.findAll('textarea')
    await textareas[0].setValue('Updated handling draft')
    const selects = wrapper.findAll('select')
    await selects[0].setValue('repair')
    await selects[1].setValue('asset.create_maintenance')
    await textareas[1].setValue('draft-1\ndraft-2')
    await textareas[2].setValue('Waiting for maintenance lead review')

    const saveDraftButton = wrapper.findAll('button').find((button) => button.text() === 'Save Draft')
    expect(saveDraftButton).toBeDefined()

    await saveDraftButton!.trigger('click')
    await flushPromises()

    expect(request).toHaveBeenCalledWith(expect.objectContaining({
      url: '/system/objects/InventoryItem/diff-1/save-draft/',
      method: 'post',
      data: {
        resolution: 'Updated handling draft',
        closureType: 'repair',
        linkedActionCode: 'asset.create_maintenance',
        evidenceRefs: ['draft-1', 'draft-2'],
        closureNotes: 'Waiting for maintenance lead review',
      },
      unwrap: 'none',
    }))
    expect(ElMessage.success).toHaveBeenCalledWith('Draft saved successfully')
  })

  it('tracks dirty draft state and disables save when nothing changed', async () => {
    vi.mocked(request).mockResolvedValue({
      success: true,
      message: 'Draft saved successfully',
      data: {},
    })

    const wrapper = mountPanel({
      status: 'confirmed',
      status_label: 'Confirmed',
      difference_type_label: 'Missing',
      task_code: 'INV-004',
      resolution: 'Saved note',
      closure_type: 'financial_adjustment',
      linked_action_code: 'finance_adjustment',
      evidence_refs: ['draft-1'],
      closure_notes: 'Saved closure note',
    })

    expect(wrapper.text()).toContain('Draft Saved')
    let saveDraftButton = wrapper.findAll('button').find((button) => button.text() === 'Save Draft')
    expect(saveDraftButton?.attributes('disabled')).toBeDefined()

    const textareas = wrapper.findAll('textarea')
    await textareas[0].setValue('Saved note updated')
    await flushPromises()

    expect(wrapper.text()).toContain('Unsaved Changes')
    saveDraftButton = wrapper.findAll('button').find((button) => button.text() === 'Save Draft')
    expect(saveDraftButton?.attributes('disabled')).toBeUndefined()

    await saveDraftButton!.trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Draft Saved')
    saveDraftButton = wrapper.findAll('button').find((button) => button.text() === 'Save Draft')
    expect(saveDraftButton?.attributes('disabled')).toBeDefined()
  })

  it('keeps legacy linked action values selectable when they are not in the configured catalog', async () => {
    const wrapper = mountPanel({
      status: 'approved',
      status_label: 'Approved',
      difference_type_label: 'Location Mismatch',
      task_code: 'INV-005',
      resolution: 'Legacy action retained',
      closure_type: 'location_correction',
      linked_action_code: 'transfer',
      evidence_refs: [],
      closure_notes: '',
    })

    const options = wrapper.findAll('option').map((option) => option.text())
    expect(options).toContain('Current Value: {code}')
  })

  it('executes approved resolution with syncAsset flag', async () => {
    vi.mocked(request).mockResolvedValue({
      success: true,
      message: 'Executed successfully',
      data: {},
    })

    const wrapper = mountPanel({
      status: 'approved',
      status_label: 'Approved',
      difference_type_label: 'Location Mismatch',
      task_code: 'INV-002',
      resolution: 'Move asset to scanned location',
      closure_type: 'location_correction',
      linked_action_code: 'transfer',
      evidence_refs: ['photo-1'],
      closure_notes: '',
    })

    const checkbox = wrapper.find('input[type="checkbox"]')
    expect(checkbox.exists()).toBe(true)

    const executeButton = wrapper.findAll('button').find((button) => button.text() === 'Execute Resolution')
    expect(executeButton).toBeDefined()

    await executeButton!.trigger('click')
    await flushPromises()

    expect(request).toHaveBeenCalledWith(expect.objectContaining({
      url: '/system/objects/InventoryItem/diff-1/execute-resolution/',
      method: 'post',
      data: {
        resolution: 'Move asset to scanned location',
        syncAsset: true,
        linkedActionCode: 'transfer',
      },
      unwrap: 'none',
    }))
  })

  it('renders linked action execution details and navigates to the generated record', async () => {
    const wrapper = mountPanel({
      status: 'resolved',
      status_label: 'Resolved',
      difference_type_label: 'Damaged',
      task_code: 'INV-006',
      resolution: 'Maintenance request created',
      closure_type: 'repair',
      linked_action_code: 'asset.create_maintenance',
      evidence_refs: ['photo-1'],
      closure_notes: '',
      custom_fields: {
        linked_action_execution: {
          action_code: 'asset.create_maintenance',
          status: 'executed',
          target_object_code: 'Maintenance',
          target_id: 'maint-1',
          target_url: '/objects/Maintenance/maint-1',
          message: 'Maintenance request created successfully.',
          executed_at: '2026-03-26T12:00:00Z',
        },
      },
    })

    expect(wrapper.text()).toContain('Linked Action Result')
    expect(wrapper.text()).toContain('Executed')
    expect(wrapper.text()).toContain('Create Maintenance Record')
    expect(wrapper.text()).toContain('Maintenance / maint-1')
    expect(wrapper.text()).toContain('Maintenance request created successfully.')

    const viewButton = wrapper.find('.inventory-difference-panel__execution-link')
    expect(viewButton.exists()).toBe(true)

    await viewButton.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/objects/Maintenance/maint-1')
  })

  it('renders manual follow-up execution without a navigation button', () => {
    const wrapper = mountPanel({
      status: 'resolved',
      status_label: 'Resolved',
      difference_type_label: 'Missing',
      task_code: 'INV-007',
      resolution: 'Finance follow-up required',
      closure_type: 'financial_adjustment',
      linked_action_code: 'finance_adjustment',
      evidence_refs: [],
      closure_notes: '',
      custom_fields: {
        linked_action_execution: {
          action_code: 'finance_adjustment',
          status: 'manual_follow_up',
          message: 'Manual finance adjustment follow-up is required.',
          can_send_follow_up: false,
        },
      },
    })

    expect(wrapper.text()).toContain('Manual Follow-up')
    expect(wrapper.text()).toContain('Create Financial Adjustment')
    expect(wrapper.text()).toContain('Manual finance adjustment follow-up is required.')
    expect(wrapper.find('.inventory-difference-panel__execution-link').exists()).toBe(false)
  })

  it('shows follow-up notification metadata and opens the notification center', async () => {
    const wrapper = mountPanel({
      status: 'resolved',
      status_label: 'Resolved',
      difference_type_label: 'Missing',
      task_code: 'INV-008',
      resolution: 'Finance follow-up required',
      closure_type: 'financial_adjustment',
      linked_action_code: 'finance_adjustment',
      evidence_refs: [],
      closure_notes: '',
      custom_fields: {
        linked_action_execution: {
          action_code: 'finance_adjustment',
          status: 'manual_follow_up',
          message: 'Follow-up assigned to inventory-owner.',
          can_send_follow_up: true,
          follow_up_assignee_name: 'inventory-owner',
          follow_up_task_code: 'IFU2026030001',
          follow_up_task_status: 'pending',
          follow_up_task_url: '/objects/InventoryFollowUp/follow-up-1',
          follow_up_notification_id: 'notif-1',
          follow_up_notification_url: '/notifications/center',
          follow_up_sent_count: 1,
        },
      },
    })

    expect(wrapper.text()).toContain('Follow-up Owner')
    expect(wrapper.text()).toContain('inventory-owner')
    expect(wrapper.text()).toContain('Follow-up Task')
    expect(wrapper.text()).toContain('IFU2026030001')
    expect(wrapper.text()).toContain('Follow-up Status')
    expect(wrapper.text()).toContain('Pending')
    expect(wrapper.text()).toContain('Follow-up Count')
    expect(wrapper.text()).toContain('Notification')
    expect(wrapper.text()).toContain('notif-1')

    const taskButton = wrapper.find('.inventory-difference-panel__follow-up-task-button')
    expect(taskButton.exists()).toBe(true)

    await taskButton.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/objects/InventoryFollowUp/follow-up-1')

    const openButton = wrapper.find('.inventory-difference-panel__follow-up-center-button')
    expect(openButton.exists()).toBe(true)

    await openButton.trigger('click')

    expect(pushMock).toHaveBeenCalledWith('/notifications/center')
  })

  it('sends a follow-up reminder from the execution panel', async () => {
    vi.mocked(request).mockResolvedValue({
      success: true,
      message: 'Follow-up reminder sent successfully',
      data: {},
    })

    const wrapper = mountPanel({
      status: 'resolved',
      status_label: 'Resolved',
      difference_type_label: 'Missing',
      task_code: 'INV-009',
      resolution: 'Finance follow-up required',
      closure_type: 'financial_adjustment',
      linked_action_code: 'finance_adjustment',
      evidence_refs: [],
      closure_notes: '',
      custom_fields: {
        linked_action_execution: {
          action_code: 'finance_adjustment',
          status: 'manual_follow_up',
          message: 'Follow-up assigned to inventory-owner.',
          can_send_follow_up: true,
        },
      },
    })

    const reminderButton = wrapper.find('.inventory-difference-panel__follow-up-button')
    expect(reminderButton.exists()).toBe(true)

    await reminderButton.trigger('click')
    await flushPromises()

    expect(request).toHaveBeenCalledWith(expect.objectContaining({
      url: '/system/objects/InventoryItem/diff-1/send-follow-up/',
      method: 'post',
      data: {},
      unwrap: 'none',
    }))
    expect(ElMessage.success).toHaveBeenCalledWith('Follow-up reminder sent successfully')
  })

  it('completes and reopens a manual follow-up task from the execution panel', async () => {
    vi.mocked(request)
      .mockResolvedValueOnce({
        success: true,
        message: 'Follow-up task completed successfully',
        data: {},
      })
      .mockResolvedValueOnce({
        success: true,
        message: 'Follow-up task reopened successfully',
        data: {},
      })

    const wrapper = mountPanel({
      status: 'resolved',
      status_label: 'Resolved',
      difference_type_label: 'Missing',
      task_code: 'INV-010',
      resolution: 'Finance follow-up required',
      closure_type: 'financial_adjustment',
      linked_action_code: 'finance_adjustment',
      evidence_refs: [],
      closure_notes: 'Finance booking completed',
      custom_fields: {
        linked_action_execution: {
          action_code: 'finance_adjustment',
          status: 'manual_follow_up',
          message: 'Follow-up assigned to inventory-owner.',
          can_send_follow_up: true,
          follow_up_task_code: 'IFU2026030002',
          follow_up_task_status: 'pending',
        },
      },
    })

    const completeButton = wrapper.find('.inventory-difference-panel__follow-up-complete-button')
    expect(completeButton.exists()).toBe(true)

    await completeButton.trigger('click')
    await flushPromises()

    expect(request).toHaveBeenCalledWith(expect.objectContaining({
      url: '/system/objects/InventoryItem/diff-1/complete-follow-up/',
      method: 'post',
      data: {
        completionNotes: 'Finance booking completed',
        evidenceRefs: [],
      },
      unwrap: 'none',
    }))

    await wrapper.setProps({
      recordData: {
        ...wrapper.props('recordData'),
        custom_fields: {
          linked_action_execution: {
            action_code: 'finance_adjustment',
            status: 'manual_follow_up',
            message: 'Manual follow-up completed.',
            can_send_follow_up: false,
            follow_up_task_code: 'IFU2026030002',
            follow_up_task_status: 'completed',
            follow_up_completed_at: '2026-03-27T14:00:00',
          },
        },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Completed')
    expect(wrapper.text()).toContain('Follow-up Completed At')

    const reopenButton = wrapper.find('.inventory-difference-panel__follow-up-reopen-button')
    expect(reopenButton.exists()).toBe(true)

    await reopenButton.trigger('click')
    await flushPromises()

    expect(request).toHaveBeenCalledWith(expect.objectContaining({
      url: '/system/objects/InventoryItem/diff-1/reopen-follow-up/',
      method: 'post',
      data: {},
      unwrap: 'none',
    }))
  })
})
