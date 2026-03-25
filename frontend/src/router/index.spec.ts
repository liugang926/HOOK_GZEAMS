import { describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

import { ADDITIONAL_BUSINESS_OBJECT_ROUTES, buildLegacyObjectAliasRoutes, routes } from './index'

function buildTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes
  })
}

function collectRouteNames(routeRecords: RouteRecordRaw[]): string[] {
  return routeRecords.flatMap((route) => {
    const ownName = typeof route.name === 'string' ? [route.name] : []
    const childNames = Array.isArray(route.children) ? collectRouteNames(route.children) : []
    return [...ownName, ...childNames]
  })
}

describe('router coverage', () => {
  it('should generate 4 alias routes for every additional legacy object route', () => {
    const aliases = buildLegacyObjectAliasRoutes(ADDITIONAL_BUSINESS_OBJECT_ROUTES)
    expect(aliases).toHaveLength(Object.keys(ADDITIONAL_BUSINESS_OBJECT_ROUTES).length * 4)
  })

  it('should redirect key legacy URLs to unified object routes', async () => {
    const router = buildTestRouter()

    await router.push('/assets')
    expect(router.currentRoute.value.fullPath).toBe('/objects/Asset')

    await router.push('/assets/create')
    expect(router.currentRoute.value.fullPath).toBe('/objects/Asset/create')

    await router.push('/assets/create?source=dashboard')
    expect(router.currentRoute.value.fullPath).toBe('/objects/Asset/create?source=dashboard')

    await router.push('/assets/123/edit')
    expect(router.currentRoute.value.fullPath).toBe('/objects/Asset/123?action=edit')

    await router.push('/objects/DisposalRequest/42/edit')
    expect(router.currentRoute.value.fullPath).toBe('/objects/DisposalRequest/42/edit-form')

    await router.push('/assets/lifecycle/maintenance/create')
    expect(router.currentRoute.value.fullPath).toBe('/objects/Maintenance/create')

    await router.push('/assets/lifecycle/maintenance/create?view=calendar')
    expect(router.currentRoute.value.fullPath).toBe('/objects/Maintenance/create?view=calendar')

    await router.push('/assets/lifecycle/purchase-requests?status=draft')
    expect(router.currentRoute.value.fullPath).toBe('/objects/PurchaseRequest?status=draft')

    await router.push('/assets/lifecycle/maintenance?status=in_progress')
    expect(router.currentRoute.value.fullPath).toBe('/objects/Maintenance?status=in_progress')

    await router.push('/assets/lifecycle/asset-warranties?page=2')
    expect(router.currentRoute.value.fullPath).toBe('/objects/AssetWarranty?page=2')

    await router.push('/assets/lifecycle/disposal-requests/create')
    expect(router.currentRoute.value.fullPath).toBe('/objects/DisposalRequest/create')

    await router.push('/assets/lifecycle/asset-receipts/create')
    expect(router.currentRoute.value.fullPath).toBe('/objects/AssetReceipt/create')

    await router.push('/assets/lifecycle/maintenance-plans/create')
    expect(router.currentRoute.value.fullPath).toBe('/objects/MaintenancePlan/create')

    await router.push('/assets/lifecycle/maintenance-tasks/create')
    expect(router.currentRoute.value.fullPath).toBe('/objects/MaintenanceTask/create')

    await router.push('/assets/lifecycle/asset-warranties/create')
    expect(router.currentRoute.value.fullPath).toBe('/objects/AssetWarranty/create')

    await router.push('/assets/lifecycle/asset-warranties/42')
    expect(router.currentRoute.value.fullPath).toBe('/objects/AssetWarranty/42')

    await router.push('/assets/lifecycle/asset-warranties/42?action=renew')
    expect(router.currentRoute.value.fullPath).toBe('/objects/AssetWarranty/42?action=renew')

    await router.push('/inventory/items')
    expect(router.currentRoute.value.fullPath).toBe('/objects/InventoryItem')

    await router.push('/inventory/items?tab=pending')
    expect(router.currentRoute.value.fullPath).toBe('/objects/InventoryItem?tab=pending')

    await router.push('/insurance/policies/42')
    expect(router.currentRoute.value.fullPath).toBe('/objects/InsurancePolicy/42')

    await router.push('/leasing/contracts/create')
    expect(router.currentRoute.value.fullPath).toBe('/objects/LeasingContract/create')

    await router.push('/finance/vouchers')
    expect(router.currentRoute.value.fullPath).toBe('/objects/FinanceVoucher')

    await router.push('/finance/vouchers/v-1')
    expect(router.currentRoute.value.fullPath).toBe('/objects/FinanceVoucher/v-1')
  })

  it('should resolve core system and module routes', () => {
    const router = buildTestRouter()

    expect(router.resolve('/system/page-layouts').name).toBe('PageLayoutList')
    expect(router.resolve('/system/menu-management').name).toBe('MenuManagement')
    expect(router.resolve('/system/menu-layout-management').name).toBe('MenuLayoutManagement')
    expect(router.resolve('/system/branding').name).toBe('SystemBranding')
    expect(router.resolve('/system/module-workbench').name).toBe('ModuleWorkbench')
    expect(router.resolve('/it-assets').name).toBe('ITAssetList')
    expect(router.resolve('/software-licenses/software').name).toBe('SoftwareCatalog')
    expect(router.resolve('/objects/Asset').name).toBe('DynamicObjectList')
  })

  it('should not expose retired lifecycle list route names', () => {
    const routeNames = collectRouteNames(routes)

    expect(routeNames).not.toContain('PurchaseRequestList')
    expect(routeNames).not.toContain('MaintenanceList')
    expect(routeNames).not.toContain('DisposalRequestList')
    expect(routeNames).not.toContain('AssetReceiptList')
    expect(routeNames).not.toContain('MaintenancePlanList')
    expect(routeNames).not.toContain('MaintenanceTaskList')
    expect(routeNames).not.toContain('AssetWarrantyList')
  })
})
