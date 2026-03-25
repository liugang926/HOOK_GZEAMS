<template>
  <div
    v-if="visibleActions.length > 0"
    class="object-action-bar"
  >
    <el-button
      v-for="action in visibleActions"
      :key="action.actionCode"
      :type="normalizeButtonType(action.buttonType)"
      :loading="loadingActionCode === action.actionCode"
      :disabled="!action.enabled || !!loadingActionCode"
      :title="action.disabledReason || ''"
      @click="handleAction(action)"
    >
      {{ action.label }}
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { dynamicApi, type ObjectActionDefinition, type ObjectActionExecutionResult } from '@/api/dynamic'

const props = defineProps<{
  objectCode: string
  recordId: string
}>()

const emit = defineEmits<{
  (e: 'action-success', actionCode: string, result: ObjectActionExecutionResult): void
  (e: 'action-error', actionCode: string, error: unknown): void
}>()

const router = useRouter()
const { t } = useI18n()
const actions = ref<ObjectActionDefinition[]>([])
const loadingActionCode = ref<string | null>(null)

const visibleActions = computed(() => actions.value)

const normalizeButtonType = (buttonType?: string) => {
  const candidate = String(buttonType || 'default')
  if (['primary', 'success', 'warning', 'danger', 'info', 'default'].includes(candidate)) {
    return candidate as 'primary' | 'success' | 'warning' | 'danger' | 'info' | 'default'
  }
  return 'default'
}

const loadActions = async () => {
  if (!props.objectCode || !props.recordId) {
    actions.value = []
    return
  }

  try {
    const payload = await dynamicApi.getActions(props.objectCode, props.recordId)
    actions.value = Array.isArray(payload?.actions) ? payload.actions : []
  } catch (error: any) {
    actions.value = []
    const message = error?.response?.data?.error?.message || error?.message
    if (message) {
      ElMessage.error(message)
    }
  }
}

const handleAction = async (action: ObjectActionDefinition) => {
  if (!action.enabled) {
    if (action.disabledReason) {
      ElMessage.warning(action.disabledReason)
    }
    return
  }

  if (action.confirmMessage) {
    try {
      await ElMessageBox.confirm(
        action.confirmMessage,
        t('common.dialog.confirmTitle') || t('common.messages.confirmTitle'),
        {
          type: 'info',
          confirmButtonText: t('common.actions.confirm'),
          cancelButtonText: t('common.actions.cancel'),
        }
      )
    } catch {
      return
    }
  }

  loadingActionCode.value = action.actionCode
  try {
    const result = await dynamicApi.executeAction(props.objectCode, props.recordId, action.actionCode)
    ElMessage.success(result?.message || t('common.messages.operationSuccess') || 'Success')
    emit('action-success', action.actionCode, result)

    if (result?.targetUrl && result?.navigateAfterSuccess !== false) {
      await router.push(result.targetUrl)
      return
    }

    await loadActions()
  } catch (error: any) {
    const message =
      error?.response?.data?.error?.message ||
      error?.response?.data?.detail ||
      error?.message ||
      t('common.messages.operationFailed')
    ElMessage.error(message)
    emit('action-error', action.actionCode, error)
  } finally {
    loadingActionCode.value = null
  }
}

watch(
  () => [props.objectCode, props.recordId],
  () => {
    loadActions()
  },
  { immediate: true }
)

defineExpose({
  reload: loadActions
})
</script>

<style scoped>
.object-action-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 8px 0 12px;
}
</style>
