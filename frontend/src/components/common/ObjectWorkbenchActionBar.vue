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
import { toRef } from 'vue'
import { useI18n } from 'vue-i18n'
import { useObjectWorkbench } from '@/composables/useObjectWorkbench'
import type { RuntimeWorkbench } from '@/types/runtime'
import type { WorkbenchAction } from './workbenchHelpers'
import {
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
const { hasActions, primaryActions, secondaryActions } = useObjectWorkbench({
  workbench: toRef(props, 'workbench'),
  recordData: toRef(props, 'recordData'),
})

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
