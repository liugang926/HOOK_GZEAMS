import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage } from 'element-plus'
import { integrationConfigApi, integrationLogApi } from '@/api/integration'
import { createDefaultIntegrationFormData } from '@/views/integration/integrationConfig.constants'
import { useIntegrationConfigList } from '@/views/integration/composables'
import type { IntegrationConfig, IntegrationFormData, IntegrationLog } from '@/types/integration'

vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key
  })
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn()
  }
}))

vi.mock('@/api/integration', () => ({
  integrationConfigApi: {
    list: vi.fn(),
    stats: vi.fn(),
    detail: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    test: vi.fn(),
    sync: vi.fn()
  },
  integrationLogApi: {
    list: vi.fn(),
    detail: vi.fn(),
    retry: vi.fn()
  }
}))

const flush = () => new Promise((resolve) => setTimeout(resolve, 0))

const sampleConfig: IntegrationConfig = {
  id: 'cfg-1',
  systemType: 'sap',
  systemName: 'SAP PROD',
  isEnabled: true,
  enabledModules: ['finance', 'inventory'],
  connectionConfig: {
    apiUrl: 'https://sap.example.com',
    timeout: 30
  },
  syncConfig: {
    autoSync: false,
    interval: 60
  },
  healthStatus: 'healthy',
  lastSyncAt: '2026-03-01T00:00:00Z',
  lastSyncStatus: 'success'
}

const sampleLog: IntegrationLog = {
  id: 'log-1',
  createdAt: '2026-03-01T00:00:00Z',
  integrationType: 'sap',
  action: 'push',
  requestMethod: 'POST',
  statusCode: 200,
  success: true,
  durationMs: 123,
  requestBody: { id: 1 },
  responseBody: { ok: true },
  errorMessage: '',
  businessType: 'asset'
}

describe('useIntegrationConfigList', () => {
  beforeEach(() => {
    vi.clearAllMocks()

    vi.mocked(integrationConfigApi.list).mockResolvedValue({
      count: 2,
      next: null,
      previous: null,
      results: [
        sampleConfig,
        {
          ...sampleConfig,
          id: 'cfg-2',
          systemName: 'SAP DR',
          healthStatus: 'degraded'
        }
      ]
    })
    vi.mocked(integrationConfigApi.stats).mockResolvedValue({
      total: 2,
      healthy: 1,
      degraded: 1,
      unhealthy: 0
    })

    vi.mocked(integrationConfigApi.create).mockResolvedValue({
      success: true,
      message: 'created'
    })

    vi.mocked(integrationConfigApi.update).mockResolvedValue({
      success: true,
      message: 'updated'
    })

    vi.mocked(integrationConfigApi.delete).mockResolvedValue({
      success: true,
      message: 'deleted'
    })

    vi.mocked(integrationConfigApi.test).mockResolvedValue({
      success: true,
      message: 'ok'
    })

    vi.mocked(integrationConfigApi.sync).mockResolvedValue({
      success: true,
      message: 'ok'
    })

    vi.mocked(integrationLogApi.list).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [sampleLog]
    })
  })

  it('fetches list and computes stats from response', async () => {
    const state = useIntegrationConfigList()
    state.filterForm.systemType = 'sap'

    await state.fetchData()

    expect(integrationConfigApi.list).toHaveBeenCalledWith({
      page: 1,
      page_size: 20,
      systemType: 'sap'
    })
    expect(integrationConfigApi.stats).toHaveBeenCalledWith({
      systemType: 'sap'
    })
    expect(state.tableData.value).toHaveLength(2)
    expect(state.pagination.total).toBe(2)
    expect(state.stats.value).toEqual({
      total: 2,
      healthy: 1,
      degraded: 1,
      unhealthy: 0
    })
  })

  it('exposes grouped APIs while keeping flat compatibility', () => {
    const state = useIntegrationConfigList()

    expect(state.query.fetchData).toBe(state.fetchData)
    expect(state.actions.handleCreate).toBe(state.handleCreate)
    expect(state.logViewer.handleViewLogs).toBe(state.handleViewLogs)
  })

  it('prefers stats API values when stats endpoint returns different aggregates', async () => {
    vi.mocked(integrationConfigApi.stats).mockResolvedValueOnce({
      total: 99,
      healthy: 88,
      degraded: 7,
      unhealthy: 4
    })
    const state = useIntegrationConfigList()

    await state.fetchData()

    expect(state.stats.value).toEqual({
      total: 99,
      healthy: 88,
      degraded: 7,
      unhealthy: 4
    })
  })

  it('falls back to page-derived stats when stats API fails', async () => {
    vi.mocked(integrationConfigApi.stats).mockRejectedValueOnce(new Error('stats failed'))
    const state = useIntegrationConfigList()

    await state.fetchData()

    expect(state.stats.value).toEqual({
      total: 2,
      healthy: 1,
      degraded: 1,
      unhealthy: 0
    })
  })

  it('resets filters and pagination then triggers reload', async () => {
    const state = useIntegrationConfigList()
    state.filterForm.systemType = 'sap'
    state.filterForm.isEnabled = true
    state.filterForm.healthStatus = 'healthy'
    state.pagination.page = 3

    state.handleFilterReset()
    await flush()

    expect(state.filterForm.systemType).toBeUndefined()
    expect(state.filterForm.isEnabled).toBeUndefined()
    expect(state.filterForm.healthStatus).toBeUndefined()
    expect(state.pagination.page).toBe(1)
    expect(integrationConfigApi.list).toHaveBeenCalledWith({
      page: 1,
      page_size: 20
    })
    expect(integrationConfigApi.stats).toHaveBeenCalledWith({})
  })

  it('keeps boolean false filter in list and stats params', async () => {
    const state = useIntegrationConfigList()
    state.filterForm.isEnabled = false
    state.filterForm.healthStatus = 'unhealthy'

    await state.fetchData()

    expect(integrationConfigApi.list).toHaveBeenCalledWith({
      page: 1,
      page_size: 20,
      isEnabled: false,
      healthStatus: 'unhealthy'
    })
    expect(integrationConfigApi.stats).toHaveBeenCalledWith({
      isEnabled: false,
      healthStatus: 'unhealthy'
    })
  })

  it('updates list pagination and reloads data', async () => {
    const state = useIntegrationConfigList()

    state.handlePageChange(3)
    await flush()
    expect(state.pagination.page).toBe(3)
    expect(integrationConfigApi.list).toHaveBeenCalledWith({
      page: 3,
      page_size: 20
    })
    expect(integrationConfigApi.stats).toHaveBeenCalledWith({})

    state.handlePageSizeChange(50)
    await flush()
    expect(state.pagination.page).toBe(1)
    expect(state.pagination.pageSize).toBe(50)
    expect(integrationConfigApi.list).toHaveBeenCalledWith({
      page: 1,
      page_size: 50
    })
    expect(integrationConfigApi.stats).toHaveBeenCalledWith({})
  })

  it('opens create dialog with default form data', () => {
    const state = useIntegrationConfigList()
    state.handleViewLogs(sampleConfig)
    state.formData.value.systemName = 'old'

    state.handleCreate()

    expect(state.isEdit.value).toBe(false)
    expect(state.editingConfig.value).toBeNull()
    expect(state.currentConfig.value?.id).toBe('cfg-1')
    expect(state.dialogVisible.value).toBe(true)
    expect(state.formData.value).toEqual(createDefaultIntegrationFormData())
  })

  it('updates existing config when editing and submitting', async () => {
    const state = useIntegrationConfigList()
    state.handleEdit(sampleConfig)

    const payload: IntegrationFormData = {
      ...state.formData.value,
      systemName: 'SAP PROD UPDATED'
    }

    await state.handleSubmit(payload)

    expect(integrationConfigApi.update).toHaveBeenCalledWith('cfg-1', payload)
    expect(ElMessage.success).toHaveBeenCalledWith('updated')
    expect(state.dialogVisible.value).toBe(false)
  })

  it('creates config in create mode and handles submit errors', async () => {
    const state = useIntegrationConfigList()
    state.handleCreate()

    const payload = createDefaultIntegrationFormData()
    payload.systemType = 'sap'
    payload.systemName = 'SAP NEW'

    await state.handleSubmit(payload)
    expect(integrationConfigApi.create).toHaveBeenCalledWith(payload)
    expect(ElMessage.success).toHaveBeenCalledWith('created')

    vi.mocked(integrationConfigApi.create).mockRejectedValueOnce(new Error('create failed'))
    await state.handleSubmit(payload)

    expect(ElMessage.error).toHaveBeenCalledWith('integration.messages.operationFailed')
    expect(state.submitting.value).toBe(false)
  })

  it('runs test and sync actions with status feedback', async () => {
    const state = useIntegrationConfigList()

    await state.handleTest(sampleConfig)
    expect(integrationConfigApi.test).toHaveBeenCalledWith('cfg-1')
    expect(state.testing.value['cfg-1']).toBe(false)
    expect(ElMessage.success).toHaveBeenCalledWith('ok')

    vi.mocked(integrationConfigApi.sync).mockResolvedValueOnce({
      success: false,
      message: 'sync failed from api'
    })
    await state.handleSync(sampleConfig)

    expect(integrationConfigApi.sync).toHaveBeenCalledWith('cfg-1')
    expect(state.syncing.value['cfg-1']).toBe(false)
    expect(ElMessage.warning).toHaveBeenCalledWith('sync failed from api')
  })

  it('loads logs and supports pagination/detail handlers', async () => {
    const state = useIntegrationConfigList()

    state.handleViewLogs(sampleConfig)
    await flush()

    expect(state.logsDrawerVisible.value).toBe(true)
    expect(state.currentConfig.value?.id).toBe('cfg-1')
    expect(integrationLogApi.list).toHaveBeenCalledWith({
      page: 1,
      page_size: 20,
      systemType: 'sap'
    })
    expect(state.logs.value).toEqual([sampleLog])

    state.handleLogsPageSizeChange(50)
    await flush()

    expect(state.logsPagination.page).toBe(1)
    expect(state.logsPagination.pageSize).toBe(50)
    expect(integrationLogApi.list).toHaveBeenCalledWith({
      page: 1,
      page_size: 50,
      systemType: 'sap'
    })

    state.handleViewLogDetail(sampleLog)
    expect(state.currentLog.value).toEqual(sampleLog)
    expect(state.logDetailVisible.value).toBe(true)
  })
})
