<template>
  <el-select
    v-model="internalValue"
    :placeholder="field.name || '请选择'"
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

const isMultiple = computed(() => {
  return props.field.field_type === 'multi_select'
})

onMounted(async () => {
  const dictCode = props.field.component_props?.dictionary
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
