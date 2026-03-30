export type PortalRequestType = 'pickup' | 'transfer' | 'loan' | 'return'

export interface PortalStatusOption {
  value: string
  label: string
}

export interface PortalAssetRecord {
  id: string
  assetCode?: string
  code?: string
  name?: string
  assetName?: string
  categoryDisplay?: string
  categoryName?: string
  status?: string
  statusDisplay?: string
  locationDisplay?: string
  locationName?: string
  currentValue?: number | string | null
  netValue?: number | string | null
}

export interface PortalRequestRecord {
  id: string
  code?: string
  requestNo?: string
  pickupNo?: string
  transferNo?: string
  loanNo?: string
  returnNo?: string
  title?: string
  assetName?: string
  reason?: string
  status?: string
  statusDisplay?: string
  createdAt?: string
  updatedAt?: string
}

export interface PortalTaskRecord {
  id: string
  title?: string
  taskName?: string
  nodeName?: string
  businessTitle?: string
  instanceTitle?: string
  initiatorDisplay?: string
  createdBy?: string
  createdAt?: string
  assignedAt?: string
}
