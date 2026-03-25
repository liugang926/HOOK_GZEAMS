import { beforeEach, describe, expect, it, vi } from 'vitest'

const postMock = vi.fn()
const getMock = vi.fn()

const buildDynamicClientMock = () => ({
  list: vi.fn(),
  get: vi.fn(),
  create: vi.fn(),
  update: vi.fn(),
  delete: vi.fn()
})

const purchaseRequestClientMock = buildDynamicClientMock()
const assetReceiptClientMock = buildDynamicClientMock()
const maintenanceClientMock = buildDynamicClientMock()
const maintenancePlanClientMock = buildDynamicClientMock()
const maintenanceTaskClientMock = buildDynamicClientMock()
const disposalRequestClientMock = buildDynamicClientMock()
const assetWarrantyClientMock = buildDynamicClientMock()

vi.mock('@/utils/request', () => ({
  default: {
    post: postMock,
    get: getMock
  }
}))

vi.mock('@/api/dynamic', () => ({
  purchaseRequestApi: purchaseRequestClientMock,
  assetReceiptApi: assetReceiptClientMock,
  maintenanceApi: maintenanceClientMock,
  maintenancePlanApi: maintenancePlanClientMock,
  maintenanceTaskApi: maintenanceTaskClientMock,
  disposalRequestApi: disposalRequestClientMock,
  assetWarrantyApi: assetWarrantyClientMock
}))

describe('lifecycleApi modules', () => {
  beforeEach(() => {
    postMock.mockReset()
    getMock.mockReset()

    for (const client of [
      purchaseRequestClientMock,
      assetReceiptClientMock,
      maintenanceClientMock,
      maintenancePlanClientMock,
      maintenanceTaskClientMock,
      disposalRequestClientMock,
      assetWarrantyClientMock
    ]) {
      client.list.mockReset()
      client.get.mockReset()
      client.create.mockReset()
      client.update.mockReset()
      client.delete.mockReset()
    }
  })

  it('delegates lifecycle CRUD wrappers to dynamic object clients', async () => {
    purchaseRequestClientMock.list.mockResolvedValue({
      success: true,
      data: {
        count: 1,
        next: null,
        previous: null,
        results: [{ id: 'pr-1', request_no: 'PR-001' }]
      }
    })
    purchaseRequestClientMock.get.mockResolvedValue({
      success: true,
      data: { id: 'pr-1', request_no: 'PR-001' }
    })
    purchaseRequestClientMock.create.mockResolvedValue({
      success: true,
      data: { id: 'pr-2' }
    })
    purchaseRequestClientMock.update.mockResolvedValue({
      success: true,
      data: { id: 'pr-1', status: 'approved' }
    })
    purchaseRequestClientMock.delete.mockResolvedValue({
      success: true,
      data: null
    })

    const { purchaseRequestCrudApi } = await import('@/api/lifecycleCrudAdapters')

    const listResult = await purchaseRequestCrudApi.list({ status: 'submitted' })
    const detailResult = await purchaseRequestCrudApi.detail('pr-1')
    const createdResult = await purchaseRequestCrudApi.create({ request_no: 'PR-002' })
    const updatedResult = await purchaseRequestCrudApi.update('pr-1', { status: 'approved' })
    await purchaseRequestCrudApi.delete('pr-1')

    expect(listResult.count).toBe(1)
    expect(listResult.results[0].id).toBe('pr-1')
    expect(detailResult).toEqual({ id: 'pr-1', request_no: 'PR-001' })
    expect(createdResult).toEqual({ id: 'pr-2' })
    expect(updatedResult).toEqual({ id: 'pr-1', status: 'approved' })
    expect(purchaseRequestClientMock.list).toHaveBeenCalledWith({ status: 'submitted' })
    expect(purchaseRequestClientMock.get).toHaveBeenCalledWith('pr-1')
    expect(purchaseRequestClientMock.create).toHaveBeenCalledWith({ request_no: 'PR-002' })
    expect(purchaseRequestClientMock.update).toHaveBeenCalledWith('pr-1', { status: 'approved' })
    expect(purchaseRequestClientMock.delete).toHaveBeenCalledWith('pr-1')
  })

  it('keeps lifecycle-specific action endpoints on request client', async () => {
    const { assetReceiptCrudApi } = await import('@/api/lifecycleCrudAdapters')
    const { assetReceiptActionApi, maintenanceTaskActionApi, assetWarrantyActionApi } = await import('@/api/lifecycleActionApi')

    expect('update' in assetReceiptCrudApi).toBe(false)
    expect('create' in maintenanceTaskActionApi).toBe(false)

    await assetReceiptActionApi.submitInspection('receipt-1')
    await maintenanceTaskActionApi.overdue()
    await assetWarrantyActionApi.renew('warranty-1', {
      end_date: '2026-12-31',
      warranty_cost: 320
    })

    expect(postMock).toHaveBeenNthCalledWith(
      1,
      '/lifecycle/asset-receipts/receipt-1/submit_inspection/'
    )
    expect(getMock).toHaveBeenNthCalledWith(1, '/lifecycle/maintenance-tasks/overdue/')
    expect(postMock).toHaveBeenNthCalledWith(
      2,
      '/lifecycle/asset-warranties/warranty-1/renew/',
      { end_date: '2026-12-31', warranty_cost: 320 }
    )
  })
})
