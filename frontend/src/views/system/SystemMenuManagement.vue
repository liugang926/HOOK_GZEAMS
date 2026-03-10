<template>
  <div class="system-menu-management page-container">
    <MenuManagementHero
      :copy="copy"
      :category-count="orderedCategories.length"
      :entry-count="orderedItems.length"
      :visible-entry-count="visibleEntryCount"
      :locked-entry-count="lockedEntryCount"
      :saving="saving"
      @reload="reloadManagement"
      @save="saveManagementChanges"
    />

    <el-row :gutter="20">
      <el-col
        :lg="8"
        :md="24"
      >
        <MenuManagementCategoryPanel
          :copy="copy"
          :ordered-categories="orderedCategories"
          :paged-categories="pagedCategories"
          :visible-category-count="visibleCategoryCount"
          :extra-language-count="extraLanguageCount"
          :category-page="categoryPage"
          :category-page-size="categoryPageSize"
          :available-icons="availableIcons"
          :can-move-category="canMoveCategory"
          :is-selected-category="isSelectedCategory"
          :get-category-entry-count="getCategoryEntryCount"
          :get-category-locale-name="getCategoryLocaleName"
          :resolve-icon="resolveIcon"
          @add-category="addLocalizedCategory"
          @select-category="selectCategory"
          @move-category="moveCategory"
          @remove-category="removeCategory"
          @update-locale-name="updateCategoryLocaleName"
          @update:category-page="categoryPage = $event"
          @page-size-change="handleCategoryPageSizeChange"
          @drag-reorder="handleCategoryDrag"
        />
      </el-col>

      <el-col
        :lg="16"
        :md="24"
      >
        <MenuManagementEntriesPanel
          :copy="copy"
          :search="search"
          :view-all-entries="viewAllEntries"
          :filtered-items="filteredItems"
          :visible-entry-count="visibleEntryCount"
          :locked-entry-count="lockedEntryCount"
          :visible-entry-groups="visibleEntryGroups"
          :displayed-entry-groups="displayedEntryGroups"
          :entry-page="entryPage"
          :entry-page-size="entryPageSize"
          :selected-entry="selectedEntry"
          :selectable-categories="selectableCategories"
          :get-category-label="getCategoryLabel"
          :get-item-label="getItemLabel"
          :get-item-group-label="getItemGroupLabel"
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
          @change-item-group="handleItemGroupChange"
          @update:entry-page="entryPage = $event"
          @entry-page-size-change="handleEntryPageSizeChange"
          @board-drag="handleEntryBoardDrag"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import {
  MenuManagementCategoryPanel,
  MenuManagementEntriesPanel,
  MenuManagementHero,
  useSystemMenuManagement,
} from './menu-management'

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
  extraLanguageCount,
  availableIcons,
  orderedCategories,
  orderedItems,
  visibleCategoryCount,
  visibleEntryCount,
  lockedEntryCount,
  filteredItems,
  pagedCategories,
  visibleEntryGroups,
  displayedEntryGroups,
  selectableCategories,
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
} = useSystemMenuManagement()
</script>

<style scoped lang="scss">
.system-menu-management {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-bottom: 12px;
}
</style>
