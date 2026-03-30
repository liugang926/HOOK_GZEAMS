<template>
  <el-dialog
    :model-value="modelValue"
    :title="dialogTitle"
    width="640px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-form label-width="150px">
      <el-alert
        :title="integrationName"
        :description="t('integration.m18.syncDialog.description')"
        type="info"
        show-icon
        :closable="false"
        class="m18-sync-dialog__notice"
      />

      <el-form-item :label="t('integration.m18.syncDialog.fields.mode')">
        <el-radio-group v-model="form.mode">
          <el-radio-button value="purchaseOrders">
            {{ t('integration.m18.syncDialog.modes.purchaseOrders') }}
          </el-radio-button>
          <el-radio-button value="vendors">
            {{ t('integration.m18.syncDialog.modes.vendors') }}
          </el-radio-button>
          <el-radio-button value="assets">
            {{ t('integration.m18.syncDialog.modes.assets') }}
          </el-radio-button>
          <el-radio-button value="depreciation">
            {{ t('integration.m18.syncDialog.modes.depreciation') }}
          </el-radio-button>
        </el-radio-group>
      </el-form-item>

      <el-form-item
        v-if="form.mode === 'purchaseOrders'"
        :label="t('integration.m18.syncDialog.fields.dateRange')"
      >
        <el-date-picker
          v-model="form.dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          range-separator="~"
          :start-placeholder="t('integration.m18.syncDialog.placeholders.startDate')"
          :end-placeholder="t('integration.m18.syncDialog.placeholders.endDate')"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item
        v-if="form.mode === 'purchaseOrders'"
        :label="t('integration.m18.syncDialog.fields.orderNos')"
      >
        <el-input
          v-model="form.orderNos"
          type="textarea"
          :rows="3"
          :placeholder="t('integration.m18.syncDialog.placeholders.orderNos')"
        />
      </el-form-item>

      <el-form-item
        v-if="form.mode === 'depreciation'"
        :label="t('integration.m18.syncDialog.fields.period')"
      >
        <el-date-picker
          v-model="form.period"
          type="month"
          value-format="YYYY-MM"
          :placeholder="t('integration.m18.syncDialog.placeholders.period')"
          style="width: 100%"
        />
      </el-form-item>

      <el-alert
        :description="currentHelperText"
        type="success"
        :closable="false"
        show-icon
      />
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
        {{ t('integration.actions.syncNow') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type {
  IntegrationConfig,
  M18SyncFormData,
  TriggerSyncPayload,
} from '@/types/integration'

const props = defineProps<{
  modelValue: boolean
  integration: IntegrationConfig | null
  submitting: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  trigger: [payload: TriggerSyncPayload]
}>()

const { t } = useI18n()

const createDefaultForm = (): M18SyncFormData => ({
  mode: 'purchaseOrders',
  dateRange: [],
  orderNos: '',
  period: new Date().toISOString().slice(0, 7),
})

const form = reactive<M18SyncFormData>(createDefaultForm())

const dialogTitle = computed(() => t('integration.m18.syncDialog.title'))
const integrationName = computed(() => props.integration?.systemName || props.integration?.name || 'M18')
const currentHelperText = computed(() => t(`integration.m18.syncDialog.helpers.${form.mode}`))

watch(
  () => props.modelValue,
  (visible) => {
    if (!visible) {
      return
    }

    const next = createDefaultForm()
    form.mode = next.mode
    form.dateRange = next.dateRange
    form.orderNos = next.orderNos
    form.period = next.period
  }
)

const normalizeOrderNos = () => {
  return form.orderNos
    .split(/[\n,]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

const buildPayload = (): TriggerSyncPayload => {
  if (form.mode === 'purchaseOrders') {
    return {
      moduleType: 'procurement',
      businessType: 'purchase_orders',
      direction: 'pull',
      async: true,
      execute: true,
      syncParams: {
        startDate: form.dateRange[0],
        endDate: form.dateRange[1],
        orderNos: normalizeOrderNos(),
      },
    }
  }

  if (form.mode === 'vendors') {
    return {
      moduleType: 'procurement',
      businessType: 'vendors',
      direction: 'pull',
      async: true,
      execute: true,
    }
  }

  if (form.mode === 'assets') {
    return {
      moduleType: 'inventory',
      businessType: 'assets',
      direction: 'pull',
      async: true,
      execute: true,
    }
  }

  return {
    moduleType: 'finance',
    businessType: 'depreciation',
    direction: 'push',
    async: true,
    execute: true,
    syncParams: {
      period: form.period,
    },
  }
}

const handleSubmit = () => {
  emit('trigger', buildPayload())
}
</script>

<style scoped>
.m18-sync-dialog__notice {
  margin-bottom: 16px;
}
</style>
