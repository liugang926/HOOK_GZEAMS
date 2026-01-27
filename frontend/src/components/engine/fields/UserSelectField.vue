<template>
  <UserPicker
    :model-value="modelValue"
    :multiple="field.multiple || field.field_type === 'multi_user'"
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
</script>
