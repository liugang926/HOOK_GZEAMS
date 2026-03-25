<template>
  <FieldRenderer
    :field="field"
    :model-value="modelValue"
    :form-data="formData"
    :disabled="disabled"
    @update:model-value="(val: any) => emit('update:modelValue', val)"
    @request-save="emit('request-save')"
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
  (e: 'request-save'): void
}>()
</script>
