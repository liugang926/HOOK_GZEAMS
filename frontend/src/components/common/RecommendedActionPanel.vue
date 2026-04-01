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

  <WorkbenchActionPromptDialog
    v-model="promptVisible"
    :action="activeAction"
    :prompt="activePrompt"
    :values="promptValues"
    :loading="Boolean(loadingActionCode)"
    @set-value="setPromptValue"
    @confirm="confirmPromptAction"
    @cancel="closePromptDialog"
  />
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import type { RuntimeWorkbenchRecommendedAction } from '@/types/runtime'
import type { WorkbenchAction } from './workbenchHelpers'
import {
  resolveWorkbenchActionDescription,
  resolveWorkbenchActionLabel,
  resolveWorkbenchButtonType,
} from './workbenchHelpers'
import WorkbenchActionPromptDialog from './WorkbenchActionPromptDialog.vue'
import { useWorkbenchActionExecutor } from './useWorkbenchActionExecutor'

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
const {
  activeAction,
  activePrompt,
  closePromptDialog,
  confirmPromptAction,
  handleAction,
  loadingActionCode,
  promptValues,
  promptVisible,
  setPromptValue,
} = useWorkbenchActionExecutor({
  objectCode: props.objectCode,
  recordId: props.recordId,
  taskStateKey: props.taskStateKey,
  startTaskPolling: props.startTaskPolling,
  onRefreshRequested: () => emit('refresh-requested'),
})

const resolveButtonType = (action: WorkbenchAction) => resolveWorkbenchButtonType(action)
const resolveActionLabel = (action: WorkbenchAction) => resolveWorkbenchActionLabel(action, t, te)
const resolveActionDescription = (action: WorkbenchAction) => resolveWorkbenchActionDescription(action, t, te)
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
