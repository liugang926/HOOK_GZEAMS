import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { menuApi, type MenuManagementItem } from '@/api/system'
import { languageApi } from '@/api/translations'
import { useLocaleStore } from '@/stores/locale'
import { useMenuStore } from '@/stores/menu'
import {
  CATEGORY_EDIT_LOCALES,
  MANAGEMENT_COPY,
  getCategoryFallbackName,
  getCategoryLocaleName,
  getItemIdentity,
  hydrateCategory,
  normalizeIconList,
  normalizeLanguageCodes,
  normalizeLocaleNames,
  resolveIcon,
  syncCategoryFallbackName,
  type EditableCategory,
  type LocaleKey,
} from './shared'
import {
  applyGroupOrder,
  buildGroupCodeMap,
  moveCategoryList,
  normalizeOrder,
  reorderByPageMove,
  syncItemCollections,
} from './reorder'
import { useSystemMenuDerivedState } from './useSystemMenuDerivedState'

const isTestRuntime = Boolean(import.meta.env?.MODE === 'test' || import.meta.env?.VITEST)

const getErrorMessage = (error: unknown) => (
  error instanceof Error && error.message
    ? error.message
    : ''
)

const reportMenuManagementError = (
  scope: 'load failed' | 'save failed' | 'refresh runtime menu failed',
  error: unknown,
) => {
  if (isTestRuntime) return

  const message = getErrorMessage(error)
  if (scope === 'save failed' && message) {
    return
  }

  console.error(`[menu-management] ${scope}`, error)
}

export const useSystemMenuManagement = () => {
  const localeStore = useLocaleStore()
  const menuStore = useMenuStore()
  const router = useRouter()
  const { t, te } = useI18n()

  const loading = ref(false)
  const saving = ref(false)
  const search = ref('')
  const categories = ref<EditableCategory[]>([])
  const items = ref<MenuManagementItem[]>([])
  const iconLibrary = ref<string[]>([])
  const activeLanguageCodes = ref<string[]>([...CATEGORY_EDIT_LOCALES])
  const categoryPage = ref(1)
  const categoryPageSize = ref(4)
  const entryPage = ref(1)
  const entryPageSize = ref(3)
  const collapsedGroupCodes = ref<string[]>([])
  const selectedCategoryCode = ref('')
  const viewAllEntries = ref(false)
  const selectedEntryId = ref('')

  const currentLocale = computed<LocaleKey>(() => localeStore.currentLocale === 'en-US' ? 'en-US' : 'zh-CN')
  const copy = computed(() => MANAGEMENT_COPY[currentLocale.value])
  const availableIcons = computed(() =>
    Array.from(
      new Set([
        ...iconLibrary.value,
        ...categories.value.map((category) => String(category.icon || '').trim()).filter(Boolean),
      ]),
    ),
  )

  const extraLanguageCount = computed(() =>
    activeLanguageCodes.value.filter((code) => !CATEGORY_EDIT_LOCALES.includes(code as LocaleKey)).length
  )

  const {
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
  } = useSystemMenuDerivedState({
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
  })

  const getGroupToggleLabel = (groupCode: string) => isGroupCollapsed(groupCode) ? copy.value.toggles.expand : copy.value.toggles.collapse
  const toggleGroupCollapse = (groupCode: string) => {
    collapsedGroupCodes.value = isGroupCollapsed(groupCode)
      ? collapsedGroupCodes.value.filter((code) => code !== groupCode)
      : [...collapsedGroupCodes.value, groupCode]
  }

  const selectCategory = (category: Pick<EditableCategory, 'originalCode'>) => {
    selectedCategoryCode.value = category.originalCode
    viewAllEntries.value = false
  }

  const selectEntry = (item: Pick<MenuManagementItem, 'sourceType' | 'sourceCode' | 'code'>) => {
    selectedEntryId.value = getItemIdentity(item)
  }

  const handleCategoryPageSizeChange = (value: number) => {
    categoryPageSize.value = value
    categoryPage.value = 1
  }

  const handleEntryPageSizeChange = (value: number) => {
    entryPageSize.value = value
    entryPage.value = 1
  }

  const canMoveCategory = (originalCode: string, offset: -1 | 1) => {
    const index = orderedCategories.value.findIndex((item) => item.originalCode === originalCode)
    const targetIndex = index + offset
    return index >= 0 && targetIndex >= 0 && targetIndex < orderedCategories.value.length
  }

  const moveCategory = (originalCode: string, offset: -1 | 1) => {
    categories.value = moveCategoryList(orderedCategories.value, originalCode, offset)
  }

  const handleCategoryDrag = (oldIndex: number, newIndex: number) => {
    const reordered = reorderByPageMove(
      orderedCategories.value,
      pagedCategories.value,
      oldIndex,
      newIndex,
      (item) => item.originalCode,
    )
    normalizeOrder(reordered)
    categories.value = reordered
  }

  const canMoveItem = (item: Pick<MenuManagementItem, 'groupCode' | 'sourceType' | 'sourceCode' | 'code'>, offset: -1 | 1) => {
    const category = getItemCategory(item)
    if (!category) return false
    const current = getItemsForCategory(category)
    const index = current.findIndex((entry) => getItemIdentity(entry) === getItemIdentity(item))
    const targetIndex = index + offset
    return index >= 0 && targetIndex >= 0 && targetIndex < current.length
  }

  const moveItem = (item: Pick<MenuManagementItem, 'groupCode' | 'sourceType' | 'sourceCode' | 'code'>, offset: -1 | 1) => {
    const category = getItemCategory(item)
    if (!category) return
    const current = [...getItemsForCategory(category)]
    const index = current.findIndex((entry) => getItemIdentity(entry) === getItemIdentity(item))
    const targetIndex = index + offset
    if (index < 0 || targetIndex < 0 || targetIndex >= current.length) return
    ;[current[index], current[targetIndex]] = [current[targetIndex], current[index]]
    const updates = new Map<string, { groupCode: string; order: number }>()
    applyGroupOrder(category, current, updates)
    items.value = syncItemCollections(items.value, updates)
  }

  const handleEntryBoardDrag = (sourceGroupCode: string, targetGroupCode: string, oldIndex: number, newIndex: number) => {
    const sourceCategory = orderedCategories.value.find((category) => category.code === sourceGroupCode)
    const targetCategory = orderedCategories.value.find((category) => category.code === targetGroupCode)
    if (!sourceCategory || !targetCategory) return

    const sourceItems = [...getItemsForCategory(sourceCategory)]
    const targetItems = sourceCategory.originalCode === targetCategory.originalCode ? sourceItems : [...getItemsForCategory(targetCategory)]
    const [movedItem] = sourceItems.splice(oldIndex, 1)
    if (!movedItem) return

    targetItems.splice(newIndex, 0, { ...movedItem, groupCode: targetCategory.code.trim() })

    const updates = new Map<string, { groupCode: string; order: number }>()
    applyGroupOrder(targetCategory, targetItems, updates)
    if (sourceCategory.originalCode !== targetCategory.originalCode) {
      applyGroupOrder(sourceCategory, sourceItems, updates)
    }
    items.value = syncItemCollections(items.value, updates)
  }

  const reloadManagement = async () => {
    loading.value = true
    try {
      const [payloadResult, configResult, languagesResult] = await Promise.allSettled([
        menuApi.management(),
        menuApi.config(),
        languageApi.getActive(),
      ])

      if (payloadResult.status !== 'fulfilled') throw payloadResult.reason

      if (configResult.status === 'fulfilled') {
        iconLibrary.value = normalizeIconList(configResult.value)
      }
      if (languagesResult.status === 'fulfilled') {
        const loadedCodes = normalizeLanguageCodes(languagesResult.value)
        activeLanguageCodes.value = loadedCodes.length ? loadedCodes : [...CATEGORY_EDIT_LOCALES]
      }

      const payload = payloadResult.value
      categories.value = payload.categories
        .map((category) => hydrateCategory(category, currentLocale.value))
        .map((category) => syncCategoryFallbackName(category))
      items.value = payload.items
      if (!selectedCategoryCode.value && payload.categories.length) {
        selectedCategoryCode.value = payload.categories[0].code
      }
      syncSelectedEntry()
      syncCollapsedGroups()
      syncPaginationBounds()
    } catch (error) {
      reportMenuManagementError('load failed', error)
      ElMessage.error(copy.value.messages.loadFailed)
    } finally {
      loading.value = false
    }
  }

  const addLocalizedCategory = () => {
    let index = categories.value.filter((item) => !item.isDefault).length + 1
    while (categories.value.some((item) => item.code === `custom_group_${index}` || item.originalCode === `custom_group_${index}`)) {
      index += 1
    }

    categories.value.push(syncCategoryFallbackName({
      code: `custom_group_${index}`,
      originalCode: `custom_group_${index}`,
      name: `Custom Group ${index}`,
      translationKey: '',
      localeNames: {
        'zh-CN': `自定义分类 ${index}`,
        'en-US': `Custom Group ${index}`,
      },
      icon: 'Menu',
      order: (Math.max(0, ...categories.value.map((item) => item.order)) || 0) + 10,
      isVisible: true,
      isLocked: false,
      isDefault: false,
      entryCount: 0,
      supportsDelete: true,
    }))
    categoryPage.value = categoryPageCount.value
  }

  const updateCategoryLocaleName = (category: EditableCategory, locale: LocaleKey, value: string) => {
    category.localeNames = {
      ...category.localeNames,
      [locale]: value.trim(),
    }
    syncCategoryFallbackName(category)
  }

  const removeCategory = async (originalCode: string) => {
    const category = categories.value.find((item) => item.originalCode === originalCode)
    if (!category) return

    const currentCode = category.code.trim()
    const inUse = items.value.some((item) => item.groupCode === currentCode || item.groupCode === originalCode)
    if (inUse) {
      ElMessage.warning(copy.value.messages.categoryInUse)
      return
    }

    try {
      await ElMessageBox.confirm(
        copy.value.messages.confirmDeleteMessage.replace('{name}', category.name || currentCode),
        copy.value.messages.confirmDeleteTitle,
        { type: 'warning' },
      )
    } catch {
      return
    }

    categories.value = categories.value.filter((item) => item.originalCode !== originalCode)
    syncPaginationBounds()
  }

  const openCategoryTranslations = async (category: EditableCategory) => {
    const target = category.translationTarget
    if (!target?.objectId) {
      ElMessage.warning(copy.value.messages.saveBeforeTranslations)
      return
    }

    await router.push({
      name: 'TranslationList',
      query: {
        type: 'object_field',
        content_type_model: target.contentTypeModel,
        object_id: target.objectId,
        field_name: target.fieldName,
        show_all_languages: '1',
        focus_label: getCategoryFallbackName(category),
        focus_code: category.code,
      },
    })
  }

  const validateLocalizedCategories = () => {
    const seen = new Set<string>()
    for (const category of categories.value) {
      const code = category.code.trim()
      const zhName = getCategoryLocaleName(category, 'zh-CN')
      const enName = getCategoryLocaleName(category, 'en-US')
      if (!code || !/^[A-Za-z0-9_-]+$/.test(code)) {
        ElMessage.error(copy.value.messages.invalidCategory)
        return false
      }
      if (!zhName || !enName) {
        ElMessage.error(copy.value.messages.invalidCategoryName)
        return false
      }
      if (seen.has(code)) {
        ElMessage.error(copy.value.messages.duplicateCategory)
        return false
      }
      seen.add(code)
    }
    return true
  }

  const handleItemGroupChange = (item: Pick<MenuManagementItem, 'groupCode' | 'sourceType' | 'sourceCode' | 'code'>, targetGroupCode: string) => {
    const sourceCategory = getItemCategory(item)
    const targetCategory = orderedCategories.value.find((category) => category.code === targetGroupCode)
    if (!sourceCategory || !targetCategory || sourceCategory.originalCode === targetCategory.originalCode) {
      items.value = items.value.map((entry) =>
        getItemIdentity(entry) === getItemIdentity(item) ? { ...entry, groupCode: targetGroupCode } : entry,
      )
      return
    }

    const sourceItems = getItemsForCategory(sourceCategory).filter((entry) => getItemIdentity(entry) !== getItemIdentity(item))
    const movingItem = items.value.find((entry) => getItemIdentity(entry) === getItemIdentity(item))
    if (!movingItem) return
    const targetItems = [...getItemsForCategory(targetCategory), { ...movingItem, groupCode: targetCategory.code.trim() }]
    const updates = new Map<string, { groupCode: string; order: number }>()
    applyGroupOrder(sourceCategory, sourceItems, updates)
    applyGroupOrder(targetCategory, targetItems, updates)
    items.value = syncItemCollections(items.value, updates)
  }

  const saveManagementChanges = async () => {
    if (!validateLocalizedCategories()) return

    saving.value = true
    try {
      const groupCodeMap = buildGroupCodeMap(categories.value)
      const payload = {
        categories: orderedCategories.value.map((category) => ({
          code: category.code.trim(),
          name: getCategoryFallbackName(category),
          translationKey: category.translationKey,
          localeNames: normalizeLocaleNames(category.localeNames),
          icon: category.icon,
          order: category.order,
          isVisible: category.isVisible,
          isLocked: false,
          isDefault: category.isDefault,
          entryCount: getCategoryEntryCount(category),
          supportsDelete: true,
        })),
        items: orderedItems.value.map((item) => ({
          ...item,
          groupCode: groupCodeMap.get(item.groupCode) || item.groupCode.trim(),
        })),
      }

      const saved = await menuApi.updateManagement(payload)
      categories.value = saved.categories
        .map((category) => hydrateCategory(category, currentLocale.value))
        .map((category) => syncCategoryFallbackName(category))
      items.value = saved.items
      if (!selectedCategoryCode.value && saved.categories.length) {
        selectedCategoryCode.value = saved.categories[0].code
      }
      syncSelectedEntry()
      syncCollapsedGroups()
      syncPaginationBounds()
      try {
        await menuStore.fetchMenu()
      } catch (refreshError) {
        reportMenuManagementError('refresh runtime menu failed', refreshError)
      }
      ElMessage.success(copy.value.messages.saveSuccess)
    } catch (error) {
      reportMenuManagementError('save failed', error)
      const message = getErrorMessage(error) || copy.value.messages.saveFailed
      ElMessage.error(message)
    } finally {
      saving.value = false
    }
  }

  watch(() => currentLocale.value, () => {
    categories.value = categories.value.map((category) => syncCategoryFallbackName(category))
  })

  watch(() => [orderedCategories.value.length, filteredEntryGroups.value.length], syncPaginationBounds)
  watch(() => orderedItems.value.map((item) => getItemIdentity(item)).join('|'), syncSelectedEntry)
  watch(() => orderedCategories.value.map((category) => category.code).join('|'), () => {
    if (!selectedCategory.value && orderedCategories.value.length) {
      selectedCategoryCode.value = orderedCategories.value[0].originalCode
    }
    syncCollapsedGroups()
  })

  onMounted(async () => {
    await localeStore.initialize()
    await reloadManagement()
  })

  return {
    loading,
    saving,
    search,
    categories,
    items,
    categoryPage,
    categoryPageSize,
    entryPage,
    entryPageSize,
    selectedEntry,
    viewAllEntries,
    copy,
    currentLocale,
    extraLanguageCount,
    availableIcons,
    orderedCategories,
    orderedItems,
    selectedCategory,
    visibleCategoryCount,
    visibleEntryCount,
    lockedEntryCount,
    filteredItems,
    pagedCategories,
    visibleEntryGroups,
    displayedEntryGroups,
    selectableCategories,
    getItemCategory,
    getItemsForCategory,
    getCategoryEntryCount,
    getCategoryLabel,
    getCategoryLocaleName,
    getItemGroupLabel,
    getItemLabel,
    getGroupToggleLabel,
    isGroupCollapsed,
    toggleGroupCollapse,
    isSelectedCategory,
    selectCategory,
    canMoveCategory,
    moveCategory,
    removeCategory,
    openCategoryTranslations,
    updateCategoryLocaleName,
    canMoveItem,
    moveItem,
    handleItemGroupChange,
    getItemIdentity,
    selectEntry,
    isSelectedEntry,
    handleCategoryPageSizeChange,
    handleEntryPageSizeChange,
    handleCategoryDrag,
    handleEntryBoardDrag,
    reloadManagement,
    saveManagementChanges,
    addLocalizedCategory,
    resolveIcon,
  }
}
