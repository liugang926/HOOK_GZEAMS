<template>
  <el-switch
    v-if="renderType === 'switch'"
    v-model="internalValue"
    :disabled="disabled"
    :active-text="field.component_props?.activeText"
    :inactive-text="field.component_props?.inactiveText"
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

const renderType = computed(() => {
  return props.field.component_props?.renderType || 'switch'
})

const handleChange = (val: any) => {
  emit('change', val)
}
</script>
