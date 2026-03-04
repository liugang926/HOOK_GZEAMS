<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? t('integration.formDialog.titles.edit') : t('integration.formDialog.titles.create')"
    width="700px"
    @update:model-value="handleDialogVisibilityChange"
    @close="handleDialogClose"
  >
    <el-form
      ref="formRef"
      :model="localFormData"
      :rules="rules"
      label-width="150px"
    >
      <el-divider content-position="left">
        {{ t('integration.formDialog.sections.basic') }}
      </el-divider>

      <el-form-item
        :label="t('integration.formDialog.fields.systemType')"
        prop="systemType"
      >
        <el-select
          v-model="localFormData.systemType"
          :placeholder="t('integration.formDialog.placeholders.selectSystemType')"
          style="width: 100%"
          :disabled="isEdit"
        >
          <el-option
            v-for="option in SYSTEM_TYPE_OPTIONS"
            :key="option"
            :label="getSystemTypeLabel(option, t)"
            :value="option"
          />
        </el-select>
      </el-form-item>

      <el-form-item
        :label="t('integration.formDialog.fields.systemName')"
        prop="systemName"
      >
        <el-input
          v-model="localFormData.systemName"
          :placeholder="t('integration.formDialog.placeholders.systemName')"
        />
      </el-form-item>

      <el-form-item :label="t('integration.formDialog.fields.enabled')">
        <el-switch v-model="localFormData.isEnabled" />
      </el-form-item>

      <el-divider content-position="left">
        {{ t('integration.formDialog.sections.connection') }}
      </el-divider>

      <el-form-item :label="t('integration.formDialog.fields.apiEndpoint')">
        <el-input
          v-model="localFormData.connectionConfig.apiUrl"
          :placeholder="t('integration.formDialog.placeholders.apiEndpoint')"
        />
      </el-form-item>

      <el-form-item :label="t('integration.formDialog.fields.apiKey')">
        <el-input
          v-model="localFormData.connectionConfig.apiKey"
          type="password"
          show-password
          :placeholder="t('integration.formDialog.placeholders.apiKey')"
        />
      </el-form-item>

      <el-form-item :label="t('integration.formDialog.fields.apiSecret')">
        <el-input
          v-model="localFormData.connectionConfig.apiSecret"
          type="password"
          show-password
          :placeholder="t('integration.formDialog.placeholders.apiSecret')"
        />
      </el-form-item>

      <el-form-item :label="t('integration.formDialog.fields.timeoutSeconds')">
        <el-input-number
          v-model="localFormData.connectionConfig.timeout"
          :min="1"
          :max="300"
          style="width: 100%"
        />
      </el-form-item>

      <el-divider content-position="left">
        {{ t('integration.formDialog.sections.modules') }}
      </el-divider>

      <el-form-item :label="t('integration.formDialog.fields.enabledModules')">
        <el-checkbox-group v-model="localFormData.enabledModules">
          <el-checkbox
            v-for="option in MODULE_OPTIONS"
            :key="option"
            :label="option"
          >
            {{ getModuleLabel(option, t) }}
          </el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <el-divider content-position="left">
        {{ t('integration.formDialog.sections.sync') }}
      </el-divider>

      <el-form-item :label="t('integration.formDialog.fields.autoSync')">
        <el-switch v-model="localFormData.syncConfig.autoSync" />
      </el-form-item>

      <el-form-item
        v-if="localFormData.syncConfig.autoSync"
        :label="t('integration.formDialog.fields.syncIntervalMinutes')"
      >
        <el-input-number
          v-model="localFormData.syncConfig.interval"
          :min="1"
          :max="1440"
          style="width: 100%"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="emit('update:modelValue', false)">
        {{ t('integration.actions.cancel') }}
      </el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ isEdit ? t('integration.actions.save') : t('integration.actions.create') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import type { FormInstance, FormRules } from 'element-plus'
import type { IntegrationFormData } from '@/types/integration'
import {
  MODULE_OPTIONS,
  SYSTEM_TYPE_OPTIONS,
  getModuleLabel,
  getSystemTypeLabel
} from '@/views/integration/integrationConfig.constants'

const props = defineProps<{
  modelValue: boolean
  isEdit: boolean
  submitting: boolean
  formData: IntegrationFormData
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  submit: [payload: IntegrationFormData]
}>()

const { t } = useI18n()
const formRef = ref<FormInstance>()
const cloneFormData = (data: IntegrationFormData): IntegrationFormData =>
  JSON.parse(JSON.stringify(data)) as IntegrationFormData

const localFormData = ref<IntegrationFormData>(cloneFormData(props.formData))

const rules = computed<FormRules>(() => ({
  systemType: [
    { required: true, message: t('integration.validation.selectSystemType'), trigger: 'change' }
  ],
  systemName: [
    { required: true, message: t('integration.validation.enterSystemName'), trigger: 'blur' }
  ]
}))

const handleDialogVisibilityChange = (value: boolean) => {
  emit('update:modelValue', value)
}

const handleDialogClose = () => {
  formRef.value?.clearValidate()
}

watch(
  () => props.modelValue,
  (visible) => {
    if (visible) {
      localFormData.value = cloneFormData(props.formData)
    }
  }
)

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    emit('submit', cloneFormData(localFormData.value))
  } catch {
    // Element Plus validation throws on invalid form; no extra handling needed.
  }
}
</script>
