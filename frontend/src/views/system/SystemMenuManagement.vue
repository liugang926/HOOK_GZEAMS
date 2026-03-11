<template>
  <div class="system-menu-management page-container">
    <MenuManagementHero
      :copy="copy"
      :title="pageCopy.title"
      :subtitle="pageCopy.subtitle"
      :category-count="orderedCategories.length"
      :entry-count="orderedItems.length"
      :visible-entry-count="visibleEntryCount"
      :locked-entry-count="lockedEntryCount"
      :saving="saving"
      @reload="reloadManagement"
      @save="saveManagementChanges"
    />

    <MenuManagementViewSwitch
      current="resource"
      :resource-label="pageCopy.resourceLabel"
      :layout-label="pageCopy.layoutLabel"
      @change="handleViewChange"
    />

    <el-row :gutter="20">
      <el-col
        :lg="8"
        :md="24"
      >
        <MenuManagementCategoryResourcePanel
          :copy="copy"
          :subtitle="pageCopy.categorySubtitle"
          :ordered-categories="orderedCategories"
          :paged-categories="pagedCategories"
          :visible-category-count="visibleCategoryCount"
          :extra-language-count="extraLanguageCount"
          :category-page="categoryPage"
          :category-page-size="categoryPageSize"
          :available-icons="availableIcons"
          :is-selected-category="isSelectedCategory"
          :get-category-entry-count="getCategoryEntryCount"
          :get-category-locale-name="getCategoryLocaleName"
          :resolve-icon="resolveIcon"
          @add-category="addLocalizedCategory"
          @select-category="selectCategory"
          @remove-category="removeCategory"
          @open-category-translations="openCategoryTranslations"
          @update-locale-name="updateCategoryLocaleName"
          @update:category-page="categoryPage = $event"
          @page-size-change="handleCategoryPageSizeChange"
        />
      </el-col>

      <el-col
        :lg="16"
        :md="24"
      >
        <MenuManagementEntryCatalogPanel
          :copy="copy"
          :title="pageCopy.entryTitle"
          :subtitle="pageCopy.entrySubtitle"
          :detail-kicker="pageCopy.detailKicker"
          :route-label="pageCopy.routeLabel"
          :empty-title="pageCopy.emptyTitle"
          :empty-hint="pageCopy.emptyHint"
          :layout-tip="pageCopy.layoutTip"
          :search="search"
          :view-all-entries="viewAllEntries"
          :visible-items="resourceItems"
          :selected-entry="selectedEntry"
          :selectable-categories="selectableCategories"
          :available-icons="availableIcons"
          :get-category-label="getCategoryLabel"
          :get-item-label="getItemLabel"
          :get-item-group-label="getItemGroupLabel"
          :get-item-identity="getItemIdentity"
          :is-selected-entry="isSelectedEntry"
          :resolve-icon="resolveIcon"
          @update:view-all="viewAllEntries = $event"
          @update:search="search = $event"
          @select-entry="selectEntry"
          @change-item-group="handleItemGroupChange"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  MenuManagementCategoryResourcePanel,
  MenuManagementEntryCatalogPanel,
  MenuManagementHero,
  MenuManagementViewSwitch,
  useSystemMenuManagement,
} from './menu-management'

const router = useRouter()

const {
  saving,
  search,
  categoryPage,
  categoryPageSize,
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
  pagedCategories,
  selectableCategories,
  getCategoryEntryCount,
  getCategoryLabel,
  getCategoryLocaleName,
  getItemGroupLabel,
  getItemLabel,
  isSelectedCategory,
  selectCategory,
  removeCategory,
  openCategoryTranslations,
  updateCategoryLocaleName,
  handleItemGroupChange,
  getItemIdentity,
  getItemCategory,
  selectEntry,
  isSelectedEntry,
  handleCategoryPageSizeChange,
  reloadManagement,
  saveManagementChanges,
  addLocalizedCategory,
  resolveIcon,
} = useSystemMenuManagement()

const pageCopy = computed(() =>
  currentLocale.value === 'en-US'
    ? {
        title: 'Menu Resources',
        subtitle: 'Define menu categories, multilingual labels, icons, and item ownership. Display and ordering move to the layout workspace.',
        resourceLabel: 'Menu Resources',
        layoutLabel: 'Menu Layout',
        categorySubtitle: 'Maintain category names, multilingual labels, stable codes, and icon assets here.',
        entryTitle: 'Menu Resource Catalog',
        entrySubtitle: 'Review menu entries and assign each entry to its owning category. Ordering and visibility are managed in Menu Layout.',
        detailKicker: 'Resource Detail',
        routeLabel: 'Route',
        emptyTitle: 'No menu entries',
        emptyHint: 'Switch categories or search globally to locate another menu entry.',
        layoutTip: 'Need to adjust visibility or sort order? Switch to Menu Layout for navigation arrangement.',
      }
    : {
        title: '菜单资源管理',
        subtitle: '集中维护菜单分类、图标、多语言名称和菜单项归属。显示状态与排序已拆到菜单布局页面处理。',
        resourceLabel: '菜单资源',
        layoutLabel: '菜单布局',
        categorySubtitle: '这里更适合维护分类名称、多语言、稳定编码以及图标资源。',
        entryTitle: '菜单资源目录',
        entrySubtitle: '在这里查看菜单项资源并调整所属分类。显示状态与排序请切换到菜单布局页面。',
        detailKicker: '资源详情',
        routeLabel: '路由地址',
        emptyTitle: '当前没有菜单项',
        emptyHint: '可以切换分类，或切到“查看全部”搜索其他菜单项。',
        layoutTip: '需要调整显示状态或排序时，请切换到“菜单布局”工作区处理。',
      },
)

const resourceItems = computed(() => {
  const categoryCode = selectedCategory.value?.code?.trim()
  return orderedItems.value.filter((item) => {
    if (!search.value.trim()) {
      return viewAllEntries.value || !categoryCode || item.groupCode === categoryCode
    }

    const label = getItemLabel(item).toLowerCase()
    const keyword = search.value.trim().toLowerCase()
    const matchesKeyword =
      label.includes(keyword) ||
      item.code.toLowerCase().includes(keyword) ||
      item.path.toLowerCase().includes(keyword)

    if (!matchesKeyword) return false
    if (viewAllEntries.value || !categoryCode) return true

    const category = getItemCategory(item)
    return category?.code === categoryCode || category?.originalCode === selectedCategory.value?.originalCode
  })
})

const handleViewChange = (view: 'resource' | 'layout') => {
  if (view === 'resource') return
  void router.push({ name: 'MenuLayoutManagement' })
}
</script>

<style scoped lang="scss">
.system-menu-management {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-bottom: 12px;
}
</style>
