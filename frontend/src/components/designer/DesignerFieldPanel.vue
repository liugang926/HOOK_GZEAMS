<template>
  <div
    v-if="renderMode === 'design'"
    class="field-panel"
    data-testid="layout-field-panel"
  >
    <div class="panel-header">
      <el-input
        ref="searchInputRef"
        :model-value="searchQuery"
        :placeholder="t('system.pageLayout.designer.placeholders.searchField')"
        :prefix-icon="Search"
        size="small"
        clearable
        @update:model-value="$emit('update:searchQuery', String($event || ''))"
      />
      <div class="assignment-summary">
        <div class="assignment-summary__meta">
          <span class="assignment-summary__label">{{ t('system.pageLayout.designer.stats.assigned', 'Assigned') }}</span>
          <span class="assignment-summary__value">{{ assignedFieldCount }}/{{ totalFieldCount }}</span>
        </div>
        <el-progress
          :percentage="assignmentPercentage"
          :stroke-width="6"
          :show-text="false"
        />
      </div>
    </div>
    <div class="panel-content">
      <div
        v-for="group in filteredFieldGroups"
        :key="group.type"
        class="field-group"
      >
        <div
          class="group-header"
          @click="$emit('toggleGroup', group.type)"
        >
          <span class="group-title">{{ group.label }}</span>
          <el-icon
            class="expand-icon"
            :class="{ expanded: isGroupExpanded(group.type) }"
          >
            <ArrowRight />
          </el-icon>
        </div>
        <div
          v-show="isGroupExpanded(group.type)"
          class="group-fields-grid"
        >
          <div
            v-for="field in group.fields"
            :key="field.code"
            class="field-tile"
            :data-testid="`layout-palette-field-${field.code}`"
            :draggable="canAddField(field)"
            :title="getDisabledReason(field) || field.name"
            :class="{
              'is-added': isFieldAdded(field.code),
              'is-unassigned': !isFieldAdded(field.code) && canAddField(field),
              'is-disabled': !canAddField(field)
            }"
            @dragstart="$emit('fieldDragStart', $event, field)"
            @dragend="$emit('dragEnd')"
            @click="$emit('fieldClick', field)"
          >
            <el-icon class="tile-icon" :style="{ color: resolveFieldColor(field) }">
              <component :is="resolveFieldIcon(field)" />
            </el-icon>
            <span class="tile-label" :title="field.name">{{ field.name }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, type Component } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ArrowRight, Check, Search,
  Edit, EditPen, Document, Histogram, Calendar, Timer,
  Message, Link, Connection, User, OfficeBuilding,
  Folder, Picture, Select, CircleCheck, Ticket, FolderOpened
} from '@element-plus/icons-vue'
import { normalizeFieldType } from '@/utils/fieldType'
import type { DesignerFieldDefinition, FieldGroup } from '@/components/designer/designerTypes'

const props = defineProps<{
  renderMode: 'design' | 'preview'
  searchQuery: string
  filteredFieldGroups: FieldGroup[]
  assignedFieldCount: number
  totalFieldCount: number
  isGroupExpanded: (type: string) => boolean
  canAddField: (field: DesignerFieldDefinition) => boolean
  getDisabledReason: (field: DesignerFieldDefinition) => string | null
  isFieldAdded: (code: string) => boolean
}>()

defineEmits<{
  (e: 'update:searchQuery', value: string): void
  (e: 'toggleGroup', type: string): void
  (e: 'fieldClick', field: DesignerFieldDefinition): void
  (e: 'fieldDragStart', event: DragEvent, field: DesignerFieldDefinition): void
  (e: 'dragEnd'): void
}>()

const { t } = useI18n()
const searchInputRef = ref<{ focus: () => void } | null>(null)
const assignmentPercentage = computed(() => {
  if (props.totalFieldCount <= 0) return 0
  return Math.max(0, Math.min(100, Math.round((props.assignedFieldCount / props.totalFieldCount) * 100)))
})



// ── Per-field-type icon / color resolution ──
const fieldTypeVisuals: Record<string, { icon: Component; color: string }> = {
  text: { icon: EditPen, color: '#606266' },
  textarea: { icon: Document, color: '#409eff' },
  rich_text: { icon: Document, color: '#409eff' },
  number: { icon: Histogram, color: '#e6a23c' },
  currency: { icon: Histogram, color: '#e6a23c' },
  percent: { icon: Histogram, color: '#e6a23c' },
  boolean: { icon: CircleCheck, color: '#67c23a' },
  date: { icon: Calendar, color: '#409eff' },
  datetime: { icon: Timer, color: '#409eff' },
  email: { icon: Message, color: '#409eff' },
  url: { icon: Link, color: '#3498db' },
  reference: { icon: Connection, color: '#9b59b6' },
  user: { icon: User, color: '#f56c6c' },
  department: { icon: OfficeBuilding, color: '#f56c6c' },
  file: { icon: Folder, color: '#e6a23c' },
  image: { icon: Picture, color: '#e91e63' },
  select: { icon: Select, color: '#67c23a' },
  multi_select: { icon: Select, color: '#67c23a' },
  radio: { icon: CircleCheck, color: '#67c23a' },
  checkbox: { icon: Check, color: '#67c23a' },
  sub_table: { icon: FolderOpened, color: '#909399' },
  formula: { icon: Ticket, color: '#9c27b0' },
  empty: { icon: Edit, color: '#c0c4cc' }
}

const defaultVisual = { icon: EditPen, color: '#909399' }

function resolveFieldIcon(field: DesignerFieldDefinition): Component {
  const ft = normalizeFieldType(field.fieldType || field.type || 'text')
  return (fieldTypeVisuals[ft] || defaultVisual).icon
}

function resolveFieldColor(field: DesignerFieldDefinition): string {
  const ft = normalizeFieldType(field.fieldType || field.type || 'text')
  return (fieldTypeVisuals[ft] || defaultVisual).color
}

defineExpose({
  focusSearch: () => searchInputRef.value?.focus()
})
</script>

<style scoped>
.field-panel {
  width: 268px;
  min-width: 268px;
  background: #ffffff;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  min-height: 0;
  box-shadow: 1px 0 4px rgba(0, 0, 0, 0.04);
}

.panel-header {
  padding: 14px 16px;
  border-bottom: 1px solid #e4e7ed;
}

.assignment-summary {
  margin-top: 12px;
}

.assignment-summary__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 12px;
}

.assignment-summary__label {
  color: #606266;
}

.assignment-summary__value {
  color: #303133;
  font-weight: 600;
}

.panel-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 0;
}

.panel-content::-webkit-scrollbar {
  width: 5px;
}
.panel-content::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
  border-radius: 4px;
}

.field-group {
  margin-bottom: 2px;
}

.group-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}
.group-header:hover {
  background: #f5f7fa;
}
.group-title {
  flex: 1;
}
.expand-icon {
  transition: transform 0.25s ease;
  font-size: 12px;
  color: #909399;
}
.expand-icon.expanded {
  transform: rotate(90deg);
}

.group-fields-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  padding: 4px 12px 14px;
}

.field-tile {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 4px;
  border-radius: 4px;
  cursor: grab;
  transition: all 0.2s ease;
  border: 1px solid #f1f2f3;
  position: relative;
  background: #fdfdfe;
  min-height: 64px;
}
.tile-icon {
  font-size: 20px;
  transition: all 0.2s ease;
  color: #555555 !important;
}
.tile-label {
  font-size: 11px;
  color: #333333;
  text-align: center;
  line-height: 1.2;
  width: 100%;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-word;
}

.field-tile:hover {
  background: #ffffff;
  border-color: #409EFF;
  box-shadow: 0 2px 6px rgba(64, 158, 255, 0.15);
}
.field-tile:hover .tile-icon {
  color: #409EFF !important;
}
.field-tile:hover .tile-label {
  color: #409EFF;
}

.field-tile:active {
  cursor: grabbing;
  transform: scale(0.96);
  background: var(--el-color-primary-light-9, #ecf5ff);
}

.field-tile.is-added {
  /* FormCreate uses a subtle blue border for added/selected items, no green background */
  border-color: #409EFF;
  background: #ffffff;
}
.field-tile.is-added .tile-icon {
  color: #409EFF !important;
}
.field-tile.is-added .tile-label {
  color: #409EFF;
}

.field-tile.is-unassigned:not(.is-added) {
  border-color: #d9ecff;
  background: linear-gradient(180deg, #f8fbff 0%, #ffffff 100%);
}

.field-tile.is-disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
  background: #f5f7fa;
  border-color: #e4e7ed;
}
</style>
