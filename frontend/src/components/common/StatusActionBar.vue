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

  <el-dialog
    v-model="promptVisible"
    :title="activePromptTitle"
    width="520px"
    destroy-on-close
    append-to-body
    class="status-action-bar__dialog"
  >
    <div
      v-if="activePrompt?.message"
      class="status-action-bar__prompt-message"
    >
      {{ activePrompt.message }}
    </div>

    <el-form
      v-if="activePrompt"
      label-position="top"
      class="status-action-bar__prompt-form"
    >
      <el-form-item
        v-for="field in activePrompt.fields"
        :key="field.key"
        :label="field.label"
        :required="field.required"
      >
        <el-select
          v-if="field.type === 'select'"
          :model-value="promptValues[field.key]"
          class="status-action-bar__input"
          clearable
          @update:model-value="setPromptValue(field.key, $event)"
        >
          <el-option
            v-for="option in field.options || []"
            :key="String(option.value)"
            :label="option.label"
            :value="option.value"
          />
        </el-select>

        <el-date-picker
          v-else-if="field.type === 'date'"
          :model-value="stringifyPromptValue(promptValues[field.key])"
          type="date"
          class="status-action-bar__input"
          :placeholder="field.placeholder"
          :value-format="field.valueFormat || 'YYYY-MM-DD'"
          @update:model-value="setPromptValue(field.key, $event)"
        />

        <el-input-number
          v-else-if="field.type === 'number'"
          :model-value="normalizeNumberPromptValue(promptValues[field.key])"
          class="status-action-bar__input"
          :placeholder="field.placeholder"
          :min="field.min"
          :max="field.max"
          :precision="field.precision"
          controls-position="right"
          @update:model-value="setPromptValue(field.key, $event)"
        />

        <el-input
          v-else
          :model-value="stringifyPromptValue(promptValues[field.key])"
          :type="field.type === 'textarea' ? 'textarea' : 'text'"
          :rows="field.type === 'textarea' ? (field.rows || 4) : undefined"
          :placeholder="field.placeholder"
          @update:model-value="setPromptValue(field.key, $event)"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="status-action-bar__dialog-actions">
        <el-button @click="closePromptDialog">
          {{ activePrompt?.cancelButtonText || t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="loadingKey === activeAction?.key"
          @click="confirmPromptAction"
        >
          {{ activePrompt?.confirmButtonText || t('common.actions.confirm') }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'

export interface StatusActionExecutionContext {
  values: Record<string, unknown>
}

export interface StatusActionPromptFieldOption {
  label: string
  value: string | number | boolean
}

export interface StatusActionPromptField {
  key: string
  label: string
  type?: 'text' | 'textarea' | 'select' | 'date' | 'number'
  placeholder?: string
  required?: boolean
  rows?: number
  defaultValue?: string | number | boolean | null
  options?: StatusActionPromptFieldOption[]
  valueFormat?: string
  min?: number
  max?: number
  precision?: number
}

export interface StatusActionPrompt {
  title?: string
  message?: string
  confirmButtonText?: string
  cancelButtonText?: string
  fields: StatusActionPromptField[]
}

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
  /** Optional input prompt shown before executing the action. */
  prompt?: StatusActionPrompt
  /** API call function. Should return a Promise. */
  apiCall: (context?: StatusActionExecutionContext) => Promise<unknown>
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
const promptVisible = ref(false)
const activeAction = ref<StatusAction | null>(null)
const promptValues = ref<Record<string, unknown>>({})

const visibleActions = computed(() =>
  props.actions.filter(a => a.visibleWhen(props.status))
)

const activePrompt = computed(() => activeAction.value?.prompt || null)
const activePromptTitle = computed(() => {
  return activePrompt.value?.title || activeAction.value?.label || t('common.dialog.confirmTitle')
})

const stringifyPromptValue = (value: unknown) => {
  if (typeof value === 'string') return value
  if (value === null || value === undefined) return ''
  return String(value)
}

const normalizeNumberPromptValue = (value: unknown) => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : undefined
  }
  return undefined
}

const setPromptValue = (key: string, value: unknown) => {
  promptValues.value = {
    ...promptValues.value,
    [key]: value,
  }
}

const resetPromptState = () => {
  promptVisible.value = false
  activeAction.value = null
  promptValues.value = {}
}

const closePromptDialog = () => {
  if (loadingKey.value) return
  resetPromptState()
}

const buildPromptDefaults = (action: StatusAction) => {
  const fields = action.prompt?.fields || []
  return fields.reduce<Record<string, unknown>>((accumulator, field) => {
    accumulator[field.key] = field.defaultValue ?? ''
    return accumulator
  }, {})
}

const validatePromptFields = (action: StatusAction) => {
  const fields = action.prompt?.fields || []
  for (const field of fields) {
    if (!field.required) continue
    const value = promptValues.value[field.key]
    if (typeof value === 'string' && value.trim()) continue
    if (value !== null && value !== undefined && value !== '') continue
    ElMessage.warning(t('common.messages.formValidationFailed'))
    return false
  }
  return true
}

const executeAction = async (action: StatusAction, values: Record<string, unknown> = {}) => {
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
      return
    }
  }

  loadingKey.value = action.key
  try {
    const result = await action.apiCall({ values })
    ElMessage.success(t('common.messages.operationSuccess') || 'Success')
    emit('action-success', action.key, result)
    if (activeAction.value?.key === action.key) {
      resetPromptState()
    }
  } catch (error: any) {
    const msg = error?.response?.data?.detail || error?.message || t('common.messages.operationFailed')
    ElMessage.error(msg)
    emit('action-error', action.key, error)
  } finally {
    loadingKey.value = null
  }
}

const confirmPromptAction = async () => {
  if (!activeAction.value) return
  if (!validatePromptFields(activeAction.value)) return
  await executeAction(activeAction.value, { ...promptValues.value })
}

const handleAction = async (action: StatusAction) => {
  if (action.prompt?.fields?.length) {
    activeAction.value = action
    promptValues.value = buildPromptDefaults(action)
    promptVisible.value = true
    return
  }

  await executeAction(action)
}
</script>

<style scoped>
.status-action-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 0;
}

.status-action-bar__prompt-message {
  margin-bottom: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.status-action-bar__prompt-form {
  margin-bottom: 4px;
}

.status-action-bar__input {
  width: 100%;
}

.status-action-bar__dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
