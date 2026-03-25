<template>
  <div class="color-field">
    <el-color-picker
      :model-value="modelValue"
      :disabled="disabled"
      :show-alpha="field.showAlpha || false"
      :color-format="field.format || 'hex'"
      :predefine="predefineColors"
      @update:model-value="$emit('update:modelValue', $event)"
    />
    <span
      v-if="modelValue"
      class="color-value"
    >{{ modelValue }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  field: Object,
  modelValue: String,
  disabled: Boolean
})

defineEmits(['update:modelValue'])

const predefineColors = computed(() => {
  return props.field.predefine || [
    '#ff4500',
    '#ff8c00',
    '#ffd700',
    '#90ee90',
    '#00ced1',
    '#1e90ff',
    '#c71585',
    'rgba(255, 69, 0, 0.68)',
    'rgb(255, 120, 0)',
    'hsv(50, 100, 100)'
  ]
})
</script>

<style scoped>
.color-field {
  display: flex;
  align-items: center;
  gap: 12px;
}

.color-value {
  font-family: monospace;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
