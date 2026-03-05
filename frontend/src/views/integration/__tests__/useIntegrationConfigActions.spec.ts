import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ElMessage } from 'element-plus'
import { integrationConfigApi } from '@/api/integration'
import { useIntegrationConfigActions } from '@/views/integration/composables/useIntegrationConfigActions'
import type { IntegrationConfig } from '@/types/integration'

vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    warning: vi.fn(),
    error: vi.fn()
  }
}))

vi.mock('@/api/integration', () => ({
  integrationConfigApi: {
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    test: vi.fn(),
    sync: vi.fn()
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

describe('useIntegrationConfigActions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(integrationConfigApi.create).mockResolvedValue({ success: true, message: 'created' })
    vi.mocked(integrationConfigApi.update).mockResolvedValue({ success: true, message: 'updated' })
    vi.mocked(integrationConfigApi.delete).mockResolvedValue({ success: true, message: 'deleted' })
    vi.mocked(integrationConfigApi.test).mockResolvedValue({ success: true, message: 'ok' })
    vi.mocked(integrationConfigApi.sync).mockResolvedValue({ success: false, message: 'sync fail' })
  })

  it('supports create and update submit flows', async () => {
    const refresh = vi.fn(async () => undefined)
    const state = useIntegrationConfigActions({
      t: (key) => key,
      refresh
    })

    state.handleCreate()
    expect(state.editingConfig.value).toBeNull()
    await state.handleSubmit(state.formData.value)
    expect(integrationConfigApi.create).toHaveBeenCalled()
    expect(ElMessage.success).toHaveBeenCalledWith('created')
    expect(refresh).toHaveBeenCalled()

    state.handleEdit(config)
    expect(state.editingConfig.value?.id).toBe('cfg-1')
    expect(state.formData.value.connectionConfig.timeout).toBe(30)
    expect(state.formData.value.syncConfig.autoSync).toBe(false)
    await state.handleSubmit(state.formData.value)
    expect(integrationConfigApi.update).toHaveBeenCalledWith('cfg-1', state.formData.value)
    expect(ElMessage.success).toHaveBeenCalledWith('updated')
  })

  it('handles delete and action commands with refresh', async () => {
    const refresh = vi.fn(async () => undefined)
    const state = useIntegrationConfigActions({
      t: (key) => key,
      refresh
    })

    await state.handleDelete(config)
    await state.handleTest(config)
    await state.handleSync(config)

    expect(integrationConfigApi.delete).toHaveBeenCalledWith('cfg-1')
    expect(integrationConfigApi.test).toHaveBeenCalledWith('cfg-1')
    expect(integrationConfigApi.sync).toHaveBeenCalledWith('cfg-1')
    expect(ElMessage.warning).toHaveBeenCalledWith('sync fail')
    expect(refresh).toHaveBeenCalledTimes(3)
  })

  it('shows error message when submit fails', async () => {
    vi.mocked(integrationConfigApi.create).mockRejectedValueOnce(new Error('create fail'))
    const state = useIntegrationConfigActions({
      t: (key) => key,
      refresh: async () => undefined
    })

    state.handleCreate()
    await state.handleSubmit(state.formData.value)

    expect(ElMessage.error).toHaveBeenCalledWith('integration.messages.operationFailed')
    expect(state.submitting.value).toBe(false)
  })

  it('keeps dialog open and skips refresh when submit returns success false', async () => {
    const refresh = vi.fn(async () => undefined)
    vi.mocked(integrationConfigApi.create).mockResolvedValueOnce({
      success: false,
      message: 'validation failed'
    })
    const state = useIntegrationConfigActions({
      t: (key) => key,
      refresh
    })

    state.handleCreate()
    await state.handleSubmit(state.formData.value)

    expect(ElMessage.warning).toHaveBeenCalledWith('validation failed')
    expect(state.dialogVisible.value).toBe(true)
    expect(refresh).not.toHaveBeenCalled()
  })

  it('shows warning and skips refresh when delete returns success false', async () => {
    const refresh = vi.fn(async () => undefined)
    vi.mocked(integrationConfigApi.delete).mockResolvedValueOnce({
      success: false,
      message: 'cannot delete'
    })
    const state = useIntegrationConfigActions({
      t: (key) => key,
      refresh
    })

    await state.handleDelete(config)

    expect(ElMessage.warning).toHaveBeenCalledWith('cannot delete')
    expect(refresh).not.toHaveBeenCalled()
  })

  it('deduplicates repeated test and submit actions while loading', async () => {
    const deferredTest = createDeferred<{ success: boolean; message: string }>()
    vi.mocked(integrationConfigApi.test).mockReturnValueOnce(deferredTest.promise)
    const deferredCreate = createDeferred<{ success: boolean; message: string }>()
    vi.mocked(integrationConfigApi.create).mockReturnValueOnce(deferredCreate.promise)
    const state = useIntegrationConfigActions({
      t: (key) => key,
      refresh: async () => undefined
    })

    const firstTest = state.handleTest(config)
    const secondTest = state.handleTest(config)
    expect(integrationConfigApi.test).toHaveBeenCalledTimes(1)
    deferredTest.resolve({ success: true, message: 'ok' })
    await Promise.all([firstTest, secondTest])

    state.handleCreate()
    const firstSubmit = state.handleSubmit(state.formData.value)
    const secondSubmit = state.handleSubmit(state.formData.value)
    expect(integrationConfigApi.create).toHaveBeenCalledTimes(1)
    deferredCreate.resolve({ success: true, message: 'created' })
    await Promise.all([firstSubmit, secondSubmit])
  })
})
