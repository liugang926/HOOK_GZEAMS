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
      :data="internalValue"
      border
      size="small"
    >
      <el-table-column
        type="index"
        width="50"
        label="#"
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
        <template #default="{ $index }">
          <el-button
            type="danger"
            link
            size="small"
            @click="handleRemoveRow($index)"
          >
            {{ $t('fields.delete') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { normalizeFieldType } from '@/utils/fieldType'

// Avoid circular dependency in recursion if FieldRenderer is used inside SubTable
// But FieldRenderer uses SubTable, so we need Async, or just importing FieldRenderer is fine if build system handles it.
// To be safe, let's use AsyncComponent for the recursive nature or just standard import. A standard import usually works in Vue 3 SFCs.
// However, the user provided code structure implies FieldRenderer is the main dispatcher.
import FieldRenderer from '@/components/engine/FieldRenderer.vue'

const props = defineProps<{
  modelValue: any[]
  field: any
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

const getColumnCode = (col: any): string => col.code || col.fieldCode || ''

const buildColumnField = (col: any) => {
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
  const newRow: any = {}
  columns.value.forEach((col: any) => {
    const key = getColumnCode(col)
    const defaultValue = col.defaultValue !== undefined ? col.defaultValue : col.default_value
    if (key) {
      newRow[key] = defaultValue !== undefined ? defaultValue : null
    }
  })
  const newList = [...internalValue.value, newRow]
  emit('update:modelValue', newList)
}

const handleRemoveRow = (index: number) => {
  const newList = [...internalValue.value]
  newList.splice(index, 1)
  emit('update:modelValue', newList)
}
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
</style>
