<template>
  <el-card
    shadow="never"
    class="layout-card"
  >
    <template #header>
      <div class="layout-board-header">
        <div class="layout-board-heading">
          <div class="layout-board-title-row">
            <div class="layout-board-title">
              {{ title }}
            </div>
            <div class="layout-board-pills">
              <span class="layout-board-pill">{{ filteredItemsCount }}</span>
              <span class="layout-board-pill muted">{{ visibleEntryCount }} {{ copy.fields.visible }}</span>
              <span class="layout-board-pill accent">{{ lockedEntryCount }} {{ copy.tags.locked }}</span>
            </div>
          </div>
          <div class="layout-board-subtitle">
            {{ subtitle }}
          </div>
        </div>

        <div class="layout-board-toolbar">
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
            class="layout-search"
            clearable
            :placeholder="copy.placeholders.search"
            @update:model-value="$emit('update:search', String($event || ''))"
          />
        </div>
      </div>
    </template>

    <div
      ref="boardRef"
      class="layout-board"
    >
      <section
        v-for="group in visibleEntryGroups"
        :key="group.category.originalCode"
        class="entry-group"
        :data-group-code="group.category.code"
      >
        <header class="entry-group-header">
          <div class="entry-group-heading">
            <strong>{{ getCategoryLabel(group.category) }}</strong>
            <span>{{ group.category.code }}</span>
          </div>
          <div class="entry-group-actions">
            <span class="layout-board-pill soft">{{ group.items.length }} {{ copy.labels.entries }}</span>
            <span class="layout-board-pill soft">{{ copy.fields.visible }} {{ group.visibleCount }}</span>
            <el-button
              link
              class="group-toggle"
              :data-testid="`toggle-group-${group.category.code}`"
              @click="$emit('toggle-group', group.category.code)"
            >
              {{ getGroupToggleLabel(group.category.code) }}
            </el-button>
          </div>
        </header>

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

          <article
            v-for="item in group.items"
            :key="getItemIdentity(item)"
            class="entry-item"
            :class="{ active: isSelectedEntry(item), hidden: !item.isVisible }"
            :data-row-id="getItemIdentity(item)"
            :data-testid="`entry-item-${getItemIdentity(item)}`"
            @click="$emit('select-entry', item)"
          >
            <div class="entry-item-main">
              <span
                class="drag-handle"
                :title="copy.labels.dragHandle"
              >::</span>
              <div class="entry-copy">
                <div class="entry-copy-line">
                  <strong>{{ getItemLabel(item) }}</strong>
                  <span class="entry-path">{{ item.path }}</span>
                </div>
                <div class="entry-copy-meta">
                  <span>{{ item.code }}</span>
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
            </div>

            <div
              class="entry-controls"
              @click.stop
            >
              <span class="entry-order">#{{ item.order }}</span>
              <el-switch v-model="item.isVisible" />
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
          </article>
        </div>
      </section>
    </div>

    <el-pagination
      v-if="viewAllEntries && visibleEntryGroups.length > 0"
      class="layout-pagination"
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

const props = defineProps<{
  copy: any
  title: string
  subtitle: string
  search: string
  viewAllEntries: boolean
  filteredItemsCount: number
  visibleEntryCount: number
  lockedEntryCount: number
  visibleEntryGroups: Array<{ category: EditableCategory; items: MenuManagementItem[]; visibleCount: number }>
  displayedEntryGroups: Array<{ category: EditableCategory; items: MenuManagementItem[]; visibleCount: number }>
  entryPage: number
  entryPageSize: number
  getCategoryLabel: (category: EditableCategory) => string
  getItemLabel: (item: Pick<MenuManagementItem, 'translationKey' | 'name' | 'nameEn' | 'code'>) => string
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
  (event: 'update:entry-page', value: number): void
  (event: 'entry-page-size-change', value: number): void
  (event: 'group-drag', groupCode: string, oldIndex: number, newIndex: number): void
}>()

const boardRef = ref<HTMLElement | null>(null)
const sortables = new Map<string, Sortable>()

const rebuildSortables = async () => {
  await nextTick()
  for (const sortable of sortables.values()) sortable.destroy()
  sortables.clear()
  if (!boardRef.value) return

  const containers = Array.from(boardRef.value.querySelectorAll<HTMLElement>('.entry-group-list'))
  containers.forEach((container) => {
    const groupCode = container.dataset.groupCode
    if (!groupCode) return

    const sortable = Sortable.create(container, {
      animation: 180,
      handle: '.drag-handle',
      draggable: '.entry-item',
      onEnd: (event) => {
        if (event.oldIndex == null || event.newIndex == null || event.oldIndex === event.newIndex) return
        emit('group-drag', groupCode, event.oldIndex, event.newIndex)
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

.layout-card {
  @include panel-card;
}

.layout-board-header,
.layout-board-heading {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.layout-board-title-row,
.layout-board-pills,
.layout-board-toolbar,
.entry-group-header,
.entry-group-actions,
.entry-item,
.entry-item-main,
.entry-controls,
.entry-copy-line,
.entry-copy-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.layout-board-header {
  gap: 14px;
}

.layout-board-title-row {
  align-items: center;
}

.layout-board-title {
  @include title-strong(24px);
}

.layout-board-subtitle {
  color: #41556f;
  line-height: 1.7;
}

.layout-board-pill {
  @include pill;
}

.layout-board-pill.muted,
.layout-board-pill.soft {
  background: #eef3f9;
  color: #41556f;
}

.layout-board-pill.accent {
  background: #dbe7f7;
}

.layout-board-toolbar {
  align-items: center;
}

.layout-search {
  width: 320px;
  max-width: 100%;
}

.layout-board {
  display: flex;
  flex-direction: column;
  gap: 18px;
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

.entry-group-header {
  justify-content: space-between;
  align-items: flex-start;
}

.entry-group-heading {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.entry-group-heading strong {
  color: #10203a;
  font-size: 18px;
}

.entry-group-heading span {
  color: #71839b;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.entry-group-actions {
  align-items: center;
}

.entry-group-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.entry-group-empty {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
  justify-content: center;
  min-height: 110px;
  border: 1px dashed #c7d3e3;
  border-radius: 18px;
  background: rgba(240, 245, 252, 0.64);
  text-align: center;
  color: #41556f;
}

.entry-item {
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border: 1px solid #d8e1ee;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.98);
  cursor: pointer;
}

.entry-item.active {
  border-color: rgba(16, 32, 58, 0.26);
  box-shadow: 0 0 0 1px rgba(16, 32, 58, 0.08);
}

.entry-item.hidden {
  opacity: 0.65;
}

.entry-item-main {
  align-items: center;
  min-width: 0;
  flex: 1 1 auto;
}

.drag-handle {
  @include drag-handle;
}

.entry-copy {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.entry-copy-line {
  align-items: center;
}

.entry-copy-line strong {
  color: #10203a;
  font-size: 16px;
}

.entry-path {
  color: #71839b;
  font-size: 13px;
  word-break: break-all;
}

.entry-copy-meta {
  align-items: center;
}

.entry-copy-meta span {
  color: #71839b;
  font-size: 12px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.entry-controls {
  align-items: center;
  justify-content: flex-end;
}

.entry-order {
  @include pill(#f8fbff, #10203a);
  border: 1px solid #d8e1ee;
}

.layout-pagination {
  margin-top: 18px;
  justify-content: flex-end;
}

@media (max-width: 960px) {
  .layout-board-toolbar,
  .entry-group-header,
  .entry-item {
    flex-direction: column;
    align-items: stretch;
  }

  .entry-controls {
    justify-content: flex-start;
  }
}
</style>
