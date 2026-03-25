import { ElLoading, ElMessage } from 'element-plus'

import i18n from '@/locales'
import { getErrorMessage } from '@/utils/errorHandler'

type LoadingServiceInstance = ReturnType<typeof ElLoading.service>

export interface LoadingStateOptions {
  text?: string
  target?: string | HTMLElement
  lock?: boolean
  fullscreen?: boolean
  background?: string
}

export interface EmptyStateConfig {
  type: 'empty' | 'search' | 'error'
  title: string
  description: string
  actionText?: string
}

export interface FeedbackTaskOptions extends LoadingStateOptions {
  successMessage?: string
  successParams?: Record<string, unknown>
  fallbackErrorKey?: string
  showSuccess?: boolean
  showError?: boolean
}

const translate = (messageOrKey?: string, params?: Record<string, unknown>, fallbackKey = 'common.messages.operationSuccess'): string => {
  const key = messageOrKey || fallbackKey
  return i18n.global.te(key) ? i18n.global.t(key, params || {}) : key
}

export function createLoadingController(baseOptions: LoadingStateOptions = {}) {
  let instance: LoadingServiceInstance | null = null
  let loadingCount = 0

  const start = (options: LoadingStateOptions = {}) => {
    loadingCount += 1
    if (!instance) {
      instance = ElLoading.service({
        lock: true,
        text: translate(options.text ?? baseOptions.text, undefined, 'common.messages.loading'),
        background: 'rgba(255, 255, 255, 0.72)',
        ...baseOptions,
        ...options,
      })
    }
    return instance
  }

  const stop = () => {
    if (loadingCount > 0) {
      loadingCount -= 1
    }
    if (loadingCount === 0 && instance) {
      instance.close()
      instance = null
    }
  }

  const withLoading = async <T>(
    task: Promise<T> | (() => Promise<T>),
    options: LoadingStateOptions = {},
  ): Promise<T> => {
    start(options)
    try {
      return typeof task === 'function' ? await task() : await task
    } finally {
      stop()
    }
  }

  return {
    start,
    stop,
    withLoading,
    isLoading: () => loadingCount > 0,
  }
}

export function resolveUxErrorMessage(
  error: unknown,
  fallbackKey = 'common.messages.operationFailed',
): string {
  if (typeof error === 'string' && error.trim()) {
    return error.trim()
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message
  }

  const message = getErrorMessage(error)
  if (message && message.trim()) {
    return message
  }

  return translate(fallbackKey, undefined, fallbackKey)
}

export function showUxError(
  error: unknown,
  fallbackKey = 'common.messages.operationFailed',
): string {
  const message = resolveUxErrorMessage(error, fallbackKey)
  ElMessage.error(message)
  return message
}

export function showUxSuccess(
  messageOrKey = 'common.messages.operationSuccess',
  params?: Record<string, unknown>,
): string {
  const message = translate(messageOrKey, params, 'common.messages.operationSuccess')
  ElMessage.success(message)
  return message
}

export function createEmptyState(
  type: EmptyStateConfig['type'] = 'empty',
  overrides: Partial<EmptyStateConfig> = {},
): EmptyStateConfig {
  const defaults: Record<EmptyStateConfig['type'], EmptyStateConfig> = {
    empty: {
      type: 'empty',
      title: translate('common.messages.noData', undefined, 'common.messages.noData'),
      description: translate('common.messages.noData', undefined, 'common.messages.noData'),
    },
    search: {
      type: 'search',
      title: translate('common.messages.noSearchResults', undefined, 'common.messages.noSearchResults'),
      description: translate('common.messages.noSearchResults', undefined, 'common.messages.noSearchResults'),
    },
    error: {
      type: 'error',
      title: translate('common.messages.systemError', undefined, 'common.messages.systemError'),
      description: translate('common.messages.operationFailed', undefined, 'common.messages.operationFailed'),
    },
  }

  return {
    ...defaults[type],
    ...overrides,
    type,
  }
}

export async function withUxFeedback<T>(
  task: Promise<T> | (() => Promise<T>),
  options: FeedbackTaskOptions = {},
): Promise<T> {
  const controller = createLoadingController(options)
  controller.start(options)

  try {
    const result = typeof task === 'function' ? await task() : await task
    if (options.showSuccess !== false && options.successMessage) {
      showUxSuccess(options.successMessage, options.successParams)
    }
    return result
  } catch (error) {
    if (options.showError !== false) {
      showUxError(error, options.fallbackErrorKey)
    }
    throw error
  } finally {
    controller.stop()
  }
}
