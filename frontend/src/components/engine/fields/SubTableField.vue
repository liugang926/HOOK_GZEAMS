<template>
  <div class="sub-table-field">
    <div class="header">
      <span>{{ field.name }}</span>
      <el-button
        v-if="!readonly && !disabled"
        type="primary"
        size="small"
        link
        @click="handleAddRow"
      >
        {{ $t('fields.addRow') }}
      </el-button>
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
        :index="resolveRowIndex"
      />

      <el-table-column
        v-for="col in columns"
        :key="col.code || col.fieldCode"
        :label="col.name || col.label || col.code || col.fieldCode"
        :min-width="col.width || 120"
      >
        <template #default="{ row }">
          <FieldRenderer
            v-model="row[getColumnCode(col)]"
            :field="buildColumnField(col)"
            :disabled="disabled"
            :readonly="readonly"
          />
        </template>
      </el-table-column>

      <el-table-column
        v-if="!readonly && !disabled"
        :label="$t('fields.operations')"
        width="80"
      >
        <template #default="{ row }">
          <el-button
            type="danger"
            link
            size="small"
            @click="handleRemoveRow(row)"
          >
            {{ $t('fields.delete') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

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
import { computed, ref, watch } from 'vue'
import { normalizeFieldType } from '@/utils/fieldType'

// Avoid circular dependency in recursion if FieldRenderer is used inside SubTable
// But FieldRenderer uses SubTable, so we need Async, or just importing FieldRenderer is fine if build system handles it.
// To be safe, let's use AsyncComponent for the recursive nature or just standard import. A standard import usually works in Vue 3 SFCs.
// However, the user provided code structure implies FieldRenderer is the main dispatcher.
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

const emit = defineEmits(['update:modelValue'])

const internalValue = computed({
  get: () => props.modelValue || [],
  set: (val) => emit('update:modelValue', val)
})

const columns = computed(() => {
  return (
    props.field.related_fields ||
    props.field.relatedFields ||
    props.field.componentProps?.relatedFields ||
    props.field.component_props?.related_fields ||
    []
  )
})

const currentPage = ref(1)

const toPositiveInt = (value: unknown, fallback: number) => {
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed <= 0) return fallback
  return Math.max(1, Math.floor(parsed))
}

const rowsPerPage = computed(() => {
  const componentProps = props.field?.componentProps || props.field?.component_props || {}
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

const handlePageChange = (page: number) => {
  currentPage.value = page
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

const handleAddRow = () => {
  const newRow: SubTableFieldModel = {}
  columns.value.forEach((col: ColumnDefinition) => {
    const key = getColumnCode(col)
    const defaultValue = col.defaultValue !== undefined ? col.defaultValue : col.default_value
    if (key) {
      newRow[key] = defaultValue !== undefined ? defaultValue : null
    }
  })
  const newList = [...internalValue.value, newRow]
  emit('update:modelValue', newList)
  currentPage.value = Math.max(1, Math.ceil(newList.length / rowsPerPage.value))
}

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
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 10px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-weight: bold;
}
.pagination {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}
</style>
