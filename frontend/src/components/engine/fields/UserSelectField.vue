<template>
  <ReferenceField
    :field="lookupField"
    :model-value="modelValue"
    :disabled="disabled"
    :placeholder="placeholder"
    @update:model-value="$emit('update:modelValue', $event)"
    @change="$emit('change', $event)"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import ReferenceField from './ReferenceField.vue'

type AnyRecord = Record<string, any>

const props = defineProps({
  field: Object,
  modelValue: [String, Number, Object, Array],
  disabled: Boolean,
  placeholder: String
})

defineEmits(['update:modelValue', 'change'])

// Determine multi-select from camelCase field metadata
const isMultiple = computed(() => {
  const field = (props.field || {}) as AnyRecord
  const fieldType = String(field.fieldType || '').toLowerCase()
  return (
    field.multiple === true ||
    field.componentProps?.multiple === true ||
    fieldType === 'multi_user' ||
    fieldType === 'multiuser'
  )
})

const lookupField = computed(() => {
  const field = (props.field || {}) as AnyRecord
  const componentProps = {
    ...(field.componentProps || {}),
    multiple: isMultiple.value
  }

  return {
    ...field,
    fieldType: field.fieldType || 'user',
    referenceObject: field.referenceObject || 'User',
    referenceDisplayField:
      field.referenceDisplayField ||
      field.displayField ||
      'fullName',
    referenceSecondaryField:
      field.referenceSecondaryField ||
      'username',
    componentProps
  }
})
</script>
