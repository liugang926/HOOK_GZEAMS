import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import type { IntegrationConfig } from '@/types/integration'
import {
  buildIntegrationFormDataFromConfig,
  emitIntegrationActionMessage,
  runFlagIntegrationAction,
  runIntegrationAction,
  runRowIntegrationAction,
  withFlagLoading,
  withRowLoading
} from '@/views/integration/composables/integrationConfigActions.helpers'

const config: IntegrationConfig = {
  id: 'cfg-1',
  systemType: 'sap',
  systemName: 'SAP PROD',
  isEnabled: true,
  enabledModules: ['finance'],
  connectionConfig: {
    apiUrl: 'https://sap.example.com'
  },
  syncConfig: {},
  healthStatus: 'healthy',
  lastSyncAt: null,
  lastSyncStatus: null
}

describe('integrationConfigActions.helpers', () => {
  it('builds form data from config with default fallback fields', () => {
    expect(buildIntegrationFormDataFromConfig(config)).toEqual({
      systemType: 'sap',
      systemName: 'SAP PROD',
      isEnabled: true,
      enabledModules: ['finance'],
      connectionConfig: {
        apiUrl: 'https://sap.example.com',
        apiKey: '',
        apiSecret: '',
        timeout: 30
      },
      syncConfig: {
        autoSync: false,
        interval: 60
      }
    })
  })

  it('sets and resets boolean loading flag around async action', async () => {
    const loading = ref(false)

    await withFlagLoading(loading, async () => {
      expect(loading.value).toBe(true)
    })

    expect(loading.value).toBe(false)
  })

  it('sets and resets row loading map around async action', async () => {
    const loadingMap = ref<Record<string, boolean>>({})

    await withRowLoading(loadingMap, 'cfg-1', async () => {
      expect(loadingMap.value['cfg-1']).toBe(true)
    })

    expect(loadingMap.value['cfg-1']).toBe(false)
  })

  it('skips duplicate execution when loading is already active', async () => {
    const loading = ref(true)
    const runner = vi.fn(async () => 'done')
    const result = await withFlagLoading(loading, runner)

    expect(result).toBeUndefined()
    expect(runner).not.toHaveBeenCalled()
    expect(loading.value).toBe(true)
  })

  it('skips duplicate row execution when row loading is already active', async () => {
    const loadingMap = ref<Record<string, boolean>>({ 'cfg-1': true })
    const runner = vi.fn(async () => 'done')
    const result = await withRowLoading(loadingMap, 'cfg-1', runner)

    expect(result).toBeUndefined()
    expect(runner).not.toHaveBeenCalled()
    expect(loadingMap.value['cfg-1']).toBe(true)
  })

  it('routes command messages by success state', () => {
    const onSuccess = vi.fn()
    const onFailure = vi.fn()

    const successResult = emitIntegrationActionMessage({
      result: { success: true, message: '' },
      successFallback: 'success fallback',
      failureFallback: 'failure fallback',
      onSuccess,
      onFailure
    })
    expect(successResult).toBe(true)
    expect(onSuccess).toHaveBeenCalledWith('success fallback')
    expect(onFailure).not.toHaveBeenCalled()

    const failureResult = emitIntegrationActionMessage({
      result: { success: false, message: 'api warning' },
      successFallback: 'success fallback',
      failureFallback: 'failure fallback',
      onSuccess,
      onFailure
    })
    expect(failureResult).toBe(false)
    expect(onFailure).toHaveBeenCalledWith('api warning')
  })

  it('runs integration action and returns success outcome', async () => {
    const notifier = {
      success: vi.fn(),
      warning: vi.fn(),
      error: vi.fn()
    }
    const onSuccess = vi.fn()
    const outcome = await runIntegrationAction({
      invoke: async () => ({ success: true, message: '' }),
      messages: {
        successFallback: 'success fallback',
        failureFallback: 'failure fallback',
        errorFallback: 'error fallback'
      },
      notifier,
      onSuccess
    })

    expect(outcome).toBe('success')
    expect(notifier.success).toHaveBeenCalledWith('success fallback')
    expect(notifier.warning).not.toHaveBeenCalled()
    expect(notifier.error).not.toHaveBeenCalled()
    expect(onSuccess).toHaveBeenCalled()
  })

  it('runs integration action and returns failure outcome', async () => {
    const notifier = {
      success: vi.fn(),
      warning: vi.fn(),
      error: vi.fn()
    }
    const onFailure = vi.fn()
    const outcome = await runIntegrationAction({
      invoke: async () => ({ success: false, message: 'failed from api' }),
      messages: {
        successFallback: 'success fallback',
        failureFallback: 'failure fallback',
        errorFallback: 'error fallback'
      },
      notifier,
      onFailure
    })

    expect(outcome).toBe('failure')
    expect(notifier.warning).toHaveBeenCalledWith('failed from api')
    expect(onFailure).toHaveBeenCalled()
  })

  it('runs integration action and returns error outcome', async () => {
    const notifier = {
      success: vi.fn(),
      warning: vi.fn(),
      error: vi.fn()
    }
    const onError = vi.fn()
    const outcome = await runIntegrationAction({
      invoke: async () => {
        throw new Error('network')
      },
      messages: {
        successFallback: 'success fallback',
        failureFallback: 'failure fallback',
        errorFallback: 'error fallback'
      },
      notifier,
      onError
    })

    expect(outcome).toBe('error')
    expect(notifier.error).toHaveBeenCalledWith('error fallback')
    expect(onError).toHaveBeenCalled()
  })

  it('returns skipped outcome when flag action is already loading', async () => {
    const outcome = await runFlagIntegrationAction({
      loadingFlag: ref(true),
      invoke: async () => ({ success: true, message: '' }),
      messages: {
        successFallback: 'success fallback',
        failureFallback: 'failure fallback',
        errorFallback: 'error fallback'
      },
      notifier: {
        success: vi.fn(),
        warning: vi.fn(),
        error: vi.fn()
      }
    })

    expect(outcome).toBe('skipped')
  })

  it('returns skipped outcome when row action is already loading', async () => {
    const outcome = await runRowIntegrationAction({
      loadingMap: ref({ 'cfg-1': true }),
      rowId: 'cfg-1',
      invoke: async () => ({ success: true, message: '' }),
      messages: {
        successFallback: 'success fallback',
        failureFallback: 'failure fallback',
        errorFallback: 'error fallback'
      },
      notifier: {
        success: vi.fn(),
        warning: vi.fn(),
        error: vi.fn()
      }
    })

    expect(outcome).toBe('skipped')
  })
})
