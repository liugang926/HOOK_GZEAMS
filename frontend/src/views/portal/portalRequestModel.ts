import {
  purchaseRequestCrudApi,
  maintenanceCrudApi,
  disposalRequestCrudApi
} from '@/api/lifecycleCrudAdapters'
import {
  purchaseRequestActionApi,
  maintenanceActionApi,
  disposalRequestActionApi
} from '@/api/lifecycleActionApi'

export type PortalRequestType = 'purchase' | 'maintenance' | 'disposal'

export interface PortalRequestApi {
  list: (params?: Record<string, unknown>) => Promise<any>
  submit?: (id: string) => Promise<any>
  cancel?: (id: string) => Promise<any>
}

export const getPortalRequestStatusTagType = (status: string) => {
  const tagTypeMap: Record<string, string> = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger',
    completed: '',
    cancelled: 'info',
  }
  return tagTypeMap[status] || 'info'
}

const portalRequestObjectCodeMap: Record<PortalRequestType, string> = {
  purchase: 'PurchaseRequest',
  maintenance: 'Maintenance',
  disposal: 'DisposalRequest',
}

export const portalRequestApiMap: Record<PortalRequestType, PortalRequestApi> = {
  purchase: {
    list: purchaseRequestCrudApi.list,
    submit: purchaseRequestActionApi.submit,
    cancel: purchaseRequestActionApi.cancel,
  },
  maintenance: {
    list: maintenanceCrudApi.list,
    cancel: maintenanceActionApi.cancel,
  },
  disposal: {
    list: disposalRequestCrudApi.list,
    submit: disposalRequestActionApi.submit,
    cancel: disposalRequestActionApi.cancel,
  }
}

export const getPortalRequestDetailPath = (type: PortalRequestType, id: string | number) =>
  `/objects/${portalRequestObjectCodeMap[type]}/${id}`

export const getPortalRequestCreatePath = (type: PortalRequestType) =>
  `/objects/${portalRequestObjectCodeMap[type]}/create`

export const canSubmitPortalRequest = (
  type: PortalRequestType,
  row: Record<string, any>,
  apiMap: Record<PortalRequestType, PortalRequestApi> = portalRequestApiMap
) => {
  return row?.status === 'draft' && Boolean(apiMap[type].submit)
}

export const canCancelPortalRequest = (
  type: PortalRequestType,
  row: Record<string, any>,
  apiMap: Record<PortalRequestType, PortalRequestApi> = portalRequestApiMap
) => {
  return ['draft', 'pending'].includes(String(row?.status || '')) && Boolean(apiMap[type].cancel)
}
