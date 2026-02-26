<template>
  <el-form
    ref="formRef"
    :model="formModel"
    :label-width="labelWidth"
    :rules="rules"
    class="base-form"
  >
    <el-row :gutter="gutter">
      <template
        v-for="field in fields"
        :key="field.prop"
      >
        <el-col
          v-if="field.visible !== false && field.type !== 'divider'"
          :span="field.span || 12"
        >
          <el-form-item
            :label="field.label"
            :prop="field.prop"
            :rules="field.required ? [{ required: true, message: `${field.label} is required`, trigger: 'change' }] : field.rules"
          >
            <!-- Input -->
            <el-input
              v-if="!field.type || field.type === 'input'"
              v-model="formModel[field.prop]"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              v-bind="field.props"
            />

            <!-- Select -->
            <el-select
              v-else-if="field.type === 'select'"
              v-model="formModel[field.prop]"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              style="width: 100%"
              v-bind="field.props"
            >
              <el-option
                v-for="opt in field.options"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>

            <!-- Number -->
            <el-input-number
              v-else-if="field.type === 'number' || field.type === 'percent'"
              v-model="formModel[field.prop]"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              style="width: 100%"
              v-bind="field.props"
            />

            <!-- Date -->
            <el-date-picker
              v-else-if="field.type === 'date' || field.type === 'datetime' || field.type === 'time'"
              v-model="formModel[field.prop]"
              :type="field.type === 'datetime' ? 'datetime' : (field.type === 'time' ? 'time' : 'date')"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              :value-format="field.type === 'datetime' ? 'YYYY-MM-DD HH:mm:ss' : (field.type === 'time' ? 'HH:mm:ss' : 'YYYY-MM-DD')"
              style="width: 100%"
              v-bind="field.props"
            />

            <!-- Textarea -->
            <el-input
              v-else-if="field.type === 'textarea' || field.type === 'rich_text'"
              v-model="formModel[field.prop]"
              type="textarea"
              :rows="3"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              v-bind="field.props"
            />

            <!-- Switch -->
            <el-switch
              v-else-if="field.type === 'switch'"
              v-model="formModel[field.prop]"
              :disabled="field.disabled"
              v-bind="field.props"
            />

            <!-- Tree Select -->
            <el-tree-select
              v-else-if="field.type === 'tree-select'"
              v-model="formModel[field.prop]"
              :data="field.options"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              check-strictly
              style="width: 100%"
              v-bind="field.props"
            />

            <!-- File / Attachment Field -->
            <FieldRenderer
              v-else-if="field.type === 'file' || field.type === 'attachment'"
              :field="{ code: field.prop, name: field.label, fieldType: field.type, componentProps: field.props || {} }"
              :model-value="formModel[field.prop]"
              @update:model-value="updateField(field.prop, $event)"
            />

            <!-- Image Field -->
            <FieldRenderer
              v-else-if="field.type === 'image'"
              :field="{ code: field.prop, name: field.label, fieldType: 'image', componentProps: field.props || {} }"
              :model-value="formModel[field.prop]"
              @update:model-value="updateField(field.prop, $event)"
            />

            <!-- QR Code Field -->
            <FieldRenderer
              v-else-if="field.type === 'qr_code' || field.type === 'qrcode'"
              :field="{ code: field.prop, name: field.label, fieldType: 'qr_code', componentProps: field.props || {} }"
              :model-value="formModel[field.prop]"
              @update:model-value="updateField(field.prop, $event)"
            />

            <!-- Barcode Field -->
            <FieldRenderer
              v-else-if="field.type === 'barcode'"
              :field="{ code: field.prop, name: field.label, fieldType: 'barcode', componentProps: field.props || {} }"
              :model-value="formModel[field.prop]"
              @update:model-value="updateField(field.prop, $event)"
            />

            <!-- Location Field -->
            <FieldRenderer
              v-else-if="field.type === 'location'"
              :field="{ code: field.prop, name: field.label, fieldType: 'location', componentProps: field.props || {} }"
              :model-value="formModel[field.prop]"
              @update:model-value="updateField(field.prop, $event)"
            />

            <!-- Slot -->
            <slot
              v-else-if="field.type === 'slot'"
              :name="field.prop"
              :model="formModel"
              :field="field"
            />

            <!-- Fallback for unknown field types -->
            <el-input
              v-else
              v-model="formModel[field.prop]"
              :placeholder="field.placeholder || `Enter ${field.label}`"
              :disabled="field.disabled"
            />
          </el-form-item>
        </el-col>
        <!-- Custom handling for Divider to break out of form-item -->
        <el-col
          v-if="field.type === 'divider' && field.visible !== false"
          :span="24"
        >
          <el-divider content-position="left">
            {{ field.label }}
          </el-divider>
        </el-col>
      </template>
    </el-row>
  </el-form>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { FormField } from '@/types/models'
import FieldRenderer from '@/components/engine/FieldRenderer.vue'

interface Props {
  modelValue: Record<string, any>
  fields: FormField[]
  labelWidth?: string
  gutter?: number
  rules?: FormRules
}

const props = withDefaults(defineProps<Props>(), {
  labelWidth: '120px',
  gutter: 20,
  rules: () => ({})
})

const emit = defineEmits(['update:modelValue'])

const formRef = ref<FormInstance>()
const formModel = ref<Record<string, any>>({ ...(props.modelValue || {}) })
let syncingFromProps = false

watch(
  () => props.modelValue,
  (value) => {
    syncingFromProps = true
    formModel.value = { ...(value || {}) }
    syncingFromProps = false
  },
  { deep: true }
)

watch(
  formModel,
  (value) => {
    if (syncingFromProps) return
    emit('update:modelValue', { ...(value || {}) })
  },
  { deep: true }
)

const updateField = (prop: string, value: any) => {
  formModel.value = { ...formModel.value, [prop]: value }
}

const validate = async () => {
  if (!formRef.value) return false
  return await formRef.value.validate()
}

const resetFields = () => {
  formRef.value?.resetFields()
}

const clearValidate = () => {
  formRef.value?.clearValidate()
}

defineExpose({
  validate,
  resetFields,
  clearValidate,
  formModel,
  ref: formRef
})
</script>

<style scoped>
.base-form {
  padding: 10px;
}
</style>
