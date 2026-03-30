<template>
  <section
    v-if="actions.length > 0"
    class="recommended-action-panel"
  >
    <header class="recommended-action-panel__header">
      <div>
        <p class="recommended-action-panel__eyebrow">
          {{ t('common.workbench.eyebrows.recommendedActions') }}
        </p>
        <h3 class="recommended-action-panel__title">
          {{ t('common.workbench.titles.recommendedActions') }}
        </h3>
      </div>
      <p class="recommended-action-panel__description">
        {{ t('common.workbench.messages.recommendedActionHint') }}
      </p>
    </header>

    <ul class="recommended-action-panel__list">
      <li
        v-for="action in actions"
        :key="action.code"
        class="recommended-action-panel__item"
      >
        <div class="recommended-action-panel__copy">
          <strong>{{ resolveActionLabel(action) }}</strong>
          <p v-if="resolveActionDescription(action)">
            {{ resolveActionDescription(action) }}
          </p>
        </div>

        <el-button
          :type="resolveButtonType(action)"
          :loading="loadingActionCode === action.code"
          :disabled="action.enabled === false"
          @click="handleAction(action)"
        >
          {{ t('common.workbench.actions.run') }}
        </el-button>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import type { RuntimeWorkbenchRecommendedAction } from '@/types/runtime'
import type { WorkbenchAction } from './workbenchHelpers'
import {
  executeWorkbenchAction,
  resolveWorkbenchActionDescription,
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

const props = withDefaults(defineProps<{
  actions?: RuntimeWorkbenchRecommendedAction[]
  objectCode: string
  recordId: string
  taskStateKey?: string
  startTaskPolling?: (key: string, syncTaskId: string, options?: { onDone?: (state: SyncTaskState) => void | Promise<void> }) => void
}>(), {
  actions: () => [],
  taskStateKey: '',
  startTaskPolling: undefined,
})

const emit = defineEmits<{
  (e: 'refresh-requested'): void
}>()

const { t, te } = useI18n()
const loadingActionCode = ref<string | null>(null)

const resolveButtonType = (action: WorkbenchAction) => resolveWorkbenchButtonType(action)
const resolveActionLabel = (action: WorkbenchAction) => resolveWorkbenchActionLabel(action, t, te)
const resolveActionDescription = (action: WorkbenchAction) => resolveWorkbenchActionDescription(action, t, te)

const handleAction = async (action: WorkbenchAction) => {
  const confirmMessage = resolveWorkbenchConfirmMessage(action, t, te)
  if (confirmMessage) {
    try {
      await ElMessageBox.confirm(
        confirmMessage,
        t('common.dialog.confirmTitle'),
        {
          type: 'warning',
          confirmButtonText: t('common.actions.confirm'),
          cancelButtonText: t('common.actions.cancel'),
        },
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

<style scoped lang="scss">
@use '@/styles/object-workspace.scss' as workspace;

.recommended-action-panel {
  @include workspace.workspace-panel();
  padding: 24px;
}

.recommended-action-panel__header {
  @include workspace.workspace-panel-header();
}

.recommended-action-panel__eyebrow {
  @include workspace.panel-kicker();
}

.recommended-action-panel__title {
  @include workspace.panel-title();
}

.recommended-action-panel__description {
  @include workspace.panel-text(360px);
}

.recommended-action-panel__list {
  display: grid;
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.recommended-action-panel__item {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: center;
  padding: 16px 18px;
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  background: rgba(248, 250, 252, 0.9);
}

.recommended-action-panel__copy {
  min-width: 0;

  strong {
    display: block;
    font-size: 15px;
    font-weight: 700;
    color: rgba(15, 23, 42, 0.96);
  }

  p {
    margin: 8px 0 0;
    font-size: 13px;
    line-height: 1.6;
    color: rgba(71, 85, 105, 0.92);
  }
}

@media (max-width: 768px) {
  .recommended-action-panel__header,
  .recommended-action-panel__item {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
