<!--
  DynamicForm Component

  A metadata-driven form component that renders form layouts
  based on BusinessObject and PageLayout metadata.

  Key features:
  - Automatic form generation from metadata
  - Real-time formula calculation
  - Field dependency handling
  - Master-detail table support
  - Validation based on field rules

  Usage:
  <DynamicForm
    v-model="formData"
    :business-object="assetMetadata"
    :layout="formLayout"
    :readonly="false"
    @submit="handleSubmit"
  />
-->

<script setup lang="ts">
/**
 * DynamicForm Component
 *
 * The core component for metadata-driven form rendering.
 * Parses PageLayout metadata and dynamically generates the form UI.
 */

import { ref, computed, watch, provide, inject } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { evaluateFormula, buildDependencies } from '@/utils/formula'
import type { FieldConfig, FormSection } from '@/types/common'
import DynamicFieldRenderer from './DynamicFieldRenderer.vue'

// ============================================================================
// Types
// ============================================================================

export interface DynamicFormProps {
  /** Form data (v-model) */
  modelValue: Record<string, any>
  /** Field metadata definitions */
  fields: FieldConfig[]
  /** Form layout sections */
  sections?: FormSection[]
  /** Validation rules */
  rules?: FormRules
  /** Read-only mode */
  readonly?: boolean
  /** Form layout direction */
  layout?: 'horizontal' | 'vertical' | 'inline'
  /** Label width */
  labelWidth?: string | number
  /** Label position */
  labelPosition?: 'left' | 'right' | 'top'
  /** Column span for fields (1-24) */
  columnSpan?: number
  /** Show submit button */
  showSubmit?: boolean
  /** Show cancel button */
  showCancel?: boolean
  /** Submit loading state */
  loading?: boolean
  /** Submit button text */
  submitText?: string
  /** Cancel button text */
  cancelText?: string
  /** Field-level permissions (fieldCode -> permission) */
  fieldPermissions?: Record<string, 'read' | 'write' | 'hidden'>
  /** Enable formula calculation */
  enableFormula?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: Record<string, any>): void
  (e: 'submit', data: Record<string, any>): void
  (e: 'cancel'): void
  (e: 'field-change', fieldCode: string, value: any, data: Record<string, any>): void
}

// ============================================================================
// Props & Emits
// ============================================================================

const props = withDefaults(defineProps<DynamicFormProps>(), {
  sections: () => [],
  layout: 'horizontal',
  labelWidth: '120px',
  labelPosition: 'right',
  columnSpan: 12,
  showSubmit: true,
  showCancel: true,
  submitText: '提交',
  cancelText: '取消',
  fieldPermissions: () => ({}),
  enableFormula: true
})

const emit = defineEmits<Emits>()

// ============================================================================
// State
// ============================================================================

const formRef = ref<FormInstance>()
const formData = ref<Record<string, any>>({})
const fieldRefs = ref<Record<string, InstanceType<typeof DynamicFieldRenderer>>>({})

// Formula calculation state
const dependencyGraph = computed(() => {
  if (!props.enableFormula) return {}
  return buildDependencies(props.fields)
})

// ============================================================================
// Computed
// ============================================================================

/** Visible sections */
const visibleSections = computed(() => {
  if (props.sections.length === 0) {
    // Auto-generate single section from fields
    return [{
      title: '',
      fields: props.fields.filter(f => !isFieldHidden(f))
    }]
  }
  return props.sections.map(section => ({
    ...section,
    fields: section.fields.filter(fieldCode => {
      const field = props.fields.find(f => f.code === fieldCode)
      return field && !isFieldHidden(field)
    }).map(fieldCode => props.fields.find(f => f.code === fieldCode))
  })).filter(section => section.fields.length > 0)
})

/** Check if field should be hidden */
const isFieldHidden = (field: FieldConfig): boolean => {
  const permission = props.fieldPermissions[field.code]
  if (permission === 'hidden') return true
  if (field.hidden) {
    // Check conditional visibility
    if (field.visibleWhen && formData.value) {
      const { field: depField, value: depValue } = field.visibleWhen
      return formData.value[depField] !== depValue
    }
    return true
  }
  return false
}

/** Get field permission */
const getFieldPermission = (fieldCode: string): 'read' | 'write' | 'hidden' => {
  return props.fieldPermissions[fieldCode] || 'write'
}

/** Check if field is readonly */
const isFieldReadonly = (field: FieldConfig): boolean => {
  if (props.readonly) return true
  if (getFieldPermission(field.code) === 'read') return true
  if (field.readonly) return true
  return false
}

// ============================================================================
// Methods
// ============================================================================

/**
 * Initialize form data with default values
 */
const initFormData = () => {
  const data: Record<string, any> = {}

  props.fields.forEach(field => {
    if (props.modelValue[field.code] !== undefined) {
      data[field.code] = props.modelValue[field.code]
    } else if (field.defaultValue !== undefined) {
      data[field.code] = field.defaultValue
    } else if (field.type === 'boolean' || field.type === 'switch') {
      data[field.code] = false
    } else if (field.type === 'checkbox') {
      data[field.code] = []
    } else if (field.type === 'number') {
      data[field.code] = field.min !== undefined ? field.min : 0
    } else {
      data[field.code] = undefined
    }
  })

  formData.value = data
}

/**
 * Calculate formula fields
 */
const calculateFormulas = (triggerField?: string) => {
  if (!props.enableFormula) return

  const fieldsToCalculate = triggerField
    ? (dependencyGraph.value[triggerField] || [])
    : props.fields.filter(f => f.type === 'formula')

  fieldsToCalculate.forEach((field: FieldConfig) => {
    if (field.type === 'formula' && field.formulaExpression) {
      try {
        const result = evaluateFormula(field.formulaExpression, formData.value)
        formData.value[field.code] = result
      } catch (error) {
        console.warn(`Formula calculation failed for ${field.code}:`, error)
      }
    }
  })
}

/**
 * Handle field value change
 */
const handleFieldChange = (fieldCode: string, value: any) => {
  formData.value[fieldCode] = value

  // Trigger dependent formula calculations
  calculateFormulas(fieldCode)

  // Emit change event
  emit('field-change', fieldCode, value, formData.value)
}

/**
 * Validate form
 */
const validate = async () => {
  return await formRef.value?.validate()
}

/**
 * Validate specific field
 */
const validateField = async (fieldCode: string) => {
  return await formRef.value?.validateField(fieldCode)
}

/**
 * Clear form validation
 */
const clearValidation = () => {
  formRef.value?.clearValidate()
}

/**
 * Reset form to initial state
 */
const resetForm = () => {
  formRef.value?.resetFields()
  initFormData()
  calculateFormulas()
}

/**
 * Set field value
 */
const setFieldValue = (fieldCode: string, value: any) => {
  formData.value[fieldCode] = value
  calculateFormulas(fieldCode)
}

/**
 * Get field value
 */
const getFieldValue = (fieldCode: string) => {
  return formData.value[fieldCode]
}

/**
 * Handle form submit
 */
const handleSubmit = async () => {
  try {
    await validate()
    emit('submit', { ...formData.value })
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

// ============================================================================
// Watch
// ============================================================================

// Watch for external model value changes
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    Object.keys(newVal).forEach(key => {
      formData.value[key] = newVal[key]
    })
  }
}, { deep: true })

// Watch form data changes and emit update
watch(formData, (newVal) => {
  emit('update:modelValue', { ...newVal })
}, { deep: true })

// Watch fields changes to recalculate formulas
watch(() => props.fields, () => {
  calculateFormulas()
}, { deep: true })

// ============================================================================
// Lifecycle
// ============================================================================

initFormData()
calculateFormulas()

// ============================================================================
// Provide formula context for nested components
// ============================================================================

provide('formData', formData)
provide('setFieldValue', setFieldValue)
provide('getFieldValue', getFieldValue)

// ============================================================================
// Expose public methods
// ============================================================================

defineExpose({
  formRef,
  validate,
  validateField,
  clearValidation,
  resetForm,
  setFieldValue,
  getFieldValue,
  calculateFormulas
})
</script>

<template>
  <div class="dynamic-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      :label-width="labelWidth"
      :label-position="labelPosition"
      :disabled="loading"
      class="form-container"
    >
      <el-row :gutter="20">
        <template v-for="section in visibleSections" :key="section.title || 'default'">
          <!-- Section with title -->
          <el-col v-if="section.title" :span="24" class="form-section">
            <div class="section-header">
              <el-icon v-if="section.icon" class="section-icon">
                <component :is="section.icon" />
              </el-icon>
              <h4 class="section-title">{{ section.title }}</h4>
              <span v-if="section.description" class="section-description">
                {{ section.description }}
              </span>
            </div>
          </el-col>

          <!-- Section fields -->
          <template v-for="field in section.fields" :key="field.code">
            <el-col
              v-if="field && !isFieldHidden(field)"
              :span="field.span || columnSpan"
              class="field-col"
            >
              <el-form-item
                :prop="field.code"
                :label="field.label"
                :required="field.required"
              >
                <!-- Dynamic field renderer -->
                <DynamicFieldRenderer
                  :ref="(el: any) => { if (el) fieldRefs[field.code] = el }"
                  :model-value="formData[field.code]"
                  :field="field"
                  :form-data="formData"
                  :readonly="isFieldReadonly(field)"
                  :permission="getFieldPermission(field.code)"
                  @update:model-value="(v: any) => handleFieldChange(field.code, v)"
                  @change="(v: any) => handleFieldChange(field.code, v)"
                  @blur="validateField(field.code)"
                />
              </el-form-item>
            </el-col>
          </template>
        </template>
      </el-row>
    </el-form>

    <!-- Form Actions -->
    <div v-if="showSubmit || showCancel || $slots.actions" class="form-actions">
      <slot name="actions" :form="formData" :loading="loading">
        <el-button
          v-if="showCancel"
          @click="handleCancel"
        >
          {{ cancelText }}
        </el-button>
        <el-button
          v-if="showSubmit"
          type="primary"
          :loading="loading"
          @click="handleSubmit"
        >
          {{ submitText }}
        </el-button>
      </slot>
    </div>

    <!-- Formula fields are hidden but included in form data -->
    <template v-for="field in fields.filter(f => f.type === 'formula')" :key="`formula-${field.code}`">
      <input
        v-model="formData[field.code]"
        type="hidden"
        :name="field.code"
      >
    </template>
  </div>
</template>

<style scoped lang="scss">
.dynamic-form {
  .form-container {
    :deep(.el-form-item__label) {
      font-weight: 400;
    }

    :deep(.el-form-item) {
      margin-bottom: 18px;
    }
  }

  .form-section {
    margin-bottom: 16px;
    padding-bottom: 8px;

    .section-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 16px;
      background-color: #f5f7fa;
      border-radius: 4px;
      border-left: 3px solid #409eff;

      .section-icon {
        font-size: 18px;
        color: #409eff;
      }

      .section-title {
        margin: 0;
        font-size: 15px;
        font-weight: 500;
        color: #303133;
      }

      .section-description {
        margin-left: 12px;
        font-size: 13px;
        color: #909399;
      }
    }
  }

  .field-col {
    margin-bottom: 8px;
  }

  .form-actions {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid #ebeef5;
  }
}

// Mobile responsive
@media (max-width: 768px) {
  .dynamic-form {
    :deep(.el-col) {
      span: 24 !important;
    }

    .form-actions {
      flex-direction: column-reverse;

      button {
        width: 100%;
      }
    }
  }
}
</style>
