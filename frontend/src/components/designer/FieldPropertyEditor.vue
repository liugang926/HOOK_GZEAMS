<template>
  <el-form
    :model="modelValue"
    label-position="top"
    size="small"
    class="field-property-editor"
  >
    <template
      v-for="section in sections"
      :key="section"
    >
      <el-divider>{{ sectionLabels[section] }}</el-divider>
      <el-form-item
        v-for="item in groupedSchema[section]"
        :key="item.key"
        :label="item.label"
        :data-property-key="item.key"
      >
        <div :data-testid="`field-prop-${item.key}`">
          <el-select
            v-if="item.key === 'span'"
            :data-testid="`field-prop-${item.key}`"
            :model-value="modelValue?.span"
            @change="handleSelectChange(item.key, $event)"
          >
            <el-option
              v-for="span in availableSpans"
              :key="span"
              :label="`${span} / ${availableSpanColumns}`"
              :value="span"
            />
          </el-select>

          <el-switch
            v-else-if="item.inputType === 'switch'"
            :data-testid="`field-prop-${item.key}`"
            :model-value="modelValue?.[item.key]"
            :active-text="item.key === 'readonly' && mode === 'readonly' ? 'Readonly by default in detail mode' : ''"
            :active-value="item.key === 'visible' ? true : undefined"
            :inactive-value="item.key === 'visible' ? false : undefined"
            @change="handleSwitchChange(item.key, $event)"
          />

          <el-input-number
            v-else-if="item.inputType === 'number'"
            :data-testid="`field-prop-${item.key}`"
            :model-value="numberValue(item.key)"
            :min="getNumberMin(item.key)"
            :step="getNumberStep(item.key)"
            @change="handleNumberChange(item.key, $event)"
          />

          <el-select
            v-else-if="item.inputType === 'select'"
            :data-testid="`field-prop-${item.key}`"
            :model-value="modelValue?.[item.key]"
            @change="handleSelectChange(item.key, $event)"
          >
            <el-option
              v-for="option in getSelectOptions(item.key)"
              :key="option.value"
              :label="option.label"
              :value="option.value"
              :disabled="option.disabled"
            />
          </el-select>

          <el-input
            v-else-if="item.inputType === 'textarea'"
            :data-testid="`field-prop-${item.key}`"
            :model-value="stringValue(item.key)"
            type="textarea"
            :rows="item.key === 'helpText' ? 2 : 4"
            @input="handleTextChange(item.key, $event)"
          />

          <el-input
            v-else-if="item.inputType === 'json'"
            :data-testid="`field-prop-${item.key}`"
            :model-value="jsonValue(item.key)"
            type="textarea"
            :rows="4"
            @input="handleJsonChange(item.key, $event)"
          />

          <el-input
            v-else
            :data-testid="`field-prop-${item.key}`"
            :model-value="stringValue(item.key)"
            @input="handleTextChange(item.key, $event)"
          />
        </div>
      </el-form-item>
    </template>
  </el-form>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getFieldPropertySchema } from '@/composables/useFieldPropertySchema'
import { normalizeFieldType } from '@/utils/fieldType'
import { getCoreFieldTypes } from '@/platform/layout/fieldCapabilityMatrix'
import { getFieldDisabledReason } from '@/platform/layout/designerFieldGuard'

interface Props {
  modelValue?: Record<string, any>
  fieldType?: string
  mode?: string
  availableSpans?: number[]
  availableSpanColumns?: number
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: () => ({}),
  fieldType: 'text',
  mode: 'edit',
  availableSpans: () => [1, 2],
  availableSpanColumns: 2
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: Record<string, any>): void
  (e: 'update-property', payload: { key: string; value: any }): void
}>()

const normalizedFieldType = computed(() => normalizeFieldType(props.fieldType || props.modelValue?.fieldType || 'text'))
const schema = computed(() => getFieldPropertySchema(normalizedFieldType.value))
const fieldTypeOptions = computed(() => {
  const baseTypes = getCoreFieldTypes()
  const currentType = normalizedFieldType.value
  const uniqueTypes = baseTypes.includes(currentType) ? baseTypes : [currentType, ...baseTypes]

  return uniqueTypes.map((value) => {
    const reason = getFieldDisabledReason(value, props.mode)
    return {
      label: humanizeFieldType(value),
      value,
      disabled: Boolean(reason),
      reason
    }
  })
})

const sectionLabels: Record<string, string> = {
  basic: 'Basic',
  display: 'Display',
  validation: 'Validation',
  advanced: 'Advanced'
}
const sections = ['basic', 'display', 'validation', 'advanced'] as const

const groupedSchema = computed(() => {
  const map: Record<string, Array<{ key: string; label: string; inputType: string }>> = {
    basic: [],
    display: [],
    validation: [],
    advanced: []
  }
  for (const item of schema.value) {
    map[item.section].push(item)
  }
  return map
})

const emitUpdate = (key: string, value: any) => {
  const next = { ...(props.modelValue || {}), [key]: value }
  emit('update:modelValue', next)
  emit('update-property', { key, value })
}

const handleSelectChange = (key: string, value: unknown) => emitUpdate(key, value)
const handleSwitchChange = (key: string, value: unknown) => emitUpdate(key, value)
const handleNumberChange = (key: string, value: unknown) => emitUpdate(key, value)
const handleTextChange = (key: string, value: unknown) => emitUpdate(key, value)
const handleJsonChange = (key: string, value: unknown) => emitJsonUpdate(key, value)

const emitJsonUpdate = (key: string, value: any) => {
  let parsed: any = value
  if (typeof value === 'string') {
    const trimmed = value.trim()
    if (!trimmed) {
      parsed = ''
    } else {
      try {
        parsed = JSON.parse(trimmed)
      } catch {
        parsed = value
      }
    }
  }
  emitUpdate(key, parsed)
}

const stringValue = (key: string): string => String(props.modelValue?.[key] ?? '')
const numberValue = (key: string): number | undefined => {
  const value = props.modelValue?.[key]
  if (value === null || value === undefined || value === '') return undefined
  const num = Number(value)
  return Number.isFinite(num) ? num : undefined
}
const jsonValue = (key: string): string => {
  const value = props.modelValue?.[key]
  if (typeof value === 'string') return value
  if (value === null || value === undefined) return ''
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

const getNumberMin = (key: string): number | undefined => {
  if (key === 'minHeight') return 44
  if (key.includes('min_') || key.includes('max_')) return undefined
  return 0
}

const getNumberStep = (key: string): number => {
  if (key === 'minHeight') return 8
  return 1
}

const humanizeFieldType = (value: string): string =>
  value
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')

const getSelectOptions = (key: string): Array<{ label: string; value: string; disabled?: boolean }> => {
  if (key === 'fieldType') {
    return fieldTypeOptions.value.map((option) => ({
      label: option.reason ? `${option.label} (${option.reason})` : option.label,
      value: option.value,
      disabled: option.disabled
    }))
  }

  if (key === 'toolbar') {
    return [
      { label: 'Standard', value: 'standard' },
      { label: 'Simple', value: 'simple' },
      { label: 'Full', value: 'full' }
    ]
  }
  return []
}
</script>
