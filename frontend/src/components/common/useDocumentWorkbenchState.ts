import { computed, type Ref } from 'vue'
import type { StatusAction } from '@/components/common/StatusActionBar.vue'
import type { AggregateDocumentPageMode, AggregateDocumentResponse } from '@/types/runtime'
import { resolveDocumentWorkflowProgress } from '@/platform/workflow/documentWorkflowProgress'
import {
  buildDocumentWorkbenchNavigation,
} from '@/components/common/documentWorkbenchModel'
import {
  buildDocumentWorkbenchAuditRows,
  buildDocumentWorkbenchCapabilityItems,
  buildDocumentWorkbenchDisposalBatchActions,
  buildDocumentWorkbenchFieldPermissions,
  buildDocumentWorkbenchLatestSignalSummary,
  buildDocumentWorkbenchProcessSummaryRows,
  buildDocumentWorkbenchProcessSummaryStats,
  buildDocumentWorkbenchTimelineEntries,
  buildDocumentWorkbenchWorkflowActivityItems,
  resolveDocumentWorkbenchModeLabel,
  resolveDocumentWorkbenchReadonly,
  resolveDocumentWorkbenchRecordId,
  resolveDocumentWorkbenchWorkflowStatusLabel,
  resolveDocumentWorkbenchWorkflowTitle,
  buildDocumentWorkbenchRecordRows,
  buildDocumentWorkbenchWorkflowRows,
  shouldShowDocumentWorkbenchHeaderShell,
  type DocumentWorkbenchTranslateFn,
} from '@/components/common/documentWorkbenchViewModel'

interface DocumentWorkbenchStateProps {
  objectCode: string
  recordId?: string
  mode: AggregateDocumentPageMode
  modelValue: Record<string, any>
  document?: AggregateDocumentResponse | null
  readonly?: boolean
  statusActions?: StatusAction[]
  showObjectActions?: boolean
}

interface UseDocumentWorkbenchStateOptions {
  props: DocumentWorkbenchStateProps
  t: DocumentWorkbenchTranslateFn
  locale: Ref<string>
}

export function useDocumentWorkbenchState({
  props,
  t,
  locale,
}: UseDocumentWorkbenchStateOptions) {
  const cardVariant = computed(() => (props.mode === 'readonly' ? 'detail' : 'form'))
  const effectiveRecordId = computed(() => resolveDocumentWorkbenchRecordId({
    recordId: props.recordId,
    document: props.document,
  }))
  const recordStatusLabel = computed(() => String((props.document?.master?.status as string) || '-'))
  const effectiveReadonly = computed(() => resolveDocumentWorkbenchReadonly({
    readonly: props.readonly,
    mode: props.mode,
    document: props.document,
  }))
  const fieldPermissions = computed(() => buildDocumentWorkbenchFieldPermissions({
    document: props.document,
    readonly: effectiveReadonly.value,
  }))
  const modeLabel = computed(() => resolveDocumentWorkbenchModeLabel({
    mode: props.mode,
    t,
  }))
  const recordRows = computed(() => buildDocumentWorkbenchRecordRows({
    document: props.document,
    modeLabel: modeLabel.value,
    recordStatusLabel: recordStatusLabel.value,
    readonly: effectiveReadonly.value,
    t,
  }))
  const workflowTitle = computed(() => resolveDocumentWorkbenchWorkflowTitle({
    document: props.document,
    t,
  }))
  const workflowRows = computed(() => buildDocumentWorkbenchWorkflowRows({
    document: props.document,
    t,
  }))
  const workflowStatusLabel = computed(() => resolveDocumentWorkbenchWorkflowStatusLabel(props.document))
  const latestSignalSummary = computed(() => buildDocumentWorkbenchLatestSignalSummary({
    document: props.document,
    locale: locale.value || 'en-US',
    t,
      objectCode: props.objectCode,
      effectiveRecordId: effectiveRecordId.value,
    }))
  const processSummaryStats = computed(() => buildDocumentWorkbenchProcessSummaryStats({
    objectCode: props.objectCode,
    document: props.document,
    modelValue: props.modelValue,
    t,
  }))
  const auditRows = computed(() => buildDocumentWorkbenchAuditRows({
    document: props.document,
    locale: locale.value || 'en-US',
    t,
      objectCode: props.objectCode,
      effectiveRecordId: effectiveRecordId.value,
    }))
  const navigationSection = computed(() => buildDocumentWorkbenchNavigation({
    objectCode: props.objectCode,
    document: props.document,
    modelValue: props.modelValue,
    t,
  }))
  const workflowProgress = computed(() => resolveDocumentWorkflowProgress({
    objectCode: props.objectCode,
    document: props.document,
    t: (key: string) => t(key),
  }))
  const processSummaryRows = computed(() => buildDocumentWorkbenchProcessSummaryRows({
    document: props.document,
    locale: locale.value || 'en-US',
    t,
    objectCode: props.objectCode,
    effectiveRecordId: effectiveRecordId.value,
    workflowProgress: workflowProgress.value,
  }))
  const capabilityItems = computed(() => buildDocumentWorkbenchCapabilityItems({
    document: props.document,
    t,
  }))
  const sourceLabels = computed(() => ({
    activity: t('common.documentWorkbench.sources.activity'),
    workflowApproval: t('common.documentWorkbench.sources.workflowApproval'),
    workflowOperation: t('common.documentWorkbench.sources.workflowOperation'),
  }))
  const workflowActivityItems = computed(() => buildDocumentWorkbenchWorkflowActivityItems({
    document: props.document,
    locale: locale.value || 'en-US',
    t,
  }))
  const timelineEntries = computed(() => buildDocumentWorkbenchTimelineEntries({
    objectCode: props.objectCode,
    effectiveRecordId: effectiveRecordId.value,
    document: props.document,
    sourceLabels: sourceLabels.value,
  }))
  const disposalBatchActions = computed(() => buildDocumentWorkbenchDisposalBatchActions({
    objectCode: props.objectCode,
    document: props.document,
    modelValue: props.modelValue,
    readonly: effectiveReadonly.value,
    recordStatusLabel: recordStatusLabel.value,
    t,
  }))
  const showHeaderShell = computed(() => shouldShowDocumentWorkbenchHeaderShell({
    statusActionCount: props.statusActions?.length || 0,
    showObjectActions: props.showObjectActions !== false,
    effectiveRecordId: effectiveRecordId.value,
    capabilityItems: capabilityItems.value,
    hasLatestSignal: Boolean(latestSignalSummary.value),
  }))

  return {
    auditRows,
    capabilityItems,
    cardVariant,
    disposalBatchActions,
    effectiveReadonly,
    effectiveRecordId,
    fieldPermissions,
    modeLabel,
    navigationSection,
    processSummaryRows,
    processSummaryStats,
    recordRows,
    recordStatusLabel,
    showHeaderShell,
    timelineEntries,
    workflowActivityItems,
    workflowProgress,
    workflowRows,
    workflowStatusLabel,
    workflowTitle,
  }
}
