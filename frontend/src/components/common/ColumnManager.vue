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
          :key="col.prop"
          class="column-item"
          :class="{ 'column-item-dragging': draggingIndex === index }"
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

            <el-checkbox
              :model-value="col.visible !== false"
              @update:model-value="(val: boolean) => handleToggleVisibility(col, val)"
            >
              <span class="column-label">{{ col.label }}</span>
            </el-checkbox>

            <div class="column-actions">
              <el-input-number
                :model-value="col.width || col.defaultWidth || 120"
                :min="50"
                :max="500"
                :step="10"
                size="small"
                controls-position="right"
                style="width: 90px"
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
import { Setting, DCaret } from '@element-plus/icons-vue'
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
  col.visible = visible
  emitChanges()
}

// Toggle all columns
const handleToggleAll = (visible: boolean) => {
  internalColumns.value.forEach(col => {
    col.visible = visible
  })
  emitChanges()
}

// Column width change
const handleWidthChange = (col: ColumnItem, width: number) => {
  col.width = width
  emitChanges()
}

// Reset to default configuration
const handleReset = () => {
  internalColumns.value = props.columns.map(col => ({
    ...col,
    defaultWidth: col.defaultWidth || col.width || 120,
    visible: col.defaultVisible !== false,
    width: col.defaultWidth || col.width || 120
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

.column-label {
  font-size: 13px;
  user-select: none;
}

.column-actions {
  margin-left: auto;
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
