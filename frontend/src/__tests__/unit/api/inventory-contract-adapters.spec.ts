import { beforeEach, describe, expect, it, vi } from 'vitest'

type RequestMock = ReturnType<typeof vi.fn> & {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  put: ReturnType<typeof vi.fn>
  patch: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

const requestMock = vi.hoisted(() => {
  const fn = vi.fn() as RequestMock
  fn.get = vi.fn()
  fn.post = vi.fn()
  fn.put = vi.fn()
  fn.patch = vi.fn()
  fn.delete = vi.fn()
  return fn
})

vi.mock('@/utils/request', () => ({
  default: requestMock,
}))

import { inventoryApi, reconciliationApi } from '@/api/inventory'

describe('inventory api contract adapters', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('inventoryApi.getReconciliations should query the reconciliation object route', async () => {
    requestMock.mockResolvedValue({
      success: true,
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 'rec-1',
            reconciliationNo: 'IRC2026030001',
            status: 'draft',
          },
        ],
      },
    })

    const result = await inventoryApi.getReconciliations({
      page: 1,
      pageSize: 20,
      taskId: 'task-1',
      status: 'draft',
      dateFrom: '2026-03-01',
      dateTo: '2026-03-31',
    })

    expect(requestMock).toHaveBeenCalledWith({
      url: '/system/objects/InventoryReconciliation/',
      method: 'get',
      params: {
        page: 1,
        page_size: 20,
        task: 'task-1',
        status: 'draft',
        reconciled_at_from: '2026-03-01',
        reconciled_at_to: '2026-03-31',
      },
    })
    expect(result.results[0].reconciliationNo).toBe('IRC2026030001')
  })

  it('inventoryApi.createReconciliation should create through the reconciliation object route', async () => {
    requestMock.mockResolvedValue({
      success: true,
      data: {
        id: 'rec-1',
        task: 'task-1',
        note: 'Ready for approval',
      },
    })

    const result = await inventoryApi.createReconciliation({
      taskId: 'task-1',
      note: 'Ready for approval',
    })

    expect(requestMock).toHaveBeenCalledWith({
      url: '/system/objects/InventoryReconciliation/',
      method: 'post',
      data: {
        task: 'task-1',
        note: 'Ready for approval',
      },
    })
    expect(result.id).toBe('rec-1')
  })

  it('inventoryApi.getReports should query the report object route', async () => {
    requestMock.mockResolvedValue({
      success: true,
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: 'rep-1',
            reportNo: 'IRP2026030001',
            status: 'draft',
          },
        ],
      },
    })

    const result = await inventoryApi.getReports({
      page: 2,
      pageSize: 10,
      taskId: 'task-2',
      status: 'approved',
      dateFrom: '2026-03-10',
      dateTo: '2026-03-29',
    })

    expect(requestMock).toHaveBeenCalledWith({
      url: '/system/objects/InventoryReport/',
      method: 'get',
      params: {
        page: 2,
        page_size: 10,
        task: 'task-2',
        status: 'approved',
        generated_at_from: '2026-03-10',
        generated_at_to: '2026-03-29',
      },
    })
    expect(result.results[0].reportNo).toBe('IRP2026030001')
  })

  it('inventoryApi.generateReport should create through the report object route', async () => {
    requestMock.mockResolvedValue({
      success: true,
      data: {
        id: 'rep-1',
        task: 'task-3',
        templateId: 'tpl-1',
      },
    })

    const result = await inventoryApi.generateReport({
      taskId: 'task-3',
      templateId: 'tpl-1',
    })

    expect(requestMock).toHaveBeenCalledWith({
      url: '/system/objects/InventoryReport/',
      method: 'post',
      data: {
        task: 'task-3',
        templateId: 'tpl-1',
      },
    })
    expect(result.id).toBe('rep-1')
  })

  it('inventoryApi.exportReport should call the report export action route', async () => {
    const blob = new Blob(['report'])
    requestMock.get.mockResolvedValue(blob)

    const result = await inventoryApi.exportReport('rep-1', 'excel')

    expect(requestMock.get).toHaveBeenCalledWith('/system/objects/InventoryReport/rep-1/export/', {
      params: {
        fileFormat: 'excel',
      },
      responseType: 'blob',
      unwrap: 'none',
    })
    expect(result).toBe(blob)
  })

  it('reconciliationApi.delete should use the reconciliation object route base path', async () => {
    requestMock.delete.mockResolvedValue(undefined)

    await reconciliationApi.delete('rec-9')

    expect(requestMock.delete).toHaveBeenCalledWith('/system/objects/InventoryReconciliation/rec-9/')
  })
})
