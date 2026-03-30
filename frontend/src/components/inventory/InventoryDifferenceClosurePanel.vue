<template>
  <el-card
    class="inventory-difference-panel"
    shadow="never"
  >
    <template #header>
      <div class="inventory-difference-panel__header">
        <div class="inventory-difference-panel__heading">
          <div class="inventory-difference-panel__title-row">
            <span>{{ title }}</span>
            <el-tag :type="statusTagType">
              {{ statusLabel || '--' }}
            </el-tag>
            <el-tag
              v-if="showDraftState"
              :type="draftStateTagType"
            >
              {{ draftStateLabel }}
            </el-tag>
          </div>
          <p class="inventory-difference-panel__hint">
            {{ t('inventory.workbench.messages.differenceClosureHint') }}
          </p>
          <p
            v-if="showDraftState"
            :class="[
              'inventory-difference-panel__draft-hint',
              isDraftDirty ? 'inventory-difference-panel__draft-hint--dirty' : 'inventory-difference-panel__draft-hint--saved',
            ]"
          >
            {{ draftStateHint }}
          </p>
        </div>

        <el-button
          size="small"
          @click="emitRefresh"
        >
          {{ t('common.actions.refresh') }}
        </el-button>
      </div>
    </template>

    <div class="inventory-difference-panel__body">
      <div class="inventory-difference-panel__summary">
        <div class="inventory-difference-panel__summary-item">
          <span>{{ t('inventory.workbench.summary.differenceType') }}</span>
          <strong>{{ differenceTypeLabel || '--' }}</strong>
        </div>
        <div class="inventory-difference-panel__summary-item">
          <span>{{ t('inventory.workbench.summary.taskCode') }}</span>
          <strong>{{ taskCode || '--' }}</strong>
        </div>
        <div class="inventory-difference-panel__summary-item">
          <span>{{ t('common.workbench.labels.owner') }}</span>
          <strong>{{ ownerName || '--' }}</strong>
        </div>
      </div>

      <div
        v-if="linkedActionExecution"
        class="inventory-difference-panel__execution"
      >
        <div class="inventory-difference-panel__execution-header">
          <div>
            <p class="inventory-difference-panel__execution-eyebrow">
              {{ t('inventory.workbench.execution.title') }}
            </p>
            <h4 class="inventory-difference-panel__execution-title">
              {{ executionActionLabel }}
            </h4>
          </div>

          <el-tag :type="executionStatusTagType">
            {{ executionStatusLabel }}
          </el-tag>
        </div>

        <div class="inventory-difference-panel__execution-grid">
          <div class="inventory-difference-panel__execution-item">
            <span>{{ t('inventory.workbench.execution.action') }}</span>
            <strong>{{ executionActionLabel }}</strong>
          </div>
          <div
            v-if="linkedActionExecution.followUpAssigneeName"
            class="inventory-difference-panel__execution-item"
          >
            <span>{{ t('inventory.workbench.execution.followUpOwner') }}</span>
            <strong>{{ linkedActionExecution.followUpAssigneeName }}</strong>
          </div>
          <div
            v-if="linkedActionExecution.followUpTaskCode"
            class="inventory-difference-panel__execution-item"
          >
            <span>{{ t('inventory.workbench.execution.followUpTask') }}</span>
            <strong>{{ linkedActionExecution.followUpTaskCode }}</strong>
          </div>
          <div
            v-if="linkedActionExecution.followUpTaskStatus"
            class="inventory-difference-panel__execution-item"
          >
            <span>{{ t('inventory.workbench.execution.followUpTaskStatus') }}</span>
            <strong>{{ followUpTaskStatusLabel }}</strong>
          </div>
          <div
            v-if="linkedActionExecution.followUpSentCount"
            class="inventory-difference-panel__execution-item"
          >
            <span>{{ t('inventory.workbench.execution.followUpCount') }}</span>
            <strong>{{ linkedActionExecution.followUpSentCount }}</strong>
          </div>
          <div
            v-if="linkedActionExecution.followUpNotificationId"
            class="inventory-difference-panel__execution-item"
          >
            <span>{{ t('inventory.workbench.execution.notification') }}</span>
            <strong>{{ linkedActionExecution.followUpNotificationId }}</strong>
          </div>
          <div
            v-if="executionTargetLabel"
            class="inventory-difference-panel__execution-item"
          >
            <span>{{ t('inventory.workbench.execution.targetRecord') }}</span>
            <strong>{{ executionTargetLabel }}</strong>
          </div>
          <div
            v-if="linkedActionExecution.executedAt"
            class="inventory-difference-panel__execution-item"
          >
            <span>{{ t('inventory.workbench.execution.executedAt') }}</span>
            <strong>{{ linkedActionExecution.executedAt }}</strong>
          </div>
          <div
            v-if="linkedActionExecution.followUpCompletedAt"
            class="inventory-difference-panel__execution-item"
          >
            <span>{{ t('inventory.workbench.execution.followUpCompletedAt') }}</span>
            <strong>{{ linkedActionExecution.followUpCompletedAt }}</strong>
          </div>
        </div>

        <p
          v-if="linkedActionExecution.message"
          class="inventory-difference-panel__execution-message"
        >
          {{ linkedActionExecution.message }}
        </p>

        <el-button
          v-if="linkedActionExecution.targetUrl"
          class="inventory-difference-panel__execution-link"
          type="primary"
          text
          @click="navigateToLinkedRecord"
        >
          {{ t('common.actions.view') }}
        </el-button>

        <div
          v-if="showFollowUpActions"
          class="inventory-difference-panel__execution-actions"
        >
          <el-button
            v-if="linkedActionExecution.followUpTaskUrl"
            class="inventory-difference-panel__follow-up-task-button"
            type="primary"
            text
            @click="openFollowUpTask"
          >
            {{ t('inventory.workbench.execution.openFollowUpTask') }}
          </el-button>
          <el-button
            v-if="canCompleteFollowUp"
            class="inventory-difference-panel__follow-up-complete-button"
            type="success"
            text
            :loading="loadingActionCode === 'complete_follow_up'"
            @click="handleCompleteFollowUp"
          >
            {{ t('inventory.workbench.actions.completeFollowUp') }}
          </el-button>
          <el-button
            v-if="canReopenFollowUp"
            class="inventory-difference-panel__follow-up-reopen-button"
            type="primary"
            text
            :loading="loadingActionCode === 'reopen_follow_up'"
            @click="handleReopenFollowUp"
          >
            {{ t('inventory.workbench.actions.reopenFollowUp') }}
          </el-button>
          <el-button
            v-if="canSendFollowUp"
            class="inventory-difference-panel__follow-up-button"
            type="warning"
            text
            :loading="loadingActionCode === 'send_follow_up'"
            @click="handleSendFollowUp"
          >
            {{ t('inventory.workbench.actions.sendFollowUp') }}
          </el-button>
          <el-button
            v-if="linkedActionExecution.followUpNotificationUrl"
            class="inventory-difference-panel__follow-up-center-button"
            type="primary"
            text
            @click="openFollowUpNotificationCenter"
          >
            {{ t('inventory.workbench.execution.openNotificationCenter') }}
          </el-button>
        </div>
      </div>

      <el-alert
        v-if="status === 'pending'"
        type="info"
        :closable="false"
        show-icon
        :title="t('inventory.workbench.messages.pendingConfirmHint')"
      />

      <div
        v-else
        class="inventory-difference-panel__form"
      >
        <div class="inventory-difference-panel__field">
          <label for="inventory-difference-resolution">{{ t('inventory.workbench.form.resolution') }}</label>
          <el-input
            id="inventory-difference-resolution"
            v-model="form.resolution"
            type="textarea"
            :rows="4"
            :placeholder="t('inventory.workbench.placeholders.resolution')"
          />
        </div>

        <div
          v-if="showClosureType"
          class="inventory-difference-panel__field"
        >
          <label for="inventory-difference-closure-type">{{ t('inventory.workbench.form.closureType') }}</label>
          <el-select
            id="inventory-difference-closure-type"
            v-model="form.closureType"
            class="inventory-difference-panel__select"
            :placeholder="t('inventory.workbench.placeholders.closureType')"
          >
            <el-option
              v-for="option in closureTypeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </div>

        <div class="inventory-difference-panel__field">
          <label for="inventory-difference-linked-action">{{ t('inventory.workbench.form.linkedActionCode') }}</label>
          <el-select
            v-if="showLinkedActionSelect"
            id="inventory-difference-linked-action"
            v-model="form.linkedActionCode"
            class="inventory-difference-panel__select"
            :placeholder="t('inventory.workbench.placeholders.linkedActionCode')"
          >
            <el-option
              v-for="option in linkedActionOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <el-input
            v-else
            id="inventory-difference-linked-action"
            v-model="form.linkedActionCode"
            :placeholder="t('inventory.workbench.placeholders.linkedActionCode')"
          />
        </div>

        <div class="inventory-difference-panel__field">
          <label for="inventory-difference-evidence">{{ t('inventory.workbench.form.evidenceRefs') }}</label>
          <el-input
            id="inventory-difference-evidence"
            v-model="form.evidenceText"
            type="textarea"
            :rows="3"
            :placeholder="t('inventory.workbench.placeholders.evidenceRefs')"
          />
        </div>

        <div class="inventory-difference-panel__field">
          <label for="inventory-difference-closure-notes">{{ t('inventory.workbench.form.closureNotes') }}</label>
          <el-input
            id="inventory-difference-closure-notes"
            v-model="form.closureNotes"
            type="textarea"
            :rows="3"
            :placeholder="t('inventory.workbench.placeholders.closureNotes')"
          />
        </div>

        <div
          v-if="status === 'approved'"
          class="inventory-difference-panel__switch"
        >
          <span>{{ t('inventory.workbench.form.syncAsset') }}</span>
          <el-switch v-model="form.syncAsset" />
        </div>
      </div>

      <div
        v-if="actionButtons.length > 0"
        class="inventory-difference-panel__actions"
      >
        <el-button
          v-for="action in actionButtons"
          :key="action.code"
          :type="action.type"
          :loading="loadingActionCode === action.code"
          :disabled="action.disabled"
          @click="action.handler"
        >
          {{ action.label }}
        </el-button>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import request from '@/utils/request'

type WorkbenchRefreshPayload = {
  summary?: boolean
  detail?: boolean
  panels?: string[]
}

interface ActionButton {
  code: string
  label: string
  type: 'primary' | 'success' | 'warning' | 'danger' | 'default'
  disabled?: boolean
  handler: () => Promise<void>
}

interface LinkedActionOption {
  value: string
  label: string
  closureTypes: string[]
}

interface LinkedActionExecutionPayload {
  actionCode: string
  status: string
  targetObjectCode: string
  targetId: string
  targetUrl: string
  message: string
  executedAt: string
  canSendFollowUp: boolean
  followUpAssigneeId: string
  followUpAssigneeName: string
  followUpNotificationId: string
  followUpNotificationUrl: string
  followUpSentCount: number
  followUpTaskId: string
  followUpTaskCode: string
  followUpTaskStatus: string
  followUpTaskUrl: string
  followUpCompletedAt: string
}

const props = defineProps<{
  panel: Record<string, unknown>
  objectCode?: string
  recordId: string
  recordData?: Record<string, unknown> | null
  refreshVersion?: number
  panelRefreshVersion?: number
}>()

const emit = defineEmits<{
  (e: 'workbench-refresh-requested', payload: WorkbenchRefreshPayload): void
}>()

const router = useRouter()
const { t, te } = useI18n()

const form = reactive({
  resolution: '',
  closureType: '',
  linkedActionCode: '',
  evidenceText: '',
  closureNotes: '',
  syncAsset: true,
})
const loadingActionCode = ref<string | null>(null)
const lastSavedDraftSignature = ref('')

const title = computed(() => {
  const titleKey = String(props.panel.titleKey || props.panel.title_key || '').trim()
  if (titleKey && te(titleKey)) {
    return t(titleKey)
  }
  return String(props.panel.title || t('inventory.workbench.panels.differenceClosure'))
})

const status = computed(() => String(props.recordData?.status || '').trim())
const statusLabel = computed(() => String(props.recordData?.status_label || props.recordData?.statusLabel || status.value || '').trim())
const differenceTypeLabel = computed(() => String(props.recordData?.difference_type_label || props.recordData?.differenceTypeLabel || '').trim())
const taskCode = computed(() => String(props.recordData?.task_code || props.recordData?.taskCode || '').trim())
const ownerName = computed(() => {
  const owner = props.recordData?.owner as Record<string, unknown> | undefined
  if (!owner || typeof owner !== 'object') return ''
  return String(owner.displayName || owner.display_name || owner.username || '').trim()
})

const statusTagType = computed(() => {
  if (['resolved', 'closed'].includes(status.value)) return 'success'
  if (['approved', 'confirmed'].includes(status.value)) return 'warning'
  if (['ignored'].includes(status.value)) return 'info'
  if (['pending'].includes(status.value)) return 'danger'
  return 'primary'
})

const showClosureType = computed(() => ['confirmed', 'approved'].includes(status.value))
const showDraftState = computed(() => status.value !== 'pending')

const panelProps = computed<Record<string, unknown>>(() => {
  const rawProps = props.panel.props
  return rawProps && typeof rawProps === 'object' ? rawProps as Record<string, unknown> : {}
})

const asRecord = (value: unknown): Record<string, unknown> | null => {
  return value && typeof value === 'object' ? value as Record<string, unknown> : null
}

const normalizeEvidenceRefs = (value: unknown) => {
  if (!Array.isArray(value)) {
    return []
  }
  return value
    .map((item) => String(item || '').trim())
    .filter(Boolean)
}

const buildDraftState = (source?: Record<string, unknown> | null) => {
  if (source) {
    return {
      resolution: String(source.resolution || '').trim(),
      closureType: String(source.closure_type || source.closureType || '').trim(),
      linkedActionCode: String(source.linked_action_code || source.linkedActionCode || '').trim(),
      evidenceRefs: normalizeEvidenceRefs(source.evidence_refs || source.evidenceRefs),
      closureNotes: String(source.closure_notes || source.closureNotes || '').trim(),
    }
  }

  return {
    resolution: form.resolution.trim(),
    closureType: form.closureType.trim(),
    linkedActionCode: form.linkedActionCode.trim(),
    evidenceRefs: buildEvidenceRefs(),
    closureNotes: form.closureNotes.trim(),
  }
}

const normalizeClosureTypeList = (value: unknown) => {
  if (!Array.isArray(value)) {
    return []
  }
  return value
    .map((item) => String(item || '').trim())
    .filter(Boolean)
}

const configuredLinkedActionOptions = computed<LinkedActionOption[]>(() => {
  const rawValue = panelProps.value.linkedActionOptions || panelProps.value.linked_action_options
  if (!Array.isArray(rawValue)) {
    return []
  }

  return rawValue
    .map((item) => {
      if (!item || typeof item !== 'object') {
        return null
      }
      const candidate = item as Record<string, unknown>
      const value = String(candidate.value || candidate.code || '').trim()
      if (!value) {
        return null
      }
      const labelKey = String(candidate.labelKey || candidate.label_key || '').trim()
      const fallbackLabel = String(candidate.label || value).trim() || value
      return {
        value,
        label: labelKey && te(labelKey) ? t(labelKey) : fallbackLabel,
        closureTypes: normalizeClosureTypeList(candidate.closureTypes || candidate.closure_types),
      } satisfies LinkedActionOption
    })
    .filter((item): item is LinkedActionOption => Boolean(item))
})

const linkedActionLabelMap = computed(() => {
  return new Map(configuredLinkedActionOptions.value.map((item) => [item.value, item.label]))
})

const linkedActionExecution = computed<LinkedActionExecutionPayload | null>(() => {
  const recordData = asRecord(props.recordData)
  const customFields = asRecord(recordData?.custom_fields || recordData?.customFields)
  const rawExecution = asRecord(customFields?.linked_action_execution || customFields?.linkedActionExecution)
  if (!rawExecution) {
    return null
  }

  const execution = {
    actionCode: String(rawExecution.action_code || rawExecution.actionCode || '').trim(),
    status: String(rawExecution.status || '').trim(),
    targetObjectCode: String(rawExecution.target_object_code || rawExecution.targetObjectCode || '').trim(),
    targetId: String(rawExecution.target_id || rawExecution.targetId || '').trim(),
    targetUrl: String(rawExecution.target_url || rawExecution.targetUrl || '').trim(),
    message: String(rawExecution.message || '').trim(),
    executedAt: String(rawExecution.executed_at || rawExecution.executedAt || '').trim(),
    canSendFollowUp: Boolean(rawExecution.can_send_follow_up ?? rawExecution.canSendFollowUp),
    followUpAssigneeId: String(rawExecution.follow_up_assignee_id || rawExecution.followUpAssigneeId || '').trim(),
    followUpAssigneeName: String(rawExecution.follow_up_assignee_name || rawExecution.followUpAssigneeName || '').trim(),
    followUpNotificationId: String(rawExecution.follow_up_notification_id || rawExecution.followUpNotificationId || '').trim(),
    followUpNotificationUrl: String(rawExecution.follow_up_notification_url || rawExecution.followUpNotificationUrl || '').trim(),
    followUpSentCount: Number(rawExecution.follow_up_sent_count || rawExecution.followUpSentCount || 0),
    followUpTaskId: String(rawExecution.follow_up_task_id || rawExecution.followUpTaskId || '').trim(),
    followUpTaskCode: String(rawExecution.follow_up_task_code || rawExecution.followUpTaskCode || '').trim(),
    followUpTaskStatus: String(rawExecution.follow_up_task_status || rawExecution.followUpTaskStatus || '').trim(),
    followUpTaskUrl: String(rawExecution.follow_up_task_url || rawExecution.followUpTaskUrl || '').trim(),
    followUpCompletedAt: String(rawExecution.follow_up_completed_at || rawExecution.followUpCompletedAt || '').trim(),
  }

  if (Object.values(execution).every((value) => !value)) {
    return null
  }

  return execution
})

const currentClosureType = computed(() => {
  return String(form.closureType || props.recordData?.closure_type || props.recordData?.closureType || '').trim()
})

const linkedActionOptions = computed<LinkedActionOption[]>(() => {
  const closureType = currentClosureType.value
  const visibleOptions = configuredLinkedActionOptions.value.filter((option) => {
    return option.closureTypes.length === 0 || !closureType || option.closureTypes.includes(closureType)
  })

  const currentValue = form.linkedActionCode.trim()
  if (!currentValue || visibleOptions.some((option) => option.value === currentValue)) {
    return visibleOptions
  }

  return [
    ...visibleOptions,
    {
      value: currentValue,
      label: t('inventory.workbench.linkedActions.currentValue', { code: currentValue }),
      closureTypes: [],
    },
  ]
})

const showLinkedActionSelect = computed(() => linkedActionOptions.value.length > 0)

const executionActionLabel = computed(() => {
  const actionCode = linkedActionExecution.value?.actionCode || ''
  return linkedActionLabelMap.value.get(actionCode) || actionCode || '--'
})

const executionStatusLabel = computed(() => {
  const statusValue = linkedActionExecution.value?.status || ''
  if (statusValue === 'executed') {
    return t('inventory.workbench.execution.states.executed')
  }
  if (statusValue === 'manual_follow_up') {
    return t('inventory.workbench.execution.states.manualFollowUp')
  }
  return statusValue || '--'
})

const executionStatusTagType = computed(() => {
  const statusValue = linkedActionExecution.value?.status || ''
  if (statusValue === 'executed') {
    return 'success'
  }
  if (statusValue === 'manual_follow_up') {
    return 'warning'
  }
  return 'info'
})

const followUpTaskStatusLabel = computed(() => {
  const statusValue = linkedActionExecution.value?.followUpTaskStatus || ''
  if (!statusValue) {
    return '--'
  }
  const translationKey = `inventory.workbench.execution.states.${statusValue}`
  return te(translationKey) ? t(translationKey) : statusValue
})

const executionTargetLabel = computed(() => {
  const execution = linkedActionExecution.value
  if (!execution) {
    return ''
  }
  return [execution.targetObjectCode, execution.targetId].filter(Boolean).join(' / ')
})

const canSendFollowUp = computed(() => {
  return Boolean(
    linkedActionExecution.value &&
    linkedActionExecution.value.status === 'manual_follow_up' &&
    linkedActionExecution.value.canSendFollowUp,
  )
})

const canCompleteFollowUp = computed(() => {
  return Boolean(
    linkedActionExecution.value &&
    linkedActionExecution.value.status === 'manual_follow_up' &&
    linkedActionExecution.value.followUpTaskStatus &&
    linkedActionExecution.value.followUpTaskStatus !== 'completed',
  )
})

const canReopenFollowUp = computed(() => {
  return linkedActionExecution.value?.followUpTaskStatus === 'completed'
})

const showFollowUpActions = computed(() => {
  return Boolean(
    linkedActionExecution.value &&
    (
      linkedActionExecution.value.followUpTaskUrl ||
      canCompleteFollowUp.value ||
      canReopenFollowUp.value ||
      canSendFollowUp.value ||
      linkedActionExecution.value.followUpNotificationUrl
    ),
  )
})

const serializeDraftState = (state: ReturnType<typeof buildDraftState>) => {
  return JSON.stringify(state)
}

const syncSavedDraftState = (source?: Record<string, unknown> | null) => {
  lastSavedDraftSignature.value = serializeDraftState(buildDraftState(source))
}

const isDraftDirty = computed(() => {
  return serializeDraftState(buildDraftState()) !== lastSavedDraftSignature.value
})

const draftStateLabel = computed(() => {
  return isDraftDirty.value
    ? t('inventory.workbench.states.unsavedChanges')
    : t('inventory.workbench.states.draftSaved')
})

const draftStateHint = computed(() => {
  return isDraftDirty.value
    ? t('inventory.workbench.messages.unsavedDraftHint')
    : t('inventory.workbench.messages.savedDraftHint')
})

const draftStateTagType = computed(() => {
  return isDraftDirty.value ? 'warning' : 'success'
})

const closureTypeOptions = computed(() => {
  return [
    'locationCorrection',
    'custodianCorrection',
    'repair',
    'disposal',
    'createAssetCard',
    'financialAdjustment',
    'invalidDifference',
  ].map((key) => ({
    value: toSnakeCase(key),
    label: t(`inventory.workbench.closureTypes.${key}`),
  }))
})

const toSnakeCase = (value: string) => {
  return value
    .replace(/[A-Z]/g, (match) => `_${match.toLowerCase()}`)
    .replace(/^_/, '')
}

const normalizeEvidenceText = (value: unknown) => {
  if (Array.isArray(value)) {
    return value.map((item) => String(item || '').trim()).filter(Boolean).join('\n')
  }
  return String(value || '').trim()
}

const hydrateForm = () => {
  const recordData = props.recordData || {}
  form.resolution = String(recordData.resolution || '').trim()
  form.closureType = String(recordData.closure_type || recordData.closureType || '').trim()
  form.linkedActionCode = String(recordData.linked_action_code || recordData.linkedActionCode || '').trim()
  form.evidenceText = normalizeEvidenceText(recordData.evidence_refs || recordData.evidenceRefs)
  form.closureNotes = String(recordData.closure_notes || recordData.closureNotes || '').trim()
  form.syncAsset = true
  syncSavedDraftState(recordData)
}

watch(
  () => [props.recordData, props.refreshVersion, props.panelRefreshVersion],
  () => {
    hydrateForm()
  },
  { immediate: true, deep: true }
)

const buildEvidenceRefs = () => {
  return form.evidenceText
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

const postAction = async (actionCode: string, actionPath: string, payload: Record<string, unknown>) => {
  if (!props.recordId) {
    return
  }

  loadingActionCode.value = actionCode
  try {
    const result = await request<{
      success?: boolean
      message?: string
      data?: Record<string, unknown>
      error?: Record<string, unknown>
    }>({
      url: `/system/objects/${props.objectCode || 'InventoryItem'}/${props.recordId}/${actionPath}/`,
      method: 'post',
      data: payload,
      unwrap: 'none',
    })

    if (result.success === false) {
      throw new Error(String(result.error?.message || result.message || t('common.messages.operationFailed')))
    }

    const hasRecordPayload = Boolean(
      result.data &&
      typeof result.data === 'object' &&
      Object.keys(result.data as Record<string, unknown>).length > 0,
    )

    if (hasRecordPayload) {
      syncSavedDraftState(result.data)
    } else if (actionCode === 'save_draft') {
      syncSavedDraftState(payload)
    }

    ElMessage.success(String(result.message || t('common.messages.operationSuccess')))
    emitRefresh()
  } catch (error: unknown) {
    ElMessage.error(error instanceof Error ? error.message : t('common.messages.operationFailed'))
  } finally {
    loadingActionCode.value = null
  }
}

const emitRefresh = () => {
  emit('workbench-refresh-requested', { detail: true })
}

const handleSubmitReview = async () => {
  if (!form.resolution.trim()) {
    ElMessage.warning(t('inventory.workbench.validation.resolutionRequired'))
    return
  }
  if (!form.closureType.trim()) {
    ElMessage.warning(t('inventory.workbench.validation.closureTypeRequired'))
    return
  }
  await postAction('submit_review', 'submit-review', {
    resolution: form.resolution.trim(),
    closureType: form.closureType.trim(),
    linkedActionCode: form.linkedActionCode.trim(),
    evidenceRefs: buildEvidenceRefs(),
  })
}

const handleSaveDraft = async () => {
  await postAction('save_draft', 'save-draft', {
    resolution: form.resolution.trim(),
    closureType: form.closureType.trim(),
    linkedActionCode: form.linkedActionCode.trim(),
    evidenceRefs: buildEvidenceRefs(),
    closureNotes: form.closureNotes.trim(),
  })
}

const handleApproveResolution = async () => {
  await postAction('approve_resolution', 'approve-resolution', {
    closureNotes: form.closureNotes.trim(),
  })
}

const handleRejectResolution = async () => {
  await postAction('reject_resolution', 'reject-resolution', {
    closureNotes: form.closureNotes.trim(),
  })
}

const handleExecuteResolution = async () => {
  if (!form.resolution.trim()) {
    ElMessage.warning(t('inventory.workbench.validation.resolutionRequired'))
    return
  }
  await postAction('execute_resolution', 'execute-resolution', {
    resolution: form.resolution.trim(),
    syncAsset: form.syncAsset,
    linkedActionCode: form.linkedActionCode.trim(),
  })
}

const handleCloseDifference = async () => {
  await postAction('close_difference', 'close-difference', {
    closureNotes: form.closureNotes.trim(),
    evidenceRefs: buildEvidenceRefs(),
  })
}

const handleSendFollowUp = async () => {
  await postAction('send_follow_up', 'send-follow-up', {})
}

const handleCompleteFollowUp = async () => {
  await postAction('complete_follow_up', 'complete-follow-up', {
    completionNotes: form.closureNotes.trim(),
    evidenceRefs: buildEvidenceRefs(),
  })
}

const handleReopenFollowUp = async () => {
  await postAction('reopen_follow_up', 'reopen-follow-up', {})
}

const navigateToLinkedRecord = async () => {
  const targetUrl = linkedActionExecution.value?.targetUrl
  if (!targetUrl) {
    return
  }
  await router.push(targetUrl)
}

const openFollowUpNotificationCenter = async () => {
  const targetUrl = linkedActionExecution.value?.followUpNotificationUrl
  if (!targetUrl) {
    return
  }
  await router.push(targetUrl)
}

const openFollowUpTask = async () => {
  const targetUrl = linkedActionExecution.value?.followUpTaskUrl
  if (!targetUrl) {
    return
  }
  await router.push(targetUrl)
}

const buildDraftAction = (): ActionButton => ({
  code: 'save_draft',
  label: t('inventory.workbench.actions.saveDraft'),
  type: 'default',
  disabled: !isDraftDirty.value,
  handler: handleSaveDraft,
})

const actionButtons = computed<ActionButton[]>(() => {
  if (status.value === 'confirmed') {
    return [
      buildDraftAction(),
      {
        code: 'submit_review',
        label: t('inventory.workbench.actions.submitReview'),
        type: 'warning',
        handler: handleSubmitReview,
      },
    ]
  }

  if (status.value === 'in_review') {
    return [
      buildDraftAction(),
      {
        code: 'approve_resolution',
        label: t('inventory.workbench.actions.approveResolution'),
        type: 'success',
        handler: handleApproveResolution,
      },
      {
        code: 'reject_resolution',
        label: t('inventory.workbench.actions.rejectResolution'),
        type: 'danger',
        handler: handleRejectResolution,
      },
    ]
  }

  if (status.value === 'approved') {
    return [
      buildDraftAction(),
      {
        code: 'execute_resolution',
        label: t('inventory.workbench.actions.executeResolution'),
        type: 'primary',
        handler: handleExecuteResolution,
      },
    ]
  }

  if (['resolved', 'ignored'].includes(status.value)) {
    return [
      buildDraftAction(),
      {
        code: 'close_difference',
        label: t('inventory.workbench.actions.closeDifference'),
        type: 'success',
        handler: handleCloseDifference,
      },
    ]
  }

  return []
})
</script>

<style scoped>
.inventory-difference-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.inventory-difference-panel__heading {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.inventory-difference-panel__title-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  font-weight: 700;
}

.inventory-difference-panel__hint {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.5;
}

.inventory-difference-panel__draft-hint {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
}

.inventory-difference-panel__draft-hint--dirty {
  color: var(--el-color-warning-dark-2);
}

.inventory-difference-panel__draft-hint--saved {
  color: var(--el-color-success-dark-2);
}

.inventory-difference-panel__body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.inventory-difference-panel__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.inventory-difference-panel__summary-item {
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color-lighter);
}

.inventory-difference-panel__summary-item span {
  display: block;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.inventory-difference-panel__summary-item strong {
  display: block;
  margin-top: 6px;
  font-size: 15px;
  color: var(--el-text-color-primary);
}

.inventory-difference-panel__execution {
  padding: 16px 18px;
  border-radius: 14px;
  border: 1px solid var(--el-border-color-lighter);
  background: linear-gradient(180deg, rgba(236, 253, 245, 0.65), rgba(255, 255, 255, 0.96));
}

.inventory-difference-panel__execution-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.inventory-difference-panel__execution-eyebrow {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
}

.inventory-difference-panel__execution-title {
  margin: 6px 0 0;
  font-size: 16px;
  color: var(--el-text-color-primary);
}

.inventory-difference-panel__execution-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 14px;
}

.inventory-difference-panel__execution-item {
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--el-border-color-lighter);
}

.inventory-difference-panel__execution-item span {
  display: block;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.inventory-difference-panel__execution-item strong {
  display: block;
  margin-top: 6px;
  font-size: 14px;
  color: var(--el-text-color-primary);
  word-break: break-word;
}

.inventory-difference-panel__execution-message {
  margin: 14px 0 0;
  font-size: 13px;
  line-height: 1.6;
  color: var(--el-text-color-regular);
}

.inventory-difference-panel__execution-link {
  margin-top: 10px;
}

.inventory-difference-panel__execution-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 10px;
}

.inventory-difference-panel__form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.inventory-difference-panel__field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.inventory-difference-panel__field label,
.inventory-difference-panel__switch span {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-regular);
}

.inventory-difference-panel__select {
  width: 100%;
}

.inventory-difference-panel__switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.inventory-difference-panel__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 768px) {
  .inventory-difference-panel__header,
  .inventory-difference-panel__summary,
  .inventory-difference-panel__execution-header,
  .inventory-difference-panel__execution-grid,
  .inventory-difference-panel__switch {
    grid-template-columns: 1fr;
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
