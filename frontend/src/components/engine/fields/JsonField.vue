<template>
  <el-input
    :model-value="textValue"
    type="textarea"
    :rows="rows"
    :disabled="disabled"
    :placeholder="placeholder"
    @update:model-value="handleUpdate"
  />
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface Props {
  field?: Record<string, any>
  modelValue?: any
  disabled?: boolean
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  field: undefined,
  modelValue: null,
  disabled: false,
  placeholder: ''
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: any): void
}>()

const rows = computed(() => {
  const fromField = Number((props.field as any)?.rows)
  if (Number.isFinite(fromField) && fromField > 0) return fromField
  return props.disabled ? 6 : 10
})

const formatJson = (value: any): string => {
  if (value === null || value === undefined) return ''
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

const draft = ref<string>(formatJson(props.modelValue))

watch(
  () => props.modelValue,
  (val) => {
    draft.value = formatJson(val)
  },
  { immediate: true }
)

const textValue = computed(() => draft.value)

const handleUpdate = (nextText: string) => {
  draft.value = nextText

  // Best-effort parse. If invalid JSON, keep text so user can continue editing.
  const trimmed = String(nextText || '').trim()
  if (!trimmed) {
    emit('update:modelValue', null)
    return
  }

  try {
    emit('update:modelValue', JSON.parse(trimmed))
  } catch {
    emit('update:modelValue', nextText)
  }
}
</script>

