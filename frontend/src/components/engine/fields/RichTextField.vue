<template>
  <div class="rich-text-field">
    <el-input
      :model-value="modelValue"
      type="textarea"
      :disabled="disabled"
      :placeholder="placeholder"
      :rows="field.rows || 5"
      :maxlength="field.maxlength"
      show-word-limit
      @update:model-value="$emit('update:modelValue', $event)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  field: Object,
  modelValue: String,
  disabled: Boolean,
  placeholder: String
})

defineEmits(['update:modelValue'])

const placeholder = computed(() => {
  return props.placeholder || `${t('fields.input')}${props.field.name}`
})
</script>

<style scoped>
.rich-text-field {
  width: 100%;
}
</style>
