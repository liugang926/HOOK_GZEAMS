<template>
  <el-date-picker
    v-model="internalValue"
    :type="type"
    :placeholder="field.name || $t('fields.selectDate')"
    :disabled="disabled"
    :readonly="readonly"
    :format="format"
    :value-format="valueFormat"
    style="width: 100%"
    @change="handleChange"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelValue: string | Date | null
  field: any
  disabled?: boolean
  readonly?: boolean
}>()

const emit = defineEmits(['update:modelValue', 'change'])

const internalValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const componentProps = computed(() => ({
  ...(props.field?.component_props || {}),
  ...(props.field?.componentProps || {})
}))

const type = computed(() => {
  if (componentProps.value.type) {
    return componentProps.value.type
  }

  const fieldType = props.field?.fieldType || props.field?.field_type
  if (['date', 'datetime', 'time', 'daterange', 'year', 'month'].includes(fieldType)) {
    return fieldType
  }

  return 'date'
})

const format = computed(() => {
  if (componentProps.value.format) {
    return componentProps.value.format
  }
  if (type.value === 'datetime') {
    return 'YYYY-MM-DD HH:mm:ss'
  }
  if (type.value === 'time') {
    return 'HH:mm:ss'
  }
  if (type.value === 'month') {
    return 'YYYY-MM'
  }
  if (type.value === 'year') {
    return 'YYYY'
  }
  return 'YYYY-MM-DD'
})

const valueFormat = computed(() => {
  if (componentProps.value.valueFormat) {
    return componentProps.value.valueFormat
  }
  if (type.value === 'datetime') {
    return 'YYYY-MM-DD HH:mm:ss'
  }
  if (type.value === 'time') {
    return 'HH:mm:ss'
  }
  if (type.value === 'month') {
    return 'YYYY-MM'
  }
  if (type.value === 'year') {
    return 'YYYY'
  }
  return 'YYYY-MM-DD'
})

const handleChange = (val: any) => {
  emit('change', val)
}
</script>
