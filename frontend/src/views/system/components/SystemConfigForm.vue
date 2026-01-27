<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? 'Edit Configuration' : 'Add Configuration'"
    width="600px"
    @update:model-value="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="140px"
    >
      <el-form-item
        label="Config Key"
        prop="config_key"
      >
        <el-input
          v-model="formData.config_key"
          placeholder="e.g., QR_CODE_TEMPLATE, ENABLE_EMAIL"
          :disabled="isEdit"
        />
        <div class="form-tip">
          Unique identifier for the configuration (uppercase recommended)
        </div>
      </el-form-item>

      <el-form-item
        label="Display Name"
        prop="name"
      >
        <el-input
          v-model="formData.name"
          placeholder="e.g., QR Code Template, Enable Email Notifications"
        />
      </el-form-item>

      <el-form-item
        label="Value Type"
        prop="value_type"
      >
        <el-select
          v-model="formData.value_type"
          placeholder="Select value type"
          :disabled="isEdit"
          @change="handleValueTypeChange"
        >
          <el-option
            label="String"
            value="string"
          />
          <el-option
            label="Integer"
            value="integer"
          />
          <el-option
            label="Float"
            value="float"
          />
          <el-option
            label="Boolean"
            value="boolean"
          />
          <el-option
            label="JSON"
            value="json"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        label="Value"
        prop="config_value"
      >
        <!-- Boolean: switch -->
        <el-switch
          v-if="formData.value_type === 'boolean'"
          v-model="booleanValue"
          active-text="Enabled"
          inactive-text="Disabled"
        />
        <!-- String/Integer/Float: input -->
        <el-input
          v-else-if="['string', 'integer', 'float'].includes(formData.value_type)"
          v-model="formData.config_value"
          :type="formData.value_type === 'string' ? 'text' : 'number'"
          :placeholder="getValuePlaceholder(formData.value_type)"
        />
        <!-- JSON: textarea with validation -->
        <el-input
          v-else-if="formData.value_type === 'json'"
          v-model="formData.config_value"
          type="textarea"
          :rows="4"
          placeholder="e.g., {&quot;key&quot;: &quot;value&quot;}"
          @blur="validateJson"
        />
        <div
          v-if="jsonError"
          class="form-tip error"
        >
          {{ jsonError }}
        </div>
      </el-form-item>

      <el-form-item
        label="Category"
        prop="category"
      >
        <el-select
          v-model="formData.category"
          placeholder="Select category"
          allow-create
          filterable
        >
          <el-option
            label="General"
            value="general"
          />
          <el-option
            label="QR Code"
            value="qrcode"
          />
          <el-option
            label="Notification"
            value="notification"
          />
          <el-option
            label="Asset"
            value="asset"
          />
          <el-option
            label="Inventory"
            value="inventory"
          />
          <el-option
            label="Finance"
            value="finance"
          />
          <el-option
            label="Workflow"
            value="workflow"
          />
          <el-option
            label="Integration"
            value="integration"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        label="Description"
        prop="description"
      >
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="2"
          placeholder="Describe what this configuration does"
        />
      </el-form-item>

      <el-form-item
        label="Is System"
        prop="is_system"
      >
        <el-switch
          v-model="formData.is_system"
          active-text="System Config"
          inactive-text="User Config"
        />
        <div class="form-tip">
          System configs cannot be deleted by users
        </div>
      </el-form-item>

      <el-form-item
        label="Is Encrypted"
        prop="is_encrypted"
      >
        <el-switch
          v-model="formData.is_encrypted"
          active-text="Encrypted"
          inactive-text="Plain Text"
        />
        <div class="form-tip">
          Encrypt value for sensitive data (passwords, API keys)
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">
        Cancel
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ isEdit ? 'Save' : 'Add' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import type { SystemConfig } from '@/api/system'
import { systemConfigApi } from '@/api/system'

interface Props {
  visible: boolean
  data?: SystemConfig | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const jsonError = ref('')

const isEdit = computed(() => !!props.data?.id)

const formData = ref({
  config_key: '',
  config_value: '',
  value_type: 'string' as 'string' | 'integer' | 'float' | 'boolean' | 'json',
  name: '',
  description: '',
  category: '',
  is_system: false,
  is_encrypted: false
})

// Boolean value computed property
const booleanValue = computed({
  get: () => formData.value.config_value === 'true',
  set: (val) => {
    formData.value.config_value = val ? 'true' : 'false'
  }
})

const rules: FormRules = {
  config_key: [
    { required: true, message: 'Please enter config key', trigger: 'blur' },
    {
      pattern: /^[A-Z_][A-Z0-9_]*$/,
      message: 'Key must be uppercase letters, numbers, and underscores only',
      trigger: 'blur'
    }
  ],
  name: [
    { required: true, message: 'Please enter display name', trigger: 'blur' }
  ],
  value_type: [
    { required: true, message: 'Please select value type', trigger: 'change' }
  ],
  config_value: [
    { required: true, message: 'Please enter config value', trigger: 'blur' }
  ]
}

const getValuePlaceholder = (type: string) => {
  const placeholders: Record<string, string> = {
    string: 'Enter text value',
    integer: 'Enter integer value',
    float: 'Enter decimal value'
  }
  return placeholders[type] || 'Enter value'
}

const validateJson = () => {
  if (formData.value.value_type === 'json' && formData.value.config_value) {
    try {
      JSON.parse(formData.value.config_value)
      jsonError.value = ''
      return true
    } catch {
      jsonError.value = 'Invalid JSON format'
      return false
    }
  }
  jsonError.value = ''
  return true
}

const handleValueTypeChange = () => {
  // Reset value when type changes
  if (formData.value.value_type === 'boolean') {
    formData.value.config_value = 'false'
  } else if (formData.value.value_type === 'json') {
    formData.value.config_value = '{}'
  } else {
    formData.value.config_value = ''
  }
}

watch(() => props.visible, (val) => {
  if (val && props.data) {
    Object.assign(formData.value, {
      config_key: props.data.config_key || '',
      config_value: props.data.config_value || '',
      value_type: props.data.value_type || 'string',
      name: props.data.name || '',
      description: props.data.description || '',
      category: props.data.category || '',
      is_system: props.data.is_system || false,
      is_encrypted: props.data.is_encrypted || false
    })
  } else if (val) {
    resetForm()
  }
  jsonError.value = ''
})

const resetForm = () => {
  formData.value = {
    config_key: '',
    config_value: '',
    value_type: 'string',
    name: '',
    description: '',
    category: '',
    is_system: false,
    is_encrypted: false
  }
  formRef.value?.clearValidate()
  jsonError.value = ''
}

const handleClose = () => {
  emit('update:visible', false)
}

const handleSubmit = async () => {
  if (!formRef.value) return

  // Validate JSON for JSON type
  if (formData.value.value_type === 'json' && !validateJson()) {
    return
  }

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value) {
        await systemConfigApi.update(props.data!.id, formData.value)
      } else {
        await systemConfigApi.create(formData.value)
      }
      ElMessage.success(isEdit.value ? 'Updated successfully' : 'Added successfully')
      emit('success')
      handleClose()
    } catch (error) {
      ElMessage.error('Operation failed')
    } finally {
      submitting.value = false
    }
  })
}
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.form-tip.error {
  color: #f56c6c;
}
</style>
