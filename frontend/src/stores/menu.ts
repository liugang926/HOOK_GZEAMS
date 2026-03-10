import { computed, ref, shallowRef } from 'vue'
import { defineStore } from 'pinia'
import { useI18n } from 'vue-i18n'
import { businessObjectApi, menuApi, type BusinessObject } from '@/api/system'
import { MenuRegistryManager } from '@/router/menuRegistry'
import { translateObjectCodeLabel } from '@/utils/objectDisplay'

// ---------------------------------------------------------------------------
// Standalone types - compatible with both MenuRegistryManager output and API
// ---------------------------------------------------------------------------
export interface LocalMenuItem {
    code: string
    name: string
    url: string
    icon?: string
    order?: number
    group?: string
    groupCode?: string
    groupTranslationKey?: string
    translationKey?: string
    badge?: unknown
}

export interface LocalMenuGroup {
    id: string
    code: string
    name: string
    icon: string
    items: LocalMenuItem[]
    translationKey?: string
    localeNames?: Record<string, string>
    order?: number
}

type AnyRecord = Record<string, unknown>

const normalizeMenuUrl = (value: unknown): string => {
    const raw = String(value || '').trim()
    if (!raw) return ''
    if (raw.startsWith('/')) return raw
    if (/^[a-z]+:\/\//i.test(raw)) return raw
    return `/${raw.replace(/^\/+/, '')}`
}

// ---------------------------------------------------------------------------
// Normalizers (pure functions - no Vue reactivity dependency)
// ---------------------------------------------------------------------------

export function normalizeBusinessObjects(payload: AnyRecord): BusinessObject[] {
    const source: AnyRecord[] = []
    if (Array.isArray(payload)) source.push(...payload)
    if (Array.isArray(payload?.results)) source.push(...payload.results)
    if (Array.isArray(payload?.hardcoded)) source.push(...payload.hardcoded)
    if (Array.isArray(payload?.custom)) source.push(...payload.custom)

    const normalized: BusinessObject[] = []
    const seen = new Set<string>()
    for (const item of source) {
        const code = String(item?.code || '').trim()
        if (!code || seen.has(code)) continue
        seen.add(code)
        normalized.push({
            id: String(item?.id || code),
            code,
            name: String(item?.name || code),
            nameEn: String(item?.nameEn || item?.name_en || ''),
            description: String(item?.description || ''),
            enableWorkflow: item?.enableWorkflow === true,
            enableVersion: item?.enableVersion === true,
            enableSoftDelete: item?.enableSoftDelete !== false,
            isHardcoded: item?.isHardcoded === true || item?.is_hardcoded === true || item?.type === 'hardcoded',
            djangoModelPath: String(item?.djangoModelPath || item?.django_model_path || item?.modelPath || ''),
            tableName: String(item?.tableName || item?.table_name || ''),
            fieldCount: Number(item?.fieldCount || item?.field_count || 0),
            layoutCount: Number(item?.layoutCount || item?.layout_count || 0),
            menuCategory: String(item?.menuCategory || item?.menu_category || ''),
            isMenuHidden: item?.isMenuHidden === true || item?.is_menu_hidden === true,
        })
    }
    return normalized
}

export function normalizeMenuGroups(payload: AnyRecord): LocalMenuGroup[] {
    const source = Array.isArray(payload?.groups) ? (payload.groups as AnyRecord[]) : []

    return source
        .map((group, groupIndex) => {
            const itemsSource = Array.isArray(group?.items) ? (group.items as AnyRecord[]) : []
            const items: LocalMenuItem[] = itemsSource.map((item, itemIndex) => ({
                code: String(item?.code || `item-${groupIndex}-${itemIndex}`),
                name: String(item?.name || item?.translationKey || item?.code || ''),
                url: normalizeMenuUrl(item?.url),
                icon: String(item?.icon || ''),
                order: Number(item?.order || itemIndex + 1),
                group: String(item?.group || item?.groupCode || group?.code || ''),
                groupCode: String(item?.groupCode || group?.code || ''),
                groupTranslationKey: String(item?.groupTranslationKey || group?.translationKey || ''),
                translationKey: String(item?.translationKey || ''),
                badge: item?.badge,
            }))

            return {
                id: String(group?.id || group?.code || group?.name || `group-${groupIndex}`),
                code: String(group?.code || ''),
                name: String(group?.name || group?.translationKey || ''),
                translationKey: String(group?.translationKey || ''),
                localeNames:
                    group?.localeNames && typeof group.localeNames === 'object'
                        ? Object.fromEntries(
                              Object.entries(group.localeNames as Record<string, unknown>)
                                  .map(([locale, text]) => [String(locale), String(text || '').trim()])
                                  .filter(([, text]) => Boolean(text))
                          )
                        : undefined,
                icon: String(group?.icon || 'Menu'),
                order: Number(group?.order || groupIndex + 1),
                items,
            }
        })
        .filter((group) => group.items.length > 0)
}

export function mergeMenuGroups(
    baseGroups: LocalMenuGroup[],
    supplementGroups: LocalMenuGroup[]
): LocalMenuGroup[] {
    const mergedGroups = new Map<string, LocalMenuGroup>()
    const normalizeCode = (value: unknown) => String(value || '').trim().toLowerCase()
    const toItemIdentity = (item: LocalMenuItem) =>
        `${normalizeCode(item.code)}::${normalizeMenuUrl(item.url).toLowerCase()}`

    for (const group of baseGroups) {
        const key = String(group.code || group.id || '').trim()
        if (!key) continue

        mergedGroups.set(key, {
            ...group,
            items: group.items.map((item) => ({
                ...item,
                url: normalizeMenuUrl(item.url),
            })),
        })
    }

    for (const group of supplementGroups) {
        const key = String(group.code || group.id || '').trim()
        if (!key) continue

        const existingGroup = mergedGroups.get(key)
        if (!existingGroup) {
            mergedGroups.set(key, {
                ...group,
                items: [...group.items],
            })
            continue
        }

        const seenItems = new Set(
            existingGroup.items.map((item) => toItemIdentity(item))
        )
        const existingItemIndexByCode = new Map(
            existingGroup.items.map((item, index) => [normalizeCode(item.code), index] as const)
        )

        for (const item of group.items) {
            const normalizedItem: LocalMenuItem = {
                ...item,
                url: normalizeMenuUrl(item.url),
            }
            const itemCode = normalizeCode(normalizedItem.code)
            const existingIndexByCode = itemCode ? existingItemIndexByCode.get(itemCode) : undefined

            if (existingIndexByCode !== undefined) {
                const existingItem = existingGroup.items[existingIndexByCode]
                existingGroup.items[existingIndexByCode] = {
                    ...existingItem,
                    ...normalizedItem,
                    badge: normalizedItem.badge ?? existingItem.badge,
                }
                seenItems.delete(toItemIdentity(existingItem))
                seenItems.add(toItemIdentity(existingGroup.items[existingIndexByCode]))
                continue
            }

            const itemKey = toItemIdentity(normalizedItem)
            if (seenItems.has(itemKey)) continue

            existingGroup.items.push(normalizedItem)
            if (itemCode) {
                existingItemIndexByCode.set(itemCode, existingGroup.items.length - 1)
            }
            seenItems.add(itemKey)
        }

        existingGroup.localeNames = group.localeNames || existingGroup.localeNames
        existingGroup.translationKey = group.translationKey || existingGroup.translationKey
        existingGroup.name = group.name || existingGroup.name
        existingGroup.icon = group.icon || existingGroup.icon
        existingGroup.items.sort((a, b) => (a.order || 0) - (b.order || 0))
    }

    return Array.from(mergedGroups.values())
        .filter((group) => group.items.length > 0)
        .sort((a, b) => (a.order || 0) - (b.order || 0))
}

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useMenuStore = defineStore('menu', () => {
    const { t, te, locale } = useI18n()

    // ----- State -----
    const menuGroups = shallowRef<LocalMenuGroup[]>([])
    const isLoading = ref(false)
    const searchQuery = ref('')

    // ----- Getters -----
    const filteredMenuGroups = computed(() => {
        if (!searchQuery.value) return menuGroups.value

        const query = searchQuery.value.toLowerCase()
        return menuGroups.value
            .map((group) => {
                const groupMatches = getGroupLabel(group).toLowerCase().includes(query)
                const filteredItems = group.items.filter(
                    (item) =>
                        groupMatches ||
                        getItemLabel(item).toLowerCase().includes(query) ||
                        String(item.name || '').toLowerCase().includes(query) ||
                        String(item.code || '').toLowerCase().includes(query),
                )
                return { ...group, items: filteredItems }
            })
            .filter((group) => group.items.length > 0)
    })

    // ----- Label helpers -----
    function getGroupLabel(group: LocalMenuGroup): string {
        const groupName = String(group.name || '').trim()
        const explicitTranslationKey = String(group.translationKey || '').trim()
        const localeNames = group.localeNames || {}
        const currentLocale = String(locale.value || 'zh-CN')

        if (localeNames[currentLocale]) {
            return localeNames[currentLocale]
        }

        if (localeNames['en-US']) {
            return localeNames['en-US']
        }

        if (localeNames['zh-CN']) {
            return localeNames['zh-CN']
        }

        if (explicitTranslationKey && te(explicitTranslationKey)) {
            return t(explicitTranslationKey)
        }

        if (group.code) {
            const translationKey = `menu.categories.${group.code}`
            if (te(translationKey)) {
                return t(translationKey)
            }
            if (groupName.startsWith('menu.categories.') && te(groupName)) {
                return t(groupName)
            }
        }

        return groupName
    }

    function getItemLabel(item: LocalMenuItem): string {
        const itemCode = String(item.code || '').trim()
        const itemName = String(item.name || '').trim()
        const explicitTranslationKey = String(item.translationKey || '').trim()

        if (explicitTranslationKey && te(explicitTranslationKey)) {
            return t(explicitTranslationKey)
        }

        if (itemCode) {
            const objectCodeLabel = translateObjectCodeLabel(itemCode, t as (key: string) => string, te)
            if (objectCodeLabel) {
                return objectCodeLabel
            }

            const menuKey = `menu.menu.${itemCode}`
            if (te(menuKey)) {
                return t(menuKey)
            }

            const routeKey = `menu.routes.${itemCode}`
            if (te(routeKey)) {
                return t(routeKey)
            }
        }

        return itemName
    }

    function getMenuGroupIdentity(group: LocalMenuGroup, index: number): string {
        const code = String(group.code || '').trim()
        if (code) return code

        const name = String(group.name || '').trim()
        if (name) return `${name}-${index}`

        return `group-${index}`
    }

    // ----- Actions -----
    async function fetchMenu(): Promise<void> {
        if (isLoading.value) return
        isLoading.value = true

        try {
            const menuResponse = await menuApi.get()
            const normalizedGroups = normalizeMenuGroups((menuResponse || {}) as unknown as AnyRecord)

            if (normalizedGroups.length > 0) {
                menuGroups.value = normalizedGroups
                return
            }

            const objectsResponse = await businessObjectApi.list({ pageSize: 500 })
            const objects = normalizeBusinessObjects((objectsResponse || {}) as unknown as AnyRecord)
            const registry = new MenuRegistryManager()
            menuGroups.value = registry.generateMenuTree(objects)
        } catch (error) {
            console.error('[useMenuStore] primary fetch failed, attempting fallback', error)

            try {
                const objectsResponse = await businessObjectApi.list({ pageSize: 500 })
                const objects = normalizeBusinessObjects((objectsResponse || {}) as unknown as AnyRecord)
                const registry = new MenuRegistryManager()
                menuGroups.value = registry.generateMenuTree(objects)
            } catch (fallbackError) {
                console.error('[useMenuStore] fallback also failed', fallbackError)
                menuGroups.value = []
            }
        } finally {
            isLoading.value = false
        }
    }

    return {
        // State
        menuGroups,
        isLoading,
        searchQuery,
        // Getters
        filteredMenuGroups,
        // Actions
        fetchMenu,
        getGroupLabel,
        getItemLabel,
        getMenuGroupIdentity,
    }
})
