<template>
  <el-card
    shadow="never"
    class="layout-card"
  >
    <template #header>
      <div class="layout-card-header">
        <div class="layout-card-heading">
          <div class="layout-card-title-row">
            <div class="layout-card-title">
              {{ title }}
            </div>
            <div class="layout-card-pills">
              <span class="layout-card-pill">{{ orderedCategories.length }}</span>
              <span class="layout-card-pill muted">{{ visibleCategoryCount }} {{ copy.fields.visible }}</span>
            </div>
          </div>
          <div class="layout-card-subtitle">
            {{ subtitle }}
          </div>
        </div>
      </div>
    </template>

    <div
      ref="categoryListRef"
      class="category-rail"
    >
      <div
        v-for="category in pagedCategories"
        :key="category.originalCode"
        class="category-item"
        :class="{ active: isSelectedCategory(category), hidden: !category.isVisible }"
        :data-row-id="category.originalCode"
        :data-testid="`category-item-${category.originalCode}`"
        @click="$emit('select-category', category)"
      >
        <div class="category-item-top">
          <div class="category-item-main">
            <span
              class="drag-handle"
              :title="copy.labels.dragHandle"
            >::</span>
            <span class="category-icon-chip">
              <component :is="resolveIcon(category.icon)" />
            </span>
            <div class="category-copy">
              <strong>{{ getCategoryLabel(category) }}</strong>
              <span>{{ category.code }}</span>
            </div>
          </div>

          <div
            class="category-item-controls"
            @click.stop
          >
            <el-switch v-model="category.isVisible" />
          </div>
        </div>

        <div class="category-item-meta">
          <span class="layout-card-pill soft">{{ getCategoryEntryCount(category) }} {{ copy.labels.entries }}</span>
          <span class="layout-card-pill soft">{{ category.isVisible ? copy.visibility.visible : copy.visibility.hidden }}</span>
          <el-button
            link
            :disabled="!canMoveCategory(category.originalCode, -1)"
            @click="$emit('move-category', category.originalCode, -1)"
          >
            {{ copy.actions.moveUp }}
          </el-button>
          <el-button
            link
            :disabled="!canMoveCategory(category.originalCode, 1)"
            @click="$emit('move-category', category.originalCode, 1)"
          >
            {{ copy.actions.moveDown }}
          </el-button>
        </div>
      </div>
    </div>

    <el-pagination
      class="layout-pagination"
      background
      layout="total, sizes, prev, pager, next"
      :total="orderedCategories.length"
      :current-page="categoryPage"
      :page-size="categoryPageSize"
      :page-sizes="[3, 4, 6, 8]"
      @update:current-page="$emit('update:category-page', $event)"
      @update:page-size="$emit('page-size-change', $event)"
    />
  </el-card>
</template>

<script setup lang="ts">
import Sortable from 'sortablejs'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { EditableCategory } from '../shared'

const props = defineProps<{
  copy: any
  title: string
  subtitle: string
  orderedCategories: EditableCategory[]
  pagedCategories: EditableCategory[]
  visibleCategoryCount: number
  categoryPage: number
  categoryPageSize: number
  canMoveCategory: (originalCode: string, offset: -1 | 1) => boolean
  isSelectedCategory: (category: Pick<EditableCategory, 'originalCode'>) => boolean
  getCategoryEntryCount: (category: Pick<EditableCategory, 'code' | 'originalCode'>) => number
  getCategoryLabel: (category: EditableCategory) => string
  resolveIcon: (iconName: string) => unknown
}>()

const emit = defineEmits<{
  (event: 'select-category', category: EditableCategory): void
  (event: 'move-category', originalCode: string, offset: -1 | 1): void
  (event: 'update:category-page', value: number): void
  (event: 'page-size-change', value: number): void
  (event: 'drag-reorder', oldIndex: number, newIndex: number): void
}>()

const categoryListRef = ref<HTMLElement | null>(null)
let sortable: Sortable | null = null

const rebuildSortable = async () => {
  await nextTick()
  sortable?.destroy()
  if (!categoryListRef.value) return

  sortable = Sortable.create(categoryListRef.value, {
    animation: 180,
    handle: '.drag-handle',
    draggable: '.category-item',
    onEnd: (event) => {
      if (event.oldIndex == null || event.newIndex == null || event.oldIndex === event.newIndex) return
      emit('drag-reorder', event.oldIndex, event.newIndex)
    },
  })
}

watch(
  () => [props.pagedCategories.map((item) => item.originalCode).join('|'), props.categoryPage, props.categoryPageSize],
  () => { void rebuildSortable() },
)

onMounted(() => { void rebuildSortable() })
onBeforeUnmount(() => sortable?.destroy())
</script>

<style scoped lang="scss">
@use '../styles/mixins' as *;

.layout-card {
  @include panel-card;
}

.layout-card-header,
.layout-card-title-row,
.layout-card-pills,
.category-item-top,
.category-item-main,
.category-item-controls,
.category-item-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.layout-card-header,
.layout-card-heading {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.layout-card-title-row {
  align-items: center;
}

.layout-card-title {
  @include title-strong(24px);
}

.layout-card-subtitle {
  color: #41556f;
  line-height: 1.7;
}

.layout-card-pill {
  @include pill;
}

.layout-card-pill.muted,
.layout-card-pill.soft {
  background: #eef3f9;
  color: #41556f;
}

.category-rail {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.category-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  border: 1px solid #d8e1ee;
  border-radius: 22px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(245, 249, 255, 0.98) 100%);
  cursor: pointer;
}

.category-item.active {
  border-color: rgba(16, 32, 58, 0.28);
  box-shadow: 0 0 0 1px rgba(16, 32, 58, 0.08);
}

.category-item.hidden {
  opacity: 0.68;
}

.category-item-top {
  justify-content: space-between;
  align-items: center;
}

.category-item-main {
  align-items: center;
  min-width: 0;
  flex: 1 1 auto;
}

.drag-handle {
  @include drag-handle;
}

.category-icon-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 14px;
  background: #edf3fb;
  color: #10203a;
}

.category-copy {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.category-copy strong {
  color: #10203a;
  font-size: 16px;
}

.category-copy span {
  color: #71839b;
  font-size: 12px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.category-item-controls {
  align-items: center;
}

.category-item-meta {
  align-items: center;
  color: #41556f;
}

.layout-pagination {
  margin-top: 18px;
  justify-content: flex-end;
}

@media (max-width: 960px) {
  .category-item-top {
    align-items: flex-start;
  }
}
</style>
