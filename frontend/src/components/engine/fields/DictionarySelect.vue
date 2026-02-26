<template>
  <el-select
    v-model="internalValue"
    :placeholder="field.name || $t('fields.select')"
    :disabled="disabled"
    :multiple="isMultiple"
    clearable
    style="width: 100%"
    @change="handleChange"
  >
    <el-option
      v-for="item in options"
      :key="item.value"
      :label="item.label"
      :value="item.value"
    />
  </el-select>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
// import { getDictionaryItems } from '@/api/system' // Assume this exists or mock

const props = defineProps<{
  modelValue: any
  field: any
  disabled?: boolean
}>()

const emit = defineEmits(['update:modelValue', 'change'])

const options = ref<any[]>([])

const internalValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const componentProps = computed(() => ({
  ...(props.field?.component_props || {}),
  ...(props.field?.componentProps || {})
}))

const isMultiple = computed(() => {
  // Support both camelCase (fieldType) and snake_case (field_type)
  const fieldType = props.field.fieldType || props.field.field_type
  return fieldType === 'multi_select' || fieldType === 'multiSelect' || props.field.multiple
})

onMounted(async () => {
  const presetOptions = props.field.options || componentProps.value.options
  if (Array.isArray(presetOptions) && presetOptions.length > 0) {
    options.value = presetOptions
    return
  }

  const dictCode = componentProps.value.dictionary || props.field.dictionaryType
  if (dictCode) {
    // TODO: Call API
    // const res = await getDictionaryItems(dictCode)
    // options.value = res
    
    // Mock
    options.value = [
        { label: 'Option A', value: 'a' },
        { label: 'Option B', value: 'b' }
    ]
  }
})

const handleChange = (val: any) => {
  emit('change', val)
}
</script>
