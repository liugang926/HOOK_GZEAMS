import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'

import type { WorkbenchAction, WorkbenchPrompt } from './workbenchHelpers'
import {
  buildWorkbenchActionPayload,
  executeWorkbenchAction,
  resolveWorkbenchConfirmMessage,
  resolveWorkbenchPrompt,
  resolveWorkbenchSyncTaskId,
} from './workbenchHelpers'

interface SyncTaskState {
  syncTaskId: string
  status: string
  statusDisplay?: string
  done: boolean
}

interface UseWorkbenchActionExecutorOptions {
  objectCode: string
  recordId: string
  taskStateKey?: string
  startTaskPolling?: (
    key: string,
    syncTaskId: string,
    options?: { onDone?: (state: SyncTaskState) => void | Promise<void> }
  ) => void
  onRefreshRequested?: () => void
}

export const useWorkbenchActionExecutor = ({
  objectCode,
  recordId,
  taskStateKey = '',
  startTaskPolling,
  onRefreshRequested,
}: UseWorkbenchActionExecutorOptions) => {
  const { t, te } = useI18n()
  const loadingActionCode = ref<string | null>(null)
  const promptVisible = ref(false)
  const activeAction = ref<WorkbenchAction | null>(null)
  const promptValues = ref<Record<string, unknown>>({})

  const activePrompt = computed<WorkbenchPrompt | null>(() => {
    if (!activeAction.value) return null
    return resolveWorkbenchPrompt(activeAction.value, t, te)
  })

  const buildPromptDefaults = (prompt: WorkbenchPrompt | null) => {
    const fields = prompt?.fields || []
    return fields.reduce<Record<string, unknown>>((accumulator, field) => {
      accumulator[field.key] = field.defaultValue ?? ''
      return accumulator
    }, {})
  }

  const setPromptValue = (key: string, value: unknown) => {
    promptValues.value = {
      ...promptValues.value,
      [key]: value,
    }
  }

  const resetPromptState = () => {
    promptVisible.value = false
    activeAction.value = null
    promptValues.value = {}
  }

  const closePromptDialog = () => {
    if (loadingActionCode.value) return
    resetPromptState()
  }

  const validatePromptFields = () => {
    const fields = activePrompt.value?.fields || []
    for (const field of fields) {
      if (!field.required) continue
      const value = promptValues.value[field.key]
      if (typeof value === 'string' && value.trim()) continue
      if (value !== null && value !== undefined && value !== '') continue
      ElMessage.warning(t('common.messages.formValidationFailed'))
      return false
    }
    return true
  }

  const executeAction = async (action: WorkbenchAction, prompt: WorkbenchPrompt | null = null) => {
    const confirmMessage = resolveWorkbenchConfirmMessage(action, t, te)
    if (confirmMessage) {
      try {
        await ElMessageBox.confirm(
          confirmMessage,
          t('common.dialog.confirmTitle') || t('common.messages.confirmTitle'),
          {
            type: 'warning',
            confirmButtonText: t('common.actions.confirm'),
            cancelButtonText: t('common.actions.cancel'),
          },
        )
      } catch {
        return
      }
    }

    loadingActionCode.value = action.code
    try {
      const result = await executeWorkbenchAction({
        action,
        objectCode,
        recordId,
        data: buildWorkbenchActionPayload(action, promptValues.value, prompt),
      })

      const syncTaskId = resolveWorkbenchSyncTaskId(result.data)
      const normalizedTaskStateKey = String(taskStateKey || `${objectCode}:${recordId}`).trim()

      if (syncTaskId && startTaskPolling && normalizedTaskStateKey) {
        startTaskPolling(normalizedTaskStateKey, syncTaskId, {
          onDone: async () => {
            onRefreshRequested?.()
          },
        })
      }

      ElMessage.success(result.message || t('common.messages.operationSuccess'))
      onRefreshRequested?.()
      if (activeAction.value?.code === action.code) {
        resetPromptState()
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : t('common.messages.operationFailed')
      ElMessage.error(message)
    } finally {
      loadingActionCode.value = null
    }
  }

  const confirmPromptAction = async () => {
    if (!activeAction.value) return
    if (!validatePromptFields()) return
    await executeAction(activeAction.value, activePrompt.value)
  }

  const handleAction = async (action: WorkbenchAction) => {
    const prompt = resolveWorkbenchPrompt(action, t, te)
    if (prompt?.fields.length) {
      activeAction.value = action
      promptValues.value = buildPromptDefaults(prompt)
      promptVisible.value = true
      return
    }

    await executeAction(action, prompt)
  }

  return {
    activeAction,
    activePrompt,
    closePromptDialog,
    confirmPromptAction,
    handleAction,
    loadingActionCode,
    promptValues,
    promptVisible,
    setPromptValue,
  }
}
