import { ref } from 'vue'
import { syncTaskApi } from '@/api/integration'
import { isSyncTaskDone } from '@/utils/syncTaskStatus'

export interface SyncTaskState {
  syncTaskId: string
  status: string
  statusDisplay?: string
  done: boolean
}

interface SyncTaskPollingOptions {
  intervalMs?: number
  maxAttempts?: number
  onError?: (error: unknown) => void
}

interface StartPollingOptions {
  onDone?: (state: SyncTaskState) => void | Promise<void>
  onTick?: (state: SyncTaskState) => void | Promise<void>
  onError?: (error: unknown) => void
}

const DEFAULT_INTERVAL_MS = 3000
const DEFAULT_MAX_ATTEMPTS = 40

export function useSyncTaskPolling(options: SyncTaskPollingOptions = {}) {
  const intervalMs = options.intervalMs ?? DEFAULT_INTERVAL_MS
  const maxAttempts = options.maxAttempts ?? DEFAULT_MAX_ATTEMPTS

  const stateByKey = ref<Record<string, SyncTaskState>>({})
  const pollTimers = new Map<string, number>()
  const pollAttempts = new Map<string, number>()

  const setState = (key: string, state: SyncTaskState) => {
    stateByKey.value = {
      ...stateByKey.value,
      [key]: state
    }
  }

  const getState = (key: string) => stateByKey.value[key]

  const stop = (key: string) => {
    const timer = pollTimers.get(key)
    if (timer) {
      window.clearInterval(timer)
      pollTimers.delete(key)
    }
    pollAttempts.delete(key)
  }

  const stopAll = () => {
    Array.from(pollTimers.keys()).forEach(stop)
  }

  const pollOnce = async (
    key: string,
    syncTaskId: string,
    hooks: StartPollingOptions = {},
    silent = true
  ) => {
    try {
      const detail = await syncTaskApi.detail(syncTaskId)
      const status = String(detail?.status || 'pending')
      const next: SyncTaskState = {
        syncTaskId,
        status,
        statusDisplay: detail?.statusDisplay || detail?.status_display || status,
        done: isSyncTaskDone(status)
      }
      setState(key, next)
      if (hooks.onTick) await hooks.onTick(next)

      if (next.done) {
        stop(key)
        if (hooks.onDone) await hooks.onDone(next)
      }
    } catch (error) {
      if (!silent) {
        const handler = hooks.onError || options.onError
        if (handler) handler(error)
      }
    }
  }

  const start = (key: string, syncTaskId: string, hooks: StartPollingOptions = {}) => {
    stop(key)
    pollAttempts.set(key, 0)
    setState(key, {
      syncTaskId,
      status: 'pending',
      statusDisplay: 'Pending',
      done: false
    })

    void pollOnce(key, syncTaskId, hooks, false)
    const timer = window.setInterval(() => {
      const attempts = (pollAttempts.get(key) || 0) + 1
      pollAttempts.set(key, attempts)
      if (attempts >= maxAttempts) {
        stop(key)
        return
      }
      void pollOnce(key, syncTaskId, hooks, true)
    }, intervalMs)
    pollTimers.set(key, timer)
  }

  return {
    stateByKey,
    getState,
    start,
    stop,
    stopAll,
  }
}
