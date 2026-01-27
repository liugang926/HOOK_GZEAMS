<template>
  <el-form
    ref="formRef"
    :model="modelValue"
    :label-width="labelWidth"
    :rules="rules"
    class="base-form"
  >
    <el-row :gutter="gutter">
      <template v-for="field in fields" :key="field.prop">
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
              v-model="modelValue[field.prop]"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              v-bind="field.props"
            />

            <!-- Select -->
            <el-select
              v-else-if="field.type === 'select'"
              v-model="modelValue[field.prop]"
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
              v-else-if="field.type === 'number'"
              v-model="modelValue[field.prop]"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              style="width: 100%"
              v-bind="field.props"
            />

            <!-- Date -->
            <el-date-picker
              v-else-if="field.type === 'date'"
              v-model="modelValue[field.prop]"
              type="date"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              value-format="YYYY-MM-DD"
              style="width: 100%"
              v-bind="field.props"
            />

            <!-- Textarea -->
            <el-input
              v-else-if="field.type === 'textarea'"
              v-model="modelValue[field.prop]"
              type="textarea"
              :rows="3"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              v-bind="field.props"
            />

            <!-- Switch -->
            <el-switch
              v-else-if="field.type === 'switch'"
              v-model="modelValue[field.prop]"
              :disabled="field.disabled"
              v-bind="field.props"
            />

            <!-- Tree Select -->
             <el-tree-select
              v-else-if="field.type === 'tree-select'"
              v-model="modelValue[field.prop]"
              :data="field.options"
              :placeholder="field.placeholder"
              :disabled="field.disabled"
              check-strictly
              style="width: 100%"
              v-bind="field.props"
            />


            <!-- Slot -->
            <slot
              v-else-if="field.type === 'slot'"
              :name="field.prop"
              :model="modelValue"
              :field="field"
            />
          </el-form-item>
          <!-- Handle Divider without FormItem wrapper if preferred, but FormItem with empty label works too. 
               Actually divider inside form-item looks weird. 
               Let's render it directly if type is divider. -->
        </el-col>
        <!-- Custom handling for Divider to break out of form-item -->
        <el-col 
          v-if="field.type === 'divider' && field.visible !== false" 
          :span="24"
        >
          <el-divider content-position="left">{{ field.label }}</el-divider>
        </el-col>
      </template>
    </el-row>
  </el-form>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import type { FormField } from '@/types/models'

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
  ref: formRef
})
</script>

<style scoped>
.base-form {
  padding: 10px;
}
</style>
