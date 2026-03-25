<template>
  <div
    class="dynamic-field-facade"
    :class="[`is-mode-${resolvedMode}`, fieldTypeClass]"
  >
    <template v-if="resolvedMode === 'read'">
      <FieldDisplay
        :field="normalizedField"
        :value="modelValue"
      />
    </template>
    <template v-else>
      <FieldRenderer
        :field="normalizedField"
        :model-value="modelValue"
        :form-data="formData"
        :disabled="disabled"
        @update:model-value="emitUpdate"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import FieldDisplay from '@/components/common/FieldDisplay.vue'
import FieldRenderer from '@/components/engine/FieldRenderer.vue'
import { buildNormalizedRuntimeField, resolveEngineFieldType } from '@/components/engine/fieldRegistry'

const props = defineProps<{
  field: Record<string, any>
  modelValue?: any
  formData?: Record<string, any>
  mode?: 'read' | 'edit' | 'auto'
  disabled?: boolean
}>()

const emit = defineEmits(['update:modelValue'])

const normalizedField = computed(() => {
  return buildNormalizedRuntimeField(props.field || {})
})

const resolvedMode = computed(() => {
  if (props.mode && props.mode !== 'auto') return props.mode
  // Infer read mode from disabled or readonly flags from normalized/runtime metadata.
  if (props.disabled) return 'read'
  const field = normalizedField.value as Record<string, any>
  const isReadonly =
    field.readonly === true ||
    field.readOnly === true ||
    field.isReadonly === true
  if (isReadonly) return 'read'
  return 'edit'
})

const fieldTypeClass = computed(() => {
  return `dynamic-field-type-${resolveEngineFieldType(normalizedField.value)}`
})

const emitUpdate = (val: any) => {
  emit('update:modelValue', val)
}
</script>

<style scoped>
.dynamic-field-facade {
  width: 100%;
  display: flex;
  align-items: center;
  position: relative;
}

.dynamic-field-facade.is-mode-read {
  min-height: 32px;
  align-items: flex-start; /* Read views often flow top-down or have images */
}

.dynamic-field-facade.is-mode-edit {
  min-height: 32px;
}
</style>
