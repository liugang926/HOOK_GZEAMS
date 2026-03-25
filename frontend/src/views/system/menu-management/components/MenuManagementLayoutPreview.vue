<template>
  <aside
    class="layout-preview"
    data-testid="layout-preview"
  >
    <div
      class="layout-preview-card"
      :class="{ compact: previewMode === 'compact' }"
    >
      <div class="layout-preview-head">
        <div class="layout-preview-head-top">
          <div>
            <div class="layout-preview-title">
              {{ title }}
            </div>
            <div class="layout-preview-subtitle">
              {{ subtitle }}
            </div>
          </div>
          <div class="layout-preview-mode-switch">
            <button
              type="button"
              class="preview-mode-button"
              :class="{ active: previewMode === 'expanded' }"
              data-testid="preview-mode-expanded"
              @click="previewMode = 'expanded'"
            >
              {{ expandedLabel }}
            </button>
            <button
              type="button"
              class="preview-mode-button"
              :class="{ active: previewMode === 'compact' }"
              data-testid="preview-mode-compact"
              @click="previewMode = 'compact'"
            >
              {{ compactLabel }}
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="!previewGroups.length"
        class="layout-preview-empty"
      >
        <strong>{{ emptyTitle }}</strong>
        <span>{{ emptyHint }}</span>
      </div>

      <div
        v-else
        class="layout-preview-stack"
      >
        <section
          v-for="group in previewGroups"
          :key="group.category.originalCode"
          class="preview-group"
          :class="{
            active: selectedCategory?.originalCode === group.category.originalCode,
            collapsed: isGroupCollapsed(group.category.code),
          }"
          :data-testid="`preview-group-${group.category.originalCode}`"
        >
          <header class="preview-group-header">
            <div class="preview-group-lead">
              <span class="preview-group-icon">
                <component :is="resolveIcon(group.category.icon)" />
              </span>
              <div class="preview-group-copy">
                <strong>{{ getCategoryLabel(group.category) }}</strong>
                <span v-if="previewMode === 'expanded'">{{ group.items.length }} {{ copy.labels.entries }}</span>
              </div>
            </div>
            <div class="preview-group-actions">
              <span
                v-if="previewMode === 'expanded' && selectedCategory?.originalCode === group.category.originalCode"
                class="preview-active-pill"
              >
                Active
              </span>
              <button
                type="button"
                class="preview-group-toggle"
                :data-testid="`preview-toggle-${group.category.code}`"
                @click="$emit('toggle-group', group.category.code)"
              >
                {{ getGroupToggleLabel(group.category.code) }}
              </button>
            </div>
          </header>

          <div class="preview-group-items">
            <div
              v-for="item in group.items"
              v-show="!isGroupCollapsed(group.category.code)"
              :key="item.code"
              class="preview-item"
              :class="{ active: selectedEntry && selectedEntry.code === item.code }"
              :data-testid="`preview-item-${item.code}`"
              :title="previewMode === 'compact' ? getItemLabel(item) : undefined"
            >
              <span
                class="preview-item-icon"
                :title="item.icon"
              >
                <component :is="resolveIcon(item.icon)" />
              </span>
              <div
                v-if="previewMode === 'expanded'"
                class="preview-item-copy"
              >
                <span class="preview-item-label">{{ getItemLabel(item) }}</span>
                <span class="preview-item-path">{{ item.path }}</span>
              </div>
            </div>
          </div>

          <div
            v-if="isGroupCollapsed(group.category.code)"
            class="preview-group-collapsed"
          >
            {{ group.items.length }} {{ copy.labels.entries }}
          </div>
        </section>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { MenuManagementItem } from '@/api/system'
import type { EditableCategory } from '../shared'

defineProps<{
  copy: any
  title: string
  subtitle: string
  expandedLabel: string
  compactLabel: string
  emptyTitle: string
  emptyHint: string
  previewGroups: Array<{ category: EditableCategory; items: MenuManagementItem[] }>
  selectedCategory: EditableCategory | null
  selectedEntry: MenuManagementItem | null
  getCategoryLabel: (category: EditableCategory) => string
  getItemLabel: (item: Pick<MenuManagementItem, 'translationKey' | 'name' | 'nameEn' | 'code'>) => string
  getGroupToggleLabel: (groupCode: string) => string
  isGroupCollapsed: (groupCode: string) => boolean
  resolveIcon: (iconName: string) => unknown
}>()

defineEmits<{
  (event: 'toggle-group', groupCode: string): void
}>()

const previewMode = ref<'expanded' | 'compact'>('expanded')
</script>

<style scoped lang="scss">
@use '../styles/mixins' as *;

.layout-preview {
  position: sticky;
  top: 96px;
}

.layout-preview-card {
  @include floating-card(18px);
}

.layout-preview-head {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.layout-preview-head-top,
.layout-preview-mode-switch {
  display: flex;
  gap: 10px;
}

.layout-preview-head-top {
  justify-content: space-between;
  align-items: flex-start;
}

.layout-preview-title {
  @include title-strong(22px);
}

.layout-preview-subtitle,
.layout-preview-empty {
  color: #41556f;
  line-height: 1.7;
}

.layout-preview-empty {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
  justify-content: center;
  min-height: 220px;
  border: 1px dashed #c7d3e3;
  border-radius: 20px;
  background: rgba(240, 245, 252, 0.72);
  text-align: center;
}

.preview-mode-button {
  border: 1px solid #d8e1ee;
  border-radius: 999px;
  background: #ffffff;
  color: #41556f;
  font-size: 12px;
  font-weight: 700;
  padding: 7px 12px;
  cursor: pointer;
}

.preview-mode-button.active {
  background: #10203a;
  border-color: #10203a;
  color: #ffffff;
}

.layout-preview-stack {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.preview-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px;
  border: 1px solid #d8e1ee;
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(245, 249, 255, 0.98) 100%);
}

.preview-group.active {
  border-color: rgba(16, 32, 58, 0.24);
}

.preview-group-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.preview-group-lead,
.preview-group-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.preview-group-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: #edf3fb;
  color: #10203a;
}

.preview-group-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.preview-group-copy strong {
  color: #10203a;
  font-size: 16px;
}

.preview-group-copy span,
.preview-item-path {
  color: #71839b;
  font-size: 12px;
}

.preview-active-pill {
  @include pill(#10203a, #ffffff);
  font-size: 11px;
}

.preview-group-toggle {
  border: 0;
  background: transparent;
  color: #41556f;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}

.preview-group-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.preview-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid transparent;
  background: rgba(237, 243, 251, 0.72);
}

.preview-item.active {
  background: #10203a;
  border-color: rgba(16, 32, 58, 0.3);
  transform: translateX(4px);
}

.preview-item.active .preview-item-label,
.preview-item.active .preview-item-path {
  color: #ffffff;
}

.preview-item-label {
  color: #10203a;
  font-size: 14px;
  font-weight: 700;
}

.preview-item-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.72);
  color: #10203a;
  flex: 0 0 auto;
}

.preview-item.active .preview-item-icon {
  background: rgba(255, 255, 255, 0.16);
  color: #ffffff;
}

.preview-item-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.preview-group-collapsed {
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(237, 243, 251, 0.72);
  color: #41556f;
  font-size: 12px;
  font-weight: 700;
}

.layout-preview-card.compact {
  padding-inline: 14px;
}

.layout-preview-card.compact .layout-preview-subtitle {
  display: none;
}

.layout-preview-card.compact .preview-group {
  padding: 12px;
}

.layout-preview-card.compact .preview-group-header {
  gap: 8px;
}

.layout-preview-card.compact .preview-group-copy strong {
  font-size: 14px;
}

.layout-preview-card.compact .preview-group-toggle {
  font-size: 11px;
}

.layout-preview-card.compact .preview-group-items {
  gap: 6px;
}

.layout-preview-card.compact .preview-item {
  align-items: center;
  justify-content: center;
  padding: 8px;
}

@media (max-width: 960px) {
  .preview-group-header {
    align-items: flex-start;
  }

  .layout-preview-head-top,
  .preview-group-header,
  .preview-group-actions {
    flex-direction: column;
  }
}
</style>
