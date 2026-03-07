import type { BusinessObject } from '@/types/businessObject'

export interface RegistryMenuItem {
    code: string
    name: string
    url: string
    icon?: string
    order?: number
}

export interface RegistryMenuCategory {
    id: string
    code: string
    name: string
    icon: string
    items: RegistryMenuItem[]
}

export class MenuRegistryManager {
    private registeredObjects = new Set<string>()

    // Pre-defined categories
    private initializeEmptyCategories(): Record<string, RegistryMenuCategory> {
        return {
            asset_master: { id: 'asset_master', code: 'asset_master', name: 'menu.categories.asset_master', icon: 'FolderOpened', items: [] },
            asset_operation: { id: 'asset_operation', code: 'asset_operation', name: 'menu.categories.asset_operation', icon: 'Operation', items: [] },
            lifecycle: { id: 'lifecycle', code: 'lifecycle', name: 'menu.categories.lifecycle', icon: 'Refresh', items: [] },
            consumable: { id: 'consumable', code: 'consumable', name: 'menu.categories.consumable', icon: 'Box', items: [] },
            inventory: { id: 'inventory', code: 'inventory', name: 'menu.categories.inventory', icon: 'Box', items: [] },
            finance: { id: 'finance', code: 'finance', name: 'menu.categories.finance', icon: 'Wallet', items: [] },
            organization: { id: 'organization', code: 'organization', name: 'menu.categories.organization', icon: 'OfficeBuilding', items: [] },
            workflow: { id: 'workflow', code: 'workflow', name: 'menu.categories.workflow', icon: 'Connection', items: [] },
            system: { id: 'system', code: 'system', name: 'menu.categories.system', icon: 'Setting', items: [] },
            reports: { id: 'reports', code: 'reports', name: 'menu.categories.reports', icon: 'DataAnalysis', items: [] },
            other: { id: 'other', code: 'other', name: 'menu.categories.other', icon: 'Menu', items: [] }
        }
    }

    private classifyObjectCategory(obj: BusinessObject): string {
        if (obj.menuCategory) {
            return obj.menuCategory.toLowerCase()
        }
        // Fallback classification based on module or code
        const module = (obj.module || '').toLowerCase()
        const code = obj.code.toLowerCase()

        if (code.includes('pickup') || code.includes('transfer') || code.includes('return') || code.includes('loan')) return 'asset_operation'
        if (code.includes('consumable')) return 'consumable'
        if (module.includes('inventory') || code.includes('inventory')) return 'inventory'
        if (
            module.includes('lifecycle') ||
            module.includes('maintenance') ||
            code.includes('maintenance') ||
            code.includes('purchase') ||
            code.includes('receipt') ||
            code.includes('disposal')
        ) return 'lifecycle'
        if (
            module.includes('finance') ||
            module.includes('insurance') ||
            module.includes('lease') ||
            code.includes('finance') ||
            code.includes('voucher') ||
            code.includes('depreciation') ||
            code.includes('insurance') ||
            code.includes('lease') ||
            code.includes('software') ||
            code.includes('license')
        ) return 'finance'
        if (
            module.includes('organization') ||
            code.includes('organization') ||
            code.includes('department') ||
            code.includes('user') ||
            code.includes('role')
        ) return 'organization'
        if (module.includes('workflow') || code.includes('workflow')) return 'workflow'
        if (module.includes('system') || module.includes('admin')) return 'system'
        if (module.includes('asset') || code.includes('asset') || code.includes('location') || code.includes('supplier')) return 'asset_master'

        return 'other'
    }

    public generateMenuTree(objects: BusinessObject[]): RegistryMenuCategory[] {
        const treeMap = this.initializeEmptyCategories()
        this.registeredObjects.clear() // Reset per generation

        for (const obj of objects) {
            if (obj.isMenuHidden) continue

            if (this.registeredObjects.has(obj.code)) {
                console.warn(`Object ${obj.code} is already registered in the menu. Skipping duplicate.`)
                continue
            }

            const categoryId = this.classifyObjectCategory(obj)

            // Ensure dynamic category exists if not predefined
            if (!treeMap[categoryId]) {
                treeMap[categoryId] = {
                    id: categoryId,
                    code: categoryId,
                    name: obj.menuCategory || categoryId,
                    icon: 'Menu',
                    items: []
                }
            }

            treeMap[categoryId].items.push({
                code: obj.code,
                name: obj.nameEn || obj.name || obj.code,
                url: `/objects/${obj.code}`,
                icon: obj.icon || 'Document',
                order: treeMap[categoryId].items.length + 1
            })

            this.registeredObjects.add(obj.code)
        }

        // Convert map to array, filter out empty categories, and sort items
        return Object.values(treeMap)
            .filter(category => category.items.length > 0)
            .map(category => {
                category.items.sort((a, b) => (a.order || 0) - (b.order || 0))
                return category
            })
    }

    public getRegisteredObjects(): Set<string> {
        return new Set(this.registeredObjects)
    }
}
