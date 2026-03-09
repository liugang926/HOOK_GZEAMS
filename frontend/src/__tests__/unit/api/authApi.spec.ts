import { beforeEach, describe, expect, it, vi } from 'vitest'

const postMock = vi.fn()

vi.mock('@/utils/request', () => ({
  default: {
    post: postMock
  }
}))

describe('authApi', () => {
  beforeEach(() => {
    postMock.mockReset()
  })

  it('marks login as noAuth to avoid stale token interception', async () => {
    const { authApi } = await import('@/api/auth')

    await authApi.login({ username: 'demo', password: 'secret' })

    expect(postMock).toHaveBeenCalledWith(
      '/auth/login/',
      { username: 'demo', password: 'secret' },
      expect.objectContaining({ noAuth: true })
    )
  })

  it('marks refresh and logout as noAuth', async () => {
    const { authApi } = await import('@/api/auth')

    await authApi.refreshToken('refresh-token')
    await authApi.logout()

    expect(postMock).toHaveBeenNthCalledWith(
      1,
      '/auth/refresh/',
      { token: 'refresh-token' },
      expect.objectContaining({ noAuth: true })
    )
    expect(postMock).toHaveBeenNthCalledWith(
      2,
      '/auth/logout/',
      undefined,
      expect.objectContaining({ noAuth: true })
    )
  })
})
