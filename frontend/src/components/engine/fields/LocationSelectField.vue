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

const isMultiple = computed(() => {
  const field = (props.field || {}) as AnyRecord
  const fieldType = String(field.fieldType || field.field_type || '').toLowerCase()
  return (
    field.multiple === true ||
    field.componentProps?.multiple === true ||
    field.component_props?.multiple === true ||
    fieldType === 'multi_location' ||
    fieldType === 'multilocation'
  )
})

const lookupField = computed(() => {
  const field = (props.field || {}) as AnyRecord
  const componentProps = {
    ...(field.component_props || {}),
    ...(field.componentProps || {}),
    multiple: isMultiple.value
  }

  return {
    ...field,
    fieldType: field.fieldType || field.field_type || 'location',
    referenceObject: field.referenceObject || field.reference_object || 'Location',
    referenceDisplayField:
      field.referenceDisplayField ||
      field.reference_display_field ||
      field.displayField ||
      field.display_field ||
      'name',
    referenceSecondaryField:
      field.referenceSecondaryField ||
      field.reference_secondary_field ||
      'code',
    componentProps,
    component_props: componentProps
  }
})
</script>

