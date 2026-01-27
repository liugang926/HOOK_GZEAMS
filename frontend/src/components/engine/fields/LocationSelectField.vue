<template>
  <el-select
    :model-value="modelValue"
    :disabled="disabled"
    :placeholder="placeholder"
    clearable
    filterable
    :multiple="field.multiple"
    style="width: 100%"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <el-option
      v-for="item in locationOptions"
      :key="item.id"
      :label="item.name"
      :value="item.id"
    />
  </el-select>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getLocations } from '@/api/locations'

const props = defineProps({
  field: Object,
  modelValue: [String, Number, Array],
  disabled: Boolean,
  placeholder: String
})

defineEmits(['update:modelValue'])

const locationOptions = ref([])
const loading = ref(false)

const placeholder = computed(() => {
  return props.placeholder || `请选择${props.field.name}`
})

onMounted(async () => {
  await loadLocations()
})

const loadLocations = async () => {
  loading.value = true
  try {
    const data = await getLocations()
    locationOptions.value = data.results || data || []
  } catch (error) {
    console.error('Failed to load locations:', error)
  } finally {
    loading.value = false
  }
}
</script>
