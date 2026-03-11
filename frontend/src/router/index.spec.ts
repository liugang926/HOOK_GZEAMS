import { describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { ADDITIONAL_BUSINESS_OBJECT_ROUTES, buildLegacyObjectAliasRoutes, routes } from './index'

function buildTestRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes
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

    await router.push('/assets/123/edit')
    expect(router.currentRoute.value.fullPath).toBe('/objects/Asset/123?action=edit')

    await router.push('/inventory/items')
    expect(router.currentRoute.value.fullPath).toBe('/objects/InventoryItem')

    await router.push('/insurance/policies/42')
    expect(router.currentRoute.value.fullPath).toBe('/objects/InsurancePolicy/42')

    await router.push('/leasing/contracts/create')
    expect(router.currentRoute.value.fullPath).toBe('/objects/LeasingContract/create')
  })

  it('should resolve core system and module routes', () => {
    const router = buildTestRouter()

    expect(router.resolve('/system/page-layouts').name).toBe('PageLayoutList')
    expect(router.resolve('/system/menu-management').name).toBe('MenuManagement')
    expect(router.resolve('/system/menu-layout-management').name).toBe('MenuLayoutManagement')
    expect(router.resolve('/system/branding').name).toBe('SystemBranding')
    expect(router.resolve('/system/module-workbench').name).toBe('ModuleWorkbench')
    expect(router.resolve('/finance/vouchers').name).toBe('VoucherList')
    expect(router.resolve('/it-assets').name).toBe('ITAssetList')
    expect(router.resolve('/software-licenses/software').name).toBe('SoftwareCatalog')
    expect(router.resolve('/objects/Asset').name).toBe('DynamicObjectList')
  })
})

