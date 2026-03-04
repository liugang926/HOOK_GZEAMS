<template>
  <el-form
    inline
    class="filter-form"
  >
    <el-form-item :label="t('integration.configList.filters.systemType')">
      <el-select
        :model-value="systemType"
        clearable
        :placeholder="t('integration.configList.filters.allSystems')"
        @update:model-value="handleSystemTypeUpdate"
        @change="emit('search')"
      >
        <el-option
          v-for="option in SYSTEM_TYPE_OPTIONS"
          :key="option"
          :label="getSystemTypeLabel(option, t)"
          :value="option"
        />
      </el-select>
    </el-form-item>

    <el-form-item :label="t('integration.configList.filters.status')">
      <el-select
        :model-value="isEnabled"
        clearable
        :placeholder="t('integration.configList.filters.all')"
        @update:model-value="handleIsEnabledUpdate"
        @change="emit('search')"
      >
        <el-option
          v-for="option in ENABLED_STATUS_OPTIONS"
          :key="String(option)"
          :label="getEnabledStatusLabel(option, t)"
          :value="option"
        />
      </el-select>
    </el-form-item>

    <el-form-item :label="t('integration.configList.filters.health')">
      <el-select
        :model-value="healthStatus"
        clearable
        :placeholder="t('integration.configList.filters.all')"
        @update:model-value="handleHealthStatusUpdate"
        @change="emit('search')"
      >
        <el-option
          v-for="option in HEALTH_STATUS_OPTIONS"
          :key="option"
          :label="getHealthStatusLabel(option, t)"
          :value="option"
        />
      </el-select>
    </el-form-item>

    <el-form-item>
      <el-button
        type="primary"
        @click="emit('search')"
      >
        {{ t('integration.actions.search') }}
      </el-button>
      <el-button @click="emit('reset')">
        {{ t('integration.actions.reset') }}
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import {
  ENABLED_STATUS_OPTIONS,
  HEALTH_STATUS_OPTIONS,
  SYSTEM_TYPE_OPTIONS,
  getEnabledStatusLabel,
  getHealthStatusLabel,
  getSystemTypeLabel
} from '@/views/integration/integrationConfig.constants'
import type { IntegrationHealthStatus, IntegrationSystemType } from '@/types/integration'

defineProps<{
  systemType?: IntegrationSystemType
  isEnabled?: boolean
  healthStatus?: IntegrationHealthStatus
}>()

const emit = defineEmits<{
  'update:systemType': [value: IntegrationSystemType | undefined]
  'update:isEnabled': [value: boolean | undefined]
  'update:healthStatus': [value: IntegrationHealthStatus | undefined]
  search: []
  reset: []
}>()

const { t } = useI18n()

const normalizeString = (value: unknown): string | undefined => {
  if (typeof value !== 'string') return undefined
  return value.length > 0 ? value : undefined
}

const normalizeBoolean = (value: unknown): boolean | undefined => {
  return typeof value === 'boolean' ? value : undefined
}

const handleSystemTypeUpdate = (value: unknown) => {
  emit('update:systemType', normalizeString(value) as IntegrationSystemType | undefined)
}

const handleIsEnabledUpdate = (value: unknown) => {
  emit('update:isEnabled', normalizeBoolean(value))
}

const handleHealthStatusUpdate = (value: unknown) => {
  emit('update:healthStatus', normalizeString(value) as IntegrationHealthStatus | undefined)
}
</script>

<style scoped>
.filter-form {
  margin-bottom: 20px;
}
</style>
