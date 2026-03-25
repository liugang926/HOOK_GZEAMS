import { describe, expect, it } from 'vitest'

import {
  getLifecycleExtension,
  hasLifecycleExtension,
} from './lifecycleDetailExtensions'

describe('lifecycleDetailExtensions', () => {
  it('resolves lifecycle detail extensions by object code', () => {
    expect(hasLifecycleExtension('Maintenance')).toBe(true)
    expect(hasLifecycleExtension('UnknownObject')).toBe(false)

    const purchaseRequestExtension = getLifecycleExtension('PurchaseRequest')
    expect(purchaseRequestExtension?.workflowSteps?.steps).toEqual([
      'draft',
      'submitted',
      'approved',
      'processing',
      'completed',
    ])
    expect(Boolean(purchaseRequestExtension?.subTable)).toBe(true)
  })

  it('builds detail actions from the separated action registry', () => {
    const assetWarrantyExtension = getLifecycleExtension('AssetWarranty')
    const actions = assetWarrantyExtension?.statusActions('w-1', (key) => key) || []

    expect(actions.map((action) => action.key)).toEqual([
      'activate',
      'renew',
      'recordClaim',
      'cancel',
    ])
    expect(actions.find((action) => action.key === 'renew')?.prompt?.fields).toHaveLength(2)
  })
})
