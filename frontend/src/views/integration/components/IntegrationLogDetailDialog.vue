<template>
  <el-dialog
    :model-value="modelValue"
    :title="t('integration.logs.detailTitle')"
    width="900px"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <el-descriptions
      v-if="currentLog"
      :column="2"
      border
    >
      <el-descriptions-item :label="t('integration.logs.columns.time')">
        {{ currentLog.createdAt }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('integration.logs.columns.type')">
        {{ currentLog.integrationType }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('integration.logs.columns.action')">
        <el-tag :type="currentLog.action === 'push' ? 'success' : 'warning'">
          {{ currentLog.action }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item :label="t('integration.logs.columns.method')">
        {{ currentLog.requestMethod }}
      </el-descriptions-item>
      <el-descriptions-item :label="t('integration.logs.columns.statusCode')">
        <el-tag :type="currentLog.statusCode < 300 ? 'success' : 'danger'">
          {{ currentLog.statusCode }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item :label="t('integration.logs.columns.success')">
        <el-tag :type="currentLog.success ? 'success' : 'danger'">
          {{ currentLog.success ? t('integration.common.yes') : t('integration.common.no') }}
        </el-tag>
      </el-descriptions-item>
      <el-descriptions-item :label="t('integration.logs.columns.duration')">
        {{ currentLog.durationMs }}ms
      </el-descriptions-item>
      <el-descriptions-item :label="t('integration.logs.columns.businessType')">
        {{ currentLog.businessType || '-' }}
      </el-descriptions-item>
    </el-descriptions>

    <el-divider>{{ t('integration.logs.request') }}</el-divider>
    <div class="code-block">
      <pre><code>{{ JSON.stringify(currentLog?.requestBody || {}, null, 2) }}</code></pre>
    </div>

    <el-divider>{{ t('integration.logs.response') }}</el-divider>
    <div class="code-block">
      <pre><code>{{ JSON.stringify(currentLog?.responseBody || {}, null, 2) }}</code></pre>
    </div>

    <div
      v-if="currentLog?.errorMessage"
      class="error-message"
    >
      <el-divider>{{ t('integration.logs.error') }}</el-divider>
      <pre>{{ currentLog.errorMessage }}</pre>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { IntegrationLog } from '@/types/integration'

withDefaults(defineProps<{
  modelValue: boolean
  currentLog: IntegrationLog | null
}>(), {
  currentLog: null
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const { t } = useI18n()
</script>

<style scoped>
.code-block {
  background: #f5f7fa;
  border-radius: 4px;
  padding: 15px;
  max-height: 300px;
  overflow: auto;
}

.code-block pre {
  margin: 0;
  font-size: 12px;
  font-family: 'Courier New', monospace;
}

.error-message {
  margin-top: 15px;
}

.error-message pre {
  background: #fef0f0;
  color: #f56c6c;
  padding: 10px;
  border-radius: 4px;
  white-space: pre-wrap;
  font-size: 12px;
}
</style>
