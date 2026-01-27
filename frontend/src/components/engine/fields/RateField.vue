<template>
  <el-rate
    :model-value="modelValue"
    :disabled="disabled"
    :max="field.max || 5"
    :allow-half="field.allowHalf || false"
    :show-text="field.showText || false"
    :texts="field.texts || ['极差', '失望', '一般', '满意', '惊喜']"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
const props = defineProps({
  field: Object,
  modelValue: Number,
  disabled: Boolean
})

defineEmits(['update:modelValue'])
</script>
