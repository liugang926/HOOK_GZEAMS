<!--
  DynamicFieldRenderer Component

  Renders form fields dynamically based on metadata configuration.
  Supports all field types defined in the low-code system including:
  - Text, Number, Date, Select, Reference, Formula, Sub-table

  This is the core component for metadata-driven UI rendering.

  Usage:
  <DynamicFieldRenderer
    v-model="formData[field.code]"
    :field="field"
    :form-data="formData"
    :readonly="false"
    @change="handleFieldChange"
  />
-->

<script setup lang="ts">
/**
 * DynamicFieldRenderer Component
 *
 * Dynamically renders form fields based on FieldDefinition metadata.
 * This enables the low-code capability where UI is driven by metadata.
 */

import { computed, watch, ref } from 'vue'
import { formatDate } from '@/utils/dateFormat'
import { formatCurrency } from '@/utils/numberFormat'
import type { FieldConfig } from '@/types/common'
import { assetApi, categoryApi, locationApi } from '@/api/assets'
import { userApi } from '@/api/users'
import { orgApi, deptApi } from '@/api/organizations'

// ============================================================================
// Types
// ============================================================================

interface Props {
  /** Field metadata configuration */
  field: FieldConfig
  /** Current field value (v-model) */
  modelValue: any
  /** Entire form data (for formula calculation) */
  formData?: Record<string, any>
  /** Read-only mode */
  readonly?: boolean
  /** Field-level permissions (read/write/hidden) */
  permission?: 'read' | 'write' | 'hidden'
  /** Disable the field */
  disabled?: boolean
  /** Form size */
  size?: 'large' | 'default' | 'small'
}

interface Emits {
  (e: 'update:modelValue', value: any): void
  (e: 'change', value: any, field: FieldConfig): void
  (e: 'blur', value: any): void
  (e: 'focus', value: any): void
}

// ============================================================================
// Props & Emits
// ============================================================================

const props = withDefaults(defineProps<Props>(), {
  formData: () => ({}),
  readonly: false,
  permission: 'write',
  disabled: false,
  size: 'default'
})

const emit = defineEmits<Emits>()

// ============================================================================
// State
// ============================================================================

/** Loading state for async options */
const loading = ref(false)

/** Options for select/reference fields */
const options = ref<Array<{ label: string; value: any }>>([])

/** Display text for reference fields */
const displayText = ref('')

// ============================================================================
// Computed
// ============================================================================

/** Whether field is visible */
const isVisible = computed(() => {
  return props.permission !== 'hidden' && !props.field.hidden
})

/** Whether field is readonly */
const isReadonly = computed(() => {
  return props.readonly || props.permission === 'read' || props.field.readonly
})

/** Whether field is disabled */
const isDisabled = computed(() => {
  return props.disabled || isReadonly.value
})

/** Field placeholder */
const placeholder = computed(() => {
  return props.field.placeholder || `请选择${props.field.label}`
})

/** Whether to show clear button */
const clearable = computed(() => {
  return props.field.clearable !== false && !isReadonly.value
})

// ============================================================================
// Methods
// ============================================================================

/**
 * Handle value change
 */
const handleChange = (value: any) => {
  emit('update:modelValue', value)
  emit('change', value, props.field)
}

/**
 * Handle blur event
 */
const handleBlur = () => {
  emit('blur', props.modelValue)
}

/**
 * Handle focus event
 */
const handleFocus = () => {
  emit('focus', props.modelValue)
}

/**
 * Load options for select/reference fields
 */
const loadOptions = async () => {
  const field = props.field

  // Static options
  if (field.options && field.options.length > 0) {
    options.value = field.options
    return
  }

  // Dynamic options from API
  if (field.optionApi) {
    loading.value = true
    try {
      const response = await fetch(field.optionApi)
      const data = await response.json()
      options.value = data.results || data
    } catch (error) {
      options.value = []
    } finally {
      loading.value = false
    }
    return
  }

  // Built-in reference types
  if (field.referenceType) {
    await loadReferenceOptions(field.referenceType)
  }
}

/**
 * Load reference options by type
 */
const loadReferenceOptions = async (type: string) => {
  loading.value = true
  try {
    switch (type) {
      case 'AssetCategory':
        const categories = await categoryApi.list()
        options.value = categories.map((cat: any) => ({
          label: cat.name,
          value: cat.id,
          data: cat
        }))
        break

      case 'Location':
        const locations = await locationApi.list()
        options.value = locations.map((loc: any) => ({
          label: loc.name,
          value: loc.id,
          data: loc
        }))
        break

      case 'User':
        const users = await userApi.list({ pageSize: 1000 })
        options.value = users.results.map((user: any) => ({
          label: `${user.firstName} ${user.lastName}`.trim(),
          value: user.id,
          data: user
        }))
        break

      case 'Organization':
        const orgs = await orgApi.list()
        options.value = orgs.map((org: any) => ({
          label: org.name,
          value: org.id,
          data: org
        }))
        break

      case 'Department':
        const depts = await deptApi.list()
        options.value = depts.map((dept: any) => ({
          label: dept.name,
          value: dept.id,
          data: dept
        }))
        break

      default:
        options.value = []
    }
  } catch (error) {
    options.value = []
  } finally {
    loading.value = false
  }
}

/**
 * Load display text for reference value
 */
const loadDisplayText = async () => {
  if (!props.modelValue || !props.field.referenceType) {
    displayText.value = props.modelValue || ''
    return
  }

  try {
    switch (props.field.referenceType) {
      case 'Asset':
        const asset = await assetApi.get(props.modelValue)
        displayText.value = `${asset.code} - ${asset.name}`
        break

      case 'AssetCategory':
        const category = await categoryApi.get(props.modelValue)
        displayText.value = category.name
        break

      case 'Location':
        const location = await locationApi.get(props.modelValue)
        displayText.value = location.name
        break

      case 'User':
        const user = await userApi.get(props.modelValue)
        displayText.value = `${user.firstName} ${user.lastName}`.trim()
        break

      default:
        displayText.value = props.modelValue
    }
  } catch (error) {
    displayText.value = props.modelValue
  }
}

// ============================================================================
// Watch
// ============================================================================

// Load options when field changes
watch(() => props.field, loadOptions, { immediate: true })

// Load display text for reference fields
watch(() => props.modelValue, loadDisplayText, { immediate: true })

// ============================================================================
// Expose
// ============================================================================

defineExpose({
  loadOptions,
  options,
  displayText
})
</script>

<template>
  <div
    v-if="isVisible"
    class="dynamic-field-renderer"
  >
    <!-- Text Input -->
    <template v-if="field.type === 'text' || field.type === 'string'">
      <el-input
        :model-value="modelValue"
        :placeholder="placeholder"
        :disabled="isDisabled"
        :clearable="clearable"
        :size="size"
        :maxlength="field.maxLength"
        :show-word-limit="field.showWordLimit"
        @update:model-value="handleChange"
        @blur="handleBlur"
        @focus="handleFocus"
      />
    </template>

    <!-- Textarea -->
    <template v-else-if="field.type === 'textarea'">
      <el-input
        :model-value="modelValue"
        type="textarea"
        :rows="field.rows || 4"
        :placeholder="placeholder"
        :disabled="isDisabled"
        :size="size"
        :maxlength="field.maxLength"
        :show-word-limit="field.showWordLimit"
        @update:model-value="handleChange"
        @blur="handleBlur"
        @focus="handleFocus"
      />
    </template>

    <!-- Number Input -->
    <template v-else-if="field.type === 'number'">
      <el-input-number
        :model-value="modelValue"
        :placeholder="placeholder"
        :disabled="isDisabled"
        :size="size"
        :min="field.min"
        :max="field.max"
        :step="field.step || 1"
        :precision="field.precision"
        :controls-position="field.controlsPosition || 'right'"
        class="full-width-number"
        @update:model-value="handleChange"
        @blur="handleBlur"
        @focus="handleFocus"
      />
    </template>

    <!-- Currency Input -->
    <template v-else-if="field.type === 'currency'">
      <el-input
        :model-value="modelValue"
        :placeholder="placeholder"
        :disabled="isDisabled"
        :clearable="clearable"
        :size="size"
      >
        <template #prefix>
          <span>{{ field.currencySymbol || '¥' }}</span>
        </template>
        @update:model-value="handleChange"
      </el-input>
    </template>

    <!-- Date Picker -->
    <template v-else-if="field.type === 'date'">
      <el-date-picker
        :model-value="modelValue"
        type="date"
        :placeholder="placeholder"
        :disabled="isDisabled"
        :clearable="clearable"
        :size="size"
        :format="field.format || 'YYYY-MM-DD'"
        :value-format="field.valueFormat || 'YYYY-MM-DD'"
        class="full-width-picker"
        @update:model-value="handleChange"
      />
    </template>

    <!-- Date Range Picker -->
    <template v-else-if="field.type === 'dateRange'">
      <el-date-picker
        :model-value="modelValue"
        type="daterange"
        range-separator="-"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        :disabled="isDisabled"
        :clearable="clearable"
        :size="size"
        :format="field.format || 'YYYY-MM-DD'"
        :value-format="field.valueFormat || 'YYYY-MM-DD'"
        class="full-width-picker"
        @update:model-value="handleChange"
      />
    </template>

    <!-- DateTime Picker -->
    <template v-else-if="field.type === 'dateTime'">
      <el-date-picker
        :model-value="modelValue"
        type="datetime"
        :placeholder="placeholder"
        :disabled="isDisabled"
        :clearable="clearable"
        :size="size"
        :format="field.format || 'YYYY-MM-DD HH:mm:ss'"
        :value-format="field.valueFormat || 'YYYY-MM-DD HH:mm:ss'"
        class="full-width-picker"
        @update:model-value="handleChange"
      />
    </template>

    <!-- Select -->
    <template v-else-if="field.type === 'select'">
      <el-select
        :model-value="modelValue"
        :placeholder="placeholder"
        :disabled="isDisabled"
        :clearable="clearable"
        :size="size"
        :multiple="field.multiple"
        :filterable="field.filterable !== false"
        :loading="loading"
        class="full-width-select"
        @update:model-value="handleChange"
      >
        <el-option
          v-for="option in options"
          :key="option.value"
          :label="option.label"
          :value="option.value"
          :disabled="option.disabled"
        />
      </el-select>
    </template>

    <!-- Radio Group -->
    <template v-else-if="field.type === 'radio'">
      <el-radio-group
        :model-value="modelValue"
        :disabled="isDisabled"
        :size="size"
        @update:model-value="handleChange"
      >
        <el-radio
          v-for="option in options"
          :key="option.value"
          :label="option.value"
          :disabled="option.disabled"
        >
          {{ option.label }}
        </el-radio>
      </el-radio-group>
    </template>

    <!-- Checkbox Group -->
    <template v-else-if="field.type === 'checkbox'">
      <el-checkbox-group
        :model-value="modelValue"
        :disabled="isDisabled"
        :size="size"
        @update:model-value="handleChange"
      >
        <el-checkbox
          v-for="option in options"
          :key="option.value"
          :label="option.value"
          :disabled="option.disabled"
        >
          {{ option.label }}
        </el-checkbox>
      </el-checkbox-group>
    </template>

    <!-- Switch -->
    <template v-else-if="field.type === 'switch' || field.type === 'boolean'">
      <el-switch
        :model-value="modelValue"
        :disabled="isDisabled"
        @update:model-value="handleChange"
      />
    </template>

    <!-- Slider -->
    <template v-else-if="field.type === 'slider'">
      <div class="slider-container">
        <el-slider
          :model-value="modelValue"
          :disabled="isDisabled"
          :min="field.min || 0"
          :max="field.max || 100"
          :step="field.step || 1"
          :show-tooltip="field.showTooltip !== false"
          @update:model-value="handleChange"
        />
        <span
          v-if="field.showValue !== false"
          class="slider-value"
        >
          {{ modelValue }}
        </span>
      </div>
    </template>

    <!-- Rate -->
    <template v-else-if="field.type === 'rate'">
      <el-rate
        :model-value="modelValue"
        :disabled="isDisabled"
        :max="field.max || 5"
        :allow-half="field.allowHalf"
        @update:model-value="handleChange"
      />
    </template>

    <!-- Color Picker -->
    <template v-else-if="field.type === 'color'">
      <el-color-picker
        :model-value="modelValue"
        :disabled="isDisabled"
        :show-alpha="field.showAlpha"
        @update:model-value="handleChange"
      />
    </template>

    <!-- Upload -->
    <template v-else-if="field.type === 'upload' || field.type === 'file'">
      <el-upload
        :file-list="modelValue || []"
        :action="field.uploadAction || '/api/upload/'"
        :disabled="isDisabled"
        :accept="field.accept"
        :limit="field.limit || 1"
        :multiple="field.multiple"
        :list-type="field.listType || 'picture-card'"
        :on-preview="field.onPreview"
        :on-remove="field.onRemove"
        :on-success="field.onSuccess"
        :before-upload="field.beforeUpload"
        @update:model-value="handleChange"
      >
        <el-icon v-if="!field.limit || (modelValue?.length || 0) < field.limit">
          <Plus />
        </el-icon>
      </el-upload>
    </template>

    <!-- Image Upload -->
    <template v-else-if="field.type === 'image'">
      <image-upload
        :model-value="modelValue"
        :disabled="isDisabled"
        :limit="field.limit || 1"
        :max-size="field.maxSize || 5"
        @update:model-value="handleChange"
      />
    </template>

    <!-- Reference Picker -->
    <template v-else-if="field.type === 'reference'">
      <reference-picker
        :model-value="modelValue"
        :reference-type="field.referenceType"
        :disabled="isDisabled"
        :multiple="field.multiple"
        :display-text="displayText"
        @update:model-value="handleChange"
      />
    </template>

    <!-- User Picker -->
    <template v-else-if="field.type === 'userPicker'">
      <user-picker
        :model-value="modelValue"
        :disabled="isDisabled"
        :multiple="field.multiple"
        :placeholder="placeholder"
        @update:model-value="handleChange"
      />
    </template>

    <!-- Department Picker -->
    <template v-else-if="field.type === 'deptPicker'">
      <dept-picker
        :model-value="modelValue"
        :disabled="isDisabled"
        :placeholder="placeholder"
        @update:model-value="handleChange"
      />
    </template>

    <!-- Rich Text Editor -->
    <template v-else-if="field.type === 'richtext'">
      <rich-text-editor
        :model-value="modelValue"
        :disabled="isDisabled"
        :placeholder="placeholder"
        @update:model-value="handleChange"
      />
    </template>

    <!-- Code Editor -->
    <template v-else-if="field.type === 'code'">
      <code-editor
        :model-value="modelValue"
        :language="field.language || 'javascript'"
        :disabled="isDisabled"
        :height="field.height || 200"
        @update:model-value="handleChange"
      />
    </template>

    <!-- Formula Display (Read-only) -->
    <template v-else-if="field.type === 'formula'">
      <div class="formula-display">
        <template v-if="field.formulaExpression">
          <span
            v-if="field.prefix"
            class="formula-prefix"
          >{{ field.prefix }}</span>
          <span class="formula-value">{{ formatDisplayValue }}</span>
          <span
            v-if="field.suffix"
            class="formula-suffix"
          >{{ field.suffix }}</span>
        </template>
        <span
          v-else
          class="formula-placeholder"
        >-</span>
      </div>
    </template>

    <!-- Sub-table -->
    <template v-else-if="field.type === 'subtable'">
      <sub-table
        :model-value="modelValue"
        :columns="field.subTableColumns || []"
        :disabled="isDisabled"
        :form-data="formData"
        @update:model-value="handleChange"
      />
    </template>

    <!-- Custom Slot -->
    <template v-else-if="field.type === 'slot'">
      <slot
        :name="`field-${field.code}`"
        :field="field"
        :value="modelValue"
        :form-data="formData"
        :disabled="isDisabled"
        :on-change="handleChange"
      />
    </template>

    <!-- Default: Text Input -->
    <template v-else>
      <el-input
        :model-value="modelValue"
        :placeholder="placeholder"
        :disabled="isDisabled"
        :clearable="clearable"
        :size="size"
        @update:model-value="handleChange"
      />
    </template>

    <!-- Field Description -->
    <div
      v-if="field.description"
      class="field-description"
    >
      {{ field.description }}
    </div>
  </div>
</template>

<style scoped lang="scss">
.dynamic-field-renderer {
  width: 100%;

  .full-width-number,
  .full-width-picker,
  .full-width-select {
    width: 100%;
  }

  .slider-container {
    display: flex;
    align-items: center;
    gap: 16px;
    flex: 1;

    .slider-value {
      min-width: 60px;
      text-align: right;
      font-variant-numeric: tabular-nums;
    }
  }

  .formula-display {
    display: flex;
    align-items: baseline;
    padding: 8px 12px;
    background-color: #f5f7fa;
    border-radius: 4px;

    .formula-prefix,
    .formula-suffix {
      color: #909399;
      font-size: 14px;
    }

    .formula-value {
      margin: 0 4px;
      font-size: 16px;
      font-weight: 500;
      color: #303133;
      font-variant-numeric: tabular-nums;
    }

    .formula-placeholder {
      color: #c0c4cc;
    }
  }

  .field-description {
    margin-top: 4px;
    font-size: 12px;
    color: #909399;
    line-height: 1.5;
  }
}
</style>
