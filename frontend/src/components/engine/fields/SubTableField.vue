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
        添加行
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
        :key="col.code" 
        :label="col.name"
        :min-width="col.width || 120"
      >
        <template #default="{ row, $index }">
          <FieldRenderer
            v-model="row[col.code]"
            :field="col"
            :disabled="disabled"
            :readonly="readonly"
          />
        </template>
      </el-table-column>

      <el-table-column
        v-if="!readonly && !disabled"
        label="操作"
        width="80"
      >
        <template #default="{ $index }">
          <el-button
            type="danger"
            link
            size="small"
            @click="handleRemoveRow($index)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue'

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
  return props.field.related_fields || []
})

const handleAddRow = () => {
  const newRow: any = {}
  columns.value.forEach((col: any) => {
    newRow[col.code] = col.default_value !== undefined ? col.default_value : null
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
