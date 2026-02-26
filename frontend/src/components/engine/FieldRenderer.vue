<template>
  <component
    :is="fieldComponent"
    :field="normalizedField"
    :model-value="modelValue"
    :form-data="formData"
    v-bind="fieldProps"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue'
import {
  FIELD_COMPONENT_LOADERS,
  buildNormalizedRuntimeField,
  resolveEngineFieldType
} from '@/components/engine/fieldRegistry'

const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { type: [String, Number, Object, Array, Boolean], default: null },
  formData: { type: Object, default: () => ({}) },
  disabled: { type: Boolean, default: false }
})

defineEmits(['update:modelValue'])

const ASYNC_FIELD_COMPONENTS = Object.fromEntries(
  Object.entries(FIELD_COMPONENT_LOADERS).map(([type, loader]) => [type, defineAsyncComponent(loader)])
)
const FALLBACK_TEXT_COMPONENT = defineAsyncComponent(FIELD_COMPONENT_LOADERS.text)

const normalizedField = computed(() => {
  return buildNormalizedRuntimeField(props.field || {})
})

const getFileUploadContext = (field) => {
  const componentProps = field.componentProps || field.component_props || {}
  return {
    objectCode: componentProps.objectCode || field.objectCode,
    instanceId: componentProps.instanceId || field.instanceId,
    fieldCode: field.code || field.fieldCode
  }
}

const fieldComponent = computed(() => {
  const fieldType = resolveEngineFieldType(normalizedField.value)
  const component = ASYNC_FIELD_COMPONENTS[fieldType]

  if (!component) {
    console.warn(`Unknown field type: ${fieldType}, falling back to TextField`)
    return FALLBACK_TEXT_COMPONENT
  }

  return component
})

const fieldProps = computed(() => {
  const field = normalizedField.value

  if (!field || Object.keys(field).length <= 2) {
    return {
      disabled: props.disabled,
      placeholder: 'Please enter'
    }
  }

  const fieldType = resolveEngineFieldType(field)
  const fallbackLabel = field.label || field.name || ''
  const placeholderText = field.placeholder || (fallbackLabel ? `Please enter ${fallbackLabel}` : 'Please enter')

  const baseProps = {
    disabled: props.disabled,
    placeholder: placeholderText,
    ...field.componentProps
  }

  const typeDefaults = {
    textarea: {
      type: 'textarea',
      rows: field.componentProps?.rows || 3
    },
    email: {
      type: 'email'
    },
    url: {
      type: 'url'
    },
    phone: {
      type: 'tel',
      maxlength: 20
    },
    password: {
      type: 'password',
      showPassword: true
    },
    currency: {
      precision: 2,
      currency: 'CNY',
      prefix: 'CNY '
    },
    percent: {
      precision: 2,
      suffix: '%'
    },
    datetime: {
      type: 'datetime',
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'YYYY-MM-DD HH:mm:ss'
    },
    time: {
      type: 'time',
      format: 'HH:mm:ss',
      valueFormat: 'HH:mm:ss'
    },
    daterange: {
      type: 'daterange',
      rangeSeparator: '-',
      startPlaceholder: 'Start date',
      endPlaceholder: 'End date',
      valueFormat: 'YYYY-MM-DD'
    },
    year: {
      type: 'year',
      format: 'YYYY',
      valueFormat: 'YYYY'
    },
    month: {
      type: 'month',
      format: 'YYYY-MM',
      valueFormat: 'YYYY-MM'
    },
    multi_select: {
      multiple: true,
      collapseTags: true,
      maxCollapseTags: 3
    },
    radio: {
      mode: 'radio'
    },
    checkbox: {
      mode: 'checkbox'
    },
    image: {
      accept: 'image/*',
      listType: 'picture-card'
    },
    qr_code: {
      readonly: true
    },
    barcode: {
      readonly: true
    },
    rate: {
      max: 5,
      allowHalf: false
    },
    slider: {
      marks: false,
      showStops: false
    }
  }

  let finalProps = {
    ...baseProps,
    ...(typeDefaults[fieldType] || {})
  }

  if (['file', 'image', 'attachment'].includes(fieldType)) {
    finalProps = {
      ...finalProps,
      ...getFileUploadContext(field)
    }
  }

  return finalProps
})
</script>
