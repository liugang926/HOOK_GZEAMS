<template>
  <el-switch
    :model-value="modelValue"
    :disabled="disabled"
    :active-text="field.activeText || $t('fields.yes')"
    :inactive-text="field.inactiveText || $t('fields.no')"
    :active-value="activeValue"
    :inactive-value="inactiveValue"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  field: Object,
  modelValue: [Boolean, String, Number],
  disabled: Boolean
})

defineEmits(['update:modelValue'])

// Support both boolean and numeric switch values
const activeValue = computed(() => {
  if (props.field.valueType === 'number') return 1
  if (props.field.valueType === 'string') return 'yes'
  return true
})

const inactiveValue = computed(() => {
  if (props.field.valueType === 'number') return 0
  if (props.field.valueType === 'string') return 'no'
  return false
})
</script>
