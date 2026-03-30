<template>
  <div class="m18-config-section">
    <el-alert
      :title="t('integration.m18.notice.title')"
      :description="t('integration.m18.notice.description')"
      type="info"
      show-icon
      :closable="false"
      class="m18-config-section__notice"
    />

    <el-divider content-position="left">
      {{ t('integration.m18.sections.account') }}
    </el-divider>

    <el-form-item :label="t('integration.m18.fields.companyCode')">
      <el-input
        :model-value="stringValue(modelValue.connectionConfig.companyCode)"
        :placeholder="t('integration.m18.placeholders.companyCode')"
        @update:model-value="updateConnectionField('companyCode', $event)"
      />
    </el-form-item>

    <el-form-item :label="t('integration.m18.fields.username')">
      <el-input
        :model-value="stringValue(modelValue.connectionConfig.username)"
        :placeholder="t('integration.m18.placeholders.username')"
        @update:model-value="updateConnectionField('username', $event)"
      />
    </el-form-item>

    <el-form-item :label="t('integration.m18.fields.password')">
      <el-input
        :model-value="stringValue(modelValue.connectionConfig.password)"
        type="password"
        show-password
        :placeholder="t('integration.m18.placeholders.password')"
        @update:model-value="updateConnectionField('password', $event)"
      />
    </el-form-item>

    <el-divider content-position="left">
      {{ t('integration.m18.sections.syncScope') }}
    </el-divider>

    <el-form-item :label="t('integration.m18.fields.syncPurchaseOrders')">
      <el-switch
        :model-value="booleanValue(modelValue.syncConfig.syncOrders)"
        @update:model-value="updateSyncField('syncOrders', $event, 'procurement')"
      />
    </el-form-item>

    <el-form-item :label="t('integration.m18.fields.syncVendors')">
      <el-switch
        :model-value="booleanValue(modelValue.syncConfig.syncVendors)"
        @update:model-value="updateSyncField('syncVendors', $event, 'procurement')"
      />
    </el-form-item>

    <el-form-item :label="t('integration.m18.fields.syncAssets')">
      <el-switch
        :model-value="booleanValue(modelValue.syncConfig.syncAssets)"
        @update:model-value="updateSyncField('syncAssets', $event, 'inventory')"
      />
    </el-form-item>

    <el-form-item :label="t('integration.m18.fields.syncDepreciation')">
      <el-switch
        :model-value="booleanValue(modelValue.syncConfig.syncDepreciation)"
        @update:model-value="updateSyncField('syncDepreciation', $event, 'finance')"
      />
    </el-form-item>

    <el-form-item :label="t('integration.m18.fields.startDate')">
      <el-date-picker
        :model-value="stringValue(modelValue.syncConfig.startDate)"
        type="date"
        value-format="YYYY-MM-DD"
        :placeholder="t('integration.m18.placeholders.startDate')"
        style="width: 100%"
        @update:model-value="updateSyncField('startDate', $event)"
      />
    </el-form-item>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type {
  IntegrationFormData,
  KnownIntegrationModuleType,
} from '@/types/integration'

const props = defineProps<{
  modelValue: IntegrationFormData
}>()

const emit = defineEmits<{
  'update:modelValue': [value: IntegrationFormData]
}>()

const { t } = useI18n()

const stringValue = (value: unknown) => (typeof value === 'string' ? value : '')
const booleanValue = (value: unknown) => Boolean(value)

const updateConnectionField = (field: string, value: unknown) => {
  emit('update:modelValue', {
    ...props.modelValue,
    connectionConfig: {
      ...props.modelValue.connectionConfig,
      [field]: value,
    },
  })
}

const updateSyncField = (
  field: string,
  value: unknown,
  linkedModule?: KnownIntegrationModuleType,
) => {
  const nextEnabledModules = [...(props.modelValue.enabledModules || [])]

  if (linkedModule && Boolean(value) && !nextEnabledModules.includes(linkedModule)) {
    nextEnabledModules.push(linkedModule)
  }

  emit('update:modelValue', {
    ...props.modelValue,
    enabledModules: nextEnabledModules,
    syncConfig: {
      ...props.modelValue.syncConfig,
      [field]: value,
    },
  })
}
</script>

<style scoped>
.m18-config-section__notice {
  margin-bottom: 16px;
}
</style>
