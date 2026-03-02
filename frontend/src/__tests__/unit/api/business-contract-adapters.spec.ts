import { beforeEach, describe, expect, it, vi } from 'vitest'
import request from '@/utils/request'
import { financeApi, integrationApi } from '@/api/finance'
import { depreciationApi } from '@/api/depreciation'
import { integrationConfigApi } from '@/api/integration'

vi.mock('@/utils/request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockedRequest = vi.mocked(request)

describe('business api contract adapters', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('financeApi.listVouchers should map query params to snake_case and return paginated data', async () => {
    mockedRequest.get.mockResolvedValue({
      success: true,
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [{ id: 'v1', voucherNo: 'VCH001' }],
      },
    })

    const result = await financeApi.listVouchers({
      page: 1,
      pageSize: 20,
      voucherNo: 'VCH001',
      businessType: 'depreciation',
    })

    expect(mockedRequest.get).toHaveBeenCalledWith('/system/objects/FinanceVoucher/', {
      params: {
        page: 1,
        page_size: 20,
        voucher_no: 'VCH001',
        business_type: 'depreciation',
      },
    })
    expect(result.count).toBe(1)
    expect(result.results[0].voucherNo).toBe('VCH001')
  })

  it('depreciationApi.calculate should call runs endpoint and expose taskId', async () => {
    mockedRequest.post.mockResolvedValue({
      success: true,
      data: { id: 'run-123', status: 'in_progress' },
    })

    const result = await depreciationApi.calculate({
      period: '2026-02',
      categoryIds: ['cat-1'],
    })

    expect(mockedRequest.post).toHaveBeenCalledWith('/system/objects/DepreciationRun/calculate/', {
      period: '2026-02',
      category_ids: ['cat-1'],
    })
    expect(result.taskId).toBe('run-123')
  })

  it('integrationConfigApi.list should return camelized result items', async () => {
    mockedRequest.get.mockResolvedValue({
      success: true,
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            system_type: 'm18',
            system_name: 'M18 Prod',
            is_enabled: true,
            enabled_modules: ['finance'],
            connection_config: { api_url: 'https://m18.example.com' },
          },
        ],
      },
    })

    const result = await integrationConfigApi.list({ page: 1, page_size: 20, systemType: 'm18' })

    expect(mockedRequest.get).toHaveBeenCalledWith('/integration/configs/', {
      params: {
        page: 1,
        page_size: 20,
        system_type: 'm18',
      },
    })
    expect(result.results[0]).toMatchObject({
      systemType: 'm18',
      systemName: 'M18 Prod',
      isEnabled: true,
      enabledModules: ['finance'],
      connectionConfig: { apiUrl: 'https://m18.example.com' },
    })
  })

  it('financeApi.pushVoucher should call compatibility endpoint', async () => {
    mockedRequest.post.mockResolvedValue({
      success: true,
      data: { success: true, externalVoucherNo: 'ERP-001' },
    })

    const result = await financeApi.pushVoucher('v1', 'm18')

    expect(mockedRequest.post).toHaveBeenCalledWith('/system/objects/FinanceVoucher/v1/push/', { system: 'm18' })
    expect(result).toMatchObject({ success: true })
    expect((result as any)?.data?.externalVoucherNo).toBe('ERP-001')
  })

  it('depreciationApi.submitRecord should call compatibility endpoint', async () => {
    mockedRequest.post.mockResolvedValue({ success: true })
    await depreciationApi.submitRecord('r1')
    expect(mockedRequest.post).toHaveBeenCalledWith('/system/objects/DepreciationRecord/r1/submit/')
  })

  it('finance integrationApi.getLogs should call compatibility endpoint', async () => {
    mockedRequest.get.mockResolvedValue([{ id: 'l1' }])
    const result = await integrationApi.getLogs('v1')
    expect(mockedRequest.get).toHaveBeenCalledWith('/system/objects/FinanceVoucher/v1/integration-logs/')
    expect(result).toEqual([{ id: 'l1' }])
  })

  it('finance integrationApi.retry should call compatibility endpoint', async () => {
    mockedRequest.post.mockResolvedValue({ success: true, queued: true, taskId: 'cel-1', syncTaskId: 'sync-1' })
    const result = await integrationApi.retry('v1')
    expect(mockedRequest.post).toHaveBeenCalledWith('/system/objects/FinanceVoucher/v1/retry/')
    expect(result).toMatchObject({ queued: true, taskId: 'cel-1', syncTaskId: 'sync-1' })
  })

  it('financeApi.batchPushVouchers should normalize task ids from compatibility payload', async () => {
    mockedRequest.post.mockResolvedValue({
      success: true,
      summary: { total: 2, succeeded: 1, failed: 1 },
      results: [
        { id: 'v1', success: true, task_id: 'cel-1', sync_task_id: 'sync-1', queued: true },
        { id: 'v2', success: false, error: 'not ready' },
      ],
    })

    const result = await financeApi.batchPushVouchers(['v1', 'v2'])

    expect(mockedRequest.post).toHaveBeenCalledWith('/system/objects/FinanceVoucher/batch_push/', { ids: ['v1', 'v2'] })
    expect(result.success).toBe(1)
    expect(result.failed).toBe(1)
    expect(result.results[0]).toMatchObject({
      id: 'v1',
      success: true,
      taskId: 'cel-1',
      syncTaskId: 'sync-1',
      queued: true,
    })
  })
})
