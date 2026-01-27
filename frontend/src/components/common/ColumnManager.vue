<template>
  <el-popover
    placement="bottom"
    :width="380"
    trigger="click"
    :teleported="true"
    @show="handleShow"
  >
    <template #reference>
      <span class="column-manager-trigger">
        <el-tooltip
          content="Column Settings"
          placement="top"
        >
          <el-button
            :icon="Setting"
            circle
            size="small"
          />
        </el-tooltip>
      </span>
    </template>

    <div class="column-manager">
      <!-- Header with actions -->
      <div class="column-manager-header">
        <span>Column Settings</span>
        <div class="header-actions">
          <el-button
            link
            size="small"
            @click="handleReset"
          >
            Reset
          </el-button>
          <el-button
            link
            type="primary"
            size="small"
            @click="handleSave"
          >
            Save
          </el-button>
        </div>
      </div>

      <el-divider style="margin: 12px 0" />

      <!-- Draggable column list -->
      <div class="column-list">
        <div
          v-for="(col, index) in internalColumns"
          :key="getFieldCode(col)"
          class="column-item"
          :class="{
            'column-item-dragging': draggingIndex === index,
            'column-item-required': isRequired(col)
          }"
          draggable="true"
          @dragstart="handleDragStart(index, $event)"
          @dragover="handleDragOver(index, $event)"
          @dragend="handleDragEnd"
          @drop="handleDrop(index, $event)"
        >
          <div class="column-item-main">
            <el-icon
              class="drag-handle"
              :size="16"
            >
              <DCaret />
            </el-icon>

            <!-- Field type badge -->
            <span
              v-if="(col as any).field_type"
              class="field-type-badge"
              :title="`Type: ${(col as any).field_type}`"
            >
              {{ getFieldTypeLabel((col as any).field_type) }}
            </span>

            <el-checkbox
              :model-value="col.visible !== false"
              :disabled="isRequired(col)"
              @update:model-value="(val: boolean) => handleToggleVisibility(col, val)"
            >
              <span
                class="column-label"
                :title="(col as any).label_override ? col.label : ''"
              >
                {{ getDisplayLabel(col) }}
              </span>
              <el-tooltip
                v-if="(col as any).label_override"
                :content="`Original: ${col.label}`"
                placement="top"
              >
                <el-icon class="override-icon" :size="12">
                  <InfoFilled />
                </el-icon>
              </el-tooltip>
            </el-checkbox>

            <div class="column-actions">
              <!-- Column fixed selector -->
              <el-select
                :model-value="(col.fixed || '') as string"
                size="small"
                style="width: 75px"
                @update:model-value="(val) => handleFixedChange(col, val)"
              >
                <el-option label="None" value="" />
                <el-option label="Left" value="left" />
                <el-option label="Right" value="right" />
              </el-select>

              <el-input-number
                :model-value="col.width || col.defaultWidth || 120"
                :min="50"
                :max="500"
                :step="10"
                size="small"
                controls-position="right"
                style="width: 85px"
                @update:model-value="(val: number) => handleWidthChange(col, val)"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- Footer actions -->
      <div class="column-manager-footer">
        <el-checkbox
          :model-value="allVisible"
          :indeterminate="someVisible"
          @update:model-value="handleToggleAll"
        >
          Select All
        </el-checkbox>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, DCaret, InfoFilled } from '@element-plus/icons-vue'
import type { ColumnItem } from '@/hooks/useColumnConfig'

interface Props {
  columns: ColumnItem[]
  objectCode?: string
  modelValue?: ColumnItem[]
}

interface Emits {
  (e: 'update:modelValue', value: ColumnItem[]): void
  (e: 'save', columns: ColumnItem[]): void
  (e: 'reset'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Internal column state with drag-drop support
const internalColumns = ref<ColumnItem[]>([])
const draggingIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

// Helper to get field_code with backward compatibility for prop
const getFieldCode = (col: ColumnItem): string => {
  return (col as any).field_code || col.prop || ''
}

// Helper to check if column is required (cannot be hidden)
const isRequired = (col: ColumnItem): boolean => {
  return (col as any).required_in_list === true
}

// Field type mapping for badges
const getFieldTypeLabel = (type: string): string => {
  const typeMap: Record<string, string> = {
    text: 'T',
    number: '#',
    date: 'D',
    datetime: 'DT',
    boolean: 'B',
    select: 'S',
    user: 'U',
    reference: 'R'
  }
  return typeMap[type] || type[0]?.toUpperCase() || ''
}

// Get display label (with override support)
const getDisplayLabel = (col: ColumnItem): string => {
  return (col as any).label_override || col.label
}

// Initialize columns
const initColumns = () => {
  internalColumns.value = props.columns.map(col => ({
    ...col,
    defaultWidth: col.defaultWidth || col.width || 120,
    visible: col.visible !== false
  }))
}

// Watch for column changes from parent
watch(() => props.columns, () => {
  initColumns()
}, { immediate: true, deep: true })

// Computed properties for select all checkbox
const allVisible = computed(() => {
  return internalColumns.value.length > 0 &&
    internalColumns.value.every(col => col.visible !== false)
})

const someVisible = computed(() => {
  const visibleCount = internalColumns.value.filter(col => col.visible !== false).length
  return visibleCount > 0 && visibleCount < internalColumns.value.length
})

// Drag and drop handlers
const handleDragStart = (index: number, event: DragEvent) => {
  draggingIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', index.toString())
  }
}

const handleDragOver = (index: number, event: DragEvent) => {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
  dragOverIndex.value = index
}

const handleDrop = (index: number, event: DragEvent) => {
  event.preventDefault()
  const fromIndex = draggingIndex.value
  if (fromIndex === null || fromIndex === index) return

  // Reorder columns
  const item = internalColumns.value.splice(fromIndex, 1)[0]
  internalColumns.value.splice(index, 0, item)

  emitChanges()
}

const handleDragEnd = () => {
  draggingIndex.value = null
  dragOverIndex.value = null
}

// Column visibility toggle
const handleToggleVisibility = (col: ColumnItem, visible: boolean) => {
  if (isRequired(col) && !visible) {
    ElMessage.warning('This column is required and cannot be hidden')
    return
  }
  col.visible = visible
  emitChanges()
}

// Toggle all columns (skip required columns)
const handleToggleAll = (visible: boolean) => {
  internalColumns.value.forEach(col => {
    if (!isRequired(col)) {
      col.visible = visible
    }
  })
  emitChanges()
}

// Column width change
const handleWidthChange = (col: ColumnItem, width: number) => {
  col.width = width
  emitChanges()
}

// Column fixed position change
const handleFixedChange = (col: ColumnItem, value: string) => {
  const fixedValue = value === '' ? null : value as 'left' | 'right' | null
  col.fixed = fixedValue
  emitChanges()
}

// Reset to default configuration
const handleReset = () => {
  internalColumns.value = props.columns.map(col => ({
    ...col,
    defaultWidth: col.defaultWidth || col.width || 120,
    visible: col.defaultVisible !== false,
    width: col.defaultWidth || col.width || 120,
    fixed: undefined
  }))
  emit('reset')
  emitChanges()
  ElMessage.info('Column configuration reset to default')
}

// Save configuration
const handleSave = () => {
  emit('save', internalColumns.value)
}

// Emit changes to parent
const emitChanges = () => {
  emit('update:modelValue', [...internalColumns.value])
}

// Handle popover show
const handleShow = () => {
  // Refresh columns when popover opens
  initColumns()
}
</script>

<style scoped>
.column-manager {
  padding: 0;
}

.column-manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.column-list {
  max-height: 350px;
  overflow-y: auto;
}

.column-item {
  padding: 8px 12px;
  margin-bottom: 4px;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 4px;
  transition: all 0.2s;
  cursor: move;
}

.column-item:hover {
  background: var(--el-fill-color-light);
  border-color: var(--el-border-color);
}

.column-item-dragging {
  opacity: 0.5;
  background: var(--el-fill-color);
}

.column-item-required {
  background: var(--el-color-warning-light-9);
  border-color: var(--el-color-warning-light-5);
}

.column-item-main {
  display: flex;
  align-items: center;
  gap: 8px;
}

.drag-handle {
  cursor: grab;
  color: var(--el-text-color-placeholder);
  flex-shrink: 0;
}

.drag-handle:active {
  cursor: grabbing;
}

.field-type-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  font-size: 10px;
  font-weight: 500;
  background: var(--el-color-info-light-9);
  color: var(--el-color-info);
  border-radius: 2px;
  flex-shrink: 0;
}

.column-label {
  font-size: 13px;
  user-select: none;
}

.override-icon {
  margin-left: 4px;
  color: var(--el-color-info);
  cursor: help;
  flex-shrink: 0;
}

.column-actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
}

.column-manager-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--el-border-color-lighter);
}

/* Scrollbar styling */
.column-list::-webkit-scrollbar {
  width: 6px;
}

.column-list::-webkit-scrollbar-track {
  background: var(--el-fill-color-lighter);
  border-radius: 3px;
}

.column-list::-webkit-scrollbar-thumb {
  background: var(--el-border-color);
  border-radius: 3px;
}

.column-list::-webkit-scrollbar-thumb:hover {
  background: var(--el-border-color-darker);
}
</style>
