import type { AggregateDocumentPageMode, AggregateDocumentResponse } from '@/types/runtime'
import type { ActivityLogEntry } from '@/composables/useActivityTimeline'
import type { ObjectWorkspaceInfoRow } from '@/components/common/object-workspace/ObjectWorkspaceInfoCard.vue'
import { snakeToCamel } from '@/utils/case'
import { summarizeDisposalProgress } from '@/components/common/documentWorkbenchModel'

export type DocumentWorkbenchTranslateFn = (key: string, params?: Record<string, unknown>) => string

export interface DocumentWorkbenchCapabilityItem {
  key: string
  label: string
  active: boolean
}

export interface DocumentWorkbenchWorkflowActivityItem {
  id: string
  title: string
  meta: string
  description?: string
  createdAt: string
}

export interface DocumentWorkbenchFieldPermission {
  readonly?: boolean
}

export type DocumentWorkbenchFieldPermissions = Record<string, DocumentWorkbenchFieldPermission>

export interface DisposalBatchActionDefinition {
  key: 'applyAppraisalResult' | 'copyNetValueToResidual' | 'applyBuyerInfo' | 'copyResidualToActual'
  label: string
  type: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  count: number
}

const WORKFLOW_ACTIVITY_LIMIT = 3

const yesNoLabel = (value: boolean | undefined, t: DocumentWorkbenchTranslateFn) => {
  return value ? t('common.yes') : t('common.no')
}

const formatTimelineDate = (value: string | null | undefined, locale: string) => {
  if (!value) return '-'
  const candidate = new Date(value)
  if (Number.isNaN(candidate.getTime())) return String(value)
  return new Intl.DateTimeFormat(locale || 'en-US', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(candidate)
}

export const resolveDocumentWorkbenchRecordId = ({
  recordId,
  document,
}: {
  recordId?: string
  document?: AggregateDocumentResponse | null
}) => {
  return String(recordId || document?.context.recordId || '')
}

export const resolveDocumentWorkbenchReadonly = ({
  readonly,
  mode,
  document,
}: {
  readonly?: boolean
  mode: AggregateDocumentPageMode
  document?: AggregateDocumentResponse | null
}) => {
  if (readonly) return true
  if (mode === 'readonly') return true
  return document?.capabilities.readOnly === true
}

export const buildDocumentWorkbenchFieldPermissions = ({
  document,
  readonly,
}: {
  document?: AggregateDocumentResponse | null
  readonly: boolean
}): DocumentWorkbenchFieldPermissions => {
  if (!document || readonly) {
    return {}
  }

  const permissions: DocumentWorkbenchFieldPermissions = {}
  const masterEditable = document.capabilities.canEditMaster === true
  const detailEditable = document.capabilities.canEditDetails === true

  const assignReadonly = (key: string, isReadonly: boolean) => {
    const normalized = String(key || '').trim()
    if (!normalized) return
    permissions[normalized] = { readonly: isReadonly }
    const camelKey = snakeToCamel(normalized)
    if (camelKey && camelKey !== normalized) {
      permissions[camelKey] = { readonly: isReadonly }
    }
  }

  if (!masterEditable) {
    Object.keys(document.master || {}).forEach((key) => assignReadonly(key, true))
  }

  for (const region of document.aggregate?.detailRegions || []) {
    const isReadonly = !detailEditable
    assignReadonly(String(region.fieldCode || ''), isReadonly)
    assignReadonly(String(region.relationCode || ''), isReadonly)
  }

  return permissions
}

export const resolveDocumentWorkbenchModeLabel = ({
  mode,
  t,
}: {
  mode: AggregateDocumentPageMode
  t: DocumentWorkbenchTranslateFn
}) => {
  const key = mode === 'create'
    ? 'common.actions.create'
    : (mode === 'edit' ? 'common.actions.edit' : 'common.actions.detail')
  return t(key)
}

export const buildDocumentWorkbenchRecordRows = ({
  document,
  modeLabel,
  recordStatusLabel,
  readonly,
  t,
}: {
  document?: AggregateDocumentResponse | null
  modeLabel: string
  recordStatusLabel: string
  readonly: boolean
  t: DocumentWorkbenchTranslateFn
}): ObjectWorkspaceInfoRow[] => {
  if (!document) return []
  const totalDetailRows = Object.values(document.details || {}).reduce((total, section) => {
    return total + Number(section?.rowCount || 0)
  }, 0)

  return [
    { label: t('common.documentWorkbench.labels.mode'), value: modeLabel },
    { label: t('common.documentWorkbench.labels.status'), value: recordStatusLabel || '-' },
    { label: t('common.documentWorkbench.labels.rows'), value: totalDetailRows },
    { label: t('common.documentWorkbench.labels.editable'), value: yesNoLabel(!readonly, t) },
  ]
}

export const resolveDocumentWorkbenchWorkflowTitle = ({
  document,
  t,
}: {
  document?: AggregateDocumentResponse | null
  t: DocumentWorkbenchTranslateFn
}) => {
  return (
    document?.workflow?.instance?.title ||
    document?.workflow?.definition?.name ||
    t('common.documentWorkbench.sections.workflow')
  )
}

export const resolveDocumentWorkbenchWorkflowStatusLabel = (
  document?: AggregateDocumentResponse | null,
) => {
  if (!document) return '-'
  return String(document.workflow?.instance?.status || document.workflow?.definition?.status || '-')
}

export const buildDocumentWorkbenchWorkflowRows = ({
  document,
  t,
}: {
  document?: AggregateDocumentResponse | null
  t: DocumentWorkbenchTranslateFn
}): ObjectWorkspaceInfoRow[] => {
  if (!document) return []
  const definition = document.workflow?.definition
  const instance = document.workflow?.instance

  return [
    { label: t('common.documentWorkbench.labels.definition'), value: String(definition?.name || '-') },
    { label: t('common.documentWorkbench.labels.instance'), value: String(instance?.title || instance?.status || '-') },
    { label: t('common.documentWorkbench.labels.status'), value: String(instance?.status || definition?.status || '-') },
    { label: t('common.documentWorkbench.labels.published'), value: yesNoLabel(document.workflow?.hasPublishedDefinition, t) },
  ]
}

export const buildDocumentWorkbenchAuditRows = ({
  document,
  t,
}: {
  document?: AggregateDocumentResponse | null
  t: DocumentWorkbenchTranslateFn
}): ObjectWorkspaceInfoRow[] => {
  if (!document) return []
  const counts = document.audit?.counts
  return [
    { label: t('common.documentWorkbench.labels.activityLogs'), value: Number(counts?.activityLogs || 0) },
    { label: t('common.documentWorkbench.labels.workflowApprovals'), value: Number(counts?.workflowApprovals || 0) },
    { label: t('common.documentWorkbench.labels.workflowOperationLogs'), value: Number(counts?.workflowOperationLogs || 0) },
  ]
}

export const buildDocumentWorkbenchCapabilityItems = ({
  document,
  t,
}: {
  document?: AggregateDocumentResponse | null
  t: DocumentWorkbenchTranslateFn
}): DocumentWorkbenchCapabilityItem[] => {
  if (!document) return []
  const capabilities = document.capabilities
  return [
    {
      key: 'editMaster',
      label: `${t('common.documentWorkbench.capabilities.editMaster')}: ${yesNoLabel(capabilities.canEditMaster, t)}`,
      active: capabilities.canEditMaster,
    },
    {
      key: 'editDetails',
      label: `${t('common.documentWorkbench.capabilities.editDetails')}: ${yesNoLabel(capabilities.canEditDetails, t)}`,
      active: capabilities.canEditDetails,
    },
    {
      key: 'save',
      label: `${t('common.documentWorkbench.capabilities.save')}: ${yesNoLabel(capabilities.canSave, t)}`,
      active: capabilities.canSave,
    },
    {
      key: 'submit',
      label: `${t('common.documentWorkbench.capabilities.submit')}: ${yesNoLabel(capabilities.canSubmit, t)}`,
      active: capabilities.canSubmit,
    },
    {
      key: 'approve',
      label: `${t('common.documentWorkbench.capabilities.approve')}: ${yesNoLabel(capabilities.canApprove, t)}`,
      active: capabilities.canApprove,
    },
    {
      key: 'readonly',
      label: `${t('common.documentWorkbench.capabilities.readOnly')}: ${yesNoLabel(capabilities.readOnly, t)}`,
      active: capabilities.readOnly,
    },
  ]
}

export const buildDocumentWorkbenchDisposalBatchActions = ({
  objectCode,
  document,
  modelValue,
  readonly,
  recordStatusLabel,
  t,
}: {
  objectCode: string
  document?: AggregateDocumentResponse | null
  modelValue: Record<string, any>
  readonly: boolean
  recordStatusLabel: string
  t: DocumentWorkbenchTranslateFn
}): DisposalBatchActionDefinition[] => {
  if (
    objectCode !== 'DisposalRequest' ||
    !document ||
    readonly ||
    document.capabilities.canEditDetails !== true
  ) {
    return []
  }

  const summary = summarizeDisposalProgress(modelValue, document.aggregate)
  const actions: DisposalBatchActionDefinition[] = []

  if (recordStatusLabel === 'appraising') {
    actions.push(
      {
        key: 'applyAppraisalResult',
        label: t('common.documentWorkbench.batchTools.actions.applyAppraisalResult'),
        type: 'primary',
        count: summary.pendingAppraisalResult,
      },
      {
        key: 'copyNetValueToResidual',
        label: t('common.documentWorkbench.batchTools.actions.copyNetValueToResidual'),
        type: 'success',
        count: summary.pendingResidualValue,
      },
    )
  }

  if (recordStatusLabel === 'executing') {
    actions.push(
      {
        key: 'applyBuyerInfo',
        label: t('common.documentWorkbench.batchTools.actions.applyBuyerInfo'),
        type: 'primary',
        count: summary.pendingBuyerInfo,
      },
      {
        key: 'copyResidualToActual',
        label: t('common.documentWorkbench.batchTools.actions.copyResidualToActual'),
        type: 'success',
        count: summary.pendingActualResidual,
      },
    )
  }

  return actions
}

export const buildDocumentWorkbenchWorkflowActivityItems = ({
  document,
  locale,
  t,
}: {
  document?: AggregateDocumentResponse | null
  locale: string
  t: DocumentWorkbenchTranslateFn
}): DocumentWorkbenchWorkflowActivityItem[] => {
  const items = document?.workflow?.timeline || []
  return items.slice(0, WORKFLOW_ACTIVITY_LIMIT).map((item) => {
    const actorName = String(item.actorName || t('common.documentWorkbench.labels.systemActor'))
    const taskName = String(item.taskName || item.operationTypeDisplay || item.actionDisplay || '-')
    const description = String(item.comment || item.description || item.resultDisplay || '').trim()
    return {
      id: String(item.id || ''),
      title: String(item.title || item.actionDisplay || item.operationTypeDisplay || taskName || '-'),
      meta: `${actorName} | ${taskName}`,
      description: description || undefined,
      createdAt: formatTimelineDate(item.createdAt, locale),
    }
  })
}

export const buildDocumentWorkbenchTimelineEntries = ({
  objectCode,
  effectiveRecordId,
  document,
  sourceLabels,
}: {
  objectCode: string
  effectiveRecordId: string
  document?: AggregateDocumentResponse | null
  sourceLabels: Record<string, string>
}): ActivityLogEntry[] => {
  if (!document) return []
  return (document.timeline || []).map((entry) => {
    const normalizedSource = String(entry.source || '').trim()
    const action = String(entry.action || entry.operationType || normalizedSource || 'update')
    const actionLabel = String(
      entry.actionDisplay ||
      entry.operationTypeDisplay ||
      entry.title ||
      entry.action ||
      entry.operationType ||
      normalizedSource ||
      'update',
    )

    return {
      id: String(entry.id || ''),
      action,
      actionLabel,
      sourceCode: normalizedSource || undefined,
      sourceLabel: sourceLabels[normalizedSource] || undefined,
      objectCode,
      objectId: effectiveRecordId || undefined,
      recordLabel: document.context.recordLabel || undefined,
      userName: entry.actorName || undefined,
      createdAt: entry.createdAt || undefined,
      timestamp: entry.createdAt || undefined,
      description: String(
        entry.description ||
        entry.comment ||
        entry.resultDisplay ||
        entry.taskName ||
        '',
      ) || undefined,
      changes: Array.isArray(entry.changes)
        ? entry.changes.map((change) => ({
            fieldCode: String(change.fieldCode || ''),
            fieldLabel: String(change.fieldLabel || change.fieldCode || ''),
            oldValue: change.oldValue,
            newValue: change.newValue,
          }))
        : [],
    }
  })
}

export const shouldShowDocumentWorkbenchHeaderShell = ({
  statusActionCount,
  showObjectActions,
  effectiveRecordId,
  capabilityItems,
}: {
  statusActionCount: number
  showObjectActions: boolean
  effectiveRecordId: string
  capabilityItems: DocumentWorkbenchCapabilityItem[]
}) => {
  return statusActionCount > 0 || (showObjectActions && !!effectiveRecordId) || capabilityItems.length > 0
}
