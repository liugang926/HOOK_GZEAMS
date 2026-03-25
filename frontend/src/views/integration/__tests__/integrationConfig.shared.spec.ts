import { describe, expect, it } from 'vitest'
import { createLatestRequestGuard, createIntegrationPaginationState } from '@/views/integration/composables'

describe('integrationConfig.shared', () => {
  it('creates default pagination state', () => {
    expect(createIntegrationPaginationState()).toEqual({
      page: 1,
      pageSize: 20,
      total: 0
    })
  })

  it('tracks latest request id as active', () => {
    const guard = createLatestRequestGuard()

    const first = guard.begin()
    const second = guard.begin()

    expect(guard.isActive(first)).toBe(false)
    expect(guard.isActive(second)).toBe(true)
  })
})
