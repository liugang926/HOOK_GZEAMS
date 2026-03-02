<template>
  <FieldRenderer
    :field="field"
    :model-value="modelValue"
    :form-data="formData"
    :disabled="disabled"
    @update:model-value="(val) => emit('update:modelValue', val)"
  />
</template>

<script setup lang="ts">
import FieldRenderer from '@/components/engine/FieldRenderer.vue'
import type { RuntimeField } from '@/types/runtime'

interface Props {
  field: RuntimeField
  modelValue: any
  formData?: Record<string, any>
  disabled?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: any): void
}>()
</script>
