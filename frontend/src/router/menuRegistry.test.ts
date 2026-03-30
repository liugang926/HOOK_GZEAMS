import { describe, expect, it, vi } from 'vitest'
import { MenuRegistryManager } from './menuRegistry'

function makeObj(code: string, overrides: Record<string, any> = {}) {
    return {
        id: code,
        code,
        name: `${code} Display Name`,
        nameEn: '',
        description: '',
        isHardcoded: false,
        enableWorkflow: false,
        enableVersion: false,
        enableSoftDelete: true,
        djangoModelPath: '',
        tableName: '',
        fieldCount: 0,
        layoutCount: 0,
        menuCategory: '',
        isMenuHidden: false,
        ...overrides,
    }
}

describe('MenuRegistryManager', () => {
    it('classifies objects by menuCategory when provided', () => {
        const registry = new MenuRegistryManager()
        const tree = registry.generateMenuTree([
            makeObj('Asset', { menuCategory: 'core', name: '资产', nameEn: 'Asset' }),
            makeObj('PurchaseOrder', { menuCategory: 'financial' }),
        ])

        const coreGroup = tree.find(g => g.code === 'core')
        const financialGroup = tree.find(g => g.code === 'financial')

        expect(coreGroup).toBeDefined()
        expect(coreGroup!.items.some(i => i.code === 'Asset')).toBe(true)
        expect(coreGroup!.items.find(i => i.code === 'Asset')?.localeNames).toEqual({
            'zh-CN': '资产',
            'en-US': 'Asset',
        })
        expect(financialGroup).toBeDefined()
        expect(financialGroup!.items.some(i => i.code === 'PurchaseOrder')).toBe(true)
    })

    it('excludes objects with isMenuHidden: true', () => {
        const registry = new MenuRegistryManager()
        const tree = registry.generateMenuTree([
            makeObj('Asset', { menuCategory: 'core' }),
            makeObj('InternalLog', { isMenuHidden: true }),
        ])

        const allItems = tree.flatMap(g => g.items)
        expect(allItems.find(i => i.code === 'InternalLog')).toBeUndefined()
        expect(allItems.find(i => i.code === 'Asset')).toBeDefined()
    })

    it('excludes detail objects from top-level navigation', () => {
        const registry = new MenuRegistryManager()
        const tree = registry.generateMenuTree([
            makeObj('AssetPickup', { menuCategory: 'asset_operation', objectRole: 'root' }),
            makeObj('PickupItem', {
                menuCategory: 'asset_operation',
                objectRole: 'detail',
                isTopLevelNavigable: false,
            }),
        ])

        const allItems = tree.flatMap(g => g.items)
        expect(allItems.find(i => i.code === 'AssetPickup')).toBeDefined()
        expect(allItems.find(i => i.code === 'PickupItem')).toBeUndefined()
    })

    it('excludes audit log objects and standalone-route-disabled objects from fallback navigation', () => {
        const registry = new MenuRegistryManager()
        const tree = registry.generateMenuTree([
            makeObj('Asset', { menuCategory: 'asset_master', objectRole: 'root' }),
            makeObj('AssetStatusLog', {
                menuCategory: 'asset_master',
                objectRole: 'log',
                isTopLevelNavigable: false,
                allowStandaloneRoute: false,
            }),
            makeObj('ConfigurationChange', {
                menuCategory: 'system',
                objectRole: 'log',
                allowStandaloneRoute: false,
            }),
        ])

        const allItems = tree.flatMap(g => g.items)
        expect(allItems.find(i => i.code === 'Asset')).toBeDefined()
        expect(allItems.find(i => i.code === 'AssetStatusLog')).toBeUndefined()
        expect(allItems.find(i => i.code === 'ConfigurationChange')).toBeUndefined()
    })

    it('deduplicates objects by code', () => {
        const spy = vi.spyOn(console, 'warn').mockImplementation(() => { })
        const registry = new MenuRegistryManager()
        const tree = registry.generateMenuTree([
            makeObj('Asset', { menuCategory: 'core' }),
            makeObj('Asset', { menuCategory: 'core', name: 'Duplicate' }),
        ])

        const allItems = tree.flatMap(g => g.items)
        const assetItems = allItems.filter(i => i.code === 'Asset')
        expect(assetItems).toHaveLength(1)
        spy.mockRestore()
    })

    it('does not return empty categories', () => {
        const registry = new MenuRegistryManager()
        const tree = registry.generateMenuTree([
            makeObj('Asset', { menuCategory: 'core' }),
        ])

        for (const group of tree) {
            expect(group.items.length).toBeGreaterThan(0)
        }
    })

    it('falls back to "other" when menuCategory is unknown or empty', () => {
        const registry = new MenuRegistryManager()
        const tree = registry.generateMenuTree([
            makeObj('CustomWidget'),
        ])

        const otherGroup = tree.find(g => g.code === 'other')
        expect(otherGroup).toBeDefined()
        expect(otherGroup!.items.some(i => i.code === 'CustomWidget')).toBe(true)
    })

    it('does not inject static system routes in frontend fallback registry', () => {
        const registry = new MenuRegistryManager()
        const tree = registry.generateMenuTree([])

        expect(tree.find(g => g.code === 'system')).toBeUndefined()
    })
})
