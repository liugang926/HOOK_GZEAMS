<template>
  <div class="system-menu-layout-management page-container">
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
      current="layout"
      :resource-label="pageCopy.resourceLabel"
      :layout-label="pageCopy.layoutLabel"
      @change="handleViewChange"
    />

    <el-row :gutter="20">
      <el-col
        :lg="6"
        :md="24"
      >
        <MenuManagementLayoutCategoryRail
          :copy="copy"
          :title="pageCopy.categoryTitle"
          :subtitle="pageCopy.categorySubtitle"
          :ordered-categories="orderedCategories"
          :paged-categories="pagedCategories"
          :visible-category-count="visibleCategoryCount"
          :category-page="categoryPage"
          :category-page-size="categoryPageSize"
          :can-move-category="canMoveCategory"
          :is-selected-category="isSelectedCategory"
          :get-category-entry-count="getCategoryEntryCount"
          :get-category-label="getCategoryLabel"
          :resolve-icon="resolveIcon"
          @select-category="selectCategory"
          @move-category="moveCategory"
          @update:category-page="categoryPage = $event"
          @page-size-change="handleCategoryPageSizeChange"
          @drag-reorder="handleCategoryDrag"
        />
      </el-col>

      <el-col
        :lg="11"
        :md="24"
      >
        <MenuManagementLayoutBoard
          :copy="copy"
          :title="pageCopy.boardTitle"
          :subtitle="pageCopy.boardSubtitle"
          :search="search"
          :view-all-entries="viewAllEntries"
          :filtered-items-count="filteredItems.length"
          :visible-entry-count="visibleEntryCount"
          :locked-entry-count="lockedEntryCount"
          :visible-entry-groups="visibleEntryGroups"
          :displayed-entry-groups="displayedEntryGroups"
          :entry-page="entryPage"
          :entry-page-size="entryPageSize"
          :get-category-label="getCategoryLabel"
          :get-item-label="getItemLabel"
          :get-group-toggle-label="getGroupToggleLabel"
          :is-group-collapsed="isGroupCollapsed"
          :get-item-identity="getItemIdentity"
          :is-selected-entry="isSelectedEntry"
          :can-move-item="canMoveItem"
          @update:view-all="viewAllEntries = $event"
          @update:search="search = $event"
          @toggle-group="toggleGroupCollapse"
          @select-entry="selectEntry"
          @move-item="moveItem"
          @update:entry-page="entryPage = $event"
          @entry-page-size-change="handleEntryPageSizeChange"
          @group-drag="handleGroupReorder"
        />
      </el-col>

      <el-col
        :lg="7"
        :md="24"
      >
        <MenuManagementLayoutPreview
          :copy="copy"
          :title="pageCopy.previewTitle"
          :subtitle="pageCopy.previewSubtitle"
          :expanded-label="pageCopy.previewExpandedLabel"
          :compact-label="pageCopy.previewCompactLabel"
          :empty-title="pageCopy.previewEmptyTitle"
          :empty-hint="pageCopy.previewEmptyHint"
          :preview-groups="previewGroups"
          :selected-category="selectedCategory"
          :selected-entry="selectedEntry"
          :get-category-label="getCategoryLabel"
          :get-item-label="getItemLabel"
          :get-group-toggle-label="getGroupToggleLabel"
          :is-group-collapsed="isGroupCollapsed"
          :resolve-icon="resolveIcon"
          @toggle-group="toggleGroupCollapse"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  MenuManagementHero,
  MenuManagementLayoutBoard,
  MenuManagementLayoutCategoryRail,
  MenuManagementLayoutPreview,
  MenuManagementViewSwitch,
  useSystemMenuManagement,
} from './menu-management'

const router = useRouter()

const {
  saving,
  search,
  categoryPage,
  categoryPageSize,
  entryPage,
  entryPageSize,
  selectedEntry,
  viewAllEntries,
  copy,
  currentLocale,
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
  getCategoryEntryCount,
  getCategoryLabel,
  getItemLabel,
  getGroupToggleLabel,
  isGroupCollapsed,
  toggleGroupCollapse,
  isSelectedCategory,
  selectCategory,
  canMoveCategory,
  moveCategory,
  canMoveItem,
  moveItem,
  getItemsForCategory,
  getItemIdentity,
  selectEntry,
  isSelectedEntry,
  handleCategoryPageSizeChange,
  handleEntryPageSizeChange,
  handleCategoryDrag,
  handleEntryBoardDrag,
  reloadManagement,
  saveManagementChanges,
  resolveIcon,
} = useSystemMenuManagement()

const pageCopy = computed(() =>
  currentLocale.value === 'en-US'
    ? {
        title: 'Menu Layout',
        subtitle: 'Use this workspace to decide what the navigation shows, in what order, and how the final sidebar will feel.',
        resourceLabel: 'Menu Resources',
        layoutLabel: 'Menu Layout',
        categoryTitle: 'Category Rail',
        categorySubtitle: 'Control category visibility and ordering here. Category names, icons, and translations stay in Menu Resources.',
        boardTitle: 'Entry Arrangement',
        boardSubtitle: 'Focus on visibility and sort order only. Entries keep their owning category from Menu Resources.',
        previewTitle: 'Navigation Preview',
        previewSubtitle: 'A lightweight preview of the final sidebar after current visibility settings are applied.',
        previewExpandedLabel: 'Expanded',
        previewCompactLabel: 'Compact',
        previewEmptyTitle: 'No visible navigation',
        previewEmptyHint: 'Turn on at least one category and one menu entry to preview the sidebar.',
      }
    : {
        title: '菜单布局编排',
        subtitle: '这个工作台只处理导航怎么展示、怎么排序，以及最终侧边栏看起来是什么样子。',
        resourceLabel: '菜单资源',
        layoutLabel: '菜单布局',
        categoryTitle: '分类编排',
        categorySubtitle: '这里只调整分类显示和顺序，分类名称、图标、多语言请回到“菜单资源管理”维护。',
        boardTitle: '菜单项编排',
        boardSubtitle: '这里聚焦菜单项显示状态和排序，不再修改所属分类，职责和资源页彻底分开。',
        previewTitle: '导航预览',
        previewSubtitle: '根据当前显示设置生成一份轻量预览，更接近最终侧边栏效果。',
        previewExpandedLabel: '展开侧栏',
        previewCompactLabel: '窄栏模式',
        previewEmptyTitle: '当前没有可见导航',
        previewEmptyHint: '至少开启一个分类和一个菜单项后，才会在这里显示预览。',
      },
)

const previewGroups = computed(() =>
  orderedCategories.value
    .filter((category) => category.isVisible)
    .map((category) => ({
      category,
      items: getItemsForCategory(category).filter((item) => item.isVisible),
    }))
    .filter((group) => group.items.length > 0),
)

const handleGroupReorder = (groupCode: string, oldIndex: number, newIndex: number) => {
  handleEntryBoardDrag(groupCode, groupCode, oldIndex, newIndex)
}

const handleViewChange = (view: 'resource' | 'layout') => {
  if (view === 'layout') return
  void router.push({ name: 'MenuManagement' })
}
</script>

<style scoped lang="scss">
.system-menu-layout-management {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-bottom: 12px;
}
</style>
