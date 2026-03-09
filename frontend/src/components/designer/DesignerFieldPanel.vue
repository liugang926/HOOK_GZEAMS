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
      <div v-for="group in filteredFieldGroups" :key="group.type" class="field-group">
        <div class="group-header" @click="$emit('toggleGroup', group.type)">
          <el-icon><component :is="group.icon" /></el-icon>
          <span>{{ group.label }}</span>
          <el-tag size="small">{{ group.fields.length }}</el-tag>
          <el-icon class="expand-icon" :class="{ expanded: isGroupExpanded(group.type) }">
            <ArrowRight />
          </el-icon>
        </div>
        <div v-show="isGroupExpanded(group.type)" class="group-fields">
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
            <el-icon class="field-icon"><Edit /></el-icon>
            <span class="field-label">{{ field.name }}</span>
            <span class="field-code">{{ field.code }}</span>
            <el-icon v-if="isFieldAdded(field.code)" class="added-icon"><Check /></el-icon>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowRight, Check, Edit, Search } from '@element-plus/icons-vue'
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

defineExpose({
  focusSearch: () => searchInputRef.value?.focus()
})
</script>
