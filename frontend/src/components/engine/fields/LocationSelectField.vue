<template>
  <el-select
    :model-value="modelValue"
    :disabled="disabled"
    :placeholder="placeholder"
    clearable
    filterable
    :multiple="field.multiple"
    style="width: 100%"
    @visible-change="handleVisibleChange"
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
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import request from '@/utils/request'
import { referenceResolver } from '@/platform/reference/referenceResolver'

const { t } = useI18n()

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
  return props.placeholder || `${t('fields.select')}${props.field.name}`
})

const getIds = () => {
  const v = props.modelValue
  const ids = Array.isArray(v) ? v : v ? [v] : []
  return ids
    .map((entry) => {
      if (!entry) return ''
      if (typeof entry === 'object') return entry.id ? String(entry.id) : ''
      return String(entry)
    })
    .filter(Boolean)
}

let lastLoadKey = ''
const loadCurrentLocations = async () => {
  const ids = getIds()
  if (ids.length === 0) {
    locationOptions.value = []
    return
  }

  const key = ids.slice().sort().join(',')
  if (key === lastLoadKey) return
  lastLoadKey = key

  loading.value = true
  try {
    const resolved = await referenceResolver.resolveMany('Location', ids)
    locationOptions.value = Object.values(resolved).filter(Boolean)
  } finally {
    loading.value = false
  }
}

const handleVisibleChange = (visible) => {
  if (!visible) return
  if (props.disabled) return
  if (loading.value) return
  if ((locationOptions.value || []).length > 0) return
  loadLocations()
}

watch(
  () => [props.disabled, props.modelValue],
  async ([disabled]) => {
    if (disabled) {
      await loadCurrentLocations()
      return
    }
    // Don't auto-load full list until the user opens the dropdown.
  },
  { immediate: true }
)

onMounted(async () => {
  if (props.disabled) await loadCurrentLocations()
})

const loadLocations = async () => {
  loading.value = true
  try {
    // Use unified object router for low-code runtime consistency.
    const data = await request.get('/system/objects/Location/', {
      params: { page: 1, page_size: 200 },
      silent: true
    })
    locationOptions.value = data?.results || []
  } catch (error) {
    console.error('Failed to load locations:', error)
  } finally {
    loading.value = false
  }
}
</script>
