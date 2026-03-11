<template>
  <el-card
    shadow="never"
    class="panel-card"
  >
    <template #header>
      <div class="panel-header">
        <div class="panel-title-row">
          <div class="panel-title">
            {{ title }}
          </div>
          <div class="panel-pills">
            <span class="panel-pill">{{ visibleItems.length }}</span>
            <span class="panel-pill muted">{{ selectableCategories.length }} {{ copy.sections.categories }}</span>
          </div>
        </div>
        <div class="panel-subtitle">
          {{ subtitle }}
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
    </template>

    <div class="catalog-workspace">
      <div class="entry-list">
        <div
          v-for="item in visibleItems"
          :key="getItemIdentity(item)"
          class="entry-card"
          :class="{ active: isSelectedEntry(item) }"
          :data-testid="`entry-item-${getItemIdentity(item)}`"
          @click="$emit('select-entry', item)"
        >
          <div class="entry-card-top">
            <div class="entry-title-row">
              <span class="entry-icon-chip" :title="item.icon">
                <el-icon
                  v-if="resolveIcon(item.icon)"
                  :size="18"
                >
                  <component :is="resolveIcon(item.icon)" />
                </el-icon>
                <span v-else>{{ item.icon.slice(0, 1) }}</span>
              </span>

              <div class="entry-title-block">
                <strong>{{ getItemLabel(item) }}</strong>
                <span class="entry-path">{{ item.path }}</span>
              </div>
            </div>
            <div class="entry-tags">
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
          <div class="entry-card-meta">
            <span>{{ copy.detail.entryCode }}: {{ item.code }}</span>
            <span>{{ copy.columns.group }}: {{ getItemGroupLabel(item) }}</span>
          </div>
        </div>
        <div
          v-if="!visibleItems.length"
          class="entry-empty"
        >
          <strong>{{ emptyTitle }}</strong>
          <span>{{ emptyHint }}</span>
        </div>
      </div>

      <aside
        v-if="selectedEntry"
        class="entry-detail"
      >
        <div class="entry-detail-card">
          <div class="entry-detail-top">
            <div class="entry-detail-kicker">
              {{ detailKicker }}
            </div>
            <h3>{{ getItemLabel(selectedEntry) }}</h3>
            <p>{{ selectedEntry.path }}</p>
          </div>

          <div class="entry-detail-meta">
            <el-tag
              size="small"
              effect="plain"
            >
              {{ selectedEntry.sourceType === 'static' ? copy.tags.static : copy.tags.object }}
            </el-tag>
            <el-tag
              v-if="selectedEntry.isLocked"
              size="small"
              type="warning"
            >
              {{ copy.tags.locked }}
            </el-tag>
            <el-tag
              size="small"
              type="info"
            >
              {{ getItemGroupLabel(selectedEntry) }}
            </el-tag>
          </div>

          <div class="entry-detail-stack">
            <div class="entry-field">
              <label>{{ copy.detail.entryCode }}</label>
              <el-input
                :model-value="selectedEntry.code"
                disabled
              />
            </div>
            <div class="entry-field">
              <label>{{ routeLabel }}</label>
              <el-input
                :model-value="selectedEntry.path"
                disabled
              />
            </div>
            <div class="entry-field">
              <label>{{ copy.columns.group }}</label>
              <el-select
                :model-value="selectedEntry.groupCode"
                @update:model-value="$emit('change-group', selectedEntry, String($event))"
              >
                <el-option
                  v-for="category in selectableCategories"
                  :key="category.originalCode"
                  :label="getCategoryLabel(category)"
                  :value="category.code"
                />
              </el-select>
            </div>
            <div class="entry-field">
              <label>{{ copy.fields.icon }}</label>
              <MenuManagementIconPicker
                :model-value="selectedEntry.icon"
                :available-icons="availableIcons"
                :placeholder="copy.placeholders.icon"
                :resolve-icon="resolveIcon"
                @update:model-value="selectedEntry.icon = $event"
              />
            </div>
            <div class="entry-summary-grid">
              <div class="entry-summary-chip">
                <span>{{ copy.columns.visible }}</span>
                <strong>{{ selectedEntry.isVisible ? copy.visibility.visible : copy.visibility.hidden }}</strong>
              </div>
              <div class="entry-summary-chip">
                <span>{{ copy.columns.order }}</span>
                <strong>{{ selectedEntry.order }}</strong>
              </div>
            </div>
          </div>

          <div class="layout-tip">
            {{ layoutTip }}
          </div>
        </div>
      </aside>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { MenuManagementItem } from '@/api/system'
import type { EditableCategory } from '../shared'
import MenuManagementIconPicker from './MenuManagementIconPicker.vue'

defineProps<{
  copy: any
  title: string
  subtitle: string
  detailKicker: string
  routeLabel: string
  emptyTitle: string
  emptyHint: string
  layoutTip: string
  search: string
  viewAllEntries: boolean
  visibleItems: MenuManagementItem[]
  selectedEntry: MenuManagementItem | null
  selectableCategories: EditableCategory[]
  availableIcons: string[]
  getCategoryLabel: (category: EditableCategory) => string
  getItemLabel: (item: Pick<MenuManagementItem, 'translationKey' | 'name' | 'nameEn' | 'code'>) => string
  getItemGroupLabel: (item: Pick<MenuManagementItem, 'groupCode'>) => string
  getItemIdentity: (item: Pick<MenuManagementItem, 'sourceType' | 'sourceCode' | 'code'>) => string
  isSelectedEntry: (item: Pick<MenuManagementItem, 'sourceType' | 'sourceCode' | 'code'>) => boolean
  resolveIcon: (iconName: string) => unknown
}>()

defineEmits<{
  (event: 'update:view-all', value: boolean): void
  (event: 'update:search', value: string): void
  (event: 'select-entry', item: MenuManagementItem): void
  (event: 'change-group', item: MenuManagementItem, groupCode: string): void
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
.panel-pills,
.entry-card-top,
.entry-tags,
.entry-detail-meta,
.entry-detail-stack,
.entry-title-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.panel-header {
  flex-direction: column;
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

.panel-subtitle {
  color: #41556f;
  line-height: 1.7;
}

.entry-search {
  width: 320px;
  max-width: 100%;
}

.catalog-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(300px, 0.95fr);
  gap: 18px;
  align-items: start;
}

.entry-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 260px;
}

.entry-card,
.entry-empty {
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.98);
}

.entry-card {
  padding: 16px 18px;
  border: 1px solid #d8e1ee;
  cursor: pointer;
}

.entry-card.active {
  border-color: rgba(16, 32, 58, 0.24);
  box-shadow: 0 0 0 1px rgba(16, 32, 58, 0.1);
}

.entry-title-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.entry-title-row {
  align-items: center;
  min-width: 0;
  flex: 1 1 auto;
}

.entry-icon-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 14px;
  background: #edf3fb;
  color: #10203a;
  flex: 0 0 auto;
}

.entry-title-block strong {
  font-size: 18px;
  color: #10203a;
}

.entry-path {
  color: #71839b;
  font-size: 13px;
  word-break: break-all;
}

.entry-card-top {
  justify-content: space-between;
  align-items: flex-start;
}

.entry-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(216, 225, 238, 0.9);
  font-size: 13px;
  color: #41556f;
}

.entry-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 180px;
  padding: 20px;
  border: 1px dashed #c7d3e3;
  color: #71839b;
  text-align: center;
}

.entry-detail {
  position: sticky;
  top: 96px;
}

.entry-detail-card {
  @include floating-card(18px);
}

.entry-detail-kicker {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: #71839b;
}

.entry-detail-top h3 {
  margin: 8px 0 0;
  font-size: 24px;
  color: #10203a;
}

.entry-detail-top p {
  margin: 8px 0 0;
  color: #41556f;
  line-height: 1.6;
  word-break: break-all;
}

.entry-detail-stack {
  flex-direction: column;
}

.entry-field {
  @include surface-field(12px);
}

.entry-field label {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 700;
  color: #71839b;
}

.entry-summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.entry-summary-chip {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 14px;
  border: 1px solid #d8e1ee;
  border-radius: 14px;
  background: rgba(237, 243, 251, 0.72);
}

.entry-summary-chip span {
  font-size: 12px;
  color: #71839b;
}

.entry-summary-chip strong {
  font-size: 16px;
  color: #10203a;
}

.layout-tip {
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(16, 32, 58, 0.05);
  color: #41556f;
  line-height: 1.6;
}

@media (max-width: 960px) {
  .catalog-workspace {
    grid-template-columns: 1fr;
  }

  .entry-card-top {
    flex-direction: column;
  }
}
</style>
