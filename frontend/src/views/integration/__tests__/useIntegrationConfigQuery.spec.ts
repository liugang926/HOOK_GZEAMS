import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage } from 'element-plus'
import { integrationConfigApi } from '@/api/integration'
import { useIntegrationConfigQuery } from '@/views/integration/composables/useIntegrationConfigQuery'
import type { IntegrationConfig } from '@/types/integration'

vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn()
  }
}))

vi.mock('@/api/integration', () => ({
  integrationConfigApi: {
    list: vi.fn(),
    stats: vi.fn()
  }
}))

const createDeferred = <T>() => {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}

const config: IntegrationConfig = {
  id: 'cfg-1',
  systemType: 'sap',
  systemName: 'SAP PROD',
  isEnabled: true,
  enabledModules: ['finance'],
  connectionConfig: {},
  syncConfig: {},
  healthStatus: 'healthy',
  lastSyncAt: null,
  lastSyncStatus: null
}

describe('useIntegrationConfigQuery', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(integrationConfigApi.list).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [config]
    })
    vi.mocked(integrationConfigApi.stats).mockResolvedValue({
      total: 10,
      healthy: 8,
      degraded: 1,
      unhealthy: 1
    })
  })

  it('fetches list and stats with aligned filter params', async () => {
    const state = useIntegrationConfigQuery({ t: (key) => key })
    state.filterForm.systemType = 'sap'
    state.filterForm.isEnabled = false

    await state.fetchData()

    expect(integrationConfigApi.list).toHaveBeenCalledWith({
      page: 1,
      page_size: 20,
      systemType: 'sap',
      isEnabled: false
    })
    expect(integrationConfigApi.stats).toHaveBeenCalledWith({
      systemType: 'sap',
      isEnabled: false
    })
    expect(state.stats.value.total).toBe(10)
  })

  it('falls back to page stats when stats endpoint fails', async () => {
    vi.mocked(integrationConfigApi.stats).mockRejectedValueOnce(new Error('stats down'))
    const state = useIntegrationConfigQuery({ t: (key) => key })

    await state.fetchData()

    expect(state.stats.value).toEqual({
      total: 1,
      healthy: 1,
      degraded: 0,
      unhealthy: 0
    })
  })

  it('handles fetch failure by showing error message', async () => {
    vi.mocked(integrationConfigApi.list).mockRejectedValueOnce(new Error('list down'))
    const state = useIntegrationConfigQuery({ t: (key) => key })

    await state.fetchData()

    expect(ElMessage.error).toHaveBeenCalledWith('integration.messages.loadConfigsFailed')
  })

  it('keeps latest fetch result when earlier request resolves later', async () => {
    const firstList = createDeferred<{
      count: number
      next: null
      previous: null
      results: IntegrationConfig[]
    }>()
    const firstStats = createDeferred<{
      total: number
      healthy: number
      degraded: number
      unhealthy: number
    }>()
    const secondList = createDeferred<{
      count: number
      next: null
      previous: null
      results: IntegrationConfig[]
    }>()
    const secondStats = createDeferred<{
      total: number
      healthy: number
      degraded: number
      unhealthy: number
    }>()

    vi.mocked(integrationConfigApi.list)
      .mockReturnValueOnce(firstList.promise)
      .mockReturnValueOnce(secondList.promise)
    vi.mocked(integrationConfigApi.stats)
      .mockReturnValueOnce(firstStats.promise)
      .mockReturnValueOnce(secondStats.promise)

    const state = useIntegrationConfigQuery({ t: (key) => key })
    const firstFetch = state.fetchData()
    const secondFetch = state.fetchData()

    secondList.resolve({
      count: 1,
      next: null,
      previous: null,
      results: [{ ...config, id: 'cfg-2', systemName: 'second' }]
    })
    secondStats.resolve({
      total: 1,
      healthy: 1,
      degraded: 0,
      unhealthy: 0
    })

    firstList.resolve({
      count: 1,
      next: null,
      previous: null,
      results: [{ ...config, id: 'cfg-1', systemName: 'first' }]
    })
    firstStats.resolve({
      total: 1,
      healthy: 0,
      degraded: 1,
      unhealthy: 0
    })

    await Promise.all([firstFetch, secondFetch])

    expect(state.tableData.value[0]?.id).toBe('cfg-2')
    expect(state.stats.value).toEqual({
      total: 1,
      healthy: 1,
      degraded: 0,
      unhealthy: 0
    })
    expect(state.loading.value).toBe(false)
  })
})
