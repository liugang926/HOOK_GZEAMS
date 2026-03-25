<template>
  <el-rate
    :model-value="modelValue"
    :disabled="disabled"
    :max="field.max || 5"
    :allow-half="field.allowHalf || false"
    :show-text="field.showText || false"
    :texts="field.texts || $t('fields.rateTexts')"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  field: Object,
  modelValue: Number,
  disabled: Boolean
})

defineEmits(['update:modelValue'])
</script>
