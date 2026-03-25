import { ElMessage, ElMessageBox } from 'element-plus'
import type { AggregateDocumentResponse } from '@/types/runtime'
import {
  applyDisposalBatchAppraisalResult,
  applyDisposalBatchBuyerInfo,
  copyDisposalNetValueToResidual,
  copyDisposalResidualToActual,
} from '@/components/common/documentWorkbenchModel'
import type {
  DisposalBatchActionDefinition,
  DocumentWorkbenchTranslateFn,
} from '@/components/common/documentWorkbenchViewModel'

interface UseDocumentWorkbenchBatchActionsOptions {
  getDocument: () => AggregateDocumentResponse | null | undefined
  getModelValue: () => Record<string, any>
  emitModelValue: (value: Record<string, any>) => void
  t: DocumentWorkbenchTranslateFn
}

export function useDocumentWorkbenchBatchActions({
  getDocument,
  getModelValue,
  emitModelValue,
  t,
}: UseDocumentWorkbenchBatchActionsOptions) {
  const promptBatchValue = async ({
    titleKey,
    messageKey,
    placeholderKey,
  }: {
    titleKey: string
    messageKey: string
    placeholderKey: string
  }) => {
    try {
      const { value } = await ElMessageBox.prompt(
        t(messageKey),
        t(titleKey),
        {
          inputType: 'textarea',
          inputPlaceholder: t(placeholderKey),
          inputValidator: (candidate) => {
            if (String(candidate || '').trim()) {
              return true
            }
            return t('common.messages.formValidationFailed')
          },
        },
      )
      return String(value || '').trim()
    } catch {
      return ''
    }
  }

  const applyDisposalBatchResult = (
    result: {
      modelValue: Record<string, any>
      changedRows: number
    },
    successKey: string,
  ) => {
    if (result.changedRows <= 0) {
      ElMessage.info(t('common.documentWorkbench.batchTools.noChanges'))
      return
    }

    emitModelValue(result.modelValue)
    ElMessage.success(t(successKey, { count: result.changedRows }))
  }

  const handleDisposalBatchAction = async (
    actionKey: DisposalBatchActionDefinition['key'],
  ) => {
    const document = getDocument()
    if (!document) return

    switch (actionKey) {
      case 'applyAppraisalResult': {
        const appraisalResult = await promptBatchValue({
          titleKey: 'common.documentWorkbench.batchTools.prompts.appraisalResult.title',
          messageKey: 'common.documentWorkbench.batchTools.prompts.appraisalResult.message',
          placeholderKey: 'common.documentWorkbench.batchTools.prompts.appraisalResult.placeholder',
        })
        if (!appraisalResult) return
        applyDisposalBatchResult(
          applyDisposalBatchAppraisalResult({
            modelValue: getModelValue(),
            aggregate: document.aggregate,
            appraisalResult,
          }),
          'common.documentWorkbench.batchTools.success.appraisalResult',
        )
        return
      }
      case 'copyNetValueToResidual':
        applyDisposalBatchResult(
          copyDisposalNetValueToResidual({
            modelValue: getModelValue(),
            aggregate: document.aggregate,
          }),
          'common.documentWorkbench.batchTools.success.copyNetValueToResidual',
        )
        return
      case 'applyBuyerInfo': {
        const buyerInfo = await promptBatchValue({
          titleKey: 'common.documentWorkbench.batchTools.prompts.buyerInfo.title',
          messageKey: 'common.documentWorkbench.batchTools.prompts.buyerInfo.message',
          placeholderKey: 'common.documentWorkbench.batchTools.prompts.buyerInfo.placeholder',
        })
        if (!buyerInfo) return
        applyDisposalBatchResult(
          applyDisposalBatchBuyerInfo({
            modelValue: getModelValue(),
            aggregate: document.aggregate,
            buyerInfo,
          }),
          'common.documentWorkbench.batchTools.success.buyerInfo',
        )
        return
      }
      case 'copyResidualToActual':
        applyDisposalBatchResult(
          copyDisposalResidualToActual({
            modelValue: getModelValue(),
            aggregate: document.aggregate,
          }),
          'common.documentWorkbench.batchTools.success.copyResidualToActual',
        )
    }
  }

  return {
    handleDisposalBatchAction,
  }
}
