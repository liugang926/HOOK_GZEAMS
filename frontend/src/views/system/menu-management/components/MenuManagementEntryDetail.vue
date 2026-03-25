<template>
  <aside
    v-if="selectedEntry"
    class="entry-detail"
  >
    <div class="entry-detail-card">
      <div class="entry-detail-top">
        <div class="entry-detail-kicker">
          {{ copy.detail.kicker }}
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
        <div class="entry-grid">
          <div class="entry-field">
            <label>{{ copy.columns.order }}</label>
            <el-input-number
              v-model="selectedEntry.order"
              class="compact-order-input"
              controls-position="right"
              :min="1"
              :max="9999"
            />
          </div>
          <div class="entry-field entry-field-toggle">
            <label>{{ copy.columns.visible }}</label>
            <el-switch v-model="selectedEntry.isVisible" />
          </div>
        </div>
      </div>

      <div class="entry-detail-actions">
        <el-button
          link
          :disabled="!canMoveItem(selectedEntry, -1)"
          @click="$emit('move-item', selectedEntry, -1)"
        >
          {{ copy.actions.moveUp }}
        </el-button>
        <el-button
          link
          :disabled="!canMoveItem(selectedEntry, 1)"
          @click="$emit('move-item', selectedEntry, 1)"
        >
          {{ copy.actions.moveDown }}
        </el-button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import type { MenuManagementItem } from '@/api/system'
import type { EditableCategory } from '../shared'

defineProps<{
  copy: any
  selectedEntry: MenuManagementItem | null
  selectableCategories: EditableCategory[]
  getItemLabel: (item: Pick<MenuManagementItem, 'translationKey' | 'name' | 'nameEn' | 'code'>) => string
  getItemGroupLabel: (item: Pick<MenuManagementItem, 'groupCode'>) => string
  getCategoryLabel: (category: EditableCategory) => string
  canMoveItem: (item: Pick<MenuManagementItem, 'groupCode' | 'sourceType' | 'sourceCode' | 'code'>, offset: -1 | 1) => boolean
}>()

defineEmits<{
  (event: 'change-group', item: MenuManagementItem, groupCode: string): void
  (event: 'move-item', item: MenuManagementItem, offset: -1 | 1): void
}>()
</script>

<style scoped lang="scss">
@use '../styles/mixins' as *;

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
  font-size: 14px;
  line-height: 1.6;
  color: #41556f;
  word-break: break-all;
}

.entry-detail-meta,
.entry-detail-actions,
.entry-detail-stack {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.entry-detail-stack {
  flex-direction: column;
}

.entry-grid {
  display: grid;
  grid-template-columns: minmax(0, 140px) minmax(0, 140px);
  gap: 12px;
}

.entry-field {
  @include surface-field(12px);
}

.entry-field label {
  font-size: 12px;
  font-weight: 700;
  color: #71839b;
}

.compact-order-input {
  width: 100% !important;
  max-width: 124px;
  flex: none;
  align-self: flex-start;
}

.entry-field-toggle {
  justify-content: center;
}
</style>
