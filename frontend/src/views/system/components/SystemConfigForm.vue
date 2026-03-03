<template>
  <el-dialog
    :model-value="visible"
    :title="isEdit ? t('system.config.form.titles.edit') : t('system.config.form.titles.create')"
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
        :label="t('system.config.form.labels.configKey')"
        prop="config_key"
      >
        <el-input
          v-model="formData.config_key"
          :placeholder="t('system.config.form.placeholders.configKey')"
          :disabled="isEdit"
        />
        <div class="form-tip">
          {{ t('system.config.form.tips.configKey') }}
        </div>
      </el-form-item>

      <el-form-item
        :label="t('system.config.form.labels.displayName')"
        prop="name"
      >
        <el-input
          v-model="formData.name"
          :placeholder="t('system.config.form.placeholders.displayName')"
        />
      </el-form-item>

      <el-form-item
        :label="t('system.config.form.labels.valueType')"
        prop="value_type"
      >
        <el-select
          v-model="formData.value_type"
          :placeholder="t('system.config.form.placeholders.valueType')"
          :disabled="isEdit"
          @change="handleValueTypeChange"
        >
          <el-option
            v-for="item in valueTypeOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        :label="t('system.config.form.labels.value')"
        prop="config_value"
      >
        <!-- Boolean: switch -->
        <el-switch
          v-if="formData.value_type === 'boolean'"
          v-model="booleanValue"
          :active-text="t('system.config.status.enabled')"
          :inactive-text="t('system.config.status.disabled')"
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
          :placeholder="t('system.config.form.placeholders.jsonValue')"
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
        :label="t('system.config.form.labels.category')"
        prop="category"
      >
        <el-select
          v-model="formData.category"
          :placeholder="t('system.config.form.placeholders.category')"
          allow-create
          filterable
        >
          <el-option
            v-for="item in categoryOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        :label="t('system.config.form.labels.description')"
        prop="description"
      >
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="2"
          :placeholder="t('system.config.form.placeholders.description')"
        />
      </el-form-item>

      <el-form-item
        :label="t('system.config.form.labels.isSystem')"
        prop="is_system"
      >
        <el-switch
          v-model="formData.is_system"
          :active-text="t('system.config.form.switches.systemConfig')"
          :inactive-text="t('system.config.form.switches.userConfig')"
        />
        <div class="form-tip">
          {{ t('system.config.form.tips.isSystem') }}
        </div>
      </el-form-item>

      <el-form-item
        :label="t('system.config.form.labels.isEncrypted')"
        prop="is_encrypted"
      >
        <el-switch
          v-model="formData.is_encrypted"
          :active-text="t('system.config.form.switches.encrypted')"
          :inactive-text="t('system.config.form.switches.plainText')"
        />
        <div class="form-tip">
          {{ t('system.config.form.tips.isEncrypted') }}
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">
        {{ t('common.actions.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ isEdit ? t('common.actions.save') : t('system.config.form.actions.add') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus/es/components/form'
import type { FormRules } from 'element-plus/es/components/form/src/types'
import type { SystemConfig } from '@/api/system'
import { systemConfigApi } from '@/api/system'

interface SystemConfigFormInput extends Partial<SystemConfig> {
  config_key?: string
  config_value?: string
  value_type?: 'string' | 'integer' | 'float' | 'boolean' | 'json'
  is_system?: boolean
  is_encrypted?: boolean
}

interface Props {
  visible: boolean
  data?: SystemConfigFormInput | null
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const { t } = useI18n()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const jsonError = ref('')

const isEdit = computed(() => !!props.data?.id)

const valueTypeOptions = computed(() => [
  { value: 'string', label: t('system.config.valueTypes.string') },
  { value: 'integer', label: t('system.config.valueTypes.integer') },
  { value: 'float', label: t('system.config.valueTypes.float') },
  { value: 'boolean', label: t('system.config.valueTypes.boolean') },
  { value: 'json', label: t('system.config.valueTypes.json') }
])

const categoryOptions = computed(() => [
  { value: 'general', label: t('system.config.categories.general') },
  { value: 'qrcode', label: t('system.config.categories.qrcode') },
  { value: 'notification', label: t('system.config.categories.notification') },
  { value: 'asset', label: t('system.config.categories.asset') },
  { value: 'inventory', label: t('system.config.categories.inventory') },
  { value: 'feature_flag', label: t('system.config.categories.feature_flag') },
  { value: 'finance', label: t('system.config.categories.finance') },
  { value: 'workflow', label: t('system.config.categories.workflow') },
  { value: 'integration', label: t('system.config.categories.integration') }
])

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
    { required: true, message: t('system.config.form.validation.configKeyRequired'), trigger: 'blur' },
    {
      pattern: /^[A-Z_][A-Z0-9_]*$/,
      message: t('system.config.form.validation.configKeyPattern'),
      trigger: 'blur'
    }
  ],
  name: [
    { required: true, message: t('system.config.form.validation.displayNameRequired'), trigger: 'blur' }
  ],
  value_type: [
    { required: true, message: t('system.config.form.validation.valueTypeRequired'), trigger: 'change' }
  ],
  config_value: [
    { required: true, message: t('system.config.form.validation.valueRequired'), trigger: 'blur' }
  ]
}

const getValuePlaceholder = (type: string) => {
  const key = `system.config.form.valuePlaceholders.${type}`
  const fallback = t('system.config.form.valuePlaceholders.default')
  const label = t(key)
  return label === key ? fallback : label
}

const validateJson = () => {
  if (formData.value.value_type === 'json' && formData.value.config_value) {
    try {
      JSON.parse(formData.value.config_value)
      jsonError.value = ''
      return true
    } catch {
      jsonError.value = t('system.config.form.messages.invalidJson')
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
      config_key: props.data.config_key || props.data.configKey || '',
      config_value: props.data.config_value || props.data.configValue || '',
      value_type: props.data.value_type || props.data.valueType || 'string',
      name: props.data.name || '',
      description: props.data.description || '',
      category: props.data.category || '',
      is_system: props.data.is_system || props.data.isSystem || false,
      is_encrypted: props.data.is_encrypted || props.data.isEncrypted || false
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
        if (!props.data?.id) {
          ElMessage.error(t('system.config.form.messages.operationFailed'))
          return
        }
        await systemConfigApi.update(props.data.id, formData.value)
      } else {
        await systemConfigApi.create(formData.value)
      }
      ElMessage.success(
        isEdit.value
          ? t('system.config.form.messages.updateSuccess')
          : t('system.config.form.messages.createSuccess')
      )
      emit('success')
      handleClose()
    } catch (error) {
      ElMessage.error(t('system.config.form.messages.operationFailed'))
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
