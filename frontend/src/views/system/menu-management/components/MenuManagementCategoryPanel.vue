<template>
  <el-card
    shadow="never"
    class="panel-card"
  >
    <template #header>
      <div class="panel-header panel-header-stacked">
        <div class="panel-heading">
          <div class="panel-title-row">
            <div class="panel-title">
              {{ copy.sections.categories }}
            </div>
            <div class="panel-pills">
              <span class="panel-pill">{{ orderedCategories.length }}</span>
              <span class="panel-pill muted">{{ visibleCategoryCount }} {{ copy.fields.visible }}</span>
            </div>
          </div>
          <div class="panel-subtitle">
            {{ copy.sections.categoriesHint }}
          </div>
          <div
            v-if="extraLanguageCount > 0"
            class="panel-caption"
          >
            {{ copy.messages.translationHint }}
          </div>
        </div>
        <div class="panel-toolbar">
          <el-button
            size="small"
            @click="$emit('add-category')"
          >
            {{ copy.actions.addCategory }}
          </el-button>
        </div>
      </div>
    </template>

    <div
      ref="categoryListRef"
      class="category-list"
    >
      <div
        v-for="category in pagedCategories"
        :key="category.originalCode"
        class="category-item"
        :class="{ active: isSelectedCategory(category) }"
        :data-row-id="category.originalCode"
        :data-testid="`category-item-${category.originalCode}`"
        @click="$emit('select-category', category)"
      >
        <div class="category-item-header">
          <div class="category-header-main">
            <div class="category-badges">
              <span
                class="drag-handle"
                :title="copy.labels.dragHandle"
              >::</span>
              <el-tag
                size="small"
                :type="category.isDefault ? 'warning' : 'success'"
              >
                {{ category.isDefault ? copy.tags.default : copy.tags.custom }}
              </el-tag>
              <el-tag
                size="small"
                effect="plain"
              >
                {{ copy.labels.entries }} {{ getCategoryEntryCount(category) }}
              </el-tag>
            </div>
          </div>
          <div class="category-actions">
            <el-button
              link
              type="primary"
              @click="handleOpenCategoryTranslations(category, $event)"
            >
              {{ copy.actions.manageTranslations }}
            </el-button>
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
            <el-button
              link
              type="danger"
              @click="$emit('remove-category', category.originalCode)"
            >
              {{ copy.actions.delete }}
            </el-button>
          </div>
        </div>

        <div class="category-form-grid">
          <div class="surface-field span-6">
            <label>{{ copy.fields.categoryNameZh }}</label>
            <el-input
              :model-value="getCategoryLocaleName(category, 'zh-CN')"
              :placeholder="copy.placeholders.categoryNameZh"
              @update:model-value="$emit('update-locale-name', category, 'zh-CN', String($event || ''))"
            />
          </div>
          <div class="surface-field span-6">
            <label>{{ copy.fields.categoryNameEn }}</label>
            <el-input
              :model-value="getCategoryLocaleName(category, 'en-US')"
              :placeholder="copy.placeholders.categoryNameEn"
              @update:model-value="$emit('update-locale-name', category, 'en-US', String($event || ''))"
            />
          </div>
        </div>

        <div class="category-meta-grid">
          <div class="surface-field meta-field span-code">
            <label>{{ copy.fields.categoryCode }}</label>
            <div class="readonly-code">
              {{ category.code }}
            </div>
          </div>
          <div class="surface-field meta-field span-icon">
            <label>{{ copy.fields.icon }}</label>
            <MenuManagementIconPicker
              :model-value="category.icon"
              :available-icons="availableIcons"
              :placeholder="copy.placeholders.icon"
              :resolve-icon="resolveIcon"
              @update:model-value="category.icon = $event"
            />
          </div>
          <div class="surface-field meta-field span-order">
            <label>{{ copy.fields.order }}</label>
            <el-input-number
              v-model="category.order"
              class="compact-order-input"
              controls-position="right"
              :min="1"
              :max="9999"
            />
          </div>
          <div class="surface-field meta-field span-visible toggle-field">
            <label>{{ copy.fields.visible }}</label>
            <div class="toggle-field-body">
              <el-switch v-model="category.isVisible" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <el-pagination
      class="panel-pagination"
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
import MenuManagementIconPicker from './MenuManagementIconPicker.vue'
import type { EditableCategory, LocaleKey } from '../shared'

const props = defineProps<{
  copy: any
  orderedCategories: EditableCategory[]
  pagedCategories: EditableCategory[]
  visibleCategoryCount: number
  extraLanguageCount: number
  categoryPage: number
  categoryPageSize: number
  availableIcons: string[]
  canMoveCategory: (originalCode: string, offset: -1 | 1) => boolean
  isSelectedCategory: (category: Pick<EditableCategory, 'originalCode'>) => boolean
  getCategoryEntryCount: (category: Pick<EditableCategory, 'code' | 'originalCode'>) => number
  getCategoryLocaleName: (category: EditableCategory, locale: LocaleKey) => string
  resolveIcon: (iconName: string) => unknown
}>()

const emit = defineEmits<{
  (event: 'add-category'): void
  (event: 'select-category', category: EditableCategory): void
  (event: 'move-category', originalCode: string, offset: -1 | 1): void
  (event: 'remove-category', originalCode: string): void
  (event: 'open-category-translations', category: EditableCategory): void
  (event: 'update-locale-name', category: EditableCategory, locale: LocaleKey, value: string): void
  (event: 'update:category-page', value: number): void
  (event: 'page-size-change', value: number): void
  (event: 'drag-reorder', oldIndex: number, newIndex: number): void
}>()

const categoryListRef = ref<HTMLElement | null>(null)
let sortable: Sortable | null = null

const handleOpenCategoryTranslations = (category: EditableCategory, event?: Event) => {
  event?.stopPropagation()
  emit('open-category-translations', category)
}

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

.panel-card {
  @include panel-card;
}

.panel-header,
.panel-title-row,
.panel-toolbar,
.category-badges,
.category-actions,
.panel-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.panel-header {
  align-items: flex-start;
  justify-content: space-between;
}

.panel-heading {
  flex: 1 1 auto;
  min-width: 0;
}

.panel-title {
  @include title-strong(26px);
}

.panel-subtitle,
.panel-caption {
  color: #41556f;
  line-height: 1.6;
}

.panel-caption {
  margin-top: 8px;
  font-size: 12px;
  color: #71839b;
}

.panel-pill {
  @include pill;
}

.panel-pill.muted {
  background: #f1f5f9;
  color: #41556f;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 180px;
}

.category-item {
  cursor: pointer;
  border: 1px solid #d8e1ee;
  border-radius: 22px;
  padding: 16px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(247, 250, 255, 0.98) 100%);
}

.category-item.active {
  border-color: rgba(16, 32, 58, 0.24);
  box-shadow: 0 0 0 1px rgba(16, 32, 58, 0.08), 0 10px 26px rgba(15, 23, 42, 0.05);
}

.category-item-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px 18px;
  align-items: start;
  margin-bottom: 14px;
}

.category-header-main {
  display: flex;
  align-items: center;
  min-height: 40px;
  min-width: 0;
}

.category-badges {
  flex: 1 1 auto;
  min-width: 0;
}

.category-actions {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: max-content;
  gap: 6px 14px;
  justify-content: flex-end;
  align-items: center;
  margin-left: 0;
  padding-top: 6px;
}

.category-actions :deep(.el-button) {
  margin: 0;
  font-weight: 700;
}

.drag-handle {
  @include drag-handle;
  font-weight: 700;
}

.category-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 14px;
  margin-bottom: 12px;
}

.category-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  align-items: stretch;
}

.span-6 {
  grid-column: span 1;
}

.span-code {
  grid-column: span 1;
}

.span-icon {
  grid-column: span 1;
}

.span-order {
  grid-column: span 1;
}

.span-visible {
  grid-column: span 1;
}

.surface-field {
  @include surface-field(10px 12px);
  gap: 6px;
}

.surface-field label {
  font-size: 12px;
  font-weight: 700;
  color: #71839b;
}

.meta-field {
  min-height: 84px;
}

.readonly-code {
  display: flex;
  align-items: center;
  min-height: 40px;
  padding: 0 12px;
  border: 1px solid #d8e1ee;
  border-radius: 12px;
  background: #f8fbff;
  color: #10203a;
  font-size: 14px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.surface-field :deep(.el-input__wrapper),
.surface-field :deep(.el-input-number),
.surface-field :deep(.el-input-number .el-input__wrapper) {
  min-height: 40px;
}

.surface-field :deep(.el-input.is-disabled .el-input__wrapper) {
  background: #f6f8fc;
}

.surface-field :deep(.el-input-number) {
  display: flex;
}

.toggle-field :deep(.el-switch) {
  align-self: center;
}

.toggle-field-body {
  display: flex;
  align-items: center;
  min-height: 40px;
}

.compact-order-input {
  width: 100% !important;
  min-width: 0;
  max-width: none;
  flex: 1 1 auto;
  align-self: center;
}

.panel-pagination {
  margin-top: 20px;
  justify-content: flex-end;
  padding-top: 14px;
  border-top: 1px solid rgba(216, 225, 238, 0.9);
}

@media (max-width: 960px) {
  .panel-header,
  .category-item-header {
    grid-template-columns: 1fr;
  }

  .category-form-grid {
    grid-template-columns: 1fr;
  }

}

@media (max-width: 640px) {
  .category-actions {
    grid-auto-flow: row;
    justify-content: start;
  }

  .category-meta-grid {
    grid-template-columns: 1fr;
  }
}
</style>
