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
          @click="refreshStatus"
        >
          {{ t('common.actions.refresh') }}
        </el-button>
      </div>
    </template>

    <div
      v-if="activeTask"
      class="finance-voucher-status"
    >
      <SyncTaskStatusBadge
        :sync-task-id="activeTask.syncTaskId"
        :status="activeTask.status"
        :status-display="activeTask.statusDisplay"
      />
      <p class="finance-voucher-status__meta">
        {{ t('finance.columns.taskId') }}: {{ activeTask.syncTaskId }}
      </p>
    </div>

    <div
      v-else-if="latestSyncTaskId"
      class="finance-voucher-status"
    >
      <SyncTaskStatusBadge
        :sync-task-id="latestSyncTaskId"
        :status="latestStatus"
        :status-display="latestStatusDisplay"
      />
      <p class="finance-voucher-status__meta">
        {{ t('finance.columns.taskId') }}: {{ latestDisplayTaskId }}
      </p>
    </div>

    <el-empty
      v-else
      :description="t('finance.messages.noSyncTask')"
    />
  </el-card>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { integrationApi } from '@/api/finance'
import SyncTaskStatusBadge from '@/components/finance/SyncTaskStatusBadge.vue'
import type { IntegrationLog } from '@/types/integration'

interface SyncTaskState {
  syncTaskId: string
  status: string
  statusDisplay?: string
  done: boolean
}

const props = defineProps<{
  panel: Record<string, unknown>
  recordId: string
  currentTask?: SyncTaskState | null
  taskStateKey?: string
  refreshVersion?: number
  startTaskPolling?: (key: string, syncTaskId: string, options?: { onDone?: (state: SyncTaskState) => void | Promise<void> }) => void
}>()

const emit = defineEmits<{
  (e: 'task-complete'): void
}>()

const { t, te } = useI18n()
const latestLog = ref<IntegrationLog | null>(null)

const title = computed(() => {
  const titleKey = String(props.panel.titleKey || props.panel.title_key || '').trim()
  if (titleKey && te(titleKey)) {
    return t(titleKey)
  }
  return String(props.panel.title || t('finance.panels.syncStatus'))
})

const activeTask = computed(() => props.currentTask || null)
const latestSyncTaskId = computed(() => String(latestLog.value?.syncTask || '').trim())
const latestDisplayTaskId = computed(() => {
  return String(latestLog.value?.taskId || latestLog.value?.syncTask || '').trim()
})
const latestStatus = computed(() => {
  if (activeTask.value?.status) return activeTask.value.status
  if (!latestLog.value) return ''
  return latestLog.value.success ? 'success' : 'failed'
})
const latestStatusDisplay = computed(() => {
  if (activeTask.value?.statusDisplay) return activeTask.value.statusDisplay
  if (!latestLog.value) return ''
  return latestLog.value.success ? t('common.status.success') : t('common.status.failed')
})

const ensurePolling = () => {
  const taskId = latestSyncTaskId.value
  const taskStateKey = String(props.taskStateKey || '').trim()
  if (!taskId || !taskStateKey || !props.startTaskPolling || activeTask.value?.syncTaskId) {
    return
  }

  props.startTaskPolling(taskStateKey, taskId, {
    onDone: async () => {
      emit('task-complete')
    },
  })
}

const loadLatestLog = async () => {
  if (!props.recordId) return
  try {
    const result = await integrationApi.getLogs(props.recordId)
    latestLog.value = Array.isArray(result) && result.length > 0 ? result[0] : null
    ensurePolling()
  } catch (error: unknown) {
    latestLog.value = null
    ElMessage.error(error instanceof Error ? error.message : t('common.messages.operationFailed'))
  }
}

const refreshStatus = async () => {
  await loadLatestLog()
}

watch(
  () => [props.recordId, props.refreshVersion],
  () => {
    void loadLatestLog()
  },
  { immediate: true }
)

watch(
  () => props.currentTask?.syncTaskId,
  () => {
    ensurePolling()
  }
)
</script>

<style scoped>
.finance-voucher-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.finance-voucher-status {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.finance-voucher-status__meta {
  margin: 0;
  font-size: 12px;
  color: #606266;
}
</style>
