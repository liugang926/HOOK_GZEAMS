import { computed, type ComputedRef, type Ref } from 'vue'
import type { MenuManagementItem } from '@/api/system'
import {
  getCategoryLocaleName,
  getItemIdentity,
  humanizeCode,
  sortByOrder,
  type EditableCategory,
  type LocaleKey,
} from './shared'

type TranslateFn = (key: string) => string
type HasTranslationFn = (key: string) => boolean

export const useSystemMenuDerivedState = (params: {
  currentLocale: ComputedRef<LocaleKey>
  categories: Ref<EditableCategory[]>
  items: Ref<MenuManagementItem[]>
  search: Ref<string>
  categoryPage: Ref<number>
  categoryPageSize: Ref<number>
  entryPage: Ref<number>
  entryPageSize: Ref<number>
  selectedCategoryCode: Ref<string>
  viewAllEntries: Ref<boolean>
  selectedEntryId: Ref<string>
  collapsedGroupCodes: Ref<string[]>
  t: TranslateFn
  te: HasTranslationFn
}) => {
  const {
    currentLocale,
    categories,
    items,
    search,
    categoryPage,
    categoryPageSize,
    entryPage,
    entryPageSize,
    selectedCategoryCode,
    viewAllEntries,
    selectedEntryId,
    collapsedGroupCodes,
    t,
    te,
  } = params

  const orderedCategories = computed(() => sortByOrder(categories.value))
  const orderedItems = computed(() => sortByOrder(items.value))
  const selectableCategories = computed(() => orderedCategories.value)
  const selectedCategory = computed(() =>
    orderedCategories.value.find((category) => category.originalCode === selectedCategoryCode.value || category.code === selectedCategoryCode.value) || null
  )

  const isItemInCategory = (
    item: Pick<MenuManagementItem, 'groupCode'>,
    category: Pick<EditableCategory, 'code' | 'originalCode'>,
  ) => {
    const groupCode = String(item.groupCode || '').trim()
    return groupCode === category.code.trim() || groupCode === category.originalCode
  }

  const getItemCategory = (item: Pick<MenuManagementItem, 'groupCode'>) =>
    orderedCategories.value.find((category) => isItemInCategory(item, category))

  const getItemsForCategory = (category: Pick<EditableCategory, 'code' | 'originalCode'>) =>
    sortByOrder(items.value.filter((item) => isItemInCategory(item, category)))

  const getCategoryEntryCount = (category: Pick<EditableCategory, 'code' | 'originalCode'>) =>
    items.value.filter((item) => isItemInCategory(item, category)).length

  const getItemLabel = (item: Pick<MenuManagementItem, 'translationKey' | 'name' | 'nameEn' | 'code'>) => {
    if (item.translationKey && te(item.translationKey)) {
      const translated = t(item.translationKey)
      if (translated && !translated.startsWith('menu.')) {
        return translated
      }
    }
    if (currentLocale.value === 'en-US' && item.nameEn) {
      return item.nameEn
    }
    return item.name || item.code
  }

  const getCategoryLabel = (category: Pick<EditableCategory, 'translationKey' | 'name' | 'code' | 'isDefault' | 'localeNames'>) => {
    const localizedName = getCategoryLocaleName(category as EditableCategory, currentLocale.value)
    if (localizedName) return localizedName

    const englishName = getCategoryLocaleName(category as EditableCategory, 'en-US')
    if (englishName) return englishName

    const chineseName = getCategoryLocaleName(category as EditableCategory, 'zh-CN')
    if (chineseName) return chineseName

    const translationKey = String(category.translationKey || '').trim()
    if (translationKey && te(translationKey)) {
      const translated = t(translationKey)
      if (translated && !translated.startsWith('menu.')) {
        return translated
      }
    }

    return String(category.name || humanizeCode(category.code))
  }

  const getItemGroupLabel = (item: Pick<MenuManagementItem, 'groupCode'>) => {
    const category = getItemCategory(item)
    return category ? getCategoryLabel(category) : String(item.groupCode || '')
  }

  const filteredItems = computed(() => {
    const keyword = search.value.trim().toLowerCase()
    if (!keyword) return orderedItems.value

    return orderedItems.value.filter((item) => {
      const label = getItemLabel(item).toLowerCase()
      return label.includes(keyword) || item.code.toLowerCase().includes(keyword) || item.path.toLowerCase().includes(keyword)
    })
  })

  const filteredEntryGroups = computed(() => {
    const keyword = search.value.trim().toLowerCase()
    return orderedCategories.value
      .map((category) => {
        const categoryItems = getItemsForCategory(category)
        const categoryMatches = !keyword || getCategoryLabel(category).toLowerCase().includes(keyword) || category.code.toLowerCase().includes(keyword)
        const groupItems = categoryMatches
          ? categoryItems
          : categoryItems.filter((item) => {
              const label = getItemLabel(item).toLowerCase()
              return label.includes(keyword) || item.code.toLowerCase().includes(keyword) || item.path.toLowerCase().includes(keyword)
            })

        return {
          category,
          items: groupItems,
          visibleCount: groupItems.filter((item) => item.isVisible).length,
        }
      })
      .filter((group) => !keyword || group.items.length > 0)
  })

  const displayedEntryGroups = computed(() => {
    if (viewAllEntries.value || !selectedCategory.value) {
      return filteredEntryGroups.value
    }

    const category = selectedCategory.value
    const keyword = search.value.trim().toLowerCase()
    const categoryItems = getItemsForCategory(category)
    const categoryMatches = !keyword || getCategoryLabel(category).toLowerCase().includes(keyword) || category.code.toLowerCase().includes(keyword)
    const groupItems = categoryMatches
      ? categoryItems
      : categoryItems.filter((item) => {
          const label = getItemLabel(item).toLowerCase()
          return label.includes(keyword) || item.code.toLowerCase().includes(keyword) || item.path.toLowerCase().includes(keyword)
        })

    return [{
      category,
      items: groupItems,
      visibleCount: groupItems.filter((item) => item.isVisible).length,
    }]
  })

  const categoryPageCount = computed(() => Math.max(1, Math.ceil(orderedCategories.value.length / categoryPageSize.value)))
  const entryPageCount = computed(() => Math.max(1, Math.ceil(displayedEntryGroups.value.length / entryPageSize.value)))
  const pagedCategories = computed(() => orderedCategories.value.slice((categoryPage.value - 1) * categoryPageSize.value, categoryPage.value * categoryPageSize.value))
  const pagedEntryGroups = computed(() => displayedEntryGroups.value.slice((entryPage.value - 1) * entryPageSize.value, entryPage.value * entryPageSize.value))
  const visibleEntryGroups = computed(() => viewAllEntries.value ? pagedEntryGroups.value : displayedEntryGroups.value)
  const visibleCategoryCount = computed(() => orderedCategories.value.filter((item) => item.isVisible).length)
  const visibleEntryCount = computed(() => orderedItems.value.filter((item) => item.isVisible).length)
  const lockedEntryCount = computed(() => orderedItems.value.filter((item) => item.isLocked).length)
  const visibleEntryItems = computed(() => visibleEntryGroups.value.flatMap((group) => group.items))
  const selectedEntry = computed<MenuManagementItem | null>(() =>
    visibleEntryItems.value.find((item) => getItemIdentity(item) === selectedEntryId.value) || visibleEntryItems.value[0] || null
  )

  const isGroupCollapsed = (groupCode: string) => collapsedGroupCodes.value.includes(groupCode)
  const syncCollapsedGroups = () => {
    const validCodes = new Set(orderedCategories.value.map((category) => category.code))
    collapsedGroupCodes.value = collapsedGroupCodes.value.filter((code) => validCodes.has(code))
  }

  const syncSelectedEntry = () => {
    if (!visibleEntryItems.value.length) {
      selectedEntryId.value = ''
      return
    }
    if (!selectedEntryId.value || !visibleEntryItems.value.some((item) => getItemIdentity(item) === selectedEntryId.value)) {
      selectedEntryId.value = getItemIdentity(visibleEntryItems.value[0])
    }
  }

  const syncPaginationBounds = () => {
    if (categoryPage.value > categoryPageCount.value) categoryPage.value = categoryPageCount.value
    if (entryPage.value > entryPageCount.value) entryPage.value = entryPageCount.value
  }

  const isSelectedCategory = (category: Pick<EditableCategory, 'originalCode'>) =>
    (selectedCategory.value?.originalCode || selectedCategory.value?.code) === category.originalCode

  const isSelectedEntry = (item: Pick<MenuManagementItem, 'sourceType' | 'sourceCode' | 'code'>) =>
    selectedEntry.value ? getItemIdentity(item) === getItemIdentity(selectedEntry.value) : false

  return {
    orderedCategories,
    orderedItems,
    selectableCategories,
    selectedCategory,
    selectedEntry,
    filteredItems,
    filteredEntryGroups,
    displayedEntryGroups,
    visibleEntryGroups,
    pagedCategories,
    categoryPageCount,
    entryPageCount,
    visibleCategoryCount,
    visibleEntryCount,
    lockedEntryCount,
    getItemCategory,
    getItemsForCategory,
    getCategoryEntryCount,
    getItemLabel,
    getCategoryLabel,
    getItemGroupLabel,
    isGroupCollapsed,
    isSelectedCategory,
    isSelectedEntry,
    syncCollapsedGroups,
    syncSelectedEntry,
    syncPaginationBounds,
  }
}
