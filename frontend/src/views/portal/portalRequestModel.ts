import { transferApi } from '@/api/assets'
import { cancelLoan, submitLoan } from '@/api/assets/loans'
import { cancelPickup, submitPickup } from '@/api/assets/pickup'
import { cancelReturn, submitReturn } from '@/api/assets/return'
import { toPaginated } from '@/api/contract'
import { assetLoanApi, assetPickupApi, assetReturnApi } from '@/api/dynamic'
import type { PortalRequestType, PortalStatusOption } from '@/types/portal'

export interface PortalRequestApi {
  list: (params?: Record<string, unknown>) => Promise<any>
  submit?: (id: string) => Promise<any>
  cancel?: (id: string) => Promise<any>
}

type PortalTranslate = (key: string) => string

const portalRequestStatusTranslationKeys: Record<string, string> = {
  draft: 'portal.requests.status.draft',
  pending: 'portal.requests.status.pending',
  out_approved: 'portal.requests.status.outApproved',
  approved: 'portal.requests.status.approved',
  rejected: 'portal.requests.status.rejected',
  confirmed: 'portal.requests.status.confirmed',
  completed: 'portal.requests.status.completed',
  borrowed: 'portal.requests.status.borrowed',
  overdue: 'portal.requests.status.overdue',
  returned: 'portal.requests.status.returned',
  cancelled: 'portal.requests.status.cancelled',
}

const portalRequestStatusOptionsByType: Record<PortalRequestType, string[]> = {
  pickup: ['draft', 'pending', 'approved', 'rejected', 'completed', 'cancelled'],
  transfer: ['draft', 'pending', 'out_approved', 'approved', 'rejected', 'completed', 'cancelled'],
  loan: ['draft', 'pending', 'approved', 'borrowed', 'overdue', 'returned', 'rejected', 'cancelled'],
  return: ['draft', 'pending', 'confirmed', 'completed', 'rejected', 'cancelled'],
}

const portalRequestCancelableStatuses: Record<PortalRequestType, string[]> = {
  pickup: ['draft', 'pending'],
  transfer: ['draft', 'pending', 'out_approved'],
  loan: ['draft', 'pending'],
  return: ['draft', 'pending'],
}

export const getPortalRequestStatusTagType = (status: string) => {
  const tagTypeMap: Record<string, string> = {
    draft: 'info',
    pending: 'warning',
    out_approved: 'warning',
    approved: 'success',
    confirmed: 'success',
    borrowed: 'primary',
    overdue: 'danger',
    returned: 'success',
    rejected: 'danger',
    completed: '',
    cancelled: 'info',
  }
  return tagTypeMap[status] || 'info'
}

const portalRequestObjectCodeMap: Record<PortalRequestType, string> = {
  pickup: 'AssetPickup',
  transfer: 'AssetTransfer',
  loan: 'AssetLoan',
  return: 'AssetReturn',
}

export const portalRequestApiMap: Record<PortalRequestType, PortalRequestApi> = {
  pickup: {
    list: async (params) => toPaginated(await assetPickupApi.list(params as Record<string, any>)),
    submit: submitPickup,
    cancel: cancelPickup,
  },
  transfer: {
    list: async (params) => transferApi.list(params as any),
    submit: transferApi.submit,
    cancel: transferApi.cancel,
  },
  loan: {
    list: async (params) => toPaginated(await assetLoanApi.list(params as Record<string, any>)),
    submit: submitLoan,
    cancel: cancelLoan,
  },
  return: {
    list: async (params) => toPaginated(await assetReturnApi.list(params as Record<string, any>)),
    submit: submitReturn,
    cancel: cancelReturn,
  }
}

export const getPortalRequestDetailPath = (type: PortalRequestType, id: string | number) =>
  `/portal/my-requests/${type}/${id}`

export const getPortalRequestCreatePath = (type: PortalRequestType) =>
  `/objects/${portalRequestObjectCodeMap[type]}/create`

export const createPortalRequestStatusOptions = (
  type: PortalRequestType,
  t: PortalTranslate,
): PortalStatusOption[] => {
  return portalRequestStatusOptionsByType[type].map((status) => ({
    value: status,
    label: t(portalRequestStatusTranslationKeys[status] || status),
  }))
}

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
  return (
    portalRequestCancelableStatuses[type].includes(String(row?.status || ''))
    && Boolean(apiMap[type].cancel)
  )
}
