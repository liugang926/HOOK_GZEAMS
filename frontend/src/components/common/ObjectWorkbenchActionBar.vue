<template>
  <div
    v-if="hasActions"
    class="object-workbench-action-bar"
  >
    <div class="object-workbench-action-bar__group">
      <el-button
        v-for="action in primaryActions"
        :key="action.code"
        :type="resolveButtonType(action)"
        :loading="loadingActionCode === action.code"
        @click="handleAction(action)"
      >
        {{ resolveActionLabel(action) }}
      </el-button>
    </div>

    <div
      v-if="secondaryActions.length > 0"
      class="object-workbench-action-bar__group"
    >
      <el-button
        v-for="action in secondaryActions"
        :key="action.code"
        :type="resolveButtonType(action)"
        plain
        :loading="loadingActionCode === action.code"
        @click="handleAction(action)"
      >
        {{ resolveActionLabel(action) }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, toRef } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import request from '@/utils/request'
import { useObjectWorkbench } from '@/composables/useObjectWorkbench'
import type { RuntimeWorkbench } from '@/types/runtime'

type WorkbenchAction = Record<string, unknown> & {
  code: string
}

interface SyncTaskState {
  syncTaskId: string
  status: string
  statusDisplay?: string
  done: boolean
}

const props = defineProps<{
  objectCode: string
  recordId: string
  recordData?: Record<string, unknown> | null
  workbench: RuntimeWorkbench | null
  taskStateKey?: string
  startTaskPolling?: (key: string, syncTaskId: string, options?: { onDone?: (state: SyncTaskState) => void | Promise<void> }) => void
}>()

const emit = defineEmits<{
  (e: 'refresh-requested'): void
}>()

const { t, te } = useI18n()
const loadingActionCode = ref<string | null>(null)

const { hasActions, primaryActions, secondaryActions } = useObjectWorkbench({
  workbench: toRef(props, 'workbench'),
  recordData: toRef(props, 'recordData'),
})

const resolveButtonType = (action: WorkbenchAction) => {
  const candidate = String(action.buttonType || action.button_type || 'default')
  if (['primary', 'success', 'warning', 'danger', 'info', 'default'].includes(candidate)) {
    return candidate as 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  }
  return 'default'
}

const resolveActionLabel = (action: WorkbenchAction) => {
  const labelKey = String(action.labelKey || action.label_key || '').trim()
  if (labelKey && te(labelKey)) {
    return t(labelKey)
  }
  return String(action.label || action.code || '')
}

const resolveConfirmMessage = (action: WorkbenchAction) => {
  const messageKey = String(action.confirmMessageKey || action.confirm_message_key || '').trim()
  if (messageKey && te(messageKey)) {
    return t(messageKey)
  }
  return String(action.confirmMessage || action.confirm_message || '').trim()
}

const resolveActionPath = (action: WorkbenchAction) => {
  const raw = String(action.actionPath || action.action_path || action.code || '').trim()
  return raw.replace(/^\/+/, '').replace(/\/+$/, '')
}

const resolveSyncTaskId = (payload: unknown) => {
  if (!payload || typeof payload !== 'object') return ''
  const candidate = payload as Record<string, unknown>
  return String(candidate.syncTaskId || candidate.sync_task_id || '').trim()
}

const executeWorkbenchAction = async (action: WorkbenchAction) => {
  const actionPath = resolveActionPath(action)
  if (!actionPath) {
    throw new Error('Workbench action path is required')
  }

  const method = String(action.method || 'post').toLowerCase()
  const response = await request<{
    success?: boolean
    message?: string
    data?: unknown
    error?: unknown
  }>({
    url: `/system/objects/${props.objectCode}/${props.recordId}/${actionPath}/`,
    method,
    data: {},
    unwrap: 'none',
  })

  const success = response.success !== false
  if (!success) {
    const error = response.error as Record<string, unknown> | undefined
    throw new Error(String(error?.message || response.message || t('common.messages.operationFailed')))
  }

  return {
    data: (response.data as Record<string, unknown> | undefined) || {},
    message: String(response.message || ''),
  }
}

const handleAction = async (action: WorkbenchAction) => {
  const confirmMessage = resolveConfirmMessage(action)
  if (confirmMessage) {
    try {
      await ElMessageBox.confirm(
        confirmMessage,
        t('common.dialog.confirmTitle') || t('common.messages.confirmTitle'),
        {
          type: 'warning',
          confirmButtonText: t('common.actions.confirm'),
          cancelButtonText: t('common.actions.cancel'),
        }
      )
    } catch {
      return
    }
  }

  loadingActionCode.value = action.code
  try {
    const result = await executeWorkbenchAction(action)
    const syncTaskId = resolveSyncTaskId(result.data)
    const taskStateKey = String(props.taskStateKey || `${props.objectCode}:${props.recordId}`).trim()

    if (syncTaskId && props.startTaskPolling && taskStateKey) {
      props.startTaskPolling(taskStateKey, syncTaskId, {
        onDone: async () => {
          emit('refresh-requested')
        },
      })
    }

    ElMessage.success(result.message || t('common.messages.operationSuccess'))
    emit('refresh-requested')
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : t('common.messages.operationFailed')
    ElMessage.error(message)
  } finally {
    loadingActionCode.value = null
  }
}
</script>

<style scoped>
.object-workbench-action-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.object-workbench-action-bar__group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
