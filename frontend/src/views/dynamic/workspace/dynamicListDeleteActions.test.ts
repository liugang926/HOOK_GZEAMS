import { describe, expect, it, vi } from 'vitest'
import { executeDynamicListDeleteOperation } from './dynamicListDeleteActions'

describe('dynamicListDeleteActions', () => {
  it('notifies success and refreshes after a successful delete', async () => {
    const refresh = vi.fn()
    const notifySuccess = vi.fn()
    const notifyError = vi.fn()

    await executeDynamicListDeleteOperation({
      runDelete: async () => {},
      refresh,
      notifySuccess,
      notifyError,
      successMessage: 'deleted',
      fallbackErrorMessage: 'failed',
    })

    expect(notifySuccess).toHaveBeenCalledWith('deleted')
    expect(refresh).toHaveBeenCalledTimes(1)
    expect(notifyError).not.toHaveBeenCalled()
  })

  it('suppresses cancel errors and reports real failures', async () => {
    const refresh = vi.fn()
    const notifySuccess = vi.fn()
    const notifyError = vi.fn()

    await executeDynamicListDeleteOperation({
      runDelete: async () => {
        throw 'cancel'
      },
      refresh,
      notifySuccess,
      notifyError,
      successMessage: 'deleted',
      fallbackErrorMessage: 'failed',
    })

    await executeDynamicListDeleteOperation({
      runDelete: async () => {
        throw new Error('boom')
      },
      refresh,
      notifySuccess,
      notifyError,
      successMessage: 'deleted',
      fallbackErrorMessage: 'failed',
    })

    expect(refresh).not.toHaveBeenCalled()
    expect(notifySuccess).not.toHaveBeenCalled()
    expect(notifyError).toHaveBeenCalledTimes(1)
    expect(notifyError).toHaveBeenCalledWith('boom')
  })
})
