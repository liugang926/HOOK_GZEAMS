<script setup lang="ts">
import { Delete } from '@element-plus/icons-vue'
import FieldDisplay from '@/components/common/FieldDisplay.vue'
import type { DetailField } from '@/components/common/BaseDetailPage.vue'

interface DesignerFieldLite {
  id: string
  fieldCode: string
  label: string
  required?: boolean
}

const props = withDefaults(defineProps<{
  field: DesignerFieldLite
  displayField: DetailField
  value: unknown
  selected?: boolean
  interactive?: boolean
  sidebar?: boolean
  sectionId: string
  sectionIndex: number
  removeTitle?: string
}>(), {
  selected: false,
  interactive: true,
  sidebar: false,
  removeTitle: 'Remove field'
})

const emit = defineEmits<{
  select: []
  remove: [fieldId: string, sectionId: string, sectionIndex: number]
}>()

function handleRemove() {
  if (!props.interactive) return
  emit('remove', props.field.id, props.sectionId, props.sectionIndex)
}

function handleSelect() {
  if (!props.interactive) return
  emit('select')
}
</script>

<template>
  <div
    class="designer-field-card dynamic-form-section__field"
    data-testid="layout-canvas-field"
    :class="{ 'is-selected': interactive && selected, 'sidebar-field-col': sidebar, 'is-readonly': !interactive }"
    :data-field-id="field.id"
    :data-field-code="field.fieldCode"
    @mousedown.stop="handleSelect"
    @click.stop="handleSelect"
  >
    <div
      class="field-item"
      :class="{ 'field-image': displayField.type === 'image', 'sidebar-field-item': sidebar }"
    >
      <span class="field-label el-form-item__label">
        {{ field.label }}
        <span
          v-if="field.required"
          style="color: red"
        >*</span>
      </span>
      <div class="field-value">
        <FieldDisplay
          :field="displayField"
          :value="value"
        />
      </div>
    </div>
    <div
      v-if="interactive && selected"
      class="field-overlay"
    >
      <div class="overlay-label">
        {{ field.label }}
        <span
          v-if="field.fieldCode"
          class="overlay-code"
        >[{{ field.fieldCode }}]</span>
      </div>
      <div class="overlay-actions">
        <el-button
          size="small"
          circle
          :title="removeTitle"
          data-testid="layout-remove-field-button"
          @click.stop="handleRemove"
        >
          <el-icon><Delete /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.designer-field-card {
  position: relative;
  min-width: 0;
  padding: 0;
  border-radius: 4px;
  transition: all 0.2s;
  cursor: move;

  &.is-selected {
    background: #ecf5ff;
    border: 1px dashed #409eff;
    border-radius: 4px;
  }

  &.is-readonly {
    cursor: default;
  }
}

.field-item {
  display: flex;
  align-items: flex-start;
}

.field-item.field-image {
  flex-direction: column;
  align-items: flex-start;
}

.field-label {
  min-width: 120px;
  padding-right: 16px;
  font-size: 13px;
  color: #606266;
  line-height: 22px;
  flex-shrink: 0;
  font-weight: 500;
}

.field-value {
  flex: 1;
  font-size: 14px;
  color: #303133;
  line-height: 22px;
  word-break: break-all;
}

.sidebar-field-col {
  margin-bottom: 10px;
}

.sidebar-field-item {
  flex-direction: column;
  align-items: flex-start;
}

.sidebar-field-item .field-label {
  min-width: 0;
  padding-right: 0;
  margin-bottom: 4px;
}

.field-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
}

.overlay-label {
  position: absolute;
  top: 2px;
  left: 8px;
  font-size: 12px;
  color: #409eff;
  background: rgba(255, 255, 255, 0.9);
  padding: 2px 6px;
  border-radius: 3px;
}

.overlay-code {
  margin-left: 6px;
  font-size: 11px;
  color: #909399;
}

.overlay-actions {
  position: absolute;
  top: 50%;
  right: 4px;
  transform: translateY(-50%);
  pointer-events: auto;
  display: flex;
  gap: 4px;
}
</style>
