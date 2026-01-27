<template>
  <el-input
    :model-value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :maxlength="field.max_length"
    :show-word-limit="field.show_word_limit"
    :type="field.field_type === 'textarea' ? 'textarea' : 'text'"
    :rows="field.rows || 3"
    clearable
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
defineProps({
  field: Object,
  modelValue: String,
  disabled: Boolean,
  placeholder: String
})

defineEmits(['update:modelValue'])
</script>
