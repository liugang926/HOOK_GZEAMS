<template>
  <el-card
    shadow="never"
    class="panel-card panel-card-entries"
  >
    <template #header>
      <div class="panel-header sticky-panel-header">
        <div class="panel-header-top">
          <div class="panel-title-row">
            <div class="panel-title">
              {{ copy.sections.entries }}
            </div>
            <div class="panel-pills">
              <span class="panel-pill">{{ filteredItems.length }}</span>
              <span class="panel-pill muted">{{ visibleEntryCount }} {{ copy.fields.visible }}</span>
              <span class="panel-pill accent">{{ lockedEntryCount }} {{ copy.tags.locked }}</span>
            </div>
          </div>
          <div class="panel-toolbar">
            <el-button
              size="small"
              :type="viewAllEntries ? 'default' : 'primary'"
              @click="$emit('update:view-all', false)"
            >
              {{ copy.focusMode.current }}
            </el-button>
            <el-button
              size="small"
              :type="viewAllEntries ? 'primary' : 'default'"
              @click="$emit('update:view-all', true)"
            >
              {{ copy.focusMode.all }}
            </el-button>
            <el-input
              :model-value="search"
              class="entry-search"
              clearable
              :placeholder="copy.placeholders.search"
              @update:model-value="$emit('update:search', String($event || ''))"
            />
          </div>
        </div>
        <div class="panel-subtitle">
          {{ copy.sections.entriesHint }}
        </div>
      </div>
    </template>

    <div class="entries-workspace">
      <div
        ref="entryBoardRef"
        class="entry-board"
      >
        <div
          v-for="group in visibleEntryGroups"
          :key="group.category.originalCode"
          class="entry-group"
          :data-group-code="group.category.code"
        >
          <div class="entry-group-header">
            <div class="entry-group-heading">
              <div class="entry-group-title">
                {{ getCategoryLabel(group.category) }}
              </div>
              <div class="entry-group-code">
                {{ group.category.code }}
              </div>
            </div>
            <div class="entry-group-header-actions">
              <div class="panel-pills">
                <span class="panel-pill">{{ group.items.length }} {{ copy.labels.entries }}</span>
                <span class="panel-pill muted">{{ copy.fields.visible }} {{ group.visibleCount }}</span>
              </div>
              <el-button
                link
                class="group-toggle"
                :data-testid="`toggle-group-${group.category.code}`"
                @click="$emit('toggle-group', group.category.code)"
              >
                {{ getGroupToggleLabel(group.category.code) }}
              </el-button>
            </div>
          </div>

          <div
            v-if="!isGroupCollapsed(group.category.code)"
            class="entry-group-list"
            :data-group-code="group.category.code"
          >
            <div
              v-if="!group.items.length"
              class="entry-group-empty"
              :data-testid="`empty-group-${group.category.code}`"
            >
              <strong>{{ copy.emptyGroup.title }}</strong>
              <span>{{ copy.emptyGroup.hint }}</span>
            </div>
            <div
              v-for="item in group.items"
              :key="getItemIdentity(item)"
              class="entry-item"
              :class="{ active: isSelectedEntry(item) }"
              :data-row-id="getItemIdentity(item)"
              :data-testid="`entry-item-${getItemIdentity(item)}`"
              @click="$emit('select-entry', item)"
            >
              <div class="entry-item-top">
                <div class="entry-title">
                  <span
                    class="drag-handle"
                    :title="copy.labels.dragHandle"
                  >::</span>
                  <div class="entry-title-text">
                    <div class="entry-mainline">
                      <strong>{{ getItemLabel(item) }}</strong>
                      <span class="entry-path">{{ item.path }}</span>
                    </div>
                    <span class="entry-code">{{ item.code }}</span>
                  </div>
                </div>
                <div class="entry-meta">
                  <el-tag
                    size="small"
                    effect="plain"
                  >
                    {{ item.sourceType === 'static' ? copy.tags.static : copy.tags.object }}
                  </el-tag>
                  <el-tag
                    v-if="item.isLocked"
                    size="small"
                    type="warning"
                  >
                    {{ copy.tags.locked }}
                  </el-tag>
                </div>
              </div>

              <div class="entry-item-body">
                <div class="entry-summary">
                  <span>{{ copy.columns.group }}: {{ getItemGroupLabel(item) }}</span>
                  <span>{{ copy.columns.order }}: {{ item.order }}</span>
                  <span>{{ copy.columns.visible }}: {{ item.isVisible ? copy.visibility.visible : copy.visibility.hidden }}</span>
                </div>
                <div
                  class="entry-actions"
                  @click.stop
                >
                  <el-button
                    link
                    :disabled="!canMoveItem(item, -1)"
                    @click="$emit('move-item', item, -1)"
                  >
                    {{ copy.actions.moveUp }}
                  </el-button>
                  <el-button
                    link
                    :disabled="!canMoveItem(item, 1)"
                    @click="$emit('move-item', item, 1)"
                  >
                    {{ copy.actions.moveDown }}
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <MenuManagementEntryDetail
        :copy="copy"
        :selected-entry="selectedEntry"
        :selectable-categories="selectableCategories"
        :get-item-label="getItemLabel"
        :get-item-group-label="getItemGroupLabel"
        :get-category-label="getCategoryLabel"
        :can-move-item="canMoveItem"
        @change-group="(item, groupCode) => $emit('change-item-group', item, groupCode)"
        @move-item="(item, offset) => $emit('move-item', item, offset)"
      />
    </div>

    <el-pagination
      v-if="viewAllEntries && visibleEntryGroups.length > 0"
      class="panel-pagination"
      background
      layout="total, sizes, prev, pager, next"
      :total="displayedEntryGroups.length"
      :current-page="entryPage"
      :page-size="entryPageSize"
      :page-sizes="[2, 3, 4, 6]"
      @update:current-page="$emit('update:entry-page', $event)"
      @update:page-size="$emit('entry-page-size-change', $event)"
    />
  </el-card>
</template>

<script setup lang="ts">
import Sortable from 'sortablejs'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { MenuManagementItem } from '@/api/system'
import type { EditableCategory } from '../shared'
import MenuManagementEntryDetail from './MenuManagementEntryDetail.vue'

const props = defineProps<{
  copy: any
  search: string
  viewAllEntries: boolean
  filteredItems: MenuManagementItem[]
  visibleEntryCount: number
  lockedEntryCount: number
  visibleEntryGroups: Array<{ category: EditableCategory; items: MenuManagementItem[]; visibleCount: number }>
  displayedEntryGroups: Array<{ category: EditableCategory; items: MenuManagementItem[]; visibleCount: number }>
  entryPage: number
  entryPageSize: number
  selectedEntry: MenuManagementItem | null
  selectableCategories: EditableCategory[]
  getCategoryLabel: (category: EditableCategory) => string
  getItemLabel: (item: Pick<MenuManagementItem, 'translationKey' | 'name' | 'nameEn' | 'code'>) => string
  getItemGroupLabel: (item: Pick<MenuManagementItem, 'groupCode'>) => string
  getGroupToggleLabel: (groupCode: string) => string
  isGroupCollapsed: (groupCode: string) => boolean
  getItemIdentity: (item: Pick<MenuManagementItem, 'sourceType' | 'sourceCode' | 'code'>) => string
  isSelectedEntry: (item: Pick<MenuManagementItem, 'sourceType' | 'sourceCode' | 'code'>) => boolean
  canMoveItem: (item: Pick<MenuManagementItem, 'groupCode' | 'sourceType' | 'sourceCode' | 'code'>, offset: -1 | 1) => boolean
}>()

const emit = defineEmits<{
  (event: 'update:view-all', value: boolean): void
  (event: 'update:search', value: string): void
  (event: 'toggle-group', groupCode: string): void
  (event: 'select-entry', item: MenuManagementItem): void
  (event: 'move-item', item: MenuManagementItem, offset: -1 | 1): void
  (event: 'change-item-group', item: MenuManagementItem, groupCode: string): void
  (event: 'update:entry-page', value: number): void
  (event: 'entry-page-size-change', value: number): void
  (event: 'board-drag', sourceGroupCode: string, targetGroupCode: string, oldIndex: number, newIndex: number): void
}>()

const entryBoardRef = ref<HTMLElement | null>(null)
const sortables = new Map<string, Sortable>()

const rebuildSortables = async () => {
  await nextTick()
  for (const sortable of sortables.values()) sortable.destroy()
  sortables.clear()
  if (!entryBoardRef.value) return

  const containers = Array.from(entryBoardRef.value.querySelectorAll<HTMLElement>('.entry-group-list'))
  containers.forEach((container) => {
    const groupCode = container.dataset.groupCode
    if (!groupCode) return
    const sortable = Sortable.create(container, {
      animation: 180,
      handle: '.drag-handle',
      draggable: '.entry-item',
      group: 'menu-entry-groups',
      onEnd: (event) => {
        if (event.oldIndex == null || event.newIndex == null) return
        const sourceGroupCode = (event.from as HTMLElement | null)?.dataset.groupCode
        const targetGroupCode = (event.to as HTMLElement | null)?.dataset.groupCode
        if (!sourceGroupCode || !targetGroupCode || (sourceGroupCode === targetGroupCode && event.oldIndex === event.newIndex)) return
        emit('board-drag', sourceGroupCode, targetGroupCode, event.oldIndex, event.newIndex)
      },
    })
    sortables.set(groupCode, sortable)
  })
}

watch(
  () => [
    props.visibleEntryGroups.map((group) => `${group.category.originalCode}:${props.isGroupCollapsed(group.category.code) ? '1' : '0'}:${group.items.map((item) => props.getItemIdentity(item)).join('|')}`).join('||'),
    props.entryPage,
    props.entryPageSize,
    props.search,
    props.viewAllEntries,
  ],
  () => { void rebuildSortables() },
)

onMounted(() => { void rebuildSortables() })
onBeforeUnmount(() => { for (const sortable of sortables.values()) sortable.destroy() })
</script>

<style scoped lang="scss">
@use '../styles/mixins' as *;

.panel-card {
  @include panel-card;
}

.sticky-panel-header {
  position: sticky;
  top: 12px;
  z-index: 6;
  padding: 10px 0 14px;
  margin: -10px 0 0;
  background: linear-gradient(180deg, rgba(249, 251, 254, 0.98) 0%, rgba(249, 251, 254, 0.88) 75%, rgba(249, 251, 254, 0) 100%);
}

.panel-header,
.panel-header-top,
.panel-title-row,
.panel-toolbar,
.panel-pills,
.entry-group-header,
.entry-group-header-actions,
.entry-meta,
.entry-actions,
.entry-summary,
.entry-title,
.entry-mainline {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.panel-header {
  flex-direction: column;
}

.panel-header-top {
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  @include title-strong(26px);
}

.panel-pill {
  @include pill;
}

.panel-pill.muted {
  background: #f1f5f9;
  color: #41556f;
}

.panel-pill.accent {
  background: #dbe7f7;
}

.panel-subtitle {
  color: #41556f;
  line-height: 1.6;
}

.entry-search {
  width: 320px;
  max-width: 100%;
}

.entries-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(280px, 0.95fr);
  gap: 18px;
  align-items: start;
}

.entry-board {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: 180px;
}

.entry-group {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
  border: 1px solid #d8e1ee;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 248, 255, 0.98) 100%);
}

.entry-group-title {
  font-size: 18px;
  font-weight: 800;
  color: #10203a;
}

.entry-group-code,
.entry-code {
  font-size: 12px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #71839b;
}

.entry-group-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 84px;
  padding: 6px;
  border-radius: 20px;
  background: rgba(237, 243, 251, 0.72);
}

.entry-group-empty,
.entry-item {
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.95);
}

.entry-group-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-height: 116px;
  padding: 18px;
  border: 1px dashed #c7d3e3;
  text-align: center;
}

.entry-item {
  border: 1px solid #d8e1ee;
  padding: 18px;
}

.entry-item.active {
  border-color: rgba(16, 32, 58, 0.24);
  box-shadow: 0 0 0 1px rgba(16, 32, 58, 0.1);
}

.drag-handle {
  @include drag-handle;
}

.entry-title {
  align-items: center;
  min-width: 0;
}

.entry-title-text {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.entry-mainline strong {
  font-size: 18px;
  color: #10203a;
}

.entry-path {
  color: #71839b;
  font-size: 13px;
  word-break: break-all;
}

.entry-item-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 6px;
  border-top: 1px solid rgba(216, 225, 238, 0.8);
}

.entry-summary {
  font-size: 13px;
  color: #41556f;
}

.panel-pagination {
  margin-top: 20px;
  justify-content: flex-end;
  padding-top: 14px;
  border-top: 1px solid rgba(216, 225, 238, 0.9);
}

@media (max-width: 960px) {
  .panel-header-top,
  .entry-group-header {
    flex-direction: column;
    align-items: stretch;
  }

  .entries-workspace {
    grid-template-columns: 1fr;
  }
}
</style>
