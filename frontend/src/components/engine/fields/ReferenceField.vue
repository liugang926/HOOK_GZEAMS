<template>
  <div class="reference-field">
    <el-select
      :model-value="normalizedValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :remote="true"
      :remote-method="debouncedSearch"
      :loading="loading"
      filterable
      clearable
      value-key="id"
      style="width: 100%"
      @visible-change="handleVisibleChange"
      @update:model-value="handleUpdate"
    >
      <el-option
        v-for="item in allOptions"
        :key="item.id"
        :label="getItemLabel(item)"
        :value="item.id"
      />
    </el-select>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { searchReferenceData } from '@/api/system'
import { debounce } from 'lodash-es'
import { referenceResolver } from '@/platform/reference/referenceResolver'

const props = defineProps({
  field: Object,
  // Detail endpoints may return expanded objects; edit submits IDs.
  modelValue: [String, Number, Object, Array],
  disabled: Boolean,
  placeholder: String
})

const emit = defineEmits(['update:modelValue', 'change'])

const loading = ref(false)
const options = ref([])
const currentValueObj = ref(null)

const resolveObjectCode = (refValue) => {
  if (!refValue) return ''
  const raw = String(refValue).trim()
  if (!raw) return ''
  const noQuery = raw.split('?')[0].replace(/\/+$/, '')
  const lastDot = noQuery.split('.').pop() || noQuery
  const lastPath = lastDot.split('/').filter(Boolean).pop() || lastDot
  return String(lastPath || '').trim()
}

const referenceObject = computed(() => {
  return (
    props.field?.referenceObject ||
    props.field?.reference_object ||
    props.field?.reference_model_path ||
    props.field?.referenceModelPath ||
    null
  )
})

const referenceObjectCode = computed(() => resolveObjectCode(referenceObject.value))

const displayField = computed(() => {
  return (
    props.field?.displayField ||
    props.field?.display_field ||
    props.field?.componentProps?.displayField ||
    props.field?.component_props?.display_field ||
    'name'
  )
})

const normalizedValue = computed(() => {
  const value = props.modelValue

  if (Array.isArray(value)) {
    return value
      .map((entry) => (entry && typeof entry === 'object' ? entry.id : entry))
      .filter((entry) => entry !== null && entry !== undefined && entry !== '')
  }

  if (value && typeof value === 'object') {
    return value.id
  }

  return value
})

const allOptions = computed(() => {
  let result = [...options.value]
  if (currentValueObj.value && !result.find((o) => o.id === currentValueObj.value.id)) {
    result = [currentValueObj.value, ...result]
  }
  return result
})

const getItemLabel = (item) => {
  if (!item) return ''
  return item[displayField.value] || item.name || item.label || item.code || item.id
}

const searchReference = async (query) => {
  if (!referenceObject.value) return

  loading.value = true
  try {
    const res = await searchReferenceData({
      reference_object: referenceObject.value,
      search: query
    })
    options.value = res.results || res.items || []
  } finally {
    loading.value = false
  }
}

const debouncedSearch = debounce(searchReference, 300)

const handleVisibleChange = (visible) => {
  if (!visible) return
  // Avoid auto-loading in read-only/disabled mode. We only need to resolve the current value.
  if (props.disabled) return
  if (loading.value) return
  if ((options.value || []).length > 0) return
  searchReference('')
}

const handleUpdate = (val) => {
  emit('update:modelValue', val)
  const selectedObj = allOptions.value.find((o) => o.id === val) || null
  emit('change', selectedObj)
}

const fetchCurrentValue = async () => {
  const value = normalizedValue.value
  if (!value || Array.isArray(value) || !referenceObject.value) return

  try {
    const objectCode = referenceObjectCode.value
    const id = String(value)

    // Prefer an exact-by-id fetch to avoid expensive list queries and to work in read-only mode.
    if (objectCode) {
      currentValueObj.value = (await referenceResolver.resolve({ objectCode, id })) || null
      return
    }

    // Fallback: try list search (legacy reference_object formats)
    const res = await searchReferenceData({
      reference_object: referenceObject.value,
      search: id.substring(0, 50)
    })
    const items = res.results || res.items || []
    const found = items.find((o) => String(o.id) === id)
    if (found) currentValueObj.value = found
  } catch (error) {
    console.warn('Failed to fetch current value for reference field:', error)
  }
}

watch(
  () => props.modelValue,
  (newVal) => {
    if (!newVal) {
      currentValueObj.value = null
      return
    }

    if (typeof newVal === 'object' && !Array.isArray(newVal)) {
      currentValueObj.value = newVal.id ? newVal : null
      return
    }

    fetchCurrentValue()
  },
  { immediate: true }
)
</script>
