import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage } from 'element-plus'
import { integrationLogApi } from '@/api/integration'
import { useIntegrationLogViewer } from '@/views/integration/composables/useIntegrationLogViewer'
import type { IntegrationConfig, IntegrationLog } from '@/types/integration'

vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn()
  }
}))

vi.mock('@/api/integration', () => ({
  integrationLogApi: {
    list: vi.fn()
  }
}))

const flush = () => new Promise((resolve) => setTimeout(resolve, 0))
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

const log: IntegrationLog = {
  id: 'log-1',
  createdAt: '2026-03-01T00:00:00Z',
  integrationType: 'sap',
  action: 'push',
  requestMethod: 'POST',
  statusCode: 200,
  success: true,
  durationMs: 120,
  requestBody: {},
  responseBody: {},
  errorMessage: '',
  businessType: 'asset'
}

const odooConfig: IntegrationConfig = {
  ...config,
  id: 'cfg-2',
  systemType: 'odoo',
  systemName: 'Odoo PROD'
}

describe('useIntegrationLogViewer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(integrationLogApi.list).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [log]
    })
  })

  it('opens logs drawer and loads logs with system type filter', async () => {
    const state = useIntegrationLogViewer({ t: (key) => key })

    state.handleViewLogs(config)
    await flush()

    expect(state.logsDrawerVisible.value).toBe(true)
    expect(integrationLogApi.list).toHaveBeenCalledWith({
      page: 1,
      page_size: 20,
      systemType: 'sap'
    })
    expect(state.logs.value).toEqual([log])
  })

  it('updates logs pagination and reloads logs', async () => {
    const state = useIntegrationLogViewer({ t: (key) => key })
    state.handleViewLogs(config)
    await flush()

    state.handleLogsPageChange(2)
    await flush()
    expect(integrationLogApi.list).toHaveBeenCalledWith({
      page: 2,
      page_size: 20,
      systemType: 'sap'
    })

    state.handleLogsPageSizeChange(50)
    await flush()
    expect(integrationLogApi.list).toHaveBeenCalledWith({
      page: 1,
      page_size: 50,
      systemType: 'sap'
    })
  })

  it('shows error message when loading logs fails', async () => {
    vi.mocked(integrationLogApi.list).mockRejectedValueOnce(new Error('load failed'))
    const state = useIntegrationLogViewer({ t: (key) => key })

    state.handleViewLogs(config)
    await flush()

    expect(ElMessage.error).toHaveBeenCalledWith('integration.messages.loadLogsFailed')
  })

  it('keeps latest logs result when previous request resolves later', async () => {
    const first = createDeferred<{
      count: number
      next: null
      previous: null
      results: IntegrationLog[]
    }>()
    const second = createDeferred<{
      count: number
      next: null
      previous: null
      results: IntegrationLog[]
    }>()

    vi.mocked(integrationLogApi.list)
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise)

    const state = useIntegrationLogViewer({ t: (key) => key })
    state.handleViewLogs(config)
    await flush()
    state.handleViewLogs(odooConfig)
    await flush()

    second.resolve({
      count: 1,
      next: null,
      previous: null,
      results: [{ ...log, id: 'log-odoo', integrationType: 'odoo' }]
    })
    first.resolve({
      count: 1,
      next: null,
      previous: null,
      results: [{ ...log, id: 'log-sap', integrationType: 'sap' }]
    })

    await Promise.all([first.promise, second.promise])
    await flush()

    expect(state.currentConfig.value?.id).toBe('cfg-2')
    expect(state.logs.value[0]?.id).toBe('log-odoo')
    expect(state.logsLoading.value).toBe(false)
  })
})
