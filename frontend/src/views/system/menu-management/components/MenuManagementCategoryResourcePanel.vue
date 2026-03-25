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
            {{ subtitle }}
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

    <div class="category-list">
      <div
        v-for="category in pagedCategories"
        :key="category.originalCode"
        class="category-item"
        :class="{ active: isSelectedCategory(category) }"
        :data-testid="`category-item-${category.originalCode}`"
        @click="$emit('select-category', category)"
      >
        <div class="category-item-header">
          <div class="category-badges">
            <span
              class="category-icon-chip"
              :title="category.icon"
            >
              <component :is="resolveIcon(category.icon)" />
            </span>
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
          <div
            class="category-actions"
            @click.stop
          >
            <el-button
              link
              type="primary"
              @click="$emit('open-category-translations', category)"
            >
              {{ copy.actions.manageTranslations }}
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
          <div class="surface-field">
            <label>{{ copy.fields.categoryNameZh }}</label>
            <el-input
              :model-value="getCategoryLocaleName(category, 'zh-CN')"
              :placeholder="copy.placeholders.categoryNameZh"
              @update:model-value="$emit('update-locale-name', category, 'zh-CN', String($event || ''))"
            />
          </div>
          <div class="surface-field">
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
import MenuManagementIconPicker from './MenuManagementIconPicker.vue'
import type { EditableCategory, LocaleKey } from '../shared'

defineProps<{
  copy: any
  subtitle: string
  orderedCategories: EditableCategory[]
  pagedCategories: EditableCategory[]
  visibleCategoryCount: number
  extraLanguageCount: number
  categoryPage: number
  categoryPageSize: number
  availableIcons: string[]
  isSelectedCategory: (category: Pick<EditableCategory, 'originalCode'>) => boolean
  getCategoryEntryCount: (category: Pick<EditableCategory, 'code' | 'originalCode'>) => number
  getCategoryLocaleName: (category: EditableCategory, locale: LocaleKey) => string
  resolveIcon: (iconName: string) => unknown
}>()

defineEmits<{
  (event: 'add-category'): void
  (event: 'select-category', category: EditableCategory): void
  (event: 'remove-category', originalCode: string): void
  (event: 'open-category-translations', category: EditableCategory): void
  (event: 'update-locale-name', category: EditableCategory, locale: LocaleKey, value: string): void
  (event: 'update:category-page', value: number): void
  (event: 'page-size-change', value: number): void
}>()
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
.panel-pills,
.category-item-header {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.panel-header {
  align-items: flex-start;
  justify-content: space-between;
}

.panel-header-stacked {
  flex-direction: column;
}

.panel-heading {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.panel-title-row {
  align-items: center;
}

.panel-title {
  @include title-strong(26px);
}

.panel-pill {
  @include pill;
}

.panel-pill.muted {
  background: #eef3f9;
  color: #41556f;
}

.panel-subtitle,
.panel-caption {
  color: #41556f;
  line-height: 1.7;
}

.panel-caption {
  font-size: 13px;
  color: #71839b;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.category-item {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 18px;
  border: 1px solid #d8e1ee;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(244, 248, 255, 0.98) 100%);
  cursor: pointer;
}

.category-item.active {
  border-color: rgba(16, 32, 58, 0.24);
  box-shadow: 0 0 0 1px rgba(16, 32, 58, 0.08);
}

.category-item-header {
  justify-content: space-between;
  align-items: flex-start;
}

.category-badges,
.category-actions {
  align-items: center;
}

.category-icon-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border: 1px dashed #c7d3e3;
  border-radius: 14px;
  background: rgba(240, 245, 252, 0.92);
  color: #10203a;
}

.category-form-grid,
.category-meta-grid {
  display: grid;
  gap: 14px;
}

.category-form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.category-meta-grid {
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
}

.surface-field {
  @include surface-field(14px);
  min-width: 0;
}

.surface-field label {
  display: block;
  margin-bottom: 10px;
  font-size: 12px;
  font-weight: 700;
  color: #71839b;
}

.readonly-code {
  display: flex;
  align-items: center;
  min-height: 40px;
  padding: 0 14px;
  border: 1px solid #d5deea;
  border-radius: 12px;
  background: rgba(237, 243, 251, 0.72);
  color: #10203a;
  font-weight: 700;
}

.panel-pagination {
  margin-top: 20px;
  justify-content: flex-end;
}

@media (max-width: 960px) {
  .category-form-grid,
  .category-meta-grid {
    grid-template-columns: 1fr;
  }

  .category-item-header {
    flex-direction: column;
  }
}
</style>
