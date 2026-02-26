<template>
  <UserPicker
    :model-value="modelValue"
    :multiple="isMultiple"
    :disabled="disabled"
    :placeholder="placeholder"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
import { computed } from 'vue'
import UserPicker from '@/components/common/UserSelector.vue'

const props = defineProps({
  field: Object,
  modelValue: [String, Number, Array],
  disabled: Boolean,
  placeholder: String
})

defineEmits(['update:modelValue'])

// Support both camelCase (fieldType) and snake_case (field_type)
const isMultiple = computed(() => {
  const fieldType = props.field.fieldType || props.field.field_type
  return props.field.multiple || fieldType === 'multi_user' || fieldType === 'multiUser'
})
</script>
