<template>
  <el-date-picker
    v-model="internalValue"
    :type="type"
    :placeholder="field.name || '请选择日期'"
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

const type = computed(() => {
  return props.field.component_props?.type || 'date'
})

const format = computed(() => {
  return props.field.component_props?.format || (type.value === 'datetime' ? 'YYYY-MM-DD HH:mm:ss' : 'YYYY-MM-DD')
})

const valueFormat = computed(() => {
  return props.field.component_props?.valueFormat || (type.value === 'datetime' ? 'YYYY-MM-DD HH:mm:ss' : 'YYYY-MM-DD')
})

const handleChange = (val: any) => {
  emit('change', val)
}
</script>
