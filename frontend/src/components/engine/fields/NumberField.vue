<template>
  <el-input-number
    :model-value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    :min="field.min_value"
    :max="field.max_value"
    :precision="field.decimal_places"
    :step="field.step || 1"
    :controls-position="field.controls_position || 'right'"
    style="width: 100%"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
defineProps({
  field: Object,
  modelValue: Number,
  disabled: Boolean,
  placeholder: String
})

defineEmits(['update:modelValue'])
</script>
