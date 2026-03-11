<template>
  <el-input
    :model-value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :maxlength="field.maxLength"
    :show-word-limit="field.showWordLimit"
    :type="inputType"
    :rows="field.rows || 3"
    clearable
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  field: Object,
  modelValue: String,
  disabled: Boolean,
  placeholder: String
})

defineEmits(['update:modelValue'])

// Determine input type from camelCase field metadata
const inputType = computed(() => {
  const fieldType = props.field.fieldType
  return fieldType === 'textarea' ? 'textarea' : 'text'
})
</script>
