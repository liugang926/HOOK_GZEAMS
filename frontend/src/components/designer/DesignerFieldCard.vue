<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { Delete, Lock, RefreshRight } from '@element-plus/icons-vue'
import FieldDisplay from '@/components/common/FieldDisplay.vue'
import FieldRenderer from '@/components/engine/FieldRenderer.vue'
import type { DetailField } from '@/components/common/BaseDetailPage.vue'

interface DesignerFieldLite {
  id: string
  fieldCode: string
  fieldType?: string
  label: string
  required?: boolean
  readonly?: boolean
  minHeight?: number
  referenceObject?: string
  placeholder?: string
  componentProps?: Record<string, unknown>
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
  labelUpdate: [fieldId: string, label: string]
}>()

const labelInputRef = ref<HTMLInputElement | null>(null)
const editingLabel = ref(false)
const labelDraft = ref('')
const cancelLabelEdit = ref(false)

watch(
  () => props.field.label,
  (value) => {
    if (!editingLabel.value) {
      labelDraft.value = String(value || '')
    }
  },
  { immediate: true }
)

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

async function startLabelEditing() {
  if (!props.interactive) return
  handleSelect()
  cancelLabelEdit.value = false
  editingLabel.value = true
  labelDraft.value = String(props.field.label || '')
  await nextTick()
  labelInputRef.value?.focus()
  labelInputRef.value?.select()
}

function submitLabelEdit() {
  if (!editingLabel.value) return
  const nextLabel = String(labelDraft.value || '').trim()
  editingLabel.value = false
  if (!nextLabel || nextLabel === props.field.label) return
  emit('labelUpdate', props.field.id, nextLabel)
}

function revertLabelEdit() {
  cancelLabelEdit.value = true
  editingLabel.value = false
  labelDraft.value = String(props.field.label || '')
}

function handleLabelInputBlur() {
  if (cancelLabelEdit.value) {
    cancelLabelEdit.value = false
    return
  }
  submitLabelEdit()
}

function handleLabelKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    event.preventDefault()
    event.stopPropagation()
    submitLabelEdit()
    return
  }
  if (event.key === 'Escape') {
    event.preventDefault()
    event.stopPropagation()
    revertLabelEdit()
  }
}

// Field types that need backend context and can't preview in designer
const NON_PREVIEWABLE_TYPES = new Set(['file', 'image', 'attachment', 'related_object', 'sub_table', 'qr_code', 'barcode'])
const UPLOAD_PREVIEW_TYPES = new Set(['file', 'image', 'attachment'])
const TABLE_PREVIEW_TYPES = new Set(['related_object', 'sub_table'])

const fieldType = computed(() => props.field.fieldType || props.displayField?.type || 'text')

const canPreviewAsControl = computed(() => {
  return props.interactive && !NON_PREVIEWABLE_TYPES.has(fieldType.value) && fieldType.value !== 'reference'
})

const fieldTypeLabel = computed(() => {
  return fieldType.value.replace(/_/g, ' ')
})

const previewMode = computed<'runtime' | 'reference' | 'upload' | 'table' | 'code'>(
  () => {
    if (!props.interactive) return 'runtime'
    if (fieldType.value === 'reference') return 'reference'
    if (UPLOAD_PREVIEW_TYPES.has(fieldType.value)) return 'upload'
    if (TABLE_PREVIEW_TYPES.has(fieldType.value)) return 'table'
    if (NON_PREVIEWABLE_TYPES.has(fieldType.value)) return 'code'
    return 'runtime'
  }
)

const runtimeField = computed(() => {
  const f = props.field as any
  const df = props.displayField
  return {
    code: f.fieldCode || df?.prop || '',
    fieldCode: f.fieldCode || df?.prop || '',
    type: fieldType.value,
    label: f.label || df?.label || '',
    placeholder: f.placeholder || '',
    componentProps: f.componentProps || {}
  }
})

const referencePreviewLabel = computed(() => {
  if (typeof props.value === 'string' && props.value.trim()) return props.value
  if (props.value && typeof props.value === 'object') {
    const raw = props.value as Record<string, unknown>
    return String(raw.name || raw.label || raw.displayName || raw.id || '').trim()
  }
  return ''
})

const referencePreviewPlaceholder = computed(() =>
  String((props.field as any).placeholder || props.displayField?.label || 'Select record')
)

const referencePreviewMeta = computed(() =>
  String((props.field.referenceObject || (props.field.componentProps as any)?.referenceObject || '').trim() || 'Reference')
)

const tablePreviewTitle = computed(() =>
  fieldType.value === 'related_object' ? 'Embedded relation preview' : 'Subtable preview'
)

const uploadPreviewTitle = computed(() =>
  fieldType.value === 'image' ? 'Image upload preview' : 'Attachment upload preview'
)

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
      <span
        v-if="!editingLabel"
        class="field-label el-form-item__label"
        data-testid="designer-field-label"
        @dblclick.stop="startLabelEditing"
      >
        {{ field.label }}
        <span
          v-if="field.required"
          style="color: red"
        >*</span>
      </span>
      <input
        v-else
        ref="labelInputRef"
        v-model="labelDraft"
        class="field-label-input"
        data-testid="designer-field-label-input"
        @click.stop
        @mousedown.stop
        @blur="handleLabelInputBlur"
        @keydown="handleLabelKeydown"
      />
      <div class="field-value">
        <FieldRenderer
          v-if="previewMode === 'runtime' && canPreviewAsControl"
          :field="runtimeField"
          :model-value="value ?? null"
          :disabled="true"
          class="designer-field-preview"
        />
        <div
          v-else-if="previewMode === 'reference'"
          class="designer-preview-shell designer-preview-shell--reference"
          data-testid="designer-reference-preview"
        >
          <div class="designer-preview-select">
            <span :class="['designer-preview-select__value', { 'is-placeholder': !referencePreviewLabel }]">
              {{ referencePreviewLabel || referencePreviewPlaceholder }}
            </span>
            <el-tag size="small" type="info" effect="plain">
              {{ referencePreviewMeta }}
            </el-tag>
          </div>
        </div>
        <div
          v-else-if="previewMode === 'upload'"
          class="designer-preview-shell designer-preview-shell--upload"
          data-testid="designer-upload-preview"
        >
          <div class="designer-preview-upload__dropzone">
            {{ uploadPreviewTitle }}
          </div>
        </div>
        <div
          v-else-if="previewMode === 'table'"
          class="designer-preview-shell designer-preview-shell--table"
          data-testid="designer-table-preview"
        >
          <div class="designer-preview-table__header">
            <span>{{ tablePreviewTitle }}</span>
            <el-tag size="small" type="info" effect="plain">{{ fieldTypeLabel }}</el-tag>
          </div>
          <div class="designer-preview-table__row"></div>
          <div class="designer-preview-table__row is-short"></div>
        </div>
        <div
          v-else-if="interactive"
          class="field-type-indicator"
        >
          <el-tag size="small" type="info" effect="plain">
            {{ fieldTypeLabel }}
          </el-tag>
        </div>
        <FieldDisplay
          v-else
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
      <div
        class="overlay-label"
        data-testid="designer-field-overlay-label"
        @dblclick.stop="startLabelEditing"
      >
        {{ editingLabel ? labelDraft : field.label }}
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
  padding: 8px 10px;
  border-radius: 6px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: move;
  border: 1.5px solid transparent;
  --detail-label-width: var(--gzeams-detail-label-width, 120px);
  --detail-field-gap: var(--gzeams-detail-field-gap, 16px);

  &:hover:not(.is-readonly):not(.is-selected) {
    background: rgba(64, 158, 255, 0.04);
    border: 1px dashed #409eff;
  }

  &.is-selected {
    background: rgba(64, 158, 255, 0.08);
    border: 1px solid #409eff;
    border-radius: 4px;
    z-index: 2;
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
  align-items: center;
  min-height: 32px;
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

.field-label-input {
  width: 100%;
  min-width: 0;
  height: 30px;
  padding: 4px 8px;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.4;
  color: #303133;
  border: 1px solid var(--el-color-primary, #409eff);
  border-radius: 6px;
  background: #ffffff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.12);
}

.field-value {
  min-width: 0;
  font-size: 14px;
  color: #303133;
  line-height: 22px;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.designer-field-preview {
  width: 100%;
  pointer-events: none;
  opacity: 0.85;

  :deep(.el-input),
  :deep(.el-select),
  :deep(.el-input-number),
  :deep(.el-date-editor),
  :deep(.el-switch),
  :deep(.el-textarea) {
    width: 100%;
  }

  :deep(.el-input__wrapper),
  :deep(.el-textarea__inner) {
    background-color: #f5f7fa;
    box-shadow: 0 0 0 1px #dcdfe6 inset;
  }
}

.designer-preview-shell {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  background: #f8fafc;
  color: #606266;
}

.designer-preview-shell--reference {
  padding: 8px 10px;
}

.designer-preview-select {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.designer-preview-select__value {
  min-width: 0;
  flex: 1;
  color: #303133;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.designer-preview-select__value.is-placeholder {
  color: #a8abb2;
}

.designer-preview-shell--upload {
  padding: 8px;
}

.designer-preview-upload__dropzone {
  min-height: 56px;
  border: 1px dashed #c0c4cc;
  border-radius: 6px;
  background: repeating-linear-gradient(
    45deg,
    #ffffff,
    #ffffff 8px,
    #f7f9fc 8px,
    #f7f9fc 16px
  );
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #909399;
}

.designer-preview-shell--table {
  padding: 8px;
}

.designer-preview-table__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #606266;
}

.designer-preview-table__row {
  height: 12px;
  border-radius: 999px;
  background: linear-gradient(90deg, #dfe6ee 0%, #eef3f8 100%);
}

.designer-preview-table__row.is-short {
  width: 68%;
  margin-top: 6px;
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
  bottom: -24px;
  right: -1px;
  pointer-events: auto;
  display: flex;
  background: #409eff;
  border-radius: 0 0 4px 4px;
  padding: 2px 4px;
  gap: 4px;

  .el-button {
    background: transparent;
    border: none;
    color: white;
    padding: 2px;
    height: auto;
    font-size: 14px;
  }
  .el-button:hover {
    background: rgba(255, 255, 255, 0.2);
    color: white;
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
