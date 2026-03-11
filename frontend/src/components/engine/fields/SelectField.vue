<template>
  <el-select
    :model-value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :multiple="isMultiSelect"
    :collapse-tags="isMultiSelect"
    :max-collapse-tags="3"
    clearable
    filterable
    style="width: 100%"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <el-option
      v-for="item in options"
      :key="item.value"
      :label="item.label"
      :value="item.value"
    />
  </el-select>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  field: Object,
  modelValue: [String, Number, Array],
  disabled: Boolean,
  placeholder: String
})

defineEmits(['update:modelValue'])

// Determine multi-select from camelCase field metadata
const isMultiSelect = computed(() => {
  const fieldType = props.field.fieldType
  return fieldType === 'multi_select' || fieldType === 'multiSelect' || props.field.multiple
})

const options = computed(() => {
  return props.field.options || []
})
</script>
