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
import { useObjectWorkbench } from '@/composables/useObjectWorkbench'
import type { RuntimeWorkbench } from '@/types/runtime'
import type { WorkbenchAction } from './workbenchHelpers'
import {
  executeWorkbenchAction,
  resolveWorkbenchActionLabel,
  resolveWorkbenchButtonType,
  resolveWorkbenchConfirmMessage,
  resolveWorkbenchSyncTaskId,
} from './workbenchHelpers'

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

const resolveButtonType = (action: WorkbenchAction) => resolveWorkbenchButtonType(action)
const resolveActionLabel = (action: WorkbenchAction) => resolveWorkbenchActionLabel(action, t, te)
const resolveConfirmMessage = (action: WorkbenchAction) => resolveWorkbenchConfirmMessage(action, t, te)

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
    const result = await executeWorkbenchAction({
      action,
      objectCode: props.objectCode,
      recordId: props.recordId,
    })
    const syncTaskId = resolveWorkbenchSyncTaskId(result.data)
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
