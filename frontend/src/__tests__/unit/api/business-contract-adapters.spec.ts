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

type MockedRequest = {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  put: ReturnType<typeof vi.fn>
  patch: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

const mockedRequest = request as unknown as MockedRequest

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

  it('depreciationApi.listRecords should normalize depreciation list fields for the finance page', async () => {
    mockedRequest.get.mockResolvedValue({
      success: true,
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 'r1',
            asset: 'asset-1',
            assetCode: 'ASSET-001',
            assetName: 'Laptop',
            period: '2026-02',
            depreciationMethod: 'straight_line',
            purchasePrice: '2000.00',
            depreciationAmount: '100.00',
            accumulatedAmount: '400.00',
            netValue: '1600.00',
            status: 'calculated',
            statusDisplay: 'Calculated',
          },
        ],
      },
    })

    const result = await depreciationApi.listRecords({
      page: 1,
      pageSize: 20,
      assetKeyword: 'ASSET-001',
      status: 'calculated',
    })

    expect(mockedRequest.get).toHaveBeenCalledWith('/system/objects/DepreciationRecord/', {
      params: {
        page: 1,
        page_size: 20,
        asset: 'ASSET-001',
        status: 'calculated',
      },
    })
    expect(result.results[0]).toMatchObject({
      assetId: 'asset-1',
      assetCode: 'ASSET-001',
      assetName: 'Laptop',
      purchasePrice: 2000,
      depreciationAmount: 100,
      accumulatedAmount: 400,
      accumulatedDepreciation: 400,
      netValue: 1600,
      status: 'calculated',
    })
  })

  it('depreciationApi.getReport should normalize report summary, category rows, and asset rows', async () => {
    mockedRequest.get.mockResolvedValue({
      success: true,
      data: {
        summary: {
          totalRecords: 2,
          totalDepreciationAmount: '300.00',
          totalAccumulatedAmount: '700.00',
          totalNetValue: '1300.00',
          postedCount: 1,
          calculatedCount: 1,
          rejectedCount: 0,
        },
        categoryBreakdown: [
          {
            categoryName: 'IT Equipment',
            categoryCode: 'IT',
            recordCount: 2,
            totalDepreciation: '300.00',
            totalAccumulated: '700.00',
            totalNet: '1300.00',
          },
        ],
        byAsset: [
          {
            assetId: 'asset-1',
            assetCode: 'ASSET-001',
            assetName: 'Laptop',
            categoryName: 'IT Equipment',
            purchasePrice: '2000.00',
            currentDepreciation: '300.00',
            accumulatedDepreciation: '700.00',
            netValue: '1300.00',
          },
        ],
      },
    })

    const result = await depreciationApi.getReport({ period: '2026-02' })

    expect(mockedRequest.get).toHaveBeenCalledWith('/system/objects/DepreciationRecord/report/', {
      params: {
        period: '2026-02',
      },
    })
    expect(result).toMatchObject({
      period: '2026-02',
      summary: {
        assetCount: 2,
        originalValue: 2000,
        currentAmount: 300,
        accumulatedAmount: 700,
        netValue: 1300,
        postedCount: 1,
        calculatedCount: 1,
        rejectedCount: 0,
      },
      byCategory: [
        {
          categoryId: 'IT',
          categoryName: 'IT Equipment',
          assetCount: 2,
          originalValue: 2000,
          currentDepreciation: 300,
          accumulatedDepreciation: 700,
          netValue: 1300,
        },
      ],
      byAsset: [
        {
          assetId: 'asset-1',
          assetCode: 'ASSET-001',
          assetName: 'Laptop',
          categoryName: 'IT Equipment',
          purchasePrice: 2000,
          currentDepreciation: 300,
          accumulatedDepreciation: 700,
          netValue: 1300,
          depreciationRate: 0,
        },
      ],
    })
  })

  it('depreciationApi.batchPost should normalize batch summary counts', async () => {
    mockedRequest.post.mockResolvedValue({
      success: false,
      summary: {
        total: 2,
        succeeded: 1,
        failed: 1,
      },
      results: [
        { id: 'r1', success: true },
        { id: 'r2', success: false, error: 'Record is already posted' },
      ],
    })

    const result = await depreciationApi.batchPost(['r1', 'r2'])

    expect(mockedRequest.post).toHaveBeenCalledWith('/system/objects/DepreciationRecord/batch_post/', {
      ids: ['r1', 'r2'],
    })
    expect(result).toEqual({
      success: 1,
      failed: 1,
      results: [
        { id: 'r1', success: true },
        { id: 'r2', success: false, error: 'Record is already posted' },
      ],
    })
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
