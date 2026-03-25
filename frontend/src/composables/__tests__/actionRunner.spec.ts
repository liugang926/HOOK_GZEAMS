import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import {
  emitActionResultMessage,
  runAction,
  runFlagAction,
  runRowAction,
  withFlagLoading,
  withRowLoading
} from '@/composables/actionRunner'

describe('actionRunner', () => {
  it('withFlagLoading toggles loading flag', async () => {
    const loading = ref(false)

    await withFlagLoading(loading, async () => {
      expect(loading.value).toBe(true)
    })

    expect(loading.value).toBe(false)
  })

  it('withRowLoading toggles row loading flag', async () => {
    const loadingMap = ref<Record<string, boolean>>({})

    await withRowLoading(loadingMap, 'row-1', async () => {
      expect(loadingMap.value['row-1']).toBe(true)
    })

    expect(loadingMap.value['row-1']).toBe(false)
  })

  it('emitActionResultMessage routes success/failure', () => {
    const onSuccess = vi.fn()
    const onFailure = vi.fn()

    expect(
      emitActionResultMessage({
        result: { success: true, message: '' },
        successFallback: 'ok',
        failureFallback: 'fail',
        onSuccess,
        onFailure
      })
    ).toBe(true)

    expect(
      emitActionResultMessage({
        result: { success: false, message: 'bad request' },
        successFallback: 'ok',
        failureFallback: 'fail',
        onSuccess,
        onFailure
      })
    ).toBe(false)

    expect(onSuccess).toHaveBeenCalledWith('ok')
    expect(onFailure).toHaveBeenCalledWith('bad request')
  })

  it('runAction returns success outcome', async () => {
    const notifier = { success: vi.fn(), warning: vi.fn(), error: vi.fn() }
    const onSuccess = vi.fn()
    const payload = { success: true, message: '', id: 'a-1' }

    const outcome = await runAction({
      invoke: async () => payload,
      messages: {
        successFallback: 'ok',
        failureFallback: 'fail',
        errorFallback: 'error'
      },
      notifier,
      onSuccess
    })

    expect(outcome).toBe('success')
    expect(notifier.success).toHaveBeenCalledWith('ok')
    expect(onSuccess).toHaveBeenCalledWith(payload)
  })

  it('runAction returns error outcome on throw', async () => {
    const notifier = { success: vi.fn(), warning: vi.fn(), error: vi.fn() }
    const onError = vi.fn()

    const outcome = await runAction({
      invoke: async () => {
        throw new Error('network')
      },
      messages: {
        successFallback: 'ok',
        failureFallback: 'fail',
        errorFallback: 'error'
      },
      notifier,
      onError
    })

    expect(outcome).toBe('error')
    expect(notifier.error).toHaveBeenCalledWith('error')
    expect(onError).toHaveBeenCalled()
  })

  it('awaits async success callback before returning', async () => {
    const notifier = { success: vi.fn(), warning: vi.fn(), error: vi.fn() }
    const order: string[] = []
    const outcome = await runAction({
      invoke: async () => ({ success: true, message: '' }),
      messages: {
        successFallback: 'ok',
        failureFallback: 'fail',
        errorFallback: 'error'
      },
      notifier,
      onSuccess: async () => {
        await Promise.resolve()
        order.push('callback')
      }
    })
    order.push('after')

    expect(outcome).toBe('success')
    expect(order).toEqual(['callback', 'after'])
  })

  it('runFlagAction and runRowAction return skipped when already loading', async () => {
    const notifier = { success: vi.fn(), warning: vi.fn(), error: vi.fn() }

    const flagOutcome = await runFlagAction({
      loadingFlag: ref(true),
      invoke: async () => ({ success: true, message: '' }),
      messages: {
        successFallback: 'ok',
        failureFallback: 'fail',
        errorFallback: 'error'
      },
      notifier
    })

    const rowOutcome = await runRowAction({
      loadingMap: ref({ 'row-1': true }),
      rowId: 'row-1',
      invoke: async () => ({ success: true, message: '' }),
      messages: {
        successFallback: 'ok',
        failureFallback: 'fail',
        errorFallback: 'error'
      },
      notifier
    })

    expect(flagOutcome).toBe('skipped')
    expect(rowOutcome).toBe('skipped')
  })
})
