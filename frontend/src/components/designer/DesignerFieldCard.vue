<script setup lang="ts">
import { computed } from 'vue'
import { Delete, Lock, RefreshRight } from '@element-plus/icons-vue'
import FieldDisplay from '@/components/common/FieldDisplay.vue'
import type { DetailField } from '@/components/common/BaseDetailPage.vue'

interface DesignerFieldLite {
  id: string
  fieldCode: string
  label: string
  required?: boolean
  readonly?: boolean
  minHeight?: number
}

type ResizeAxis = 'x' | 'y' | 'xy'

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
  readonlyTitle?: string
  resizable?: boolean
  allowHorizontalResize?: boolean
  allowVerticalResize?: boolean
  resizeTitle?: string
  resetSizeTitle?: string
  sidebarResizeHint?: string
  sizeFeedbackActive?: boolean
}>(), {
  selected: false,
  interactive: true,
  sidebar: false,
  removeTitle: 'Remove field',
  readonlyTitle: 'Readonly',
  resizable: true,
  allowHorizontalResize: true,
  allowVerticalResize: true,
  resizeTitle: 'Drag to resize field size',
  resetSizeTitle: 'Reset field size',
  sidebarResizeHint: '',
  sizeFeedbackActive: false
})

const emit = defineEmits<{
  select: []
  remove: [fieldId: string, sectionId: string, sectionIndex: number]
  resetSize: [fieldId: string]
  resizeStart: [payload: { fieldId: string; axis: ResizeAxis; startX: number; startY: number; cardWidth: number; cardHeight: number }]
}>()

function handleRemove() {
  if (!props.interactive) return
  emit('remove', props.field.id, props.sectionId, props.sectionIndex)
}

function handleSelect() {
  if (!props.interactive) return
  emit('select')
}

function handleResetSize() {
  if (!props.interactive || !props.resizable) return
  emit('resetSize', props.field.id)
}

const fieldItemStyle = computed(() => {
  const rawHeight = Number(props.field?.minHeight)
  if (!Number.isFinite(rawHeight) || rawHeight <= 0) return {}
  return { minHeight: `${Math.round(rawHeight)}px` }
})

const showSidebarResizeHint = computed(() =>
  Boolean(
    props.interactive &&
    props.selected &&
    props.resizable &&
    props.allowVerticalResize &&
    !props.allowHorizontalResize &&
    props.sidebarResizeHint
  )
)

function handleResizePointerDown(axis: ResizeAxis, event: PointerEvent) {
  if (!props.interactive || !props.resizable) return
  if (axis === 'x' && !props.allowHorizontalResize) return
  if (axis === 'y' && !props.allowVerticalResize) return
  if (axis === 'xy' && !props.allowHorizontalResize && !props.allowVerticalResize) return

  event.preventDefault()
  event.stopPropagation()

  const handleEl = event.currentTarget as HTMLElement | null
  const cardEl = handleEl?.closest('.designer-field-card') as HTMLElement | null
  const rect = cardEl?.getBoundingClientRect()

  emit('resizeStart', {
    fieldId: props.field.id,
    axis,
    startX: event.clientX,
    startY: event.clientY,
    cardWidth: rect?.width || 0,
    cardHeight: rect?.height || 0
  })
}
</script>

<template>
  <div
    class="designer-field-card dynamic-form-section__field"
    data-testid="layout-canvas-field"
    :class="{
      'is-selected': interactive && selected,
      'sidebar-field-col': sidebar,
      'is-readonly': !interactive,
      'is-field-readonly': field.readonly === true,
      'is-size-feedback': sizeFeedbackActive === true
    }"
    :data-field-id="field.id"
    :data-field-code="field.fieldCode"
    :data-field-readonly="field.readonly === true ? 'true' : 'false'"
    :data-field-min-height="field.minHeight ? String(field.minHeight) : ''"
    @mousedown.stop="handleSelect"
    @click.stop="handleSelect"
  >
    <div
      class="field-item"
      :class="{ 'field-image': displayField.type === 'image', 'sidebar-field-item': sidebar }"
      :style="fieldItemStyle"
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
      v-if="field.readonly === true"
      class="readonly-indicator"
      :title="readonlyTitle"
    >
      <el-icon><Lock /></el-icon>
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
          v-if="resizable && (allowHorizontalResize || allowVerticalResize)"
          size="small"
          circle
          :title="resetSizeTitle"
          data-testid="layout-reset-field-size-button"
          @click.stop="handleResetSize"
        >
          <el-icon><RefreshRight /></el-icon>
        </el-button>
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
      <div
        v-if="allowHorizontalResize"
        class="field-resize-handle handle-x"
        :title="resizeTitle"
        data-testid="layout-field-resize-handle-x"
        @pointerdown="handleResizePointerDown('x', $event)"
      />
      <div
        v-if="allowVerticalResize"
        class="field-resize-handle handle-y"
        :title="resizeTitle"
        data-testid="layout-field-resize-handle-y"
        @pointerdown="handleResizePointerDown('y', $event)"
      />
      <div
        v-if="allowHorizontalResize && allowVerticalResize"
        class="field-resize-handle handle-xy"
        :title="resizeTitle"
        data-testid="layout-field-resize-handle-xy"
        @pointerdown="handleResizePointerDown('xy', $event)"
      />
      <div
        v-if="showSidebarResizeHint"
        class="overlay-hint"
        data-testid="layout-sidebar-resize-hint"
      >
        {{ sidebarResizeHint }}
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
  --detail-label-width: var(--gzeams-detail-label-width, 120px);
  --detail-field-gap: var(--gzeams-detail-field-gap, 16px);

  &.is-selected {
    background: #ecf5ff;
    border: 1px dashed #409eff;
    border-radius: 4px;
  }

  &.is-size-feedback {
    box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.35);
    animation: size-feedback-pulse 0.9s ease-out 1;
  }

  &.is-readonly {
    cursor: default;
  }

  &.is-field-readonly {
    background: #f5f7fa;
    border: 1px solid #e4e7ed;
  }

  &.is-field-readonly .field-label,
  &.is-field-readonly .field-value {
    color: #909399;
  }
}

@keyframes size-feedback-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(64, 158, 255, 0.45);
  }
  100% {
    box-shadow: 0 0 0 8px rgba(64, 158, 255, 0);
  }
}

.field-item {
  display: grid;
  grid-template-columns: var(--detail-label-width) minmax(0, 1fr);
  column-gap: var(--detail-field-gap);
  align-items: flex-start;
}

.field-item.field-image {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.field-label {
  display: block;
  font-size: 13px;
  color: #606266;
  line-height: 22px;
  font-weight: 500;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.field-value {
  min-width: 0;
  font-size: 14px;
  color: #303133;
  line-height: 22px;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.sidebar-field-col {
  margin-bottom: 10px;
}

.sidebar-field-item {
  display: flex;
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
  top: 6px;
  right: 4px;
  pointer-events: auto;
  display: flex;
  gap: 4px;
}

.overlay-hint {
  position: absolute;
  left: 8px;
  bottom: 6px;
  font-size: 11px;
  line-height: 1.3;
  color: #409eff;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 3px;
  padding: 2px 6px;
}

.field-resize-handle {
  position: absolute;
  pointer-events: auto;
  background: #409eff;
  border: 1px solid #ffffff;
  border-radius: 2px;
  box-shadow: 0 0 0 1px rgba(64, 158, 255, 0.25);
  opacity: 0.95;
}

.field-resize-handle.handle-x {
  top: 50%;
  right: -6px;
  width: 10px;
  height: 28px;
  transform: translateY(-50%);
  cursor: ew-resize;
}

.field-resize-handle.handle-y {
  left: 50%;
  bottom: -6px;
  width: 28px;
  height: 10px;
  transform: translateX(-50%);
  cursor: ns-resize;
}

.field-resize-handle.handle-xy {
  right: -6px;
  bottom: -6px;
  width: 12px;
  height: 12px;
  cursor: nwse-resize;
}

.readonly-indicator {
  position: absolute;
  top: 6px;
  right: 8px;
  color: #909399;
  font-size: 12px;
  pointer-events: none;
}
</style>

<style lang="scss">
@use '@/components/common/detail/BaseDetailPage.scss';
</style>
