<template>
  <el-card
    class="finance-voucher-panel"
    shadow="never"
  >
    <template #header>
      <div class="finance-voucher-panel__header">
        <span>{{ title }}</span>
        <el-button
          size="small"
          @click="loadLogs"
        >
          {{ t('common.actions.refresh') }}
        </el-button>
      </div>
    </template>

    <el-table
      v-loading="loading"
      :data="logs"
      border
      stripe
    >
      <el-table-column
        prop="createdAt"
        :label="t('common.columns.createdAt')"
        width="180"
      />
      <el-table-column
        prop="requestMethod"
        :label="t('finance.columns.requestMethod')"
        width="100"
      />
      <el-table-column
        prop="statusCode"
        :label="t('finance.columns.httpStatus')"
        width="100"
      />
      <el-table-column
        :label="t('common.columns.status')"
        width="100"
      >
        <template #default="{ row }">
          <el-tag :type="row.success ? 'success' : 'danger'">
            {{ row.success ? t('common.status.success') : t('common.status.failed') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column
        prop="taskId"
        :label="t('finance.columns.taskId')"
        min-width="180"
      />
      <el-table-column
        prop="integrationType"
        :label="t('finance.columns.integrationType')"
        min-width="180"
      />
      <el-table-column
        prop="errorMessage"
        :label="t('finance.columns.errorMessage')"
        min-width="220"
        show-overflow-tooltip
      />
      <el-table-column
        prop="durationSeconds"
        :label="t('finance.columns.durationMs')"
        width="130"
      >
        <template #default="{ row }">
          {{ row.durationMs || row.durationSeconds || '-' }}
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { integrationApi } from '@/api/finance'
import type { IntegrationLog } from '@/types/integration'

const props = defineProps<{
  panel: Record<string, unknown>
  recordId: string
  refreshVersion?: number
}>()

const { t, te } = useI18n()
const loading = ref(false)
const logs = ref<IntegrationLog[]>([])

const title = computed(() => {
  const titleKey = String(props.panel.titleKey || props.panel.title_key || '').trim()
  if (titleKey && te(titleKey)) {
    return t(titleKey)
  }
  return String(props.panel.title || t('finance.panels.integrationLogs'))
})

const normalizeLog = (value: Record<string, unknown>): IntegrationLog => {
  const duration = Number(
    value.durationMs || value.duration_ms || value.durationSeconds || value.duration_seconds || 0
  )

  return {
    id: String(value.id || ''),
    createdAt: String(value.createdAt || value.created_at || ''),
    integrationType: String(value.integrationType || value.integration_type || ''),
    action: String(value.action || ''),
    requestMethod: String(value.requestMethod || value.request_method || ''),
    statusCode: Number(value.statusCode || value.status_code || 0),
    success: Boolean(value.success),
    durationMs: duration,
    durationSeconds: duration,
    requestBody: value.requestBody || value.request_body || null,
    responseBody: value.responseBody || value.response_body || null,
    errorMessage: String(value.errorMessage || value.error_message || ''),
    businessType: String(value.businessType || value.business_type || ''),
    syncTask: String(value.syncTask || value.sync_task || '').trim() || null,
    taskId: String(value.taskId || value.task_id || '').trim() || null,
  }
}

const loadLogs = async () => {
  if (!props.recordId) return
  loading.value = true
  try {
    const result = await integrationApi.getLogs(props.recordId)
    logs.value = Array.isArray(result)
      ? result.map((item) => normalizeLog((item || {}) as Record<string, unknown>))
      : []
  } catch (error: unknown) {
    logs.value = []
    ElMessage.error(error instanceof Error ? error.message : t('common.messages.operationFailed'))
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.recordId, props.refreshVersion],
  () => {
    void loadLogs()
  },
  { immediate: true }
)
</script>

<style scoped>
.finance-voucher-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
</style>
