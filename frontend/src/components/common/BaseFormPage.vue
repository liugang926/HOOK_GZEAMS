<!--
  BaseFormPage Component

  A reusable form page component that provides:
  - Form layout with label/section organization
  - Validation with customizable rules
  - Submit/Cancel actions
  - Loading and disabled states
  - Slot-based field customization

  Usage:
  <BaseFormPage
    title="Create Asset"
    :fields="formFields"
    :rules="validationRules"
    :loading="submitting"
    @submit="handleSubmit"
    @cancel="handleCancel"
  >
    <template #field-{prop}="{ field, form }">
      <el-input v-model="form[field.prop]" />
    </template>
  </BaseFormPage>
-->

<script setup lang="ts">
/**
 * BaseFormPage Component
 *
 * A standardized form page component for all module forms.
 * Provides validation, loading states, and customizable field rendering.
 */

import { ref, computed, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'

// ============================================================================
// Types
// ============================================================================

export interface FormField {
  /** Field identifier (maps to data key) */
  prop: string
  /** Field label */
  label: string
  /** Field type: input, textarea, select, date, number, switch, slot, etc. */
  type?: 'input' | 'textarea' | 'select' | 'date' | 'dateRange' | 'number' | 'switch' | 'radio' | 'checkbox' | 'slot' | 'upload'
  /** Placeholder text */
  placeholder?: string
  /** Whether field is required */
  required?: boolean
  /** Field options (for select/radio/checkbox) */
  options?: Array<{ label: string; value: any; disabled?: boolean }>
  /** Number of grid columns (1-24) */
  span?: number
  /** Field description/help text */
  description?: string
  /** Default value */
  defaultValue?: any
  /** Disabled state */
  disabled?: boolean
  /** Whether to hide the field */
  hidden?: boolean
  /** Rows for textarea */
  rows?: number
  /** Minimum value (for number) */
  min?: number
  /** Maximum value (for number) */
  max?: number
  /** Step for number input */
  step?: number
  /** Precision for number input */
  precision?: number
  /** Date format */
  format?: string
  /** Value format for date picker */
  valueFormat?: string
  /** Multiple select */
  multiple?: boolean
  /** Upload file type */
  accept?: string
  /** Maximum file size (MB) */
  maxSize?: number
  /** Maximum number of files */
  limit?: number
}

interface Props {
  /** Page title */
  title?: string
  /** Form field definitions */
  fields: FormField[]
  /** Validation rules */
  rules?: FormRules
  /** Submit loading state */
  loading?: boolean
  /** Submit button text */
  submitText?: string
  /** Cancel button text */
  cancelText?: string
  /** Show cancel button */
  showCancel?: boolean
  /** Form layout direction */
  layout?: 'horizontal' | 'vertical' | 'inline'
  /** Label width */
  labelWidth?: string | number
  /** Label position */
  labelPosition?: 'left' | 'right' | 'top'
  /** Form data (for v-model) */
  modelValue?: Record<string, any>
  /** Column span for form grid (1-24) */
  columnSpan?: number
  /** Show submit button */
  showSubmit?: boolean
  /** Read-only mode */
  readonly?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: Record<string, any>): void
  (e: 'submit', data: Record<string, any>): void
  (e: 'cancel'): void
}

// ============================================================================
// Props & Emits
// ============================================================================

const props = withDefaults(defineProps<Props>(), {
  submitText: '提交',
  cancelText: '取消',
  showCancel: true,
  layout: 'horizontal',
  labelWidth: '120px',
  labelPosition: 'right',
  columnSpan: 24,
  showSubmit: true,
  readonly: false,
  modelValue: () => ({})
})

const emit = defineEmits<Emits>()

// ============================================================================
// State
// ============================================================================

const formRef = ref<FormInstance>()
const formData = ref<Record<string, any>>({})

// ============================================================================
// Computed
// ============================================================================

/** Visible fields (non-hidden) */
const visibleFields = computed(() => {
  return props.fields.filter(field => !field.hidden)
})

/** Field grid class */
const fieldClass = computed(() => {
  return {
    'field-col': true,
    [`col-${props.columnSpan}`]: true
  }
})

// ============================================================================
// Methods
// ============================================================================

/**
 * Initialize form data with default values
 */
const initFormData = () => {
  const data: Record<string, any> = {}
  props.fields.forEach(field => {
    if (props.modelValue && props.modelValue[field.prop] !== undefined) {
      data[field.prop] = props.modelValue[field.prop]
    } else if (field.defaultValue !== undefined) {
      data[field.prop] = field.defaultValue
    } else {
      // Set default based on field type
      switch (field.type) {
        case 'switch':
          data[field.prop] = false
          break
        case 'checkbox':
          data[field.prop] = []
          break
        case 'number':
          data[field.prop] = 0
          break
        default:
          data[field.prop] = undefined
      }
    }
  })
  formData.value = data
  emit('update:modelValue', data)
}

/**
 * Handle form submit
 */
const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    emit('submit', formData.value)
  } catch (error) {
    // Validation failed
  }
}

/**
 * Handle form cancel
 */
const handleCancel = () => {
  emit('cancel')
}

/**
 * Reset form to initial state
 */
const resetForm = () => {
  formRef.value?.resetFields()
  initFormData()
}

/**
 * Clear form validation
 */
const clearValidation = () => {
  formRef.value?.clearValidate()
}

/**
 * Validate specific field
 */
const validateField = (prop: string) => {
  formRef.value?.validateField(prop)
}

/**
 * Get field value
 */
const getFieldValue = (prop: string) => {
  return formData.value[prop]
}

/**
 * Set field value
 */
const setFieldValue = (prop: string, value: any) => {
  formData.value[prop] = value
}

// ============================================================================
// Watch
// ============================================================================

watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    Object.keys(newVal).forEach(key => {
      formData.value[key] = newVal[key]
    })
  }
}, { deep: true })

watch(formData, (newVal) => {
  emit('update:modelValue', { ...newVal })
}, { deep: true })

// ============================================================================
// Lifecycle
// ============================================================================

initFormData()

// ============================================================================
// Expose public methods
// ============================================================================

defineExpose({
  formRef,
  resetForm,
  clearValidation,
  validateField,
  getFieldValue,
  setFieldValue,
  validate: () => formRef.value?.validate()
})
</script>

<template>
  <div class="base-form-page">
    <!-- Form Header -->
    <div
      v-if="title"
      class="form-header"
    >
      <h3 class="form-title">
        {{ title }}
      </h3>
    </div>

    <!-- Form Container -->
    <div class="form-container">
      <el-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        :label-width="labelWidth"
        :label-position="labelPosition"
        :disabled="loading"
        class="base-form"
      >
        <el-row :gutter="20">
          <template
            v-for="field in visibleFields"
            :key="field.prop"
          >
            <el-col
              :span="field.span || 12"
              :class="fieldClass"
            >
              <!-- Input Field -->
              <el-form-item
                v-if="field.type === 'input'"
                :prop="field.prop"
                :label="field.label"
              >
                <el-input
                  v-model="formData[field.prop]"
                  :placeholder="field.placeholder || `请输入${field.label}`"
                  :disabled="readonly || field.disabled"
                  clearable
                />
                <div
                  v-if="field.description"
                  class="field-description"
                >
                  {{ field.description }}
                </div>
              </el-form-item>

              <!-- Textarea Field -->
              <el-form-item
                v-else-if="field.type === 'textarea'"
                :prop="field.prop"
                :label="field.label"
              >
                <el-input
                  v-model="formData[field.prop]"
                  type="textarea"
                  :rows="field.rows || 4"
                  :placeholder="field.placeholder || `请输入${field.label}`"
                  :disabled="readonly || field.disabled"
                />
                <div
                  v-if="field.description"
                  class="field-description"
                >
                  {{ field.description }}
                </div>
              </el-form-item>

              <!-- Number Field -->
              <el-form-item
                v-else-if="field.type === 'number'"
                :prop="field.prop"
                :label="field.label"
              >
                <el-input-number
                  v-model="formData[field.prop]"
                  :min="field.min"
                  :max="field.max"
                  :step="field.step || 1"
                  :precision="field.precision"
                  :disabled="readonly || field.disabled"
                  controls-position="right"
                  class="full-width"
                />
                <div
                  v-if="field.description"
                  class="field-description"
                >
                  {{ field.description }}
                </div>
              </el-form-item>

              <!-- Select Field -->
              <el-form-item
                v-else-if="field.type === 'select'"
                :prop="field.prop"
                :label="field.label"
              >
                <el-select
                  v-model="formData[field.prop]"
                  :placeholder="field.placeholder || `请选择${field.label}`"
                  :disabled="readonly || field.disabled"
                  :multiple="field.multiple"
                  clearable
                  class="full-width"
                >
                  <el-option
                    v-for="option in field.options"
                    :key="option.value"
                    :label="option.label"
                    :value="option.value"
                    :disabled="option.disabled"
                  />
                </el-select>
                <div
                  v-if="field.description"
                  class="field-description"
                >
                  {{ field.description }}
                </div>
              </el-form-item>

              <!-- Date Field -->
              <el-form-item
                v-else-if="field.type === 'date'"
                :prop="field.prop"
                :label="field.label"
              >
                <el-date-picker
                  v-model="formData[field.prop]"
                  type="date"
                  :placeholder="field.placeholder || `请选择${field.label}`"
                  :format="field.format"
                  :value-format="field.valueFormat || 'YYYY-MM-DD'"
                  :disabled="readonly || field.disabled"
                  class="full-width"
                />
              </el-form-item>

              <!-- Date Range Field -->
              <el-form-item
                v-else-if="field.type === 'dateRange'"
                :prop="field.prop"
                :label="field.label"
              >
                <el-date-picker
                  v-model="formData[field.prop]"
                  type="daterange"
                  range-separator="-"
                  start-placeholder="开始日期"
                  end-placeholder="结束日期"
                  :value-format="field.valueFormat || 'YYYY-MM-DD'"
                  :disabled="readonly || field.disabled"
                  class="full-width"
                />
              </el-form-item>

              <!-- Switch Field -->
              <el-form-item
                v-else-if="field.type === 'switch'"
                :prop="field.prop"
                :label="field.label"
              >
                <el-switch
                  v-model="formData[field.prop]"
                  :disabled="readonly || field.disabled"
                />
                <div
                  v-if="field.description"
                  class="field-description"
                >
                  {{ field.description }}
                </div>
              </el-form-item>

              <!-- Radio Field -->
              <el-form-item
                v-else-if="field.type === 'radio'"
                :prop="field.prop"
                :label="field.label"
              >
                <el-radio-group
                  v-model="formData[field.prop]"
                  :disabled="readonly || field.disabled"
                >
                  <el-radio
                    v-for="option in field.options"
                    :key="option.value"
                    :label="option.value"
                    :disabled="option.disabled"
                  >
                    {{ option.label }}
                  </el-radio>
                </el-radio-group>
                <div
                  v-if="field.description"
                  class="field-description"
                >
                  {{ field.description }}
                </div>
              </el-form-item>

              <!-- Checkbox Field -->
              <el-form-item
                v-else-if="field.type === 'checkbox'"
                :prop="field.prop"
                :label="field.label"
              >
                <el-checkbox-group
                  v-model="formData[field.prop]"
                  :disabled="readonly || field.disabled"
                >
                  <el-checkbox
                    v-for="option in field.options"
                    :key="option.value"
                    :label="option.value"
                    :disabled="option.disabled"
                  >
                    {{ option.label }}
                  </el-checkbox>
                </el-checkbox-group>
                <div
                  v-if="field.description"
                  class="field-description"
                >
                  {{ field.description }}
                </div>
              </el-form-item>

              <!-- Upload Field -->
              <el-form-item
                v-else-if="field.type === 'upload'"
                :prop="field.prop"
                :label="field.label"
              >
                <el-upload
                  v-model:file-list="formData[field.prop]"
                  :action="uploadAction"
                  :accept="field.accept"
                  :limit="field.limit || 1"
                  :disabled="readonly || field.disabled"
                  :on-exceed="handleExceed"
                  list-type="text"
                >
                  <el-button
                    type="primary"
                    :disabled="readonly || field.disabled"
                  >
                    点击上传
                  </el-button>
                </el-upload>
                <div
                  v-if="field.description"
                  class="field-description"
                >
                  {{ field.description }}
                </div>
              </el-form-item>

              <!-- Custom Slot Field -->
              <el-form-item
                v-else-if="field.type === 'slot'"
                :prop="field.prop"
                :label="field.label"
              >
                <slot
                  :name="`field-${field.prop}`"
                  :field="field"
                  :form="formData"
                  :readonly="readonly"
                />
                <div
                  v-if="field.description"
                  class="field-description"
                >
                  {{ field.description }}
                </div>
              </el-form-item>
            </el-col>
          </template>
        </el-row>
      </el-form>
    </div>

    <!-- Form Actions -->
    <div
      v-if="showSubmit || showCancel"
      class="form-actions"
    >
      <el-button
        v-if="showSubmit"
        type="primary"
        :loading="loading"
        @click="handleSubmit"
      >
        {{ submitText }}
      </el-button>
      <el-button
        v-if="showCancel"
        :disabled="loading"
        @click="handleCancel"
      >
        {{ cancelText }}
      </el-button>
      <slot
        name="extra-actions"
        :form="formData"
        :loading="loading"
      />
    </div>
  </div>
</template>

<style scoped lang="scss">
.base-form-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100%;
}

.form-header {
  margin-bottom: 20px;
  padding: 16px 20px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

  .form-title {
    margin: 0;
    font-size: 18px;
    font-weight: 500;
    color: #303133;
  }
}

.form-container {
  padding: 24px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.base-form {
  :deep(.el-form-item__label) {
    font-weight: 400;
  }
}

.field-col {
  margin-bottom: 8px;
}

.field-description {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.full-width {
  width: 100%;
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
  padding: 16px 24px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
</style>
