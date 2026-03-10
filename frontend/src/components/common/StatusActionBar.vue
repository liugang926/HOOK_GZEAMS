<template>
  <!--
    StatusActionBar.vue
    A reusable workflow state transition button bar.
    Dynamically shows/hides action buttons based on the current record status.
  -->
  <div
    v-if="visibleActions.length > 0"
    class="status-action-bar"
  >
    <el-button
      v-for="action in visibleActions"
      :key="action.key"
      :type="action.type || 'default'"
      :icon="action.icon"
      :loading="loadingKey === action.key"
      :disabled="!!loadingKey"
      @click="handleAction(action)"
    >
      {{ action.label }}
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'

export interface StatusAction {
  /** Unique action key */
  key: string
  /** Button display label */
  label: string
  /** Element Plus button type: primary, success, warning, danger, info */
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  /** Element Plus icon component */
  icon?: any
  /** Confirmation message. If provided, shows confirm dialog before executing. */
  confirmMessage?: string
  /** Confirmation dialog type */
  confirmType?: 'info' | 'warning' | 'error'
  /** API call function. Should return a Promise. */
  apiCall: () => Promise<unknown>
  /** Predicate to determine if action is visible for the given status */
  visibleWhen: (status: string) => boolean
}

const props = defineProps<{
  /** Current record status string */
  status: string
  /** Array of action configurations */
  actions: StatusAction[]
}>()

const emit = defineEmits<{
  (e: 'action-success', key: string, result: unknown): void
  (e: 'action-error', key: string, error: unknown): void
}>()

const { t } = useI18n()
const loadingKey = ref<string | null>(null)

const visibleActions = computed(() =>
  props.actions.filter(a => a.visibleWhen(props.status))
)

const handleAction = async (action: StatusAction) => {
  if (action.confirmMessage) {
    try {
      await ElMessageBox.confirm(
        action.confirmMessage,
        t('common.dialog.confirmTitle') || t('common.messages.confirmTitle'),
        {
          type: action.confirmType || 'info',
          confirmButtonText: t('common.actions.confirm'),
          cancelButtonText: t('common.actions.cancel'),
        }
      )
    } catch {
      return // User cancelled
    }
  }

  loadingKey.value = action.key
  try {
    const result = await action.apiCall()
    ElMessage.success(t('common.messages.operationSuccess') || 'Success')
    emit('action-success', action.key, result)
  } catch (error: any) {
    const msg = error?.response?.data?.detail || error?.message || t('common.messages.operationFailed')
    ElMessage.error(msg)
    emit('action-error', action.key, error)
  } finally {
    loadingKey.value = null
  }
}
</script>

<style scoped>
.status-action-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 0;
}
</style>
