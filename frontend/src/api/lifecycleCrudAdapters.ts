import { toData, toPaginated } from '@/api/contract'
import type { ObjectClient } from '@/api/dynamic'
import {
  purchaseRequestApi as dynamicPurchaseRequestApi,
  assetReceiptApi as dynamicAssetReceiptApi,
  maintenanceApi as dynamicMaintenanceApi,
  maintenancePlanApi as dynamicMaintenancePlanApi,
  maintenanceTaskApi as dynamicMaintenanceTaskApi,
  disposalRequestApi as dynamicDisposalRequestApi,
  assetWarrantyApi as dynamicAssetWarrantyApi
} from '@/api/dynamic'
import type { PaginatedResponse } from '@/types/api'

type QueryParams = Record<string, unknown>
type MutationPayload = Record<string, unknown>

const createLifecycleReadApi = (client: ObjectClient) => ({
  async list(params?: QueryParams): Promise<PaginatedResponse<any>> {
    return toPaginated<any>(await client.list(params as Record<string, any> | undefined))
  },
  async detail(id: string): Promise<any> {
    return toData<any>(await client.get(id))
  }
})

const createLifecycleCreateApi = (client: ObjectClient) => ({
  async create(data: MutationPayload): Promise<any> {
    return toData<any>(await client.create(data as Record<string, any>))
  }
})

const createLifecycleUpdateApi = (client: ObjectClient) => ({
  async update(id: string, data: MutationPayload): Promise<any> {
    return toData<any>(await client.update(id, data as Record<string, any>))
  }
})

const createLifecycleDeleteApi = (client: ObjectClient) => ({
  async delete(id: string): Promise<void> {
    await client.delete(id)
  }
})

export const purchaseRequestCrudApi = {
  ...createLifecycleReadApi(dynamicPurchaseRequestApi),
  ...createLifecycleCreateApi(dynamicPurchaseRequestApi),
  ...createLifecycleUpdateApi(dynamicPurchaseRequestApi),
  ...createLifecycleDeleteApi(dynamicPurchaseRequestApi),
}

export const assetReceiptCrudApi = {
  ...createLifecycleReadApi(dynamicAssetReceiptApi),
  ...createLifecycleCreateApi(dynamicAssetReceiptApi),
}

export const maintenanceCrudApi = {
  ...createLifecycleReadApi(dynamicMaintenanceApi),
  ...createLifecycleCreateApi(dynamicMaintenanceApi),
  ...createLifecycleUpdateApi(dynamicMaintenanceApi),
}

export const maintenancePlanCrudApi = {
  ...createLifecycleReadApi(dynamicMaintenancePlanApi),
  ...createLifecycleCreateApi(dynamicMaintenancePlanApi),
  ...createLifecycleUpdateApi(dynamicMaintenancePlanApi),
}

export const maintenanceTaskCrudApi = {
  ...createLifecycleReadApi(dynamicMaintenanceTaskApi),
}

export const disposalRequestCrudApi = {
  ...createLifecycleReadApi(dynamicDisposalRequestApi),
  ...createLifecycleCreateApi(dynamicDisposalRequestApi),
  ...createLifecycleUpdateApi(dynamicDisposalRequestApi),
  ...createLifecycleDeleteApi(dynamicDisposalRequestApi),
}

export const assetWarrantyCrudApi = {
  ...createLifecycleReadApi(dynamicAssetWarrantyApi),
  ...createLifecycleCreateApi(dynamicAssetWarrantyApi),
  ...createLifecycleUpdateApi(dynamicAssetWarrantyApi),
}
