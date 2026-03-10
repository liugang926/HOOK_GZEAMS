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
import { computed, ref, onMounted, watch } from 'vue'
import { dictionaryItemApi } from '@/api/system'
import { withSWR } from '@/utils/cacheWrapper'

const props = defineProps<{
  modelValue: any
  field: any
  disabled?: boolean
}>()

const emit = defineEmits(['update:modelValue', 'change'])

const options = ref<any[]>([])
const loading = ref(false)

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

/**
 * Fetch dictionary items with SWR caching + deduplication.
 * Same `dictCode` on the same page will share one in-flight request.
 */
async function loadOptions() {
  const presetOptions = props.field.options || componentProps.value.options
  if (Array.isArray(presetOptions) && presetOptions.length > 0) {
    options.value = presetOptions
    return
  }

  const dictCode = componentProps.value.dictionary || props.field.dictionaryType
  if (!dictCode) return

  loading.value = true
  try {
    const items = await withSWR(
      `dict_items_${dictCode}`,
      async () => {
        const res = await dictionaryItemApi.getByType(dictCode)
        const data = res?.data?.results ?? res?.data ?? []
        return Array.isArray(data) ? data.map((item: any) => ({
          label: item.name || item.label || item.value,
          value: item.code || item.value || item.id
        })) : []
      },
      { staleTime: 1000 * 60 * 60, persist: true } // 1 hour cache
    )
    options.value = items
  } catch (e) {
    console.warn(`[DictionarySelect] Failed to load dict "${dictCode}"`, e)
    options.value = []
  } finally {
    loading.value = false
  }
}

onMounted(loadOptions)

// Reload if the dictionary type changes dynamically
watch(
  () => componentProps.value.dictionary || props.field.dictionaryType,
  (newCode, oldCode) => {
    if (newCode && newCode !== oldCode) loadOptions()
  }
)

const handleChange = (val: any) => {
  emit('change', val)
}
</script>
