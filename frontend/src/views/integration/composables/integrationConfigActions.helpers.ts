import type { Ref } from 'vue'
import type { IntegrationConfig, IntegrationFormData } from '@/types/integration'

interface IntegrationActionResult {
  success: boolean
  message?: string
}

interface LoadingGuardOptions {
  skipIfLoading?: boolean
}

type IntegrationActionOutcome = 'success' | 'failure' | 'error' | 'skipped'

interface IntegrationActionMessages {
  successFallback: string
  failureFallback: string
  errorFallback: string
}

interface IntegrationActionNotifier {
  success: (message: string) => void
  warning: (message: string) => void
  error: (message: string) => void
}

interface RunIntegrationActionOptions<T extends IntegrationActionResult> {
  invoke: () => Promise<T>
  messages: IntegrationActionMessages
  notifier: IntegrationActionNotifier
  onSuccess?: () => void
  onFailure?: () => void
  onError?: () => void
}

interface RunFlagIntegrationActionOptions<T extends IntegrationActionResult> extends RunIntegrationActionOptions<T> {
  loadingFlag: Ref<boolean>
  loadingOptions?: LoadingGuardOptions
}

interface RunRowIntegrationActionOptions<T extends IntegrationActionResult> extends RunIntegrationActionOptions<T> {
  loadingMap: Ref<Record<string, boolean>>
  rowId: string
  loadingOptions?: LoadingGuardOptions
}

interface IntegrationActionMessageOptions {
  result: IntegrationActionResult
  successFallback: string
  failureFallback: string
  onSuccess: (message: string) => void
  onFailure: (message: string) => void
}

export const buildIntegrationFormDataFromConfig = (row: IntegrationConfig): IntegrationFormData => ({
  systemType: row.systemType,
  systemName: row.systemName,
  isEnabled: row.isEnabled,
  enabledModules: row.enabledModules || [],
  connectionConfig: {
    apiUrl: '',
    apiKey: '',
    apiSecret: '',
    timeout: 30,
    ...(row.connectionConfig || {})
  },
  syncConfig: {
    autoSync: false,
    interval: 60,
    ...(row.syncConfig || {})
  }
})

export const withFlagLoading = async <T>(
  flag: Ref<boolean>,
  runner: () => Promise<T>,
  options: LoadingGuardOptions = {}
): Promise<T | undefined> => {
  const { skipIfLoading = true } = options
  if (skipIfLoading && flag.value) {
    return undefined
  }

  flag.value = true
  try {
    return await runner()
  } finally {
    flag.value = false
  }
}

export const withRowLoading = async <T>(
  loadingMap: Ref<Record<string, boolean>>,
  rowId: string,
  runner: () => Promise<T>,
  options: LoadingGuardOptions = {}
): Promise<T | undefined> => {
  const { skipIfLoading = true } = options
  if (skipIfLoading && loadingMap.value[rowId]) {
    return undefined
  }

  loadingMap.value[rowId] = true
  try {
    return await runner()
  } finally {
    loadingMap.value[rowId] = false
  }
}

export const emitIntegrationActionMessage = ({
  result,
  successFallback,
  failureFallback,
  onSuccess,
  onFailure
}: IntegrationActionMessageOptions): boolean => {
  if (result.success) {
    onSuccess(result.message || successFallback)
    return true
  }

  onFailure(result.message || failureFallback)
  return false
}

export const runIntegrationAction = async <T extends IntegrationActionResult>({
  invoke,
  messages,
  notifier,
  onSuccess,
  onFailure,
  onError
}: RunIntegrationActionOptions<T>): Promise<IntegrationActionOutcome> => {
  try {
    const result = await invoke()
    const succeeded = emitIntegrationActionMessage({
      result,
      successFallback: messages.successFallback,
      failureFallback: messages.failureFallback,
      onSuccess: notifier.success,
      onFailure: notifier.warning
    })
    if (succeeded) {
      onSuccess?.()
      return 'success'
    }
    onFailure?.()
    return 'failure'
  } catch {
    notifier.error(messages.errorFallback)
    onError?.()
    return 'error'
  }
}

export const runFlagIntegrationAction = async <T extends IntegrationActionResult>({
  loadingFlag,
  loadingOptions,
  ...options
}: RunFlagIntegrationActionOptions<T>): Promise<IntegrationActionOutcome> => {
  const result = await withFlagLoading(
    loadingFlag,
    async () => runIntegrationAction(options),
    loadingOptions
  )
  return result ?? 'skipped'
}

export const runRowIntegrationAction = async <T extends IntegrationActionResult>({
  loadingMap,
  rowId,
  loadingOptions,
  ...options
}: RunRowIntegrationActionOptions<T>): Promise<IntegrationActionOutcome> => {
  const result = await withRowLoading(
    loadingMap,
    rowId,
    async () => runIntegrationAction(options),
    loadingOptions
  )
  return result ?? 'skipped'
}
