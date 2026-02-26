<template>
  <el-switch
    v-if="renderType === 'switch'"
    v-model="internalValue"
    :disabled="disabled"
    :active-text="switchActiveText"
    :inactive-text="switchInactiveText"
    @change="handleChange"
  />
  <el-checkbox
    v-else
    v-model="internalValue"
    :disabled="disabled"
    @change="handleChange"
  >
    {{ field.name }}
  </el-checkbox>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  modelValue: boolean
  field: any
  disabled?: boolean
  readonly?: boolean
}>()

const emit = defineEmits(['update:modelValue', 'change'])

const internalValue = computed({
  get: () => !!props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const componentProps = computed(() => ({
  ...(props.field?.component_props || {}),
  ...(props.field?.componentProps || {})
}))

const renderType = computed(() => {
  if (componentProps.value.renderType) {
    return componentProps.value.renderType
  }

  const fieldType = props.field?.fieldType || props.field?.field_type
  return fieldType === 'checkbox' ? 'checkbox' : 'switch'
})

const switchActiveText = computed(() => componentProps.value.activeText || '')
const switchInactiveText = computed(() => componentProps.value.inactiveText || '')

const handleChange = (val: any) => {
  emit('change', val)
}
</script>
