<template>
  <div class="slider-field">
    <el-slider
      :model-value="modelValue"
      :disabled="disabled"
      :min="field.min || 0"
      :max="field.max || 100"
      :step="field.step || 1"
      :marks="field.marks"
      :show-stops="field.showStops || false"
      :show-tooltip="field.showTooltip !== false"
      @update:model-value="$emit('update:modelValue', $event)"
    />
    <div
      v-if="showValue"
      class="slider-value"
    >
      {{ modelValue }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  field: Object,
  modelValue: Number,
  disabled: Boolean
})

defineEmits(['update:modelValue'])

const showValue = computed(() => {
  return props.field.showValue !== false
})
</script>

<style scoped>
.slider-field {
  width: 100%;
}

.slider-value {
  margin-top: 8px;
  text-align: center;
  font-weight: 500;
  color: var(--el-color-primary);
}
</style>
