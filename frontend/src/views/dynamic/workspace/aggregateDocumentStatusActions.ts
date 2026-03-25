import type { StatusAction, StatusActionExecutionContext } from '@/components/common/StatusActionBar.vue'
import type { AggregateDocumentResponse } from '@/types/runtime'
import request from '@/utils/request'

interface AggregateDocumentStatusActionParams {
  objectCode: string
  recordId: string
  document?: AggregateDocumentResponse | null
  t: (key: string) => string
}

type ActionContextValues = Record<string, unknown>

const matchesStatus = (...allowedStatuses: string[]) => {
  const normalized = allowedStatuses.map(status => String(status || '').trim())
  return (status: string) => normalized.includes(String(status || '').trim())
}

const buildObjectActionUrl = (objectCode: string, recordId: string, actionPath: string) => {
  const safeObjectCode = encodeURIComponent(String(objectCode || '').trim())
  const safeRecordId = encodeURIComponent(String(recordId || '').trim())
  const safeActionPath = String(actionPath || '').replace(/^\/+/, '')
  return `/system/objects/${safeObjectCode}/${safeRecordId}/${safeActionPath}`
}

const postObjectAction = (
  objectCode: string,
  recordId: string,
  actionPath: string,
  payload?: Record<string, unknown>,
) => {
  return request.post(buildObjectActionUrl(objectCode, recordId, actionPath), payload)
}

const readStringValue = (values: ActionContextValues | undefined, key: string) => {
  return String(values?.[key] ?? '').trim()
}

const canSubmitDocument = (document?: AggregateDocumentResponse | null) => {
  return document?.capabilities.canSubmit === true
}

const canApproveDocument = (document?: AggregateDocumentResponse | null) => {
  return document?.capabilities.canApprove === true
}

const defineStatusAction = (action: StatusAction): StatusAction => action

const buildCommentPrompt = (t: AggregateDocumentStatusActionParams['t'], actionKey: 'approve' | 'approveFrom' | 'approveTo') => ({
  title: t(`common.documentWorkbench.prompts.${actionKey}.title`),
  message: t(`common.documentWorkbench.prompts.${actionKey}.message`),
  fields: [
    {
      key: 'comment',
      label: t('common.documentWorkbench.prompts.fields.comment'),
      type: 'textarea' as const,
      rows: 4,
      placeholder: t('common.documentWorkbench.prompts.placeholders.comment'),
    },
  ],
})

const buildRejectPrompt = (t: AggregateDocumentStatusActionParams['t']) => ({
  title: t('common.documentWorkbench.prompts.reject.title'),
  message: t('common.documentWorkbench.prompts.reject.message'),
  fields: [
    {
      key: 'reason',
      label: t('common.documentWorkbench.prompts.fields.reason'),
      type: 'textarea' as const,
      rows: 4,
      required: true,
      placeholder: t('common.documentWorkbench.prompts.placeholders.reason'),
    },
  ],
})

const buildLoanReturnPrompt = (t: AggregateDocumentStatusActionParams['t']) => ({
  title: t('common.documentWorkbench.prompts.confirmReturn.title'),
  message: t('common.documentWorkbench.prompts.confirmReturn.message'),
  fields: [
    {
      key: 'condition',
      label: t('common.documentWorkbench.prompts.fields.condition'),
      type: 'select' as const,
      required: true,
      defaultValue: 'good',
      options: [
        { value: 'good', label: t('common.documentWorkbench.prompts.conditionOptions.good') },
        { value: 'minor_damage', label: t('common.documentWorkbench.prompts.conditionOptions.minorDamage') },
        { value: 'major_damage', label: t('common.documentWorkbench.prompts.conditionOptions.majorDamage') },
        { value: 'lost', label: t('common.documentWorkbench.prompts.conditionOptions.lost') },
      ],
    },
    {
      key: 'comment',
      label: t('common.documentWorkbench.prompts.fields.comment'),
      type: 'textarea' as const,
      rows: 4,
      placeholder: t('common.documentWorkbench.prompts.placeholders.comment'),
    },
  ],
})

const buildInspectionPrompt = (
  t: AggregateDocumentStatusActionParams['t'],
  actionKey: 'passInspection' | 'rejectInspection',
  required = false,
) => ({
  title: t(`common.documentWorkbench.prompts.${actionKey}.title`),
  message: t(`common.documentWorkbench.prompts.${actionKey}.message`),
  fields: [
    {
      key: 'result',
      label: t('common.documentWorkbench.prompts.fields.result'),
      type: 'textarea' as const,
      rows: 4,
      required,
      placeholder: t('common.documentWorkbench.prompts.placeholders.result'),
    },
  ],
})

export const buildAggregateDocumentStatusActions = ({
  objectCode,
  recordId,
  document,
  t,
}: AggregateDocumentStatusActionParams): StatusAction[] => {
  const normalizedObjectCode = String(objectCode || '').trim()
  const normalizedRecordId = String(recordId || document?.context.recordId || '').trim()

  if (!normalizedObjectCode || !normalizedRecordId || !document) {
    return []
  }

  const submitAction: StatusAction = {
    key: 'submit',
    label: t('common.documentWorkbench.actions.submit'),
    type: 'primary',
    confirmMessage: t('common.documentWorkbench.confirmations.submit'),
    apiCall: () => postObjectAction(normalizedObjectCode, normalizedRecordId, 'submit/'),
    visibleWhen: matchesStatus('draft'),
  }

  const approveAction = (actionPath = 'approve/'): StatusAction => ({
    key: 'approve',
    label: t('common.documentWorkbench.actions.approve'),
    type: 'success',
    prompt: buildCommentPrompt(t, 'approve'),
    apiCall: (context?: StatusActionExecutionContext) => postObjectAction(normalizedObjectCode, normalizedRecordId, actionPath, {
      approval: 'approved',
      comment: readStringValue(context?.values, 'comment'),
    }),
    visibleWhen: matchesStatus('pending'),
  })

  const rejectAction = (
    actionPath = 'approve/',
    payloadBuilder?: (values: ActionContextValues | undefined) => Record<string, unknown>,
  ): StatusAction => ({
    key: 'reject',
    label: t('common.documentWorkbench.actions.reject'),
    type: 'danger',
    prompt: buildRejectPrompt(t),
    apiCall: (context?: StatusActionExecutionContext) => postObjectAction(
      normalizedObjectCode,
      normalizedRecordId,
      actionPath,
      payloadBuilder
        ? payloadBuilder(context?.values)
        : {
            approval: 'rejected',
            comment: readStringValue(context?.values, 'reason'),
          },
    ),
    visibleWhen: matchesStatus('pending'),
  })

  switch (normalizedObjectCode) {
    case 'PurchaseRequest':
      return [
        ...(canSubmitDocument(document) ? [submitAction] : []),
        ...(canApproveDocument(document) ? [
          defineStatusAction({
            key: 'approve',
            label: t('common.documentWorkbench.actions.approve'),
            type: 'success',
            prompt: buildCommentPrompt(t, 'approve'),
            apiCall: (context?: StatusActionExecutionContext) => postObjectAction(normalizedObjectCode, normalizedRecordId, 'approve/', {
              decision: 'approved',
              comment: readStringValue(context?.values, 'comment'),
            }),
            visibleWhen: matchesStatus('submitted'),
          }),
          defineStatusAction({
            key: 'reject',
            label: t('common.documentWorkbench.actions.reject'),
            type: 'danger',
            prompt: buildRejectPrompt(t),
            apiCall: (context?: StatusActionExecutionContext) => postObjectAction(normalizedObjectCode, normalizedRecordId, 'approve/', {
              decision: 'rejected',
              comment: readStringValue(context?.values, 'reason'),
            }),
            visibleWhen: matchesStatus('submitted'),
          }),
        ] : []),
        defineStatusAction({
          key: 'complete',
          label: t('common.documentWorkbench.actions.complete'),
          type: 'success',
          confirmMessage: t('common.documentWorkbench.confirmations.complete'),
          apiCall: () => postObjectAction(normalizedObjectCode, normalizedRecordId, 'complete/'),
          visibleWhen: matchesStatus('processing'),
        }),
        defineStatusAction({
          key: 'cancel',
          label: t('common.documentWorkbench.actions.cancel'),
          type: 'default',
          prompt: buildRejectPrompt(t),
          apiCall: (context?: StatusActionExecutionContext) => postObjectAction(normalizedObjectCode, normalizedRecordId, 'cancel/', {
            reason: readStringValue(context?.values, 'reason'),
          }),
          visibleWhen: matchesStatus('draft', 'submitted'),
        }),
      ]

    case 'AssetPickup':
      return [
        ...(canSubmitDocument(document) ? [submitAction] : []),
        ...(canApproveDocument(document) ? [
          approveAction(),
          rejectAction(),
        ] : []),
        defineStatusAction({
          key: 'complete',
          label: t('common.documentWorkbench.actions.complete'),
          type: 'success',
          confirmMessage: t('common.documentWorkbench.confirmations.complete'),
          apiCall: () => postObjectAction(normalizedObjectCode, normalizedRecordId, 'complete/'),
          visibleWhen: matchesStatus('approved'),
        }),
        defineStatusAction({
          key: 'cancel',
          label: t('common.documentWorkbench.actions.cancel'),
          type: 'default',
          confirmMessage: t('common.documentWorkbench.confirmations.cancel'),
          confirmType: 'warning',
          apiCall: () => postObjectAction(normalizedObjectCode, normalizedRecordId, 'cancel/'),
          visibleWhen: matchesStatus('draft', 'pending'),
        }),
      ]

    case 'AssetTransfer':
      return [
        ...(canSubmitDocument(document) ? [submitAction] : []),
        ...(canApproveDocument(document) ? [
          defineStatusAction({
            key: 'approveFrom',
            label: t('common.documentWorkbench.actions.approveFrom'),
            type: 'primary',
            prompt: buildCommentPrompt(t, 'approveFrom'),
            apiCall: (context?: StatusActionExecutionContext) => postObjectAction(normalizedObjectCode, normalizedRecordId, 'approve-from/', {
              comment: readStringValue(context?.values, 'comment'),
            }),
            visibleWhen: matchesStatus('pending'),
          }),
          defineStatusAction({
            key: 'approveTo',
            label: t('common.documentWorkbench.actions.approveTo'),
            type: 'success',
            prompt: buildCommentPrompt(t, 'approveTo'),
            apiCall: (context?: StatusActionExecutionContext) => postObjectAction(normalizedObjectCode, normalizedRecordId, 'approve-to/', {
              comment: readStringValue(context?.values, 'comment'),
            }),
            visibleWhen: matchesStatus('out_approved'),
          }),
        ] : []),
        defineStatusAction({
          key: 'complete',
          label: t('common.documentWorkbench.actions.complete'),
          type: 'success',
          confirmMessage: t('common.documentWorkbench.confirmations.complete'),
          apiCall: () => postObjectAction(normalizedObjectCode, normalizedRecordId, 'complete/'),
          visibleWhen: matchesStatus('approved'),
        }),
      ]

    case 'AssetReturn':
      return canApproveDocument(document)
        ? [
            defineStatusAction({
              key: 'confirmReturn',
              label: t('common.documentWorkbench.actions.confirmReturn'),
              type: 'success',
              confirmMessage: t('common.documentWorkbench.confirmations.confirmReturn'),
              apiCall: () => postObjectAction(normalizedObjectCode, normalizedRecordId, 'confirm/'),
              visibleWhen: matchesStatus('pending'),
            }),
            rejectAction('reject/', (values) => ({
              reason: readStringValue(values, 'reason'),
            })),
          ]
        : []

    case 'AssetLoan':
      return [
        ...(canApproveDocument(document) ? [
          approveAction(),
          rejectAction(),
        ] : []),
        defineStatusAction({
          key: 'confirmBorrow',
          label: t('common.documentWorkbench.actions.confirmBorrow'),
          type: 'primary',
          confirmMessage: t('common.documentWorkbench.confirmations.confirmBorrow'),
          apiCall: () => postObjectAction(normalizedObjectCode, normalizedRecordId, 'confirm-borrow/'),
          visibleWhen: matchesStatus('approved'),
        }),
        defineStatusAction({
          key: 'confirmReturn',
          label: t('common.documentWorkbench.actions.confirmReturn'),
          type: 'success',
          prompt: buildLoanReturnPrompt(t),
          apiCall: (context?: StatusActionExecutionContext) => postObjectAction(normalizedObjectCode, normalizedRecordId, 'confirm-return/', {
            condition: readStringValue(context?.values, 'condition') || 'good',
            comment: readStringValue(context?.values, 'comment'),
          }),
          visibleWhen: matchesStatus('borrowed', 'overdue'),
        }),
      ]

    case 'AssetReceipt':
      return [
        ...(canSubmitDocument(document) ? [
          defineStatusAction({
            key: 'submitInspection',
            label: t('common.documentWorkbench.actions.submitInspection'),
            type: 'primary',
            confirmMessage: t('common.documentWorkbench.confirmations.submitInspection'),
            apiCall: () => postObjectAction(normalizedObjectCode, normalizedRecordId, 'submit_inspection/'),
            visibleWhen: matchesStatus('draft', 'rejected'),
          }),
        ] : []),
        ...(canApproveDocument(document) ? [
          defineStatusAction({
            key: 'passInspection',
            label: t('common.documentWorkbench.actions.passInspection'),
            type: 'success',
            prompt: buildInspectionPrompt(t, 'passInspection'),
            apiCall: (context?: StatusActionExecutionContext) => postObjectAction(normalizedObjectCode, normalizedRecordId, 'inspect/', {
              result: readStringValue(context?.values, 'result'),
              passed: true,
            }),
            visibleWhen: matchesStatus('inspecting'),
          }),
          defineStatusAction({
            key: 'rejectInspection',
            label: t('common.documentWorkbench.actions.rejectInspection'),
            type: 'danger',
            prompt: buildInspectionPrompt(t, 'rejectInspection', true),
            apiCall: (context?: StatusActionExecutionContext) => postObjectAction(normalizedObjectCode, normalizedRecordId, 'inspect/', {
              result: readStringValue(context?.values, 'result'),
              passed: false,
            }),
            visibleWhen: matchesStatus('inspecting'),
          }),
        ] : []),
        defineStatusAction({
          key: 'cancel',
          label: t('common.documentWorkbench.actions.cancel'),
          type: 'default',
          confirmMessage: t('common.documentWorkbench.confirmations.cancel'),
          confirmType: 'warning',
          apiCall: () => postObjectAction(normalizedObjectCode, normalizedRecordId, 'cancel/'),
          visibleWhen: matchesStatus('draft', 'rejected', 'inspecting'),
        }),
      ]

    case 'DisposalRequest':
      return [
        ...(canSubmitDocument(document) ? [
          defineStatusAction({
            key: 'submit',
            label: t('common.documentWorkbench.actions.submit'),
            type: 'primary',
            confirmMessage: t('common.documentWorkbench.confirmations.submit'),
            apiCall: () => postObjectAction(normalizedObjectCode, normalizedRecordId, 'submit/'),
            visibleWhen: matchesStatus('draft', 'rejected'),
          }),
        ] : []),
        defineStatusAction({
          key: 'startAppraisal',
          label: t('common.documentWorkbench.actions.startAppraisal'),
          type: 'warning',
          confirmMessage: t('common.documentWorkbench.confirmations.startAppraisal'),
          apiCall: () => postObjectAction(normalizedObjectCode, normalizedRecordId, 'start_appraisal/'),
          visibleWhen: matchesStatus('submitted'),
        }),
        ...(canApproveDocument(document) ? [
          defineStatusAction({
            key: 'approve',
            label: t('common.documentWorkbench.actions.approve'),
            type: 'success',
            prompt: buildCommentPrompt(t, 'approve'),
            apiCall: (context?: StatusActionExecutionContext) => postObjectAction(normalizedObjectCode, normalizedRecordId, 'approve/', {
              decision: 'approved',
              comment: readStringValue(context?.values, 'comment'),
            }),
            visibleWhen: matchesStatus('appraising'),
          }),
          defineStatusAction({
            key: 'reject',
            label: t('common.documentWorkbench.actions.reject'),
            type: 'danger',
            prompt: buildRejectPrompt(t),
            apiCall: (context?: StatusActionExecutionContext) => postObjectAction(normalizedObjectCode, normalizedRecordId, 'approve/', {
              decision: 'rejected',
              comment: readStringValue(context?.values, 'reason'),
            }),
            visibleWhen: matchesStatus('submitted', 'appraising'),
          }),
        ] : []),
        defineStatusAction({
          key: 'startExecution',
          label: t('common.documentWorkbench.actions.startExecution'),
          type: 'primary',
          confirmMessage: t('common.documentWorkbench.confirmations.startExecution'),
          apiCall: () => postObjectAction(normalizedObjectCode, normalizedRecordId, 'start_execution/'),
          visibleWhen: matchesStatus('approved'),
        }),
        defineStatusAction({
          key: 'complete',
          label: t('common.documentWorkbench.actions.complete'),
          type: 'success',
          confirmMessage: t('common.documentWorkbench.confirmations.complete'),
          apiCall: () => postObjectAction(normalizedObjectCode, normalizedRecordId, 'complete/'),
          visibleWhen: matchesStatus('executing'),
        }),
        defineStatusAction({
          key: 'cancel',
          label: t('common.documentWorkbench.actions.cancel'),
          type: 'default',
          prompt: buildRejectPrompt(t),
          apiCall: (context?: StatusActionExecutionContext) => postObjectAction(normalizedObjectCode, normalizedRecordId, 'cancel/', {
            reason: readStringValue(context?.values, 'reason'),
          }),
          visibleWhen: matchesStatus('draft', 'rejected', 'submitted', 'appraising', 'approved', 'executing'),
        }),
      ]

    default:
      return []
  }
}
