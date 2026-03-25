import type { Ref } from 'vue'

export interface ActionResultLike {
  success: boolean
  message?: string
}

export interface LoadingGuardOptions {
  skipIfLoading?: boolean
}

export type ActionOutcome = 'success' | 'failure' | 'error' | 'skipped'

export interface ActionMessages {
  successFallback: string
  failureFallback: string
  errorFallback: string
}

export interface ActionNotifier {
  success: (message: string) => void
  warning: (message: string) => void
  error: (message: string) => void
}

export interface ActionMessageOptions<T extends ActionResultLike> {
  result: T
  successFallback: string
  failureFallback: string
  onSuccess: (message: string) => void
  onFailure: (message: string) => void
}

export interface RunActionOptions<T extends ActionResultLike> {
  invoke: () => Promise<T>
  messages: ActionMessages
  notifier: ActionNotifier
  onSuccess?: (result: T) => void | Promise<void>
  onFailure?: (result: T) => void | Promise<void>
  onError?: (error: unknown) => void | Promise<void>
}

export interface RunFlagActionOptions<T extends ActionResultLike> extends RunActionOptions<T> {
  loadingFlag: Ref<boolean>
  loadingOptions?: LoadingGuardOptions
}

export interface RunRowActionOptions<T extends ActionResultLike> extends RunActionOptions<T> {
  loadingMap: Ref<Record<string, boolean>>
  rowId: string
  loadingOptions?: LoadingGuardOptions
}

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

export const emitActionResultMessage = <T extends ActionResultLike>({
  result,
  successFallback,
  failureFallback,
  onSuccess,
  onFailure
}: ActionMessageOptions<T>): boolean => {
  if (result.success) {
    onSuccess(result.message || successFallback)
    return true
  }

  onFailure(result.message || failureFallback)
  return false
}

export const runAction = async <T extends ActionResultLike>({
  invoke,
  messages,
  notifier,
  onSuccess,
  onFailure,
  onError
}: RunActionOptions<T>): Promise<ActionOutcome> => {
  try {
    const result = await invoke()
    const succeeded = emitActionResultMessage({
      result,
      successFallback: messages.successFallback,
      failureFallback: messages.failureFallback,
      onSuccess: notifier.success,
      onFailure: notifier.warning
    })
    if (succeeded) {
      await onSuccess?.(result)
      return 'success'
    }
    await onFailure?.(result)
    return 'failure'
  } catch (error) {
    notifier.error(messages.errorFallback)
    await onError?.(error)
    return 'error'
  }
}

export const runFlagAction = async <T extends ActionResultLike>({
  loadingFlag,
  loadingOptions,
  ...options
}: RunFlagActionOptions<T>): Promise<ActionOutcome> => {
  const result = await withFlagLoading(
    loadingFlag,
    async () => runAction(options),
    loadingOptions
  )
  return result ?? 'skipped'
}

export const runRowAction = async <T extends ActionResultLike>({
  loadingMap,
  rowId,
  loadingOptions,
  ...options
}: RunRowActionOptions<T>): Promise<ActionOutcome> => {
  const result = await withRowLoading(
    loadingMap,
    rowId,
    async () => runAction(options),
    loadingOptions
  )
  return result ?? 'skipped'
}
