import { describe, expect, it } from 'vitest'

import {
  canCancelPortalRequest,
  canSubmitPortalRequest,
  createPortalRequestStatusOptions,
  getPortalRequestCreatePath,
  getPortalRequestDetailPath,
  getPortalRequestStatusTagType,
  type PortalRequestApi,
} from './portalRequestModel'
import type { PortalRequestType } from '@/types/portal'

const apiMap: Record<PortalRequestType, PortalRequestApi> = {
  pickup: {
    list: async () => null,
    submit: async () => null,
    cancel: async () => null,
  },
  transfer: {
    list: async () => null,
    submit: async () => null,
    cancel: async () => null,
  },
  loan: {
    list: async () => null,
    submit: async () => null,
    cancel: async () => null,
  },
  return: {
    list: async () => null,
    submit: async () => null,
    cancel: async () => null,
  }
}

describe('portalRequestModel', () => {
  it('resolves canonical create/detail paths', () => {
    expect(getPortalRequestDetailPath('pickup', 'pu-1')).toBe('/portal/my-requests/pickup/pu-1')
    expect(getPortalRequestDetailPath('transfer', 'tr-1')).toBe('/portal/my-requests/transfer/tr-1')
    expect(getPortalRequestCreatePath('return')).toBe('/objects/AssetReturn/create')
  })

  it('derives submit/cancel availability from request type and status', () => {
    expect(canSubmitPortalRequest('pickup', { status: 'draft' }, apiMap)).toBe(true)
    expect(canSubmitPortalRequest('transfer', { status: 'draft' }, apiMap)).toBe(true)
    expect(canCancelPortalRequest('transfer', { status: 'out_approved' }, apiMap)).toBe(true)
    expect(canCancelPortalRequest('loan', { status: 'pending' }, apiMap)).toBe(true)
    expect(canCancelPortalRequest('return', { status: 'completed' }, apiMap)).toBe(false)
    expect(getPortalRequestStatusTagType('out_approved')).toBe('warning')
    expect(getPortalRequestStatusTagType('returned')).toBe('success')
    expect(getPortalRequestStatusTagType('approved')).toBe('success')
    expect(getPortalRequestStatusTagType('unknown')).toBe('info')
  })

  it('builds request status options per request type', () => {
    const t = (key: string) => key

    expect(createPortalRequestStatusOptions('pickup', t).map((item) => item.value)).toEqual([
      'draft',
      'pending',
      'approved',
      'rejected',
      'completed',
      'cancelled',
    ])

    expect(createPortalRequestStatusOptions('loan', t).map((item) => item.value)).toEqual([
      'draft',
      'pending',
      'approved',
      'borrowed',
      'overdue',
      'returned',
      'rejected',
      'cancelled',
    ])
  })
})
