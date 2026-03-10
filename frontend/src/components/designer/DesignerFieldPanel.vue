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
          <el-icon :style="{ color: group.color || '#909399' }">
            <component :is="group.icon" />
          </el-icon>
          <span>{{ group.label }}</span>
          <el-tag size="small" round effect="plain">
            {{ group.fields.length }}
          </el-tag>
          <el-icon
            class="expand-icon"
            :class="{ expanded: isGroupExpanded(group.type) }"
          >
            <ArrowRight />
          </el-icon>
        </div>
        <div
          v-show="isGroupExpanded(group.type)"
          class="group-fields"
        >
          <div
            v-for="field in group.fields"
            :key="field.code"
            class="palette-field-item"
            :data-testid="`layout-palette-field-${field.code}`"
            :draggable="canAddField(field)"
            :title="getDisabledReason(field) || ''"
            :class="{
              'is-selected': isFieldAdded(field.code),
              'is-disabled': !canAddField(field)
            }"
            @dragstart="$emit('fieldDragStart', $event, field)"
            @dragend="$emit('dragEnd')"
            @click="$emit('fieldClick', field)"
          >
            <el-icon class="field-icon" :style="{ color: resolveFieldColor(field) }">
              <component :is="resolveFieldIcon(field)" />
            </el-icon>
            <span class="field-label">{{ field.name }}</span>
            <span class="field-code">{{ field.code }}</span>
            <el-icon
              v-if="isFieldAdded(field.code)"
              class="added-icon"
            >
              <Check />
            </el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, type Component } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  ArrowRight, Check, Search,
  Edit, EditPen, Document, Histogram, Calendar, Timer,
  Message, Link, Connection, User, OfficeBuilding,
  Folder, Picture, Select, CircleCheck, Ticket, FolderOpened
} from '@element-plus/icons-vue'
import { normalizeFieldType } from '@/utils/fieldType'
import type { DesignerFieldDefinition, FieldGroup } from '@/components/designer/designerTypes'

defineProps<{
  renderMode: 'design' | 'preview'
  searchQuery: string
  filteredFieldGroups: FieldGroup[]
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
  const ft = normalizeFieldType(field.fieldType || field.field_type || field.type || 'text')
  return (fieldTypeVisuals[ft] || defaultVisual).icon
}

function resolveFieldColor(field: DesignerFieldDefinition): string {
  const ft = normalizeFieldType(field.fieldType || field.field_type || field.type || 'text')
  return (fieldTypeVisuals[ft] || defaultVisual).color
}

defineExpose({
  focusSearch: () => searchInputRef.value?.focus()
})
</script>
