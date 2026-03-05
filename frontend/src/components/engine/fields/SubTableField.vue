<template>
  <div
    ref="subTableRoot"
    class="sub-table-field"
    :class="{ 'is-datagrid': isDataGrid }"
    @focusin="handleFocusIn"
    @focusout="handleFocusOut"
    @keydown="handleRootKeydown"
  >
    <div
      v-if="field.name || showShortcutHelp"
      class="header"
    >
      <span
        v-if="field.name"
        class="field-label"
      >
        {{ field.name }}
      </span>
      <span
        v-else
        class="field-label field-label--placeholder"
      />

      <el-popover
        v-if="showShortcutHelp"
        v-model:visible="shortcutPopoverVisible"
        placement="bottom-end"
        trigger="manual"
        width="420"
      >
        <template #reference>
          <el-button
            class="shortcut-help-btn"
            :class="{ 'is-pinned': shortcutPopoverPinned }"
            type="info"
            link
            circle
            :aria-label="$t('common.hotkeys.title')"
            :aria-expanded="shortcutPopoverVisible"
            :aria-pressed="shortcutPopoverPinned"
            @click.stop="toggleShortcutPopover"
          >
            <el-icon><QuestionFilled /></el-icon>
          </el-button>
        </template>

        <div class="shortcut-popover">
          <div class="shortcut-title">
            {{ $t('common.hotkeys.title') }}
            <span
              v-if="shortcutPopoverPinned"
              class="shortcut-pinned-badge"
            >
              {{ $t('common.hotkeys.subtable.pinned') }}
            </span>
          </div>
          <ul class="shortcut-list">
            <li
              v-for="item in shortcutItems"
              :key="`${item.combo}-${item.descriptionKey}`"
              class="shortcut-item"
            >
              <kbd class="shortcut-combo">{{ item.combo }}</kbd>
              <span class="shortcut-desc">{{ $t(item.descriptionKey) }}</span>
            </li>
          </ul>
        </div>
      </el-popover>
    </div>

    <el-table
      :data="pagedRows"
      border
      size="small"
    >
      <el-table-column
        type="index"
        width="50"
        label="#"
        align="center"
      >
        <template #default="{ row }">
          <div class="row-index-cell">
            <span class="index-number">{{ resolveRowIndex(pagedRows.indexOf(row)) }}</span>
            <el-button
              v-if="!readonly && !disabled"
              class="hover-delete-btn"
              type="danger"
              icon="Delete"
              circle
              size="small"
              @click="handleRemoveRow(row)"
            />
          </div>
        </template>
      </el-table-column>

      <el-table-column
        v-for="(col, colIndex) in columns"
        :key="col.code || col.fieldCode"
        :label="col.name || col.label || col.code || col.fieldCode"
        :min-width="col.width || 120"
      >
        <template #default="{ row, $index }">
          <div
            class="datagrid-cell"
            :data-row-index="$index"
            :data-col-index="colIndex"
            @keydown="handleCellKeydown($event, $index, colIndex)"
          >
            <FieldRenderer
              v-model="row[getColumnCode(col)]"
              :field="buildColumnField(col)"
              :disabled="disabled"
              :readonly="readonly"
            />
          </div>
        </template>
      </el-table-column>
    </el-table>

    <!-- Ghost Add Row Button -->
    <div
      v-if="!readonly && !disabled"
      class="ghost-add-row"
      @click="handleAddRow"
    >
      <el-icon><Plus /></el-icon>
      <span>{{ $t('form.actions.addRow') }}</span>
    </div>

    <div
      v-if="shouldPaginate"
      class="pagination"
    >
      <el-pagination
        size="small"
        :current-page="currentPage"
        :page-size="rowsPerPage"
        :total="totalRows"
        layout="total, prev, pager, next"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { Plus, QuestionFilled } from '@element-plus/icons-vue'
import { normalizeFieldType } from '@/utils/fieldType'
import { useHotkey, useHotkeyContext } from '@/composables/useHotkeys'
import { useShortcutPopover } from '@/composables/useShortcutPopover'
import { buildSubTableShortcutItems } from './subtableShortcutConfig'

// Avoid circular dependency in recursion if FieldRenderer is used inside SubTable
import FieldRenderer from '@/components/engine/FieldRenderer.vue'

interface ColumnDefinition {
  code?: string
  fieldCode?: string
  name?: string
  label?: string
  width?: number
  fieldType?: string
  field_type?: string
  type?: string
  defaultValue?: unknown
  default_value?: unknown
  componentProps?: Record<string, unknown>
  component_props?: Record<string, unknown>
}

interface SubTableFieldModel {
  [key: string]: unknown
}

interface SubTableFieldDefinition {
  name?: string
  related_fields?: ColumnDefinition[]
  relatedFields?: ColumnDefinition[]
  componentProps?: Record<string, unknown>
  component_props?: Record<string, unknown>
}

const props = defineProps<{
  modelValue: SubTableFieldModel[]
  field: SubTableFieldDefinition
  disabled?: boolean
  readonly?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: SubTableFieldModel[]): void
  (e: 'request-save'): void
}>()
const subTableRoot = ref<HTMLElement | null>(null)
const hasGridFocus = ref(false)

const internalValue = computed({
  get: () => props.modelValue || [],
  set: (val) => emit('update:modelValue', val)
})
const isDataGrid = computed(() => !props.readonly && !props.disabled)
const subTableComponentProps = computed<Record<string, unknown>>(() => {
  return (props.field.componentProps || props.field.component_props || {}) as Record<string, unknown>
})
const hotkeyContextId = useHotkeyContext({
  enabled: () => isDataGrid.value && hasGridFocus.value
})
const toBoolean = (value: unknown, fallback: boolean): boolean => {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value !== 0
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    if (['true', '1', 'yes', 'on'].includes(normalized)) return true
    if (['false', '0', 'no', 'off'].includes(normalized)) return false
  }
  return fallback
}

const isMacPlatform = computed(() => {
  if (typeof navigator === 'undefined') return false
  const platform = String(navigator.platform || '').toLowerCase()
  const userAgent = String(navigator.userAgent || '').toLowerCase()
  return platform.includes('mac') || userAgent.includes('mac')
})

const macCommandSymbol = '\u2318'
const commandCombo = (key: string) => (isMacPlatform.value ? `${macCommandSymbol} + ${key}` : `Ctrl + ${key}`)
const shiftCommandCombo = (key: string) => (isMacPlatform.value ? `Shift + ${macCommandSymbol} + ${key}` : `Shift + Ctrl + ${key}`)

const columns = computed<ColumnDefinition[]>(() => {
  if (Array.isArray(props.field.related_fields)) return props.field.related_fields
  if (Array.isArray(props.field.relatedFields)) return props.field.relatedFields

  const componentProps = subTableComponentProps.value
  const fromCamel = componentProps.relatedFields
  if (Array.isArray(fromCamel)) return fromCamel as ColumnDefinition[]

  const fromSnake = componentProps.related_fields
  if (Array.isArray(fromSnake)) return fromSnake as ColumnDefinition[]

  return [] as ColumnDefinition[]
})

const shortcutHelpEnabled = computed(() => {
  const configured = subTableComponentProps.value.showShortcutHelp ??
    subTableComponentProps.value.show_shortcut_help ??
    subTableComponentProps.value.enableShortcutHelp ??
    subTableComponentProps.value.enable_shortcut_help
  return toBoolean(configured, true)
})
const shortcutHelpDefaultPinned = computed(() => {
  const configured = subTableComponentProps.value.defaultShortcutHelpPinned ??
    subTableComponentProps.value.default_shortcut_help_pinned ??
    subTableComponentProps.value.shortcutHelpDefaultPinned ??
    subTableComponentProps.value.shortcut_help_default_pinned
  return toBoolean(configured, false)
})

const showShortcutHelp = computed(() => {
  return isDataGrid.value && shortcutHelpEnabled.value && columns.value.length > 0
})
const {
  visible: shortcutPopoverVisible,
  pinned: shortcutPopoverPinned,
  toggle: toggleShortcutPopover,
  togglePinned: toggleShortcutPopoverPinned,
  handleEscape: handleShortcutPopoverEscape
} = useShortcutPopover({
  enabled: () => showShortcutHelp.value,
  defaultPinned: () => showShortcutHelp.value && shortcutHelpDefaultPinned.value
})

const shortcutItems = computed(() => buildSubTableShortcutItems({
  commandCombo,
  shiftCommandCombo
}))

const currentPage = ref(1)

const toPositiveInt = (value: unknown, fallback: number) => {
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback
  return Math.max(1, Math.floor(parsed))
}

const rowsPerPage = computed(() => {
  const componentProps = subTableComponentProps.value
  return toPositiveInt(
    componentProps?.paginationPageSize ??
    componentProps?.pagination_page_size ??
    componentProps?.pageSize ??
    componentProps?.page_size,
    20
  )
})

const totalRows = computed(() => internalValue.value.length)
const shouldPaginate = computed(() => totalRows.value > rowsPerPage.value)

const pagedRows = computed(() => {
  if (!shouldPaginate.value) return internalValue.value
  const start = (currentPage.value - 1) * rowsPerPage.value
  const end = start + rowsPerPage.value
  return internalValue.value.slice(start, end)
})

const resolveRowIndex = (index: number) => {
  if (!shouldPaginate.value) return index + 1
  return (currentPage.value - 1) * rowsPerPage.value + index + 1
}

const resolveGlobalRowIndex = (localRowIndex: number) => {
  if (!shouldPaginate.value) return localRowIndex
  return (currentPage.value - 1) * rowsPerPage.value + localRowIndex
}

const resolveLocalRowIndex = (globalRowIndex: number) => {
  if (!shouldPaginate.value) return globalRowIndex
  return globalRowIndex - (currentPage.value - 1) * rowsPerPage.value
}

const handlePageChange = (page: number) => {
  currentPage.value = page
}

const handleFocusIn = () => {
  hasGridFocus.value = true
}

const handleFocusOut = () => {
  nextTick(() => {
    if (!subTableRoot.value) {
      hasGridFocus.value = false
      return
    }

    const active = document.activeElement
    hasGridFocus.value = !!active && subTableRoot.value.contains(active)
  })
}

const handleRootKeydown = (event: KeyboardEvent) => {
  if (event.defaultPrevented) return
  if (event.key !== 'Escape') return
  if (!handleShortcutPopoverEscape()) return

  event.preventDefault()
  event.stopPropagation()
}

const getColumnCode = (col: ColumnDefinition): string => col.code || col.fieldCode || ''

const buildColumnField = (col: ColumnDefinition) => {
  const componentProps = {
    ...(col.component_props || {}),
    ...(col.componentProps || {})
  }

  return {
    ...col,
    code: getColumnCode(col),
    name: col.name || col.label || getColumnCode(col),
    label: col.label || col.name || getColumnCode(col),
    fieldType: normalizeFieldType(col.fieldType || col.field_type || col.type || 'text'),
    field_type: normalizeFieldType(col.fieldType || col.field_type || col.type || 'text'),
    componentProps,
    component_props: componentProps
  }
}

const buildEmptyRow = (): SubTableFieldModel => {
  const newRow: SubTableFieldModel = {}
  columns.value.forEach((col: ColumnDefinition) => {
    const key = getColumnCode(col)
    const defaultValue = col.defaultValue !== undefined ? col.defaultValue : col.default_value
    if (key) {
      newRow[key] = defaultValue !== undefined ? defaultValue : null
    }
  })
  return newRow
}

const insertRowAt = (globalIndex: number): number => {
  const list = [...internalValue.value]
  const safeIndex = Math.max(0, Math.min(globalIndex, list.length))
  list.splice(safeIndex, 0, buildEmptyRow())
  emit('update:modelValue', list)
  currentPage.value = Math.max(1, Math.ceil((safeIndex + 1) / rowsPerPage.value))
  return safeIndex
}

const cloneRowData = (row: SubTableFieldModel): SubTableFieldModel => {
  if (typeof structuredClone === 'function') {
    try {
      return structuredClone(row)
    } catch {
      // Reactive proxy objects from table rows are not always cloneable in test/runtime environments.
    }
  }
  return JSON.parse(JSON.stringify(row))
}

const duplicateRowAt = (globalIndex: number, position: 'above' | 'below' = 'below'): number => {
  const list = [...internalValue.value]
  if (globalIndex < 0 || globalIndex >= list.length) return -1

  const clone = cloneRowData(list[globalIndex])
  const insertIndex = position === 'above' ? globalIndex : globalIndex + 1
  list.splice(insertIndex, 0, clone)
  emit('update:modelValue', list)
  currentPage.value = Math.max(1, Math.ceil((insertIndex + 1) / rowsPerPage.value))
  return insertIndex
}

const handleAddRow = () => {
  const newRow = buildEmptyRow()
  const newList = [...internalValue.value, newRow]
  emit('update:modelValue', newList)
  currentPage.value = Math.max(1, Math.ceil(newList.length / rowsPerPage.value))
}

const focusCell = async (globalRowIndex: number, colIndex: number): Promise<boolean> => {
  if (!subTableRoot.value) return false
  if (globalRowIndex < 0 || colIndex < 0) return false
  if (globalRowIndex >= totalRows.value) return false
  if (colIndex >= columns.value.length) return false

  const targetPage = shouldPaginate.value
    ? Math.floor(globalRowIndex / rowsPerPage.value) + 1
    : currentPage.value

  if (shouldPaginate.value && targetPage !== currentPage.value) {
    currentPage.value = targetPage
    await nextTick()
  }

  const localRowIndex = resolveLocalRowIndex(globalRowIndex)
  const selector = `.datagrid-cell[data-row-index="${localRowIndex}"][data-col-index="${colIndex}"]`
  const cellEl = subTableRoot.value.querySelector<HTMLElement>(selector)
  if (!cellEl) return false

  const focusTarget = cellEl.querySelector<HTMLElement>(
    'input:not([disabled]), textarea:not([disabled]), select:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex="-1"])'
  )
  if (!focusTarget) return false

  focusTarget.focus()
  return true
}

const shouldKeepNativeInputNavigation = (target: EventTarget | null, key: string): boolean => {
  const el = target as HTMLElement | null
  if (!el) return false

  if (el instanceof HTMLTextAreaElement || el.isContentEditable) {
    return true
  }

  if (!(el instanceof HTMLInputElement)) {
    return false
  }

  const inputType = (el.type || '').toLowerCase()
  const isNativeStructuredInput =
    inputType === 'number' ||
    inputType === 'date' ||
    inputType === 'time' ||
    inputType === 'datetime-local' ||
    inputType === 'month' ||
    inputType === 'week'

  if (isNativeStructuredInput && (key === 'ArrowUp' || key === 'ArrowDown')) {
    return true
  }

  if (key !== 'Home' && key !== 'End') return false

  const supportsSelection = typeof el.selectionStart === 'number' && typeof el.selectionEnd === 'number'
  if (!supportsSelection) return false

  const start = el.selectionStart as number
  const end = el.selectionEnd as number
  if (start !== end) return true
  if (key === 'Home') return start > 0
  if (key === 'End') return end < el.value.length
  return false
}

const handleCellKeydown = async (event: KeyboardEvent, localRowIndex: number, colIndex: number) => {
  if (!isDataGrid.value) return
  if (event.isComposing) return

  const withCommandKey = event.ctrlKey || event.metaKey
  const isTab = event.key === 'Tab'
  const isEnter = event.key === 'Enter'
  const isEscape = event.key === 'Escape'
  const isHome = event.key === 'Home'
  const isEnd = event.key === 'End'
  const isArrowUp = event.key === 'ArrowUp'
  const isArrowDown = event.key === 'ArrowDown'
  const isPageUp = event.key === 'PageUp'
  const isPageDown = event.key === 'PageDown'
  const isDuplicate = String(event.key || '').toLowerCase() === 'd'
  const isBackspace = event.key === 'Backspace'
  if (!isTab && !isEnter && !isEscape && !isHome && !isEnd && !isArrowUp && !isArrowDown && !isPageUp && !isPageDown && !isBackspace && !isDuplicate) return

  if (isEscape) {
    if (handleShortcutPopoverEscape()) {
      event.preventDefault()
      return
    }
    const target = event.target as HTMLElement | null
    target?.blur()
    return
  }

  const target = event.target as HTMLElement | null
  const isTextarea = target?.tagName === 'TEXTAREA'
  const isQuickAddRow = isEnter && withCommandKey && !event.altKey
  const isQuickDeleteRow = isBackspace && withCommandKey && !event.shiftKey && !event.altKey
  const isQuickDuplicateRow = isDuplicate && withCommandKey && !event.shiftKey && !event.altKey
  const isQuickDuplicateRowAbove = isDuplicate && withCommandKey && event.shiftKey && !event.altKey
  if (isEnter && isTextarea && !isQuickAddRow) return
  if ((isHome || isEnd || isArrowUp || isArrowDown) && shouldKeepNativeInputNavigation(target, event.key)) return

  const totalColumns = columns.value.length
  if (totalColumns === 0) return

  if (isQuickAddRow) {
    event.preventDefault()
    const insertAboveCurrent = event.shiftKey
    const nextGlobalRowIndex = insertAboveCurrent
      ? resolveGlobalRowIndex(localRowIndex)
      : totalRows.value
    insertRowAt(nextGlobalRowIndex)
    await nextTick()
    await focusCell(nextGlobalRowIndex, 0)
    return
  }

  if (isQuickDeleteRow) {
    event.preventDefault()
    const currentGlobalRowIndex = resolveGlobalRowIndex(localRowIndex)
    const list = [...internalValue.value]
    if (currentGlobalRowIndex < 0 || currentGlobalRowIndex >= list.length) return

    list.splice(currentGlobalRowIndex, 1)
    emit('update:modelValue', list)
    if (list.length === 0) return

    const nextGlobalRowIndex = Math.min(currentGlobalRowIndex, list.length - 1)
    currentPage.value = Math.max(1, Math.ceil((nextGlobalRowIndex + 1) / rowsPerPage.value))
    await nextTick()
    await focusCell(nextGlobalRowIndex, Math.min(colIndex, totalColumns - 1))
    return
  }

  if (isQuickDuplicateRow || isQuickDuplicateRowAbove) {
    event.preventDefault()
    const currentGlobalRowIndex = resolveGlobalRowIndex(localRowIndex)
    const duplicatedRowIndex = duplicateRowAt(currentGlobalRowIndex, isQuickDuplicateRowAbove ? 'above' : 'below')
    if (duplicatedRowIndex < 0) return
    await nextTick()
    await focusCell(duplicatedRowIndex, Math.min(colIndex, totalColumns - 1))
    return
  }

  event.preventDefault()

  const backward = isTab && event.shiftKey
  let nextGlobalRowIndex = resolveGlobalRowIndex(localRowIndex)
  let nextColIndex = colIndex + (backward ? -1 : 1)

  if (isHome) {
    nextColIndex = 0
  } else if (isEnd) {
    nextColIndex = totalColumns - 1
  } else if (isArrowUp) {
    nextColIndex = colIndex
    nextGlobalRowIndex -= 1
  } else if (isArrowDown) {
    nextColIndex = colIndex
    nextGlobalRowIndex += 1
  } else if (isPageUp) {
    nextColIndex = colIndex
    const step = shouldPaginate.value ? rowsPerPage.value : 1
    nextGlobalRowIndex -= step
  } else if (isPageDown) {
    nextColIndex = colIndex
    const step = shouldPaginate.value ? rowsPerPage.value : 1
    nextGlobalRowIndex += step
  }

  if (nextColIndex >= totalColumns) {
    nextColIndex = 0
    nextGlobalRowIndex += 1
  } else if (nextColIndex < 0) {
    nextColIndex = totalColumns - 1
    nextGlobalRowIndex -= 1
  }

  if (nextGlobalRowIndex < 0) return

  if (nextGlobalRowIndex >= totalRows.value) {
    if (isPageDown) return
    if (isArrowDown) return
    if (backward) return
    handleAddRow()
    await nextTick()
    if (nextGlobalRowIndex >= totalRows.value) return
  }

  await nextTick()
  await focusCell(nextGlobalRowIndex, nextColIndex)
}

useHotkey('ctrl+s', () => {
  if (!isDataGrid.value || !hasGridFocus.value) return
  emit('request-save')
  return false
}, {
  context: hotkeyContextId,
  preventDefault: true,
  stopPropagation: true,
  allowInInputs: true,
  enabled: () => isDataGrid.value && hasGridFocus.value
})

useHotkey('f1', () => {
  if (!showShortcutHelp.value || !hasGridFocus.value) return
  toggleShortcutPopover()
  return false
}, {
  context: hotkeyContextId,
  preventDefault: true,
  stopPropagation: true,
  allowInInputs: true,
  enabled: () => isDataGrid.value && hasGridFocus.value && showShortcutHelp.value
})

useHotkey('shift+f1', () => {
  if (!showShortcutHelp.value || !hasGridFocus.value) return
  toggleShortcutPopoverPinned()
  return false
}, {
  context: hotkeyContextId,
  preventDefault: true,
  stopPropagation: true,
  allowInInputs: true,
  enabled: () => isDataGrid.value && hasGridFocus.value && showShortcutHelp.value
})

const handleRemoveRow = (row: Record<string, unknown>) => {
  const index = internalValue.value.indexOf(row)
  if (index < 0) return
  const newList = [...internalValue.value]
  newList.splice(index, 1)
  emit('update:modelValue', newList)
}

watch([totalRows, rowsPerPage], () => {
  const pageCount = Math.max(1, Math.ceil(totalRows.value / rowsPerPage.value))
  if (currentPage.value > pageCount) currentPage.value = pageCount
  if (currentPage.value < 1) currentPage.value = 1
}, { immediate: true })
</script>

<style scoped>
.sub-table-field {
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 20px;
}

.sub-table-field.is-datagrid {
  border: 1px solid var(--el-border-color-lighter);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.field-label {
  font-weight: 600;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.field-label--placeholder {
  min-height: 20px;
}

.shortcut-help-btn {
  color: var(--el-text-color-secondary);
}

.shortcut-help-btn.is-pinned {
  color: var(--el-color-primary);
}

.shortcut-popover {
  max-height: min(360px, 60vh);
  overflow: auto;
}

.shortcut-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.shortcut-pinned-badge {
  margin-left: 8px;
  font-size: 11px;
  color: var(--el-color-primary);
}

.shortcut-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  row-gap: 8px;
}

.shortcut-item {
  display: grid;
  grid-template-columns: 170px 1fr;
  column-gap: 8px;
  align-items: center;
}

.shortcut-combo {
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid var(--el-border-color);
  background: var(--el-fill-color-light);
  font-size: 12px;
  line-height: 1.4;
  white-space: nowrap;
}

.shortcut-desc {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.pagination {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

/* DataGrid Styling */
.is-datagrid :deep(.el-table) {
  --el-table-border-color: var(--el-border-color-lighter);
  --el-table-header-bg-color: #f8fafc;
}

.is-datagrid :deep(.el-table .cell) {
  padding: 0; /* Remove cell padding for tight input */
}

.is-datagrid :deep(.el-table th.el-table__cell) {
  padding: 8px 12px;
}

.is-datagrid :deep(.el-form-item) {
  margin-bottom: 0;
}

/* Make inputs flush inside cells */
.is-datagrid :deep(.el-table td.el-table__cell .el-input__wrapper),
.is-datagrid :deep(.el-table td.el-table__cell .el-textarea__inner),
.is-datagrid :deep(.el-table td.el-table__cell .el-select__wrapper) {
  box-shadow: none !important;
  border-radius: 0;
  background-color: transparent;
  padding: 0 8px;
}

.is-datagrid :deep(.el-table td.el-table__cell:focus-within) {
  background-color: #f4f6f8;
  outline: 1px solid var(--el-color-primary);
  outline-offset: -1px;
}

.row-index-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: 4px 0;
}

.hover-delete-btn {
  display: none;
}

/* Show delete button on row hover */
.is-datagrid :deep(.el-table__row:hover) .index-number {
  display: none;
}
.is-datagrid :deep(.el-table__row:hover) .hover-delete-btn {
  display: inline-flex;
}

.ghost-add-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 0;
  color: var(--el-text-color-secondary);
  background-color: #fafbfc;
  border-top: 1px dashed var(--el-border-color-lighter);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
}

.ghost-add-row:hover {
  background-color: #f0f4ff;
  color: var(--el-color-primary);
}
</style>

