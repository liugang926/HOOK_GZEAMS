import { describe, expect, it } from 'vitest'
import {
  getLifecycleListStatusTranslationKey,
  getLifecycleListStatusType,
  getLifecycleQuickFilterDefinitions,
  getLifecycleRowActionDefinitions,
} from './lifecycleListExtensions'

describe('lifecycleListExtensions', () => {
  it('resolves lifecycle-specific status translation keys', () => {
    expect(getLifecycleListStatusTranslationKey('PurchaseRequest', 'submitted')).toBe(
      'assets.lifecycle.purchaseRequest.status.submitted'
    )
    expect(getLifecycleListStatusTranslationKey('FinanceVoucher', 'submitted')).toBe(
      'finance.status.submitted'
    )
    expect(getLifecycleListStatusTranslationKey('MaintenanceTask', 'pending')).toBe(
      'assets.lifecycle.maintenanceTask.status.pending'
    )
    expect(getLifecycleListStatusTranslationKey('UnknownObject', 'pending')).toBeNull()
  })

  it('resolves lifecycle-specific status badge types', () => {
    expect(getLifecycleListStatusType('AssetReceipt', 'passed')).toBe('success')
    expect(getLifecycleListStatusType('Maintenance', 'in_progress')).toBe('primary')
    expect(getLifecycleListStatusType('FinanceVoucher', 'posted')).toBe('success')
    expect(getLifecycleListStatusType('UnknownObject', 'draft')).toBeNull()
  })

  it('exposes maintenance task quick filters with active state', () => {
    const quickFilters = getLifecycleQuickFilterDefinitions('MaintenanceTask', 'today')

    expect(quickFilters.map((item) => item.key)).toEqual(['overdue', 'today', 'all'])
    expect(quickFilters.find((item) => item.key === 'today')?.active).toBe(true)
    expect(getLifecycleQuickFilterDefinitions('PurchaseRequest', 'all')).toEqual([])
  })

  it('filters row actions by object-specific status visibility rules', () => {
    expect(
      getLifecycleRowActionDefinitions('PurchaseRequest', { status: 'draft' }).map((item) => item.key)
    ).toEqual(['submit', 'cancel'])

    expect(
      getLifecycleRowActionDefinitions('MaintenancePlan', { status: 'active' }).map((item) => item.key)
    ).toEqual(['pause', 'generateTasks'])

    expect(
      getLifecycleRowActionDefinitions('AssetWarranty', { status: 'expired' }).map((item) => item.key)
    ).toEqual([])

    expect(
      getLifecycleRowActionDefinitions('FinanceVoucher', { status: 'approved' }).map((item) => item.key)
    ).toEqual(['post', 'retryPush'])

    expect(
      getLifecycleRowActionDefinitions('FinanceVoucher', { status: 'posted' }).map((item) => item.key)
    ).toEqual(['retryPush'])
  })
})
