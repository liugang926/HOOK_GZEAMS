<template>
  <el-dialog
    :model-value="modelValue"
    :title="promptTitle"
    width="520px"
    destroy-on-close
    append-to-body
    class="workbench-action-prompt-dialog"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div
      v-if="prompt?.message"
      class="workbench-action-prompt-dialog__message"
    >
      {{ prompt.message }}
    </div>

    <el-form
      v-if="prompt"
      label-position="top"
      class="workbench-action-prompt-dialog__form"
    >
      <el-form-item
        v-for="field in prompt.fields"
        :key="field.key"
        :label="field.label"
        :required="field.required"
      >
        <el-select
          v-if="field.type === 'select'"
          :model-value="values[field.key]"
          class="workbench-action-prompt-dialog__input"
          clearable
          @update:model-value="emit('set-value', field.key, $event)"
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
          :model-value="stringifyPromptValue(values[field.key])"
          type="date"
          class="workbench-action-prompt-dialog__input"
          :placeholder="field.placeholder"
          :value-format="field.valueFormat || 'YYYY-MM-DD'"
          @update:model-value="emit('set-value', field.key, $event)"
        />

        <el-input-number
          v-else-if="field.type === 'number'"
          :model-value="normalizeNumberPromptValue(values[field.key])"
          class="workbench-action-prompt-dialog__input"
          :placeholder="field.placeholder"
          :min="field.min"
          :max="field.max"
          :precision="field.precision"
          controls-position="right"
          @update:model-value="emit('set-value', field.key, $event)"
        />

        <el-input
          v-else
          :model-value="stringifyPromptValue(values[field.key])"
          :type="field.type === 'textarea' ? 'textarea' : 'text'"
          :rows="field.type === 'textarea' ? (field.rows || 4) : undefined"
          :placeholder="field.placeholder"
          @update:model-value="emit('set-value', field.key, $event)"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="workbench-action-prompt-dialog__actions">
        <el-button
          :disabled="loading"
          @click="emit('cancel')"
        >
          {{ prompt?.cancelButtonText || t('common.actions.cancel') }}
        </el-button>
        <el-button
          type="primary"
          :loading="loading"
          @click="emit('confirm')"
        >
          {{ prompt?.confirmButtonText || t('common.actions.confirm') }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { WorkbenchAction, WorkbenchPrompt } from './workbenchHelpers'

const props = defineProps<{
  modelValue: boolean
  action: WorkbenchAction | null
  prompt: WorkbenchPrompt | null
  values: Record<string, unknown>
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'set-value', key: string, value: unknown): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const { t } = useI18n()

const promptTitle = computed(() => {
  return props.prompt?.title || String(props.action?.code || '') || t('common.dialog.confirmTitle')
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
</script>

<style scoped>
.workbench-action-prompt-dialog__message {
  margin-bottom: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.workbench-action-prompt-dialog__form {
  margin-bottom: 4px;
}

.workbench-action-prompt-dialog__input {
  width: 100%;
}

.workbench-action-prompt-dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
