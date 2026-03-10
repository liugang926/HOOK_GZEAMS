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
import { useI18n } from 'vue-i18n'
import {
  FIELD_COMPONENT_LOADERS,
  buildNormalizedRuntimeField,
  resolveEngineFieldType
} from '@/components/engine/fieldRegistry'
import FieldErrorFallback from '@/components/engine/FieldErrorFallback.vue'
import FieldLoadingSkeleton from '@/components/engine/FieldLoadingSkeleton.vue'

const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { type: [String, Number, Object, Array, Boolean], default: null },
  formData: { type: Object, default: () => ({}) },
  disabled: { type: Boolean, default: false }
})

defineEmits(['update:modelValue'])
const { t } = useI18n()

const ASYNC_FIELD_COMPONENTS = Object.fromEntries(
  Object.entries(FIELD_COMPONENT_LOADERS).map(([type, loader]) => [
    type,
    defineAsyncComponent({
      loader,
      loadingComponent: FieldLoadingSkeleton,
      errorComponent: FieldErrorFallback,
      delay: 200,
      timeout: 30000
    })
  ])
)
const FALLBACK_TEXT_COMPONENT = defineAsyncComponent({
  loader: FIELD_COMPONENT_LOADERS.text,
  loadingComponent: FieldLoadingSkeleton,
  errorComponent: FieldErrorFallback,
  delay: 200,
  timeout: 30000
})

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
      placeholder: t('form.fields.inputText')
    }
  }

  const fieldType = resolveEngineFieldType(field)
  const fallbackLabel = field.label || field.name || ''
  const placeholderText =
    field.placeholder ||
    (fallbackLabel
      ? t('form.placeholders.input', { field: fallbackLabel })
      : t('form.fields.inputText'))

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
      startPlaceholder: t('common.placeholders.startDate'),
      endPlaceholder: t('common.placeholders.endDate'),
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
  
  if (fieldType === 'related_object') {
    const componentProps = field.componentProps || field.component_props || {}
    finalProps = {
      ...finalProps,
      parentObjectCode: componentProps.objectCode || field.objectCode,
      parentId: componentProps.instanceId || field.instanceId || props.formData?.id,
      mode: componentProps.displayMode || 'inline_readonly',
      title: field.label || field.name,
      targetObjectCode: componentProps.relatedObjectCode,
      pageSize: componentProps.pageSize || 5, // Match default records size design
      embedded: true
    }
  }

  return finalProps
})
</script>
