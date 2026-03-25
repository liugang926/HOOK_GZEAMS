import { describe, expect, it } from 'vitest'

import {
  canCancelPortalRequest,
  canSubmitPortalRequest,
  getPortalRequestCreatePath,
  getPortalRequestDetailPath,
  getPortalRequestStatusTagType,
  type PortalRequestApi,
  type PortalRequestType,
} from './portalRequestModel'

const apiMap: Record<PortalRequestType, PortalRequestApi> = {
  purchase: {
    list: async () => null,
    submit: async () => null,
    cancel: async () => null,
  },
  maintenance: {
    list: async () => null,
    cancel: async () => null,
  },
  disposal: {
    list: async () => null,
    submit: async () => null,
    cancel: async () => null,
  }
}

describe('portalRequestModel', () => {
  it('resolves canonical create/detail paths', () => {
    expect(getPortalRequestDetailPath('purchase', 'pr-1')).toBe('/objects/PurchaseRequest/pr-1')
    expect(getPortalRequestDetailPath('maintenance', 'mx-1')).toBe('/objects/Maintenance/mx-1')
    expect(getPortalRequestCreatePath('disposal')).toBe('/objects/DisposalRequest/create')
  })

  it('derives submit/cancel availability from request type and status', () => {
    expect(canSubmitPortalRequest('purchase', { status: 'draft' }, apiMap)).toBe(true)
    expect(canSubmitPortalRequest('maintenance', { status: 'draft' }, apiMap)).toBe(false)
    expect(canCancelPortalRequest('maintenance', { status: 'pending' }, apiMap)).toBe(true)
    expect(canCancelPortalRequest('disposal', { status: 'completed' }, apiMap)).toBe(false)
    expect(getPortalRequestStatusTagType('approved')).toBe('success')
    expect(getPortalRequestStatusTagType('unknown')).toBe('info')
  })
})
