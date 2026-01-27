<template>
  <component
    :is="fieldComponent"
    :field="field"
    :model-value="modelValue"
    :form-data="formData"
    v-bind="fieldProps"
    @update:model-value="$emit('update:modelValue', $event)"
  />
</template>

<script setup>
import { computed, defineAsyncComponent } from 'vue'

const props = defineProps({
  field: { type: Object, required: true },
  modelValue: { type: [String, Number, Object, Array, Boolean], default: null },
  formData: { type: Object, default: () => ({}) }, // Pass full form data for formula calculations
  disabled: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue'])

/**
 * Field type to component mapping
 * Supports all metadata-driven field types for the low-code platform
 */
const FIELD_COMPONENTS = {
  // Text input types
  text: () => import('./fields/TextField.vue'),
  textarea: () => import('./fields/TextField.vue'),
  email: () => import('./fields/TextField.vue'),
  url: () => import('./fields/TextField.vue'),
  phone: () => import('./fields/TextField.vue'),
  password: () => import('./fields/TextField.vue'),

  // Number types
  number: () => import('./fields/NumberField.vue'),
  currency: () => import('./fields/NumberField.vue'),
  percent: () => import('./fields/NumberField.vue'),

  // Date/Time types
  date: () => import('./fields/DateField.vue'),
  datetime: () => import('./fields/DateField.vue'),
  time: () => import('./fields/DateField.vue'),
  daterange: () => import('./fields/DateField.vue'),
  year: () => import('./fields/DateField.vue'),
  month: () => import('./fields/DateField.vue'),

  // Selection types
  select: () => import('./fields/SelectField.vue'),
  multi_select: () => import('./fields/SelectField.vue'),
  radio: () => import('./fields/SelectField.vue'),
  checkbox: () => import('./fields/BooleanField.vue'),
  boolean: () => import('./fields/BooleanField.vue'),

  // Reference types (relationships to other entities)
  reference: () => import('./fields/ReferenceField.vue'),
  user: () => import('./fields/UserSelectField.vue'),
  department: () => import('./fields/DepartmentSelectField.vue'),
  location: () => import('./fields/LocationSelectField.vue'),
  asset: () => import('./fields/AssetSelector.vue'),

  // Dictionary (system config)
  dictionary: () => import('./fields/DictionarySelect.vue'),

  // Complex types
  sub_table: () => import('./fields/SubTableField.vue'),
  formula: () => import('./fields/FormulaField.vue'),

  // File types
  file: () => import('./fields/AttachmentUpload.vue'),
  image: () => import('./fields/AttachmentUpload.vue'),
  attachment: () => import('./fields/AttachmentUpload.vue'),

  // Special types
  qr_code: () => import('./fields/QRCodeField.vue'),
  barcode: () => import('./fields/BarcodeField.vue'),
  rich_text: () => import('./fields/RichTextField.vue'),
  code: () => import('./fields/CodeField.vue'),
  color: () => import('./fields/ColorField.vue'),
  rate: () => import('./fields/RateField.vue'),
  slider: () => import('./fields/SliderField.vue'),
  switch: () => import('./fields/SwitchField.vue')
}

/**
 * Map internal field types to standard components
 * Handles type aliases for backward compatibility
 */
const getFieldType = (field) => {
  const type = field.field_type

  // Handle type aliases
  const typeAliases = {
    string: 'text',
    int: 'number',
    integer: 'number',
    float: 'number',
    decimal: 'number',
    money: 'currency',
    bool: 'boolean',
    toggle: 'switch'
  }

  return typeAliases[type] || type
}

/**
 * Computed component to render
 * Falls back to TextField for unknown types
 */
const fieldComponent = computed(() => {
  const fieldType = getFieldType(props.field)
  const componentLoader = FIELD_COMPONENTS[fieldType]

  if (!componentLoader) {
    console.warn(`Unknown field type: ${fieldType}, falling back to TextField`)
    return defineAsyncComponent(() => import('./fields/TextField.vue'))
  }

  return defineAsyncComponent(componentLoader)
})

/**
 * Props to pass to the field component
 * Combines common props with field-specific component_props
 */
const fieldProps = computed(() => {
  const fieldType = getFieldType(props.field)

  // Common props for all fields
  const baseProps = {
    disabled: props.disabled,
    placeholder: props.field.placeholder || `请输入${props.field.name}`,
    ...props.field.component_props
  }

  // Type-specific default props
  const typeDefaults = {
    textarea: {
      type: 'textarea',
      rows: props.field.component_props?.rows || 3
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
      currency: '¥',
      prefix: '¥'
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
      startPlaceholder: '开始日期',
      endPlaceholder: '结束日期',
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

  return {
    ...baseProps,
    ...(typeDefaults[fieldType] || {})
  }
})
</script>
