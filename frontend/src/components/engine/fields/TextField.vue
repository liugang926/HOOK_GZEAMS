<template>
  <el-input
    :model-value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :maxlength="field.maxLength || field.max_length"
    :show-word-limit="field.showWordLimit || field.show_word_limit"
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

// Support both camelCase (fieldType) and snake_case (field_type)
const inputType = computed(() => {
  const fieldType = props.field.fieldType || props.field.field_type
  return fieldType === 'textarea' ? 'textarea' : 'text'
})
</script>
