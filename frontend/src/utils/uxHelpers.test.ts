import { beforeEach, describe, expect, it, vi } from 'vitest'

const {
  loadingClose,
  loadingService,
  messageError,
  messageSuccess,
} = vi.hoisted(() => ({
  loadingClose: vi.fn(),
  loadingService: vi.fn(() => ({
    close: vi.fn(),
  })),
  messageError: vi.fn(),
  messageSuccess: vi.fn(),
}))

loadingService.mockImplementation(() => ({
  close: loadingClose,
}))

vi.mock('element-plus', () => ({
  ElLoading: {
    service: loadingService,
  },
  ElMessage: {
    error: messageError,
    success: messageSuccess,
  },
}))

import {
  createEmptyState,
  createLoadingController,
  resolveUxErrorMessage,
  showUxSuccess,
} from './uxHelpers'

describe('uxHelpers', () => {
  beforeEach(() => {
    loadingClose.mockReset()
    loadingService.mockClear()
    messageError.mockClear()
    messageSuccess.mockClear()
  })

  it('creates localized empty-state defaults', () => {
    const state = createEmptyState('search')

    expect(state.type).toBe('search')
    expect(state.title).toBeTruthy()
    expect(state.description).toBeTruthy()
  })

  it('resolves useful error messages from error-like values', () => {
    expect(resolveUxErrorMessage('Direct message')).toBe('Direct message')
    expect(resolveUxErrorMessage(new Error('Boom'))).toBe('Boom')
  })

  it('tracks nested loading calls and closes once', async () => {
    const controller = createLoadingController({ text: 'common.messages.loading' })
    controller.start()
    await controller.withLoading(Promise.resolve('ok'))
    controller.stop()

    expect(loadingService).toHaveBeenCalledTimes(1)
    expect(loadingClose).toHaveBeenCalledTimes(1)
    expect(controller.isLoading()).toBe(false)
  })

  it('shows translated success feedback', () => {
    const message = showUxSuccess('common.messages.saveSuccess')

    expect(message).toBeTruthy()
    expect(messageSuccess).toHaveBeenCalledTimes(1)
  })
})
