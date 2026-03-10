<script setup lang="ts">
import { computed } from 'vue'
import { Delete, Lock, RefreshRight } from '@element-plus/icons-vue'
import FieldDisplay from '@/components/common/FieldDisplay.vue'
import type { DetailField } from '@/components/common/BaseDetailPage.vue'

interface DesignerFieldLite {
  id: string
  fieldCode: string
  fieldType?: string
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
  const styles: Record<string, string> = {}
  const rawHeight = Number(props.field?.minHeight)
  if (Number.isFinite(rawHeight) && rawHeight > 0) {
    styles.minHeight = `${Math.round(rawHeight)}px`
  }

  const fieldAny = props.field as any
  if (fieldAny.labelWidth) {
    const width = fieldAny.labelWidth
    styles['--field-label-width'] = typeof width === 'number' ? `${width}px` : width
  }
  return styles
})

const fieldItemClass = computed(() => {
  const fieldAny = props.field as any
  const classes = []
  if (props.displayField.type === 'image') classes.push('field-image')
  if (props.sidebar) classes.push('sidebar-field-item')
  if (fieldAny.labelPosition === 'top') classes.push('label-position-top')
  return classes
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
      v-if="field.fieldType === 'empty'"
      class="empty-space-card"
      :style="fieldItemStyle"
    >
      <div class="empty-space-content">
        Empty Space
      </div>
    </div>
    <div
      v-else
      class="field-item"
      :class="fieldItemClass"
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
  border-radius: 6px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: move;
  border: 1.5px solid transparent;
  --detail-label-width: var(--gzeams-detail-label-width, 120px);
  --detail-field-gap: var(--gzeams-detail-field-gap, 16px);

  &:hover:not(.is-readonly):not(.is-selected) {
    background: rgba(64, 158, 255, 0.03);
    border-color: rgba(64, 158, 255, 0.15);
    border-left: 2.5px solid var(--el-color-primary-light-5, #79bbff);
  }

  &.is-selected {
    background: var(--el-color-primary-light-9, #ecf5ff);
    border: 2px solid var(--el-color-primary, #409eff);
    border-radius: 6px;
    box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
  }

  &.is-size-feedback {
    box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.35);
    animation: size-feedback-pulse 0.9s ease-out 1;
  }

  &.is-readonly {
    cursor: default;
  }

  &.is-field-readonly {
    background: #f8f9fb;
    border: 1px solid #ebedf0;
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

.empty-space-card {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 44px;
  background: repeating-linear-gradient(
    45deg,
    #f5f7fa,
    #f5f7fa 10px,
    #ffffff 10px,
    #ffffff 20px
  );
  border: 1px dashed #dcdfe6;
  border-radius: 4px;

  .empty-space-content {
    color: #909399;
    font-size: 12px;
  }
}

.field-item {
  display: grid;
  grid-template-columns: var(--field-label-width, var(--detail-label-width)) minmax(0, 1fr);
  column-gap: var(--detail-field-gap);
  align-items: flex-start;
}

.field-item.label-position-top {
  display: flex;
  flex-direction: column;
  gap: 4px;

  .field-label {
    width: 100%;
    margin-bottom: 2px;
  }
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
  top: -10px;
  left: 8px;
  font-size: 11px;
  font-weight: 600;
  color: var(--el-color-primary, #409eff);
  background: white;
  padding: 1px 8px;
  border-radius: 4px;
  border: 1px solid var(--el-color-primary-light-7, #a0cfff);
  box-shadow: 0 1px 3px rgba(64, 158, 255, 0.12);
  line-height: 1.4;
  white-space: nowrap;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.overlay-code {
  margin-left: 4px;
  font-size: 10px;
  font-weight: 400;
  color: #909399;
}

.overlay-actions {
  position: absolute;
  top: -10px;
  right: 4px;
  pointer-events: auto;
  display: flex;
  gap: 2px;

  .el-button {
    background: white;
    border: 1px solid #e4e7ed;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  }
}

.overlay-hint {
  position: absolute;
  left: 8px;
  bottom: -10px;
  font-size: 10px;
  line-height: 1.3;
  color: var(--el-color-primary, #409eff);
  background: white;
  border: 1px solid var(--el-color-primary-light-7, #a0cfff);
  border-radius: 4px;
  padding: 1px 6px;
  box-shadow: 0 1px 3px rgba(64, 158, 255, 0.12);
}

.field-resize-handle {
  position: absolute;
  pointer-events: auto;
  background: var(--el-color-primary, #409eff);
  border: 1.5px solid #ffffff;
  border-radius: 3px;
  box-shadow: 0 1px 4px rgba(64, 158, 255, 0.3);
  opacity: 0;
  transition: opacity 0.15s ease;

  .designer-field-card.is-selected & {
    opacity: 1;
  }
}

.field-resize-handle.handle-x {
  top: 50%;
  right: -5px;
  width: 8px;
  height: 24px;
  transform: translateY(-50%);
  cursor: ew-resize;
  border-radius: 4px;
}

.field-resize-handle.handle-y {
  left: 50%;
  bottom: -5px;
  width: 24px;
  height: 8px;
  transform: translateX(-50%);
  cursor: ns-resize;
  border-radius: 4px;
}

.field-resize-handle.handle-xy {
  right: -5px;
  bottom: -5px;
  width: 10px;
  height: 10px;
  cursor: nwse-resize;
  border-radius: 50%;
}

.readonly-indicator {
  position: absolute;
  top: 4px;
  right: 6px;
  color: #909399;
  font-size: 11px;
  pointer-events: none;
  background: #f5f7fa;
  border-radius: 3px;
  padding: 1px 4px;
  border: 1px solid #e4e7ed;
}
</style>

<style lang="scss">
@use '@/components/common/detail/BaseDetailPage.scss';
</style>
