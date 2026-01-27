<template>
  <div class="base-table">
    <el-table
      ref="tableRef"
      v-loading="loading"
      :data="data"
      :row-key="rowKey"
      :border="border"
      :stripe="stripe"
      :size="size"
      :fit="fit"
      :show-header="showHeader"
      :highlight-current-row="highlightCurrentRow"
      :empty-text="emptyText"
      :default-sort="defaultSort"
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
      @row-click="handleRowClick"
      @row-dblclick="handleRowDblClick"
    >
      <!-- Selection column -->
      <el-table-column
        v-if="showSelection"
        type="selection"
        :width="selectionWidth"
        :fixed="selectionFixed"
        :selectable="selectable"
      />

      <!-- Index column -->
      <el-table-column
        v-if="showIndex"
        type="index"
        label="#"
        :width="indexWidth"
        :fixed="indexFixed"
        :index="indexMethod"
      />

      <!-- Expand column -->
      <el-table-column
        v-if="showExpand"
        type="expand"
        :width="expandWidth"
        :fixed="expandFixed"
      >
        <template #default="{ row, $index }">
          <slot
            name="expand"
            :row="row"
            :index="$index"
          />
        </template>
      </el-table-column>

      <!-- Data columns -->
      <template
        v-for="column in visibleColumns"
        :key="column.prop"
      >
        <el-table-column
          :prop="column.prop"
          :label="column.label"
          :width="column.width"
          :min-width="column.minWidth"
          :fixed="column.fixed"
          :sortable="column.sortable"
          :align="column.align || 'left'"
          :class-name="column.className"
          :show-overflow-tooltip="column.showOverflowTooltip !== false"
        >
          <template #header="{ column }">
            <slot
              :name="`header-${column.prop}`"
              :column="column"
            >
              {{ column.label }}
            </slot>
          </template>

          <template #default="{ row, column: col, $index }">
            <slot
              :name="`column-${column.prop}`"
              :row="row"
              :column="col"
              :index="$index"
            >
              <span>{{ getCellValue(row, column.prop) }}</span>
            </slot>
          </template>
        </el-table-column>
      </template>

      <!-- Actions column -->
      <el-table-column
        v-if="$slots.actions || showActions"
        label="Actions"
        :width="actionsWidth"
        :fixed="actionsFixed"
        align="center"
      >
        <template #default="{ row, $index }">
          <slot
            name="actions"
            :row="row"
            :index="$index"
          >
            <el-button
              link
              type="primary"
              size="small"
              @click="handleAction('edit', row, $index)"
            >
              Edit
            </el-button>
            <el-popconfirm
              title="Are you sure to delete this item?"
              @confirm="handleAction('delete', row, $index)"
            >
              <template #reference>
                <el-button
                  link
                  type="danger"
                  size="small"
                >
                  Delete
                </el-button>
              </template>
            </el-popconfirm>
          </slot>
        </template>
      </el-table-column>
    </el-table>

    <!-- Column settings trigger -->
    <div
      v-if="showColumnSettings"
      class="column-settings-trigger"
    >
      <ColumnManager
        v-model="internalColumns"
        :object-code="objectCode"
        :columns="columns"
        @save="handleColumnSave"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { ElTable } from 'element-plus'
import ColumnManager from './ColumnManager.vue'
import type { ColumnItem } from '@/hooks/useColumnConfig'

/**
 * Column definition
 */
export interface TableColumn {
  prop: string
  label: string
  width?: number
  minWidth?: number
  fixed?: 'left' | 'right' | false
  sortable?: boolean | 'custom'
  align?: 'left' | 'center' | 'right'
  className?: string
  showOverflowTooltip?: boolean
  visible?: boolean
}

interface Props {
  data: any[]
  columns?: TableColumn[]
  loading?: boolean
  rowKey?: string | ((row: any) => string)
  border?: boolean
  stripe?: boolean
  size?: 'large' | 'default' | 'small'
  fit?: boolean
  showHeader?: boolean
  highlightCurrentRow?: boolean
  emptyText?: string
  defaultSort?: { prop: string; order: string }
  showSelection?: boolean
  selectionWidth?: number
  selectionFixed?: boolean | 'left' | 'right'
  selectable?: (row: any, index: number) => boolean
  showIndex?: boolean
  indexWidth?: number
  indexFixed?: boolean | 'left' | 'right'
  indexMethod?: (index: number) => number
  showExpand?: boolean
  expandWidth?: number
  expandFixed?: boolean | 'left' | 'right'
  showActions?: boolean
  actionsWidth?: number
  actionsFixed?: boolean | 'left' | 'right'
  showColumnSettings?: boolean
  objectCode?: string
}

interface Emits {
  (e: 'selection-change', selection: any[]): void
  (e: 'sort-change', sort: { prop: string; order: string }): void
  (e: 'row-click', row: any, column: any, event: Event): void
  (e: 'row-dblclick', row: any, column: any, event: Event): void
  (e: 'action', action: string, row: any, index: number): void
  (e: 'column-save', columns: ColumnItem[]): void
}

const props = withDefaults(defineProps<Props>(), {
  data: () => [],
  columns: () => [],
  loading: false,
  rowKey: 'id',
  border: true,
  stripe: true,
  size: 'default',
  fit: true,
  showHeader: true,
  highlightCurrentRow: false,
  emptyText: 'No Data',
  showSelection: false,
  selectionWidth: 55,
  selectionFixed: false,
  showIndex: false,
  indexWidth: 60,
  indexFixed: false,
  showExpand: false,
  expandWidth: 60,
  expandFixed: false,
  showActions: false,
  actionsWidth: 180,
  actionsFixed: 'right',
  showColumnSettings: false
})

const emit = defineEmits<Emits>()

const tableRef = ref<InstanceType<typeof ElTable>>()

// Internal columns state
const internalColumns = ref<ColumnItem[]>([])

// Initialize internal columns from props
watch(
  () => props.columns,
  (newColumns) => {
    internalColumns.value = newColumns.map(col => ({
      prop: col.prop,
      label: col.label,
      width: col.width || col.minWidth || 120,
      minWidth: col.minWidth,
      fixed: col.fixed,
      visible: col.visible !== false,
      sortable: col.sortable,
      defaultWidth: col.width || col.minWidth || 120
    }))
  },
  { immediate: true, deep: true }
)

// Computed visible columns
const visibleColumns = computed(() => {
  return internalColumns.value.filter(col => col.visible !== false)
})

// Get cell value
const getCellValue = (row: any, prop: string) => {
  return prop.split('.').reduce((obj, key) => obj?.[key], row)
}

// Handle selection change
const handleSelectionChange = (selection: any[]) => {
  emit('selection-change', selection)
}

// Handle sort change
const handleSortChange = (sort: { prop: string; order: string }) => {
  emit('sort-change', sort)
}

// Handle row click
const handleRowClick = (row: any, column: any, event: Event) => {
  emit('row-click', row, column, event)
}

// Handle row double click
const handleRowDblClick = (row: any, column: any, event: Event) => {
  emit('row-dblclick', row, column, event)
}

// Handle action button click
const handleAction = (action: string, row: any, index: number) => {
  emit('action', action, row, index)
}

// Handle column save
const handleColumnSave = (columns: ColumnItem[]) => {
  emit('column-save', columns)
}

// Expose table methods
const clearSelection = () => {
  tableRef.value?.clearSelection()
}

const toggleRowSelection = (row: any, selected?: boolean) => {
  tableRef.value?.toggleRowSelection(row, selected)
}

const toggleAllSelection = () => {
  tableRef.value?.toggleAllSelection()
}

const toggleRowExpansion = (row: any, expanded?: boolean) => {
  tableRef.value?.toggleRowExpansion(row, expanded)
}

const setCurrentRow = (row: any) => {
  tableRef.value?.setCurrentRow(row)
}

defineExpose({
  tableRef,
  clearSelection,
  toggleRowSelection,
  toggleAllSelection,
  toggleRowExpansion,
  setCurrentRow
})
</script>

<style scoped>
.base-table {
  position: relative;
}

.column-settings-trigger {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 10;
}

:deep(.el-table) {
  width: 100%;
}

:deep(.el-table__empty-block) {
  min-height: 200px;
}
</style>
